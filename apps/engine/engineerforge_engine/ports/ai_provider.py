"""The AIProvider port. Business logic depends on this, never on a vendor SDK."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..domain.ai import ChatRequest, ChatResponse, ProviderHealth

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

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Report whether this provider is usable right now (key present, reachable)."""
