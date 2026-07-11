"""AI endpoints. Everything routes through the AIProvider port via ChatService."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...application.chat_service import ChatService
from ...domain.ai import ChatRequest, ChatResponse
from ..deps import get_chat_service, require_auth

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(require_auth)])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    return await service.chat(request)
