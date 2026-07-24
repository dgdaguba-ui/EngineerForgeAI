"""Composition root: wire concrete adapters into application services.

Constructed once per app (in the FastAPI lifespan). Everything downstream
receives its dependencies from here, so tests can build a Container with a
fake provider and exercise the whole stack without network or credentials.
"""

from __future__ import annotations

from ..adapters.ai.registry import build_ai_provider
from ..adapters.blender.local import LocalBlenderAdapter
from ..adapters.cad.cadquery_freeform import CadQueryFreeformRunner
from ..adapters.cad.cadquery_kernel import CadQueryKernel
from ..application.ai_tools import AiToolbox
from ..application.blender_service import BlenderService
from ..application.chat_service import ChatService
from ..application.convert_service import ConvertService
from ..application.freeform_service import FreeformService
from ..application.parts_service import PartsService
from ..config import Settings, get_settings
from ..ports.ai_provider import AIProvider
from ..ports.blender import BlenderPort
from ..ports.cad_kernel import CadKernelPort
from ..ports.freeform_runner import FreeformRunnerPort
from ..templates import default_registry


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        self.blender: BlenderPort = LocalBlenderAdapter(
            path_override=self.settings.blender_path
        )
        self.blender_service: BlenderService = BlenderService(self.blender)
        self.convert_service: ConvertService = ConvertService(self.blender)
        # CAD kernel imports lazily inside compile (heavy OCP import).
        self.cad_kernel: CadKernelPort = CadQueryKernel()
        self.templates = default_registry()
        self.parts_service: PartsService = PartsService(self.cad_kernel, self.templates)
        # Freeform (text-to-CAD): sandboxed CadQuery script execution.
        self.freeform_runner: FreeformRunnerPort = CadQueryFreeformRunner()
        self.freeform_service: FreeformService = FreeformService(self.freeform_runner)
        # AI: provider + the engine capabilities it may orchestrate (ADR-0003)
        self.ai_provider: AIProvider = build_ai_provider(self.settings)
        self.ai_toolbox: AiToolbox = AiToolbox(self.parts_service, self.freeform_service)
        self.chat_service: ChatService = ChatService(self.ai_provider, self.ai_toolbox)
