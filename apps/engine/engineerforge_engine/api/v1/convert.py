"""Mesh conversion endpoint (STL/OBJ/PLY/GLB/GLTF/3MF native; FBX via Blender)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ...application.convert_service import ConvertResult, ConvertService
from ...di.container import Container
from ..deps import get_container, require_auth

router = APIRouter(tags=["convert"], dependencies=[Depends(require_auth)])


def get_convert_service(container: Container = Depends(get_container)) -> ConvertService:
    return container.convert_service


class ConvertRequest(BaseModel):
    src_path: str = Field(alias="srcPath")
    dst_path: str = Field(alias="dstPath")
    timeout_sec: float = Field(default=180, alias="timeoutSec")

    model_config = {"populate_by_name": True}


@router.post("/convert", response_model=ConvertResult, response_model_by_alias=True)
def convert(
    request: ConvertRequest,
    service: ConvertService = Depends(get_convert_service),
) -> ConvertResult:
    return service.convert(request.src_path, request.dst_path, timeout_sec=request.timeout_sec)
