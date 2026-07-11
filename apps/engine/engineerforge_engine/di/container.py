"""Composition root: wire concrete adapters into application services.

Constructed once per app (in the FastAPI lifespan). Everything downstream
receives its dependencies from here, so tests can build a Container with a
fake provider and exercise the whole stack without network or credentials.
"""

from __future__ import annotations

from ..adapters.ai.registry import build_ai_provider
from ..application.chat_service import ChatService
from ..config import Settings, get_settings
from ..ports.ai_provider import AIProvider


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        self.ai_provider: AIProvider = build_ai_provider(self.settings)
        self.chat_service: ChatService = ChatService(self.ai_provider)
