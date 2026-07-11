"""BlenderPort — the abstract Blender integration surface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.blender import BlenderInfo, LaunchResult, ScriptResult


class BlenderPort(ABC):
    """Local Blender integration: detection, launch, headless scripting,
    and mesh conversion for formats only Blender handles (e.g. FBX)."""

    @abstractmethod
    def detect(self) -> BlenderInfo | None:
        """Locate a Blender installation, or None. Must be cheap (cached)."""

    @abstractmethod
    def launch(self, file: str | None = None) -> LaunchResult:
        """Open the Blender GUI, optionally with a file (.blend or importable)."""

    @abstractmethod
    def run_script(
        self,
        code: str,
        args: list[str] | None = None,
        timeout_sec: float = 120,
    ) -> ScriptResult:
        """Execute Python in headless Blender (`--background --python`).

        Scripts may print ``EFC_RESULT {json}`` on stdout to return data.
        """

    @abstractmethod
    def convert(self, src: str, dst: str, timeout_sec: float = 180) -> ScriptResult:
        """Convert between mesh formats using Blender's importers/exporters."""
