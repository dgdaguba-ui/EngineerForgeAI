"""Liveness/readiness endpoint."""

from __future__ import annotations

import sys

from fastapi import APIRouter, Depends

from ...application.chat_service import ChatService
from ...config import Settings
from ..deps import get_chat_service, get_settings_dep

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health(
    settings: Settings = Depends(get_settings_dep),
    chat: ChatService = Depends(get_chat_service),
) -> dict[str, object]:
    provider = await chat.provider_health()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
        "python": sys.version.split()[0],
        "provider": provider.model_dump(),
    }
