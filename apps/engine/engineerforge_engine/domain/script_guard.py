"""Static safety validation for AI-authored freeform CAD scripts.

Freeform generation (the text-to-CAD path) executes model-authored CadQuery
Python. Executing generated code is inherently risky, so this module is the
first line of a defence-in-depth strategy (the runner adds a separate process,
an audit hook, restricted builtins, and a timeout):

  * only a small allow-list of modules may be imported (cadquery / math / numpy);
  * dunder attribute access (``__globals__``, ``__subclasses__``, …) is banned —
    it is the usual sandbox-escape vector;
  * a set of dangerous builtins/modules (``open``, ``eval``, ``exec``, ``os``,
    ``subprocess``, ``socket``, ``getattr`` …) may not be referenced at all;
  * the script must assign its final shape to a variable named ``result``.

This is a best-effort static guard, NOT a security boundary on its own — Python
cannot be made fully safe in-process. True isolation needs a container/VM. The
guarantees here are: obvious escapes are rejected before the code ever runs, and
what does run is confined to the CAD API surface.
"""

from __future__ import annotations

import ast

from .errors import EngineError

#: Modules a freeform script may import.
ALLOWED_IMPORTS = frozenset({"cadquery", "math", "numpy"})

#: Names that may never appear (builtins/modules that enable escape or I/O).
FORBIDDEN_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "__import__",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
        "memoryview",
        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "pathlib",
        "importlib",
        "requests",
        "urllib",
        "ctypes",
        "builtins",
        "pickle",
        "marshal",
    }
)

RESULT_VAR = "result"


class ScriptSecurityError(EngineError):
    """A freeform script was rejected by the static guard before execution."""

    code = "SCRIPT_REJECTED"
    http_status = 400


def _reject(message: str, node: ast.AST | None = None) -> ScriptSecurityError:
    where = f" (line {node.lineno})" if isinstance(node, ast.stmt | ast.expr) else ""
    return ScriptSecurityError(f"freeform script rejected: {message}{where}")


def validate_script(code: str) -> None:
    """Raise :class:`ScriptSecurityError` if ``code`` is unsafe or malformed.

    Enforces the module allow-list, bans dunder attribute access and forbidden
    names, and requires a top-level ``result`` assignment.
    """
    if not code.strip():
        raise ScriptSecurityError("freeform script rejected: empty script")
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise ScriptSecurityError(f"freeform script rejected: syntax error: {exc.msg}") from exc

    assigns_result = False
    for node in ast.walk(tree):
        # imports must be within the allow-list (root package only)
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise _reject(f"import of {alias.name!r} is not allowed", node)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in ALLOWED_IMPORTS:
                raise _reject(f"import from {node.module!r} is not allowed", node)
        # ban dunder attribute access (sandbox-escape vector)
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                raise _reject(f"access to dunder attribute {node.attr!r} is not allowed", node)
        # ban forbidden bare names
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                raise _reject(f"use of {node.id!r} is not allowed", node)
            if isinstance(node.ctx, ast.Store) and node.id == RESULT_VAR:
                assigns_result = True

    if not assigns_result:
        raise ScriptSecurityError(
            "freeform script rejected: must assign the final shape to a variable "
            f"named {RESULT_VAR!r} (e.g. `result = cq.Workplane('XY').box(10, 10, 5)`)"
        )
