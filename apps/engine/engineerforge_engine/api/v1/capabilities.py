"""Capability discovery — what this engine build can do.

Grows as milestones land (cad, mesh, fea, slicer, blender). The renderer
negotiates against this instead of hardcoding assumptions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...application.blender_service import BlenderService
from ...application.chat_service import ChatService
from ...application.convert_service import NATIVE_FORMATS, SUPPORTED_FORMATS
from ...config import Settings
from ..deps import get_chat_service, get_container, get_settings_dep

router = APIRouter(tags=["meta"])


def _blender_service(request: Request) -> BlenderService:
    return get_container(request).blender_service


@router.get("/capabilities")
def capabilities(
    settings: Settings = Depends(get_settings_dep),
    chat: ChatService = Depends(get_chat_service),
    blender: BlenderService = Depends(_blender_service),
) -> dict[str, object]:
    blender_status = blender.status()
    return {
        "version": settings.version,
        "ai": {
            "active_provider": chat.provider_name,
            "providers": ["stub", "claude"],
            "planned_providers": ["openai", "ollama"],
            "model": settings.ai_model,
        },
        "formats": {
            "native": sorted(NATIVE_FORMATS),
            "with_blender": sorted(SUPPORTED_FORMATS),
            "cad_pending_phase1": ["step", "iges", "dxf", "svg"],
        },
        "features": {
            "ai_chat": True,
            "mesh_convert": True,
            "blender_bridge": blender_status.detected,
            "material_catalog": True,
            "printer_profiles": True,
            "material_compatibility": True,
            "print_estimate": True,
            "multi_material_3mf_export": True,
            "cad_kernel": True,
            "parametric_templates": True,
            "step_export": True,
            # roadmap features — surfaced as they are implemented
            "mesh_repair": False,
            "fea": False,
            "slicer_export": False,
        },
        "blender": blender_status.model_dump(),
    }
