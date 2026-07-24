"""CadQuery-backed freeform runner — the sandboxed text-to-CAD execution path.

Runs a validated script in a **separate Python process** (``freeform_runner_main``)
with a hard timeout, so a hung or crashing script cannot take down the engine and
runaway loops are bounded. The child adds runtime confinement (restricted
builtins + audit hook); this parent adds process isolation, the timeout, and
output-size limits, and translates the child's JSON result into domain models.

Credit: the freeform text-to-CAD capability is inspired by
earthtojake/text-to-cad (MIT) and build123d; implemented here on CadQuery.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from ...domain.errors import EngineError
from ...domain.feature_program import MassProps, RawMesh
from ...ports.freeform_runner import FreeformRunnerPort, FreeformRunResult

_RUNNER = Path(__file__).with_name("freeform_runner_main.py")
_MARKER = "EFC_FREEFORM "
_MAX_OUTPUT = 4_000_000  # bytes; guards against a script printing unbounded output


class FreeformExecutionError(EngineError):
    """A freeform script failed to produce valid geometry (or timed out)."""

    code = "FREEFORM_ERROR"
    http_status = 422


class CadQueryFreeformRunner(FreeformRunnerPort):
    def __init__(self, python_executable: str | None = None) -> None:
        # default to the engine's own interpreter (has cadquery in its venv)
        self._python = python_executable or sys.executable

    def run(self, code: str, timeout_s: float = 20.0) -> FreeformRunResult:
        with tempfile.TemporaryDirectory(prefix="efc-freeform-") as tmp:
            code_file = Path(tmp) / "script.py"
            code_file.write_text(code, encoding="utf-8")
            try:
                proc = subprocess.run(
                    [self._python, str(_RUNNER), str(code_file), tmp],
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise FreeformExecutionError(
                    f"freeform script exceeded the {timeout_s:.0f}s time limit"
                ) from exc

            payload = self._parse(proc.stdout, proc.stderr, proc.returncode)
            if not payload.get("ok"):
                raise FreeformExecutionError(str(payload.get("error", "freeform script failed")))

            # the STEP lives in the temp dir; copy it somewhere stable for later export
            step_src = Path(payload["stepPath"])
            step_dst = Path(tempfile.mkdtemp(prefix="efc-freeform-step-")) / "freeform.step"
            step_dst.write_bytes(step_src.read_bytes())

            mesh = payload["mesh"]
            return FreeformRunResult(
                mesh=RawMesh(
                    positions_b64=mesh["positionsB64"],
                    indices_b64=mesh["indicesB64"],
                    vertex_count=mesh["vertexCount"],
                    triangle_count=mesh["triangleCount"],
                ),
                mass_props=MassProps(
                    volume_mm3=payload["volumeMm3"],
                    volume_cm3=round(payload["volumeMm3"] / 1000.0, 4),
                    cog_mm=tuple(payload["cogMm"]),
                    bbox_mm=payload["bboxMm"],
                ),
                step_path=str(step_dst),
            )

    def _parse(self, stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
        if len(stdout) > _MAX_OUTPUT:
            raise FreeformExecutionError("freeform script produced too much output")
        for line in stdout.splitlines():
            if line.startswith(_MARKER):
                try:
                    return json.loads(line[len(_MARKER) :])  # type: ignore[no-any-return]
                except json.JSONDecodeError as exc:
                    raise FreeformExecutionError("freeform runner returned invalid JSON") from exc
        # no marker → the child crashed before reporting; surface a short reason
        tail = (stderr or "no output").strip().splitlines()[-3:]
        raise FreeformExecutionError(
            f"freeform runner did not return a result (exit {returncode}): {' '.join(tail)[:400]}"
        )
