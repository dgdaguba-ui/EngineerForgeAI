"""Print preparation: usage/purge estimates + multi-material 3MF export.

Estimate and export accept either a mesh file path OR a live parametric
part id — parametric parts use exact B-rep metrics (no temp files).
"""

from __future__ import annotations

from pathlib import Path

import trimesh
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ...application.parts_service import PartsService
from ...application.print_service import (
    PurgeEstimate,
    UsageEstimate,
    estimate_from_metrics,
    estimate_purge,
    estimate_usage,
)
from ...di.container import Container
from ...domain.errors import InvalidRequestError
from ...services.mesh_io import load_mesh
from ...services.threemf import Part3MF, write_3mf
from ..deps import get_container, require_auth

router = APIRouter(tags=["print"], dependencies=[Depends(require_auth)])


def get_parts_service(container: Container = Depends(get_container)) -> PartsService:
    return container.parts_service


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EstimateRequest(_CamelModel):
    mesh_path: str | None = None
    part_id: str | None = None
    material_id: str
    infill: float = 0.2
    printer_id: str | None = None


@router.post("/print/estimate", response_model=UsageEstimate, response_model_by_alias=True)
def print_estimate(
    request: EstimateRequest,
    parts: PartsService = Depends(get_parts_service),
) -> UsageEstimate:
    if (request.mesh_path is None) == (request.part_id is None):
        raise InvalidRequestError("provide exactly one of meshPath or partId")
    if request.part_id is not None:
        detail = parts.get(request.part_id)
        props = detail.compiled.mass_props
        return estimate_from_metrics(
            props.volume_mm3,
            props.bbox_mm,
            watertight=True,  # B-rep solids are closed by construction
            material_id=request.material_id,
            infill=request.infill,
            printer_id=request.printer_id,
        )
    assert request.mesh_path is not None
    return estimate_usage(
        request.mesh_path,
        request.material_id,
        infill=request.infill,
        printer_id=request.printer_id,
    )


class PurgeRequest(_CamelModel):
    printer_id: str
    material_ids: list[str]
    height_mm: float
    layer_height_mm: float = 0.2
    changes_per_layer_factor: float = 0.5
    tool_changes: int | None = None


@router.post("/print/purge-estimate", response_model=PurgeEstimate, response_model_by_alias=True)
def purge_estimate(request: PurgeRequest) -> PurgeEstimate:
    return estimate_purge(
        request.printer_id,
        request.material_ids,
        height_mm=request.height_mm,
        layer_height_mm=request.layer_height_mm,
        changes_per_layer_factor=request.changes_per_layer_factor,
        tool_changes_override=request.tool_changes,
    )


class ExportPart(_CamelModel):
    mesh_path: str | None = None
    part_id: str | None = None
    name: str
    color_hex: str | None = None
    material_name: str | None = None


class Export3mfRequest(_CamelModel):
    parts: list[ExportPart] = Field(min_length=1)
    dst_path: str


class Export3mfResult(_CamelModel):
    dst_path: str
    parts: int
    size_bytes: int


@router.post("/export/3mf", response_model=Export3mfResult, response_model_by_alias=True)
def export_3mf(
    request: Export3mfRequest,
    parts_service: PartsService = Depends(get_parts_service),
) -> Export3mfResult:
    """Write a multi-object 3MF with per-part material/color — the container
    FlashPrint (and Orca/Bambu/Prusa) opens for multi-material jobs.
    Parts may mix imported mesh files and live parametric parts."""
    parts: list[Part3MF] = []
    for part in request.parts:
        if (part.mesh_path is None) == (part.part_id is None):
            raise InvalidRequestError(
                f"part {part.name!r}: provide exactly one of meshPath or partId"
            )
        mesh: trimesh.Trimesh
        if part.part_id is not None:
            mesh = parts_service.mesh_of(part.part_id)
        else:
            assert part.mesh_path is not None
            mesh = load_mesh(part.mesh_path)
        parts.append(
            Part3MF(
                name=part.name,
                vertices=[tuple(v) for v in mesh.vertices.tolist()],
                triangles=[tuple(f) for f in mesh.faces.tolist()],
                color_hex=part.color_hex,
                material_name=part.material_name,
            )
        )
    dst = Path(request.dst_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_3mf(dst, parts)
    return Export3mfResult(
        dst_path=str(dst), parts=len(parts), size_bytes=dst.stat().st_size
    )
