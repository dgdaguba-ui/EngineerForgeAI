"""Parts service — the parametric-part use cases.

Owns the in-session part store: create from template or raw program, live
parameter patches (validate → recompile), exports. The `.efproj` document is
the durable home of a program (saved by the desktop app); this store is the
engine's working set for the current session.
"""

from __future__ import annotations

import tempfile
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import trimesh
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from ..domain.errors import InvalidRequestError
from ..domain.expressions import ExpressionError, evaluate
from ..domain.feature_program import CompiledPart, FeatureProgram, ParamDiffEntry, Parameter
from ..ports.cad_kernel import CadKernelPort
from ..services.catalog import material_by_id
from ..services.threemf import Part3MF, write_3mf
from ..templates import PartTemplate, TemplateRegistry

MESH_EXPORT_FORMATS = frozenset({"3mf", "obj", "glb", "ply"})
KERNEL_EXPORT_FORMATS = frozenset({"step", "stl"})
EXPORT_FORMATS = KERNEL_EXPORT_FORMATS | MESH_EXPORT_FORMATS


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TemplateInfo(_CamelModel):
    id: str
    name: str
    description: str
    parameters: list[Parameter]


class PartDetail(_CamelModel):
    part_id: str
    name: str
    template_id: str | None
    program: FeatureProgram
    compiled: CompiledPart
    material_id: str | None


class ExportResult(_CamelModel):
    part_id: str
    format: str
    dst_path: str
    size_bytes: int


@dataclass
class _PartRecord:
    part_id: str
    template_id: str | None
    program: FeatureProgram
    compiled: CompiledPart
    native_solid: Any
    material_id: str | None


