"""Blender integration endpoints. Local, trusted-session operations
(bearer-token gated like every mutating endpoint)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ...application.blender_service import BlenderService
from ...di.container import Container
from ...domain.blender import BlenderStatus, LaunchResult, ScriptResult
from ..deps import get_container, require_auth

router = APIRouter(prefix="/blender", tags=["blender"], dependencies=[Depends(require_auth)])


def get_blender_service(container: Container = Depends(get_container)) -> BlenderService:
    return container.blender_service


@router.get("/status", response_model=BlenderStatus)
async def status(service: BlenderService = Depends(get_blender_service)) -> BlenderStatus:
    return service.status()


class LaunchRequest(BaseModel):
    file: str | None = None


@router.post("/launch", response_model=LaunchResult)
async def launch(
    request: LaunchRequest,
    service: BlenderService = Depends(get_blender_service),
) -> LaunchResult:
    return service.launch(request.file)


class RunScriptRequest(BaseModel):
    code: str
    args: list[str] = Field(default_factory=list)
    timeout_sec: float = Field(default=120, alias="timeoutSec")

    model_config = {"populate_by_name": True}


@router.post("/run-script", response_model=ScriptResult)
async def run_script(
    request: RunScriptRequest,
    service: BlenderService = Depends(get_blender_service),
) -> ScriptResult:
    return service.run_script(request.code, args=request.args, timeout_sec=request.timeout_sec)
