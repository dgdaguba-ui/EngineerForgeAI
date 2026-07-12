"""Material & printer catalog + compatibility analysis."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...application import compat_service
from ...domain.materials import CompatibilityReport, Material, PrinterProfile
from ...services.catalog import load_materials, load_printers
from ..deps import require_auth

router = APIRouter(tags=["catalog"], dependencies=[Depends(require_auth)])


@router.get("/materials", response_model=list[Material], response_model_by_alias=True)
def materials() -> list[Material]:
    return list(load_materials())


@router.get("/printers", response_model=list[PrinterProfile], response_model_by_alias=True)
def printers() -> list[PrinterProfile]:
    return list(load_printers())


class CompatibilityRequest(BaseModel):
    materialIds: list[str]


@router.post(
    "/materials/compatibility",
    response_model=CompatibilityReport,
    response_model_by_alias=True,
)
def compatibility(request: CompatibilityRequest) -> CompatibilityReport:
    return compat_service.analyze(request.materialIds)
