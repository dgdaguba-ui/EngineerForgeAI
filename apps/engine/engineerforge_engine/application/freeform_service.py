"""FreeformService — the text-to-CAD use case.

Validates an AI-authored CadQuery script (static guard), runs it in the
sandboxed runner, and keeps the resulting mesh geometry in the session store.
Freeform parts are **non-parametric**: unlike template parts they carry no
Feature Program, so they load into the viewport as plain meshes and are not
editable in the Parameters panel — the trade-off for unbounded geometry.

The mass/volume/bbox still originate from the exact B-rep the script produced
(never from the model's text), preserving ADR-0003 for the freeform path too.
"""

from __future__ import annotations

import shutil
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

import trimesh
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from ..domain.errors import InvalidRequestError
from ..domain.feature_program import MassProps, RawMesh
from ..domain.script_guard import validate_script
from ..ports.freeform_runner import FreeformRunnerPort

MESH_EXPORT_FORMATS = frozenset({"stl", "3mf", "obj", "glb", "ply"})
EXPORT_FORMATS = MESH_EXPORT_FORMATS | {"step"}


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class FreeformDetail(_CamelModel):
    part_id: str
    name: str
    mesh: RawMesh
    mass_props: MassProps
    code: str
    warnings: list[str] = []
    kind: str = "freeform"


class FreeformExportResult(_CamelModel):
    part_id: str
    format: str
    dst_path: str
    size_bytes: int


@dataclass
class _FreeformRecord:
    part_id: str
    name: str
    mesh: RawMesh
    mass_props: MassProps
    code: str
    step_path: str


class FreeformService:
    def __init__(self, runner: FreeformRunnerPort) -> None:
        self._runner = runner
        self._parts: dict[str, _FreeformRecord] = {}
        self._lock = threading.Lock()

    def generate(
        self, code: str, name: str | None = None, timeout_s: float = 20.0
    ) -> FreeformDetail:
        validate_script(code)  # static guard first — reject obvious escapes pre-exec
        result = self._runner.run(code, timeout_s=timeout_s)
        record = _FreeformRecord(
            part_id=uuid.uuid4().hex[:12],
            name=(name or "Freeform Part").strip() or "Freeform Part",
            mesh=result.mesh,
            mass_props=result.mass_props,
            code=code,
            step_path=result.step_path,
        )
        with self._lock:
            self._parts[record.part_id] = record
        return self._detail(record)

    def get(self, part_id: str) -> FreeformDetail:
        return self._detail(self._get_record(part_id))

    def export(self, part_id: str, format_name: str, dst_path: str) -> FreeformExportResult:
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

        if fmt == "step":
            shutil.copyfile(record.step_path, dst)
        else:
            self._as_trimesh(record).export(str(dst))
        if not dst.exists():
            raise InvalidRequestError(f"export produced no file at {dst}")
        return FreeformExportResult(
            part_id=part_id, format=fmt, dst_path=str(dst), size_bytes=dst.stat().st_size
        )

    # ── internals ─────────────────────────────────────────────────────────────

    def _get_record(self, part_id: str) -> _FreeformRecord:
        with self._lock:
            record = self._parts.get(part_id)
        if record is None:
            raise InvalidRequestError(f"unknown freeform part id: {part_id}")
        return record

    def _as_trimesh(self, record: _FreeformRecord) -> trimesh.Trimesh:
        import base64

        import numpy as np

        mesh = record.mesh
        positions = np.frombuffer(base64.b64decode(mesh.positions_b64), dtype="<f4").reshape(-1, 3)
        indices = np.frombuffer(base64.b64decode(mesh.indices_b64), dtype="<u4").reshape(-1, 3)
        return trimesh.Trimesh(vertices=positions, faces=indices, process=False)

    def _detail(self, record: _FreeformRecord) -> FreeformDetail:
        return FreeformDetail(
            part_id=record.part_id,
            name=record.name,
            mesh=record.mesh,
            mass_props=record.mass_props,
            code=record.code,
        )
