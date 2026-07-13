"""AI endpoints. Everything routes through the AIProvider port via ChatService."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

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


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Stream a chat turn as newline-delimited JSON ``ChatStreamEvent``s.

    Request-scoped one-way streaming over chunked HTTP (not a WebSocket): it
    reuses the bearer-token header, CORS rules, and error envelope of every
    other endpoint. Validation errors raise here (normal error envelope);
    provider failures mid-stream arrive as a terminal ``error`` event.
    """
    events = service.stream(request)  # validates synchronously before streaming

    async def body() -> AsyncIterator[str]:
        async for event in events:
            yield event.model_dump_json(by_alias=True) + "\n"

    return StreamingResponse(body(), media_type="application/x-ndjson")
