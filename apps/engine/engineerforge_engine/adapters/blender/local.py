"""LocalBlenderAdapter — drives a locally installed Blender.

Detection order: EFC_BLENDER_PATH → PATH (`which blender`) → platform install
locations (on Windows, the highest-versioned `Program Files\\Blender
Foundation\\Blender X.Y`). Detection results are cached per adapter instance.

Headless execution uses `--background --factory-startup --python <script>`.
Scripts return structured data by printing a line `EFC_RESULT {json}`.
The conversion script resolves import/export operators defensively across
Blender versions (4.x `wm.*` operators with legacy fallbacks).
"""

from __future__ import annotations

import glob as glob_module
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from ...domain.blender import BlenderInfo, LaunchResult, ScriptResult
from ...domain.errors import EngineError
from ...ports.blender import BlenderPort


class BlenderNotFoundError(EngineError):
    code = "BLENDER_NOT_FOUND"
    http_status = 503


_WIN_GLOBS = (
    r"C:\Program Files\Blender Foundation\Blender */blender.exe",
    r"C:\Program Files (x86)\Blender Foundation\Blender */blender.exe",
)
_MAC_PATHS = ("/Applications/Blender.app/Contents/MacOS/Blender",)


def _version_key_from_path(path: str) -> tuple[int, int]:
    """Sort key for install dirs like '...\\Blender 5.0\\blender.exe'."""
    match = re.search(r"Blender\s+(\d+)\.(\d+)", path)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def find_blender_executable(
    env: Mapping[str, str],
    platform: str,
    which: Callable[[str], str | None],
    glob_fn: Callable[[str], list[str]],
    exists: Callable[[str], bool],
) -> str | None:
    """Pure executable lookup — every dependency injected for testability."""
    override = env.get("EFC_BLENDER_PATH")
    if override:
        if exists(override):
            return override
        return None  # explicit override that is wrong should not silently fall back
    on_path = which("blender")
    if on_path:
        return on_path
    if platform == "win32":
        candidates: list[str] = []
        for pattern in _WIN_GLOBS:
            candidates.extend(glob_fn(pattern))
        if candidates:
            return max(candidates, key=_version_key_from_path)
    elif platform == "darwin":
        for candidate in _MAC_PATHS:
            if exists(candidate):
                return candidate
    return None


def parse_blender_version(version_output: str) -> str:
    """Extract '5.0.1' from `blender --version` output."""
    match = re.search(r"Blender\s+(\d+\.\d+(?:\.\d+)?)", version_output)
    return match.group(1) if match else "unknown"


def parse_efc_result(stdout: str) -> dict[str, object] | None:
    """Return the JSON payload of the last `EFC_RESULT {...}` stdout line."""
    result: dict[str, object] | None = None
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("EFC_RESULT "):
            try:
                parsed = json.loads(stripped[len("EFC_RESULT ") :])
                if isinstance(parsed, dict):
                    result = parsed
            except json.JSONDecodeError:
                continue
    return result


def build_headless_command(
    executable: str, script_path: str, args: list[str] | None
) -> list[str]:
    cmd = [executable, "--background", "--factory-startup", "--python", script_path]
    if args:
        cmd += ["--", *args]
    return cmd


# Runs inside Blender. Resolves operators defensively across versions and
# reports via the EFC_RESULT convention. Receives [src, dst] after `--`.
BLENDER_CONVERT_SCRIPT = r'''
import json
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
src, dst = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)


def try_ops(candidates, **kwargs):
    last_error = None
    for dotted in candidates:
        mod_name, _, op_name = dotted.partition(".")
        mod = getattr(bpy.ops, mod_name, None)
        op = getattr(mod, op_name, None) if mod is not None else None
        if op is None:
            continue
        try:
            op(**kwargs)
            return dotted
        except Exception as exc:  # try the next candidate
            last_error = exc
    raise RuntimeError(f"no operator succeeded from {candidates}: {last_error}")


IMPORTERS = {
    ".stl": ["wm.stl_import", "import_mesh.stl"],
    ".obj": ["wm.obj_import", "import_scene.obj"],
    ".ply": ["wm.ply_import", "import_mesh.ply"],
    ".glb": ["import_scene.gltf"],
    ".gltf": ["import_scene.gltf"],
    ".fbx": ["import_scene.fbx"],
}
EXPORTERS = {
    ".stl": ["wm.stl_export", "export_mesh.stl"],
    ".obj": ["wm.obj_export", "export_scene.obj"],
    ".ply": ["wm.ply_export", "export_mesh.ply"],
    ".glb": ["export_scene.gltf"],
    ".gltf": ["export_scene.gltf"],
    ".fbx": ["export_scene.fbx"],
}


def ext_of(path):
    dot = path.rfind(".")
    return path[dot:].lower() if dot >= 0 else ""


src_ext, dst_ext = ext_of(src), ext_of(dst)
if src_ext not in IMPORTERS:
    raise RuntimeError(f"unsupported import format: {src_ext}")
if dst_ext not in EXPORTERS:
    raise RuntimeError(f"unsupported export format: {dst_ext}")

used_import = try_ops(IMPORTERS[src_ext], filepath=src)

for obj in bpy.data.objects:
    obj.select_set(True)

export_kwargs = {"filepath": dst}
if dst_ext in (".glb", ".gltf"):
    export_kwargs["export_format"] = "GLB" if dst_ext == ".glb" else "GLTF_SEPARATE"
used_export = try_ops(EXPORTERS[dst_ext], **export_kwargs)

print(
    "EFC_RESULT "
    + json.dumps(
        {
            "ok": True,
            "importer": used_import,
            "exporter": used_export,
            "objects": len(bpy.data.objects),
        }
    )
)
'''


