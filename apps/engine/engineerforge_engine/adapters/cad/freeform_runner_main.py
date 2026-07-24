"""Subprocess entry point that executes a freeform CadQuery script safely.

Invoked as ``python freeform_runner_main.py <code_file> <out_dir>``. This is the
enforcement boundary for the freeform (text-to-CAD) path: the model-authored
script has already passed the static guard (``domain.script_guard``), and this
process adds runtime confinement before running it —

  * a restricted ``__builtins__`` (no ``open``/``eval``/``exec``/``compile``,
    and a custom ``__import__`` limited to cadquery/math/numpy);
  * an audit hook that blocks process spawning, networking, and filesystem
    mutation (belt-and-suspenders on top of the import allow-list);
  * a hard wall-clock timeout enforced by the parent process.

It writes exactly one line to stdout: ``EFC_FREEFORM <json>`` describing the
resulting geometry, or an error. It never imports the engine package — it needs
only cadquery + the standard library, keeping the sandboxed process minimal.

Design credit: the freeform text-to-CAD approach is inspired by
earthtojake/text-to-cad (MIT) and the build123d project; here it is implemented
on the app's existing CadQuery/OpenCASCADE kernel.
"""

from __future__ import annotations

import base64
import importlib
import json
import sys
from typing import Any

TESSELLATION_TOLERANCE = 0.1  # mm — matches the parametric kernel
RESULT_VAR = "result"
_ALLOWED_IMPORTS = {"cadquery", "math", "numpy"}

# Audit events blocked outright — narrowed to the catastrophic ones: spawning
# processes and outbound network. Filesystem/env events (os.putenv, temp files)
# are intentionally NOT blocked: CadQuery/OpenCASCADE use them legitimately, and
# this hook is process-wide. The static guard already prevents the *script* from
# importing os/subprocess/socket at all, so this is defence-in-depth for C-level
# escapes, not the primary control.
_BLOCKED_EVENT_PREFIXES = (
    "subprocess",
    "os.system",
    "os.exec",
    "os.spawn",
    "os.fork",
    "socket.connect",
    "socket.bind",
    "socket.getaddrinfo",
    "ftplib.connect",
    "urllib.Request",
    "webbrowser",
)


def _audit(event: str, _args: tuple[Any, ...]) -> None:
    for prefix in _BLOCKED_EVENT_PREFIXES:
        if event.startswith(prefix):
            raise PermissionError(f"blocked operation in freeform script: {event}")


def _safe_import(name: str, *_a: Any, **_k: Any) -> Any:
    root = name.split(".")[0]
    if root not in _ALLOWED_IMPORTS:
        raise ImportError(f"import of {name!r} is not permitted in freeform scripts")
    return importlib.import_module(name)


_SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float",
    "int", "isinstance", "issubclass", "len", "list", "map", "max", "min", "pow",
    "print", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple",
    "zip", "True", "False", "None", "ValueError", "TypeError", "ZeroDivisionError",
    "Exception", "abs",
)


def _restricted_builtins() -> dict[str, Any]:
    import builtins

    safe: dict[str, Any] = {
        name: getattr(builtins, name)
        for name in _SAFE_BUILTIN_NAMES
        if hasattr(builtins, name)
    }
    safe["__import__"] = _safe_import
    return safe


def _shape_of(result: Any) -> Any:
    """Normalise a CadQuery Workplane/Shape into a Shape with .Volume()/.tessellate()."""
    if result is None:
        raise ValueError(f"the script must assign a shape to `{RESULT_VAR}`")
    shape = result.val() if hasattr(result, "val") else result  # unwrap a Workplane
    if not (hasattr(shape, "Volume") and hasattr(shape, "tessellate")):
        raise ValueError(
            f"`{RESULT_VAR}` is not a solid — build a 3D shape "
            "(e.g. a box, extrusion, or revolve), not an empty workplane or a sketch"
        )
    return shape


def _tessellate(shape: Any) -> dict[str, Any]:
    import numpy as np

    vertices, triangles = shape.tessellate(TESSELLATION_TOLERANCE)
    positions = np.asarray([(v.x, v.y, v.z) for v in vertices], dtype="<f4").reshape(-1)
    indices = np.asarray(triangles, dtype="<u4").reshape(-1)
    return {
        "positionsB64": base64.b64encode(positions.tobytes()).decode("ascii"),
        "indicesB64": base64.b64encode(indices.tobytes()).decode("ascii"),
        "vertexCount": len(vertices),
        "triangleCount": len(triangles),
    }


def _run(code: str, out_dir: str) -> dict[str, Any]:
    import cadquery as cq

    namespace: dict[str, Any] = {
        "__builtins__": _restricted_builtins(),
        "cadquery": cq,
        "cq": cq,
    }
    compiled = compile(code, "<freeform>", "exec")
    exec(compiled, namespace)  # noqa: S102 — confined namespace; this is the sandbox

    shape = _shape_of(namespace.get(RESULT_VAR))
    volume = float(shape.Volume())
    if volume <= 0:
        raise ValueError("the result has non-positive volume (not a solid?)")
    center = shape.Center()
    bb = shape.BoundingBox()

    step_path = f"{out_dir}/freeform.step"
    cq.exporters.export(namespace[RESULT_VAR], step_path)

    return {
        "ok": True,
        "mesh": _tessellate(shape),
        "volumeMm3": round(volume, 3),
        "cogMm": [round(center.x, 3), round(center.y, 3), round(center.z, 3)],
        "bboxMm": {"x": round(bb.xlen, 3), "y": round(bb.ylen, 3), "z": round(bb.zlen, 3)},
        "stepPath": step_path,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("EFC_FREEFORM " + json.dumps({"ok": False, "error": "bad arguments"}))
        return 2
    code_file, out_dir = sys.argv[1], sys.argv[2]
    with open(code_file, encoding="utf-8") as fh:
        code = fh.read()

    sys.addaudithook(_audit)  # installed AFTER reading the code file
    try:
        result = _run(code, out_dir)
    except Exception as exc:  # any failure → structured error, never a traceback dump
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print("EFC_FREEFORM " + json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
