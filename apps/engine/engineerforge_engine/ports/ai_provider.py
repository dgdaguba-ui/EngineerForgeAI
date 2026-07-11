"""The AIProvider port. Business logic depends on this, never on a vendor SDK."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.ai import ChatRequest, ChatResponse, ProviderHealth


class AIProvider(ABC):
    """A pluggable AI backend (Claude, OpenAI, Ollama, Stub, …).

    Implementations must be safe to construct without network access; any
    connection/credential work happens lazily inside :meth:`chat`/:meth:`health`
    so the engine boots and stays usable offline.
    """

    #: Stable short identifier, e.g. "claude", "stub".
    name: str = "unknown"

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Produce a single assistant response for the given request."""

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Report whether this provider is usable right now (key present, reachable)."""