class LocalBlenderAdapter(BlenderPort):
    def __init__(self, path_override: str | None = None) -> None:
        self._path_override = path_override
        self._cached_info: BlenderInfo | None = None
        self._detection_done = False

    # ── detection ───────────────────────────────────────────────────────────

    def detect(self) -> BlenderInfo | None:
        if self._detection_done:
            return self._cached_info
        env: dict[str, str] = {}
        if self._path_override:
            env["EFC_BLENDER_PATH"] = self._path_override
        else:
            import os

            override = os.environ.get("EFC_BLENDER_PATH")
            if override:
                env["EFC_BLENDER_PATH"] = override
        executable = find_blender_executable(
            env=env,
            platform=sys.platform,
            which=shutil.which,
            glob_fn=lambda p: glob_module.glob(p),
            exists=lambda p: Path(p).exists(),
        )
        if executable is None:
            self._cached_info = None
        else:
            self._cached_info = BlenderInfo(
                executable=executable, version=self._probe_version(executable)
            )
        self._detection_done = True
        return self._cached_info

    def _probe_version(self, executable: str) -> str:
        try:
            proc = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return parse_blender_version(proc.stdout)
        except (OSError, subprocess.TimeoutExpired):
            return "unknown"

    def _require_executable(self) -> str:
        info = self.detect()
        if info is None:
            raise BlenderNotFoundError(
                "No Blender installation found. Install Blender or set EFC_BLENDER_PATH."
            )
        return info.executable

    # ── operations ──────────────────────────────────────────────────────────

    def launch(self, file: str | None = None) -> LaunchResult:
        executable = self._require_executable()
        cmd = [executable]
        if file:
            cmd.append(file)
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(  # noqa: S603 — launching the user's own Blender
            cmd,
            close_fds=True,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return LaunchResult(pid=proc.pid, executable=executable, file=file)

    def run_script(
        self,
        code: str,
        args: list[str] | None = None,
        timeout_sec: float = 120,
    ) -> ScriptResult:
        executable = self._require_executable()
        # mkstemp + close before spawning: Windows cannot reopen a file that
        # another handle holds, and Blender must read the script itself.
        fd, script_path = tempfile.mkstemp(suffix=".py", prefix="efc-blender-")
        try:
            with open(fd, "w", encoding="utf-8") as handle:
                handle.write(code)
            cmd = build_headless_command(executable, script_path, args)
            started = time.monotonic()
            try:
                proc = subprocess.run(  # noqa: S603
                    cmd, capture_output=True, text=True, timeout=timeout_sec
                )
            except subprocess.TimeoutExpired as exc:
                duration = int((time.monotonic() - started) * 1000)
                return ScriptResult(
                    ok=False,
                    returncode=-1,
                    stdout=(exc.stdout or b"").decode("utf-8", "replace")
                    if isinstance(exc.stdout, bytes)
                    else (exc.stdout or ""),
                    stderr=f"Blender script timed out after {timeout_sec}s",
                    duration_ms=duration,
                    result=None,
                )
            duration = int((time.monotonic() - started) * 1000)
            payload = parse_efc_result(proc.stdout)
            return ScriptResult(
                ok=proc.returncode == 0,
                returncode=proc.returncode,
                stdout=proc.stdout[-20_000:],
                stderr=proc.stderr[-20_000:],
                duration_ms=duration,
                result=payload,
            )
        finally:
            Path(script_path).unlink(missing_ok=True)

    def convert(self, src: str, dst: str, timeout_sec: float = 180) -> ScriptResult:
        return self.run_script(BLENDER_CONVERT_SCRIPT, args=[src, dst], timeout_sec=timeout_sec)
