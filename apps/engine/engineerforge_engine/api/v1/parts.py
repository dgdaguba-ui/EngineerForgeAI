"""Parametric parts API — templates, compile, live parameter patches, export."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ...application.parts_service import (
    ExportResult,
    PartDetail,
    PartsService,
    TemplateInfo,
)
from ...di.container import Container
from ...domain.feature_program import FeatureProgram
from ..deps import get_container, require_auth

router = APIRouter(tags=["parts"], dependencies=[Depends(require_auth)])


def get_parts_service(container: Container = Depends(get_container)) -> PartsService:
    return container.parts_service


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


@router.get("/templates", response_model=list[TemplateInfo], response_model_by_alias=True)
def list_templates(service: PartsService = Depends(get_parts_service)) -> list[TemplateInfo]:
    return service.list_templates()


class FromTemplateRequest(_CamelModel):
    template_id: str
    values: dict[str, float] = Field(default_factory=dict)
    material_id: str | None = None


@router.post("/parts/from-template", response_model=PartDetail, response_model_by_alias=True)
def create_from_template(
    request: FromTemplateRequest,
    service: PartsService = Depends(get_parts_service),
) -> PartDetail:
    return service.create_from_template(
        request.template_id, request.values, request.material_id
    )


class CompileRequest(_CamelModel):
    program: FeatureProgram
    material_id: str | None = None


@router.post("/parts/compile", response_model=PartDetail, response_model_by_alias=True)
def compile_program(
    request: CompileRequest,
    service: PartsService = Depends(get_parts_service),
) -> PartDetail:
    return service.compile_program(request.program, request.material_id)


@router.get("/parts/{part_id}", response_model=PartDetail, response_model_by_alias=True)
def get_part(part_id: str, service: PartsService = Depends(get_parts_service)) -> PartDetail:
    return service.get(part_id)


class PatchParamsRequest(_CamelModel):
    values: dict[str, float] = Field(default_factory=dict)
    material_id: str | None = None


@router.patch("/parts/{part_id}/params", response_model=PartDetail, response_model_by_alias=True)
def patch_params(
    part_id: str,
    request: PatchParamsRequest,
    service: PartsService = Depends(get_parts_service),
) -> PartDetail:
    return service.patch_params(part_id, request.values, request.material_id)


class ReorderFeaturesRequest(_CamelModel):
    feature_ids: list[str]


@router.post(
    "/parts/{part_id}/features/reorder",
    response_model=PartDetail,
    response_model_by_alias=True,
)
def reorder_features(
    part_id: str,
    request: ReorderFeaturesRequest,
    service: PartsService = Depends(get_parts_service),
) -> PartDetail:
    return service.reorder_features(part_id, request.feature_ids)


class ExportPartRequest(_CamelModel):
    format: str
    dst_path: str


@router.post(
    "/parts/{part_id}/export", response_model=ExportResult, response_model_by_alias=True
)
def export_part(
    part_id: str,
    request: ExportPartRequest,
    service: PartsService = Depends(get_parts_service),
) -> ExportResult:
    return service.export(part_id, request.format, request.dst_path)
