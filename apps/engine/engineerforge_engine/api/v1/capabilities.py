"""Capability discovery — what this engine build can do.

Grows as milestones land (cad, mesh, fea, slicer, blender). The renderer
negotiates against this instead of hardcoding assumptions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...application.chat_service import ChatService
from ...config import Settings
from ..deps import get_chat_service, get_settings_dep

router = APIRouter(tags=["meta"])


@router.get("/capabilities")
async def capabilities(
    settings: Settings = Depends(get_settings_dep),
    chat: ChatService = Depends(get_chat_service),
) -> dict[str, object]:
    return {
        "version": settings.version,
        "ai": {
            "active_provider": chat.provider_name,
            "providers": ["stub", "claude"],
            "planned_providers": ["openai", "ollama"],
            "model": settings.ai_model,
        },
        "features": {
            "ai_chat": True,
            # roadmap features — surfaced as they are implemented
            "cad_kernel": False,
            "mesh_repair": False,
            "fea": False,
            "slicer_export": False,
            "blender_bridge": False,
        },
    }
