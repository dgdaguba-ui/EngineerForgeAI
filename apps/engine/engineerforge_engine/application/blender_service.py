"""Blender use cases — thin, validated wrappers over BlenderPort."""

from __future__ import annotations

from pathlib import Path

from ..domain.blender import BlenderStatus, LaunchResult, ScriptResult
from ..domain.errors import FileOperationError, InvalidRequestError
from ..ports.blender import BlenderPort

MAX_SCRIPT_BYTES = 512 * 1024


class BlenderService:
    def __init__(self, blender: BlenderPort) -> None:
        self._blender = blender

    def status(self) -> BlenderStatus:
        info = self._blender.detect()
        if info is None:
            return BlenderStatus(
                detected=False,
                info=None,
                detail="No Blender installation found. Install Blender or set EFC_BLENDER_PATH.",
            )
        return BlenderStatus(
            detected=True, info=info, detail=f"Blender {info.version} at {info.executable}"
        )

    def launch(self, file: str | None = None) -> LaunchResult:
        if file is not None and not Path(file).exists():
            raise FileOperationError(f"File does not exist: {file}")
        return self._blender.launch(file)

    def run_script(
        self, code: str, args: list[str] | None = None, timeout_sec: float = 120
    ) -> ScriptResult:
        if not code.strip():
            raise InvalidRequestError("script code must not be empty")
        if len(code.encode("utf-8")) > MAX_SCRIPT_BYTES:
            raise InvalidRequestError(f"script exceeds {MAX_SCRIPT_BYTES} bytes")
        if not 1 <= timeout_sec <= 3600:
            raise InvalidRequestError("timeout_sec must be between 1 and 3600")
        return self._blender.run_script(code, args=args, timeout_sec=timeout_sec)
