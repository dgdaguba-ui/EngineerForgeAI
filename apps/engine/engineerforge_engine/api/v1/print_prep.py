"""Print preparation: usage/purge estimates + multi-material 3MF export."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ...application.print_service import (
    PurgeEstimate,
    UsageEstimate,
    estimate_purge,
    estimate_usage,
)
from ...services.mesh_io import load_mesh
from ...services.threemf import Part3MF, write_3mf
from ..deps import require_auth

router = APIRouter(tags=["print"], dependencies=[Depends(require_auth)])


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EstimateRequest(_CamelModel):
    mesh_path: str
    material_id: str
    infill: float = 0.2
    printer_id: str | None = None


@router.post("/print/estimate", response_model=UsageEstimate, response_model_by_alias=True)
def print_estimate(request: EstimateRequest) -> UsageEstimate:
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
    mesh_path: str
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
def export_3mf(request: Export3mfRequest) -> Export3mfResult:
    """Write a multi-object 3MF with per-part material/color — the container
    FlashPrint (and Orca/Bambu/Prusa) opens for multi-material jobs."""
    parts: list[Part3MF] = []
    for part in request.parts:
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
