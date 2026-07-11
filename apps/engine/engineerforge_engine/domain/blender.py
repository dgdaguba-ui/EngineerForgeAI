"""Blender-integration domain models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BlenderInfo(BaseModel):
    executable: str
    version: str  # e.g. "5.0.1"


class BlenderStatus(BaseModel):
    detected: bool
    info: BlenderInfo | None = None
    detail: str = ""


class ScriptResult(BaseModel):
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int = Field(alias="durationMs")
    # JSON payload printed by the script via the EFC_RESULT convention, if any.
    result: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class LaunchResult(BaseModel):
    pid: int
    executable: str
    file: str | None = None