class PartsService:
    def __init__(self, kernel: CadKernelPort, templates: TemplateRegistry) -> None:
        self._kernel = kernel
        self._templates = templates
        self._parts: dict[str, _PartRecord] = {}
        self._lock = threading.Lock()

    # ── templates ─────────────────────────────────────────────────────────────

    def list_templates(self) -> list[TemplateInfo]:
        return [
            TemplateInfo(
                id=t.id, name=t.name, description=t.description, parameters=t.parameters
            )
            for t in self._templates.all()
        ]

    # ── creation ──────────────────────────────────────────────────────────────

    def create_from_template(
        self,
        template_id: str,
        values: dict[str, float] | None = None,
        material_id: str | None = None,
    ) -> PartDetail:
        template = self._templates.get(template_id)
        if template is None:
            raise InvalidRequestError(f"unknown template: {template_id}")
        overrides = dict(values or {})
        self._validate_values(template.parameters, overrides, allow_partial=True)
        program = template.build(overrides)
        return self._register(program, template, material_id)

    def compile_program(
        self, program: FeatureProgram, material_id: str | None = None
    ) -> PartDetail:
        """Compile a caller-provided program (e.g. reopened from a project)."""
        template = (
            self._templates.get(program.provenance.get("generator", "").removeprefix("template:"))
            if program.provenance
            else None
        )
        return self._register(program, template, material_id)

    # ── editing ───────────────────────────────────────────────────────────────

    def patch_params(
        self,
        part_id: str,
        values: dict[str, float],
        material_id: str | None = None,
    ) -> PartDetail:
        record = self._get_record(part_id)
        if not values and material_id is None:
            raise InvalidRequestError("nothing to update")

        program = record.program
        self._validate_values(program.parameters, values, allow_partial=True)

        updated_params = [
            p.model_copy(update={"value": float(values.get(p.id, p.value))})
            for p in program.parameters
        ]
        new_program = program.model_copy(update={"parameters": updated_params})
        template = self._templates.get(record.template_id) if record.template_id else None
        compiled, native = self._compile_with_checks(new_program, template)
        new_material = material_id if material_id is not None else record.material_id
        with self._lock:
            record.program = new_program
            record.compiled = self._with_mass(compiled, new_program, new_material)
            record.native_solid = native
            record.material_id = new_material
        return self._detail(record)

    def preview_params(self, part_id: str, values: dict[str, float]) -> list[ParamDiffEntry]:
        """Validate a proposed parameter edit without applying it.

        Used for AI-proposed edits awaiting user review (M2.2): the part is
        never mutated or recompiled here. No-op entries (new value equals the
        current value) are omitted from the returned diff.
        """
        record = self._get_record(part_id)
        program = record.program
        self._validate_values(program.parameters, values, allow_partial=True)
        diff: list[ParamDiffEntry] = []
        for param_id, raw in values.items():
            parameter = program.parameter_by_id(param_id)
            assert parameter is not None
            new_value = float(raw)
            if new_value == parameter.value:
                continue
            diff.append(
                ParamDiffEntry(
                    param_id=parameter.id,
                    label=parameter.label,
                    old_value=parameter.value,
                    new_value=new_value,
                    unit=parameter.unit,
                )
            )
        return diff

    def get(self, part_id: str) -> PartDetail:
        return self._detail(self._get_record(part_id))

    # ── export ────────────────────────────────────────────────────────────────

    def export(self, part_id: str, format_name: str, dst_path: str) -> ExportResult:
        record = self._get_record(part_id)
        fmt = format_name.lower().lstrip(".")
        if fmt not in EXPORT_FORMATS:
            raise InvalidRequestError(
                f"unsupported export format {fmt!r}; supported: {', '.join(sorted(EXPORT_FORMATS))}"
            )
        dst = Path(dst_path)
        if dst.suffix.lower().lstrip(".") != fmt:
            dst = dst.with_suffix(f".{fmt}")
        dst.parent.mkdir(parents=True, exist_ok=True)

        if fmt in KERNEL_EXPORT_FORMATS:
            self._kernel.export_solid(record.native_solid, str(dst))
        else:
            mesh = self._as_trimesh(record)
            if fmt == "3mf":
                material = material_by_id(record.material_id) if record.material_id else None
                write_3mf(
                    dst,
                    [
                        Part3MF(
                            name=record.program.name,
                            vertices=[tuple(v) for v in mesh.vertices.tolist()],
                            triangles=[tuple(f) for f in mesh.faces.tolist()],
                            color_hex=material.color_hex if material else None,
                            material_name=material.name if material else None,
                        )
                    ],
                )
            else:
                mesh.export(str(dst))
        if not dst.exists():
            raise InvalidRequestError(f"export produced no file at {dst}")
        return ExportResult(
            part_id=part_id, format=fmt, dst_path=str(dst), size_bytes=dst.stat().st_size
        )

    def export_to_temp_stl(self, part_id: str) -> str:
        """Write the part's current mesh to a temp STL (for Blender flows)."""
        record = self._get_record(part_id)
        tmp = Path(tempfile.mkdtemp(prefix="efc-part-")) / f"{part_id}.stl"
        self._kernel.export_solid(record.native_solid, str(tmp))
        return str(tmp)

    def mesh_of(self, part_id: str) -> trimesh.Trimesh:
        """The part's current tessellation as a Trimesh (for 3MF export etc.)."""
        return self._as_trimesh(self._get_record(part_id))

    # ── internals ─────────────────────────────────────────────────────────────

    def _register(
        self, program: FeatureProgram, template: PartTemplate | None, material_id: str | None
    ) -> PartDetail:
        if material_id is not None and material_by_id(material_id) is None:
            raise InvalidRequestError(f"unknown material id: {material_id}")
        compiled, native = self._compile_with_checks(program, template)
        record = _PartRecord(
            part_id=uuid.uuid4().hex[:12],
            template_id=template.id if template else None,
            program=program,
            compiled=self._with_mass(compiled, program, material_id),
            native_solid=native,
            material_id=material_id,
        )
        with self._lock:
            self._parts[record.part_id] = record
        return self._detail(record)

    def _compile_with_checks(
        self, program: FeatureProgram, template: PartTemplate | None
    ) -> tuple[CompiledPart, Any]:
        compiled, native = self._kernel.compile(program)
        if template:
            values = program.parameter_values()
            warnings = list(compiled.warnings)
            for check in template.checks:
                try:
                    if evaluate(check.expr, values) > 0:
                        warnings.append(check.message)
                except ExpressionError:
                    warnings.append(f"check {check.expr!r} could not be evaluated")
            compiled = compiled.model_copy(update={"warnings": warnings})
        return compiled, native

    def _with_mass(
        self, compiled: CompiledPart, program: FeatureProgram, material_id: str | None
    ) -> CompiledPart:
        if material_id is None:
            return compiled
        material = material_by_id(material_id)
        if material is None:
            raise InvalidRequestError(f"unknown material id: {material_id}")
        mass = compiled.mass_props.model_copy(
            update={
                "mass_g": round(compiled.mass_props.volume_cm3 * material.density_g_cm3, 2),
                "material_id": material.id,
            }
        )
        return compiled.model_copy(update={"mass_props": mass})

    def _get_record(self, part_id: str) -> _PartRecord:
        with self._lock:
            record = self._parts.get(part_id)
        if record is None:
            raise InvalidRequestError(f"unknown part id: {part_id}")
        return record

    def _as_trimesh(self, record: _PartRecord) -> trimesh.Trimesh:
        import base64

        import numpy as np

        mesh = record.compiled.mesh
        positions = np.frombuffer(base64.b64decode(mesh.positions_b64), dtype="<f4").reshape(
            -1, 3
        )
        indices = np.frombuffer(base64.b64decode(mesh.indices_b64), dtype="<u4").reshape(-1, 3)
        return trimesh.Trimesh(vertices=positions, faces=indices, process=False)

    def _detail(self, record: _PartRecord) -> PartDetail:
        return PartDetail(
            part_id=record.part_id,
            name=record.program.name,
            template_id=record.template_id,
            program=record.program,
            compiled=record.compiled,
            material_id=record.material_id,
        )

    def _validate_values(
        self,
        parameters: list[Parameter],
        values: dict[str, float],
        allow_partial: bool,
    ) -> None:
        known = {p.id: p for p in parameters}
        for param_id, raw in values.items():
            parameter = known.get(param_id)
            if parameter is None:
                raise InvalidRequestError(f"unknown parameter: {param_id}")
            error = parameter.clamp_check(float(raw))
            if error:
                raise InvalidRequestError(error)
        if not allow_partial:
            missing = set(known) - set(values)
            if missing:
                raise InvalidRequestError(f"missing parameters: {sorted(missing)}")
