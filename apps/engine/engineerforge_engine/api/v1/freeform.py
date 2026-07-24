"""Freeform (text-to-CAD) API — sandboxed CadQuery script → mesh geometry.

Executes model- or user-authored scripts through the static guard + sandboxed
runner. Produces non-parametric mesh parts (no Feature Program), complementing
the template/IR path for geometry the templates cannot express.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ...application.freeform_service import (
    FreeformDetail,
    FreeformExportResult,
    FreeformService,
)
from ...di.container import Container
from ..deps import get_container, require_auth

router = APIRouter(prefix="/freeform", tags=["freeform"], dependencies=[Depends(require_auth)])


def get_freeform_service(container: Container = Depends(get_container)) -> FreeformService:
    return container.freeform_service


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class GenerateRequest(_CamelModel):
    code: str
    name: str | None = None


@router.post("", response_model=FreeformDetail, response_model_by_alias=True)
def generate(
    request: GenerateRequest,
    service: FreeformService = Depends(get_freeform_service),
) -> FreeformDetail:
    return service.generate(request.code, request.name)


@router.get("/{part_id}", response_model=FreeformDetail, response_model_by_alias=True)
def get_freeform(
    part_id: str, service: FreeformService = Depends(get_freeform_service)
) -> FreeformDetail:
    return service.get(part_id)


class ExportRequest(_CamelModel):
    format: str
    dst_path: str = Field(alias="dstPath")


@router.post(
    "/{part_id}/export", response_model=FreeformExportResult, response_model_by_alias=True
)
def export_freeform(
    part_id: str,
    request: ExportRequest,
    service: FreeformService = Depends(get_freeform_service),
) -> FreeformExportResult:
    return service.export(part_id, request.format, request.dst_path)
