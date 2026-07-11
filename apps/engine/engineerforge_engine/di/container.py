"""Composition root: wire concrete adapters into application services.

Constructed once per app (in the FastAPI lifespan). Everything downstream
receives its dependencies from here, so tests can build a Container with a
fake provider and exercise the whole stack without network or credentials.
"""

from __future__ import annotations

from ..adapters.ai.registry import build_ai_provider
from ..adapters.blender.local import LocalBlenderAdapter
from ..application.blender_service import BlenderService
from ..application.chat_service import ChatService
from ..application.convert_service import ConvertService
from ..config import Settings, get_settings
from ..ports.ai_provider import AIProvider
from ..ports.blender import BlenderPort


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        self.ai_provider: AIProvider = build_ai_provider(self.settings)
        self.chat_service: ChatService = ChatService(self.ai_provider)
        self.blender: BlenderPort = LocalBlenderAdapter(
            path_override=self.settings.blender_path
        )
        self.blender_service: BlenderService = BlenderService(self.blender)
        self.convert_service: ConvertService = ConvertService(self.blender)
