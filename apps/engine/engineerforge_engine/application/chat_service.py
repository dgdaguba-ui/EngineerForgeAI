"""ChatService — the AI-chat use case. Depends only on the AIProvider port."""

from __future__ import annotations

from ..domain.ai import ChatRequest, ChatResponse, ProviderHealth
from ..domain.errors import InvalidRequestError
from ..ports.ai_provider import AIProvider
from .ai_tools import AiToolbox


class ChatService:
    def __init__(self, provider: AIProvider, toolbox: AiToolbox | None = None) -> None:
        self._provider = provider
        self._toolbox = toolbox

    @property
    def provider_name(self) -> str:
        return self._provider.name

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not request.messages:
            raise InvalidRequestError("messages must not be empty")
        return await self._provider.chat(request, self._toolbox)

    async def provider_health(self) -> ProviderHealth:
        return await self._provider.health()
