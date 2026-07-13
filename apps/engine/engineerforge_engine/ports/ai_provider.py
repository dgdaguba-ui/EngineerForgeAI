"""The AIProvider port. Business logic depends on this, never on a vendor SDK."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from ..domain.ai import ChatRequest, ChatResponse, ChatStreamEvent, ProviderHealth
from ..domain.errors import EngineError

if TYPE_CHECKING:
    from ..application.ai_tools import AiToolbox


class AIProvider(ABC):
    """A pluggable AI backend (Claude, OpenAI, Ollama, Stub, …).

    Implementations must be safe to construct without network access; any
    connection/credential work happens lazily inside :meth:`chat`/:meth:`health`
    so the engine boots and stays usable offline.
    """

    #: Stable short identifier, e.g. "claude", "stub".
    name: str = "unknown"

    @abstractmethod
    async def chat(self, request: ChatRequest, toolbox: AiToolbox | None = None) -> ChatResponse:
        """Produce a single assistant response.

        When a toolbox is provided, the provider may invoke engine tools
        (part creation/editing); every invocation is reported in
        ``ChatResponse.actions`` so the UI can react.
        """

    async def stream(
        self, request: ChatRequest, toolbox: AiToolbox | None = None
    ) -> AsyncIterator[ChatStreamEvent]:
        """Stream an assistant turn as :class:`ChatStreamEvent`s.

        The default implementation adapts the non-streaming :meth:`chat` into a
        single-chunk stream, so every provider streams out of the box; providers
        that can emit incremental tokens (Claude, Stub) override this. Errors are
        surfaced as a terminal ``error`` event rather than raised, so a partially
        consumed HTTP stream still closes cleanly with the failure reported.
        """
        try:
            response = await self.chat(request, toolbox)
        except EngineError as exc:
            yield ChatStreamEvent(
                type="error", error=exc.message, code=exc.code, retryable=exc.retryable
            )
            return
        if response.content:
            yield ChatStreamEvent(type="delta", text=response.content)
        for action in response.actions:
            yield ChatStreamEvent(type="action", action=action)
        yield ChatStreamEvent(type="done", response=response)

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Report whether this provider is usable right now (key present, reachable)."""
