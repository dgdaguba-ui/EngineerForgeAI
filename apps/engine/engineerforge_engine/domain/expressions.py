"""Safe arithmetic expression evaluator for Feature Program parameters.

Grammar: numbers, parameter identifiers, + - * / // % ** ( ), unary minus,
and the functions min/max/abs/round. Implemented over Python's AST with a
strict node whitelist — no attribute access, no subscripts, no names other
than declared parameters, no eval.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping

from .errors import InvalidRequestError


class ExpressionError(InvalidRequestError):
    code = "EXPRESSION_ERROR"


_ALLOWED_FUNCS: dict[str, object] = {"min": min, "max": max, "abs": abs, "round": round}

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_ALLOWED_UNARYOPS = (ast.USub, ast.UAdd)

Expr = str | float | int


def evaluate(expr: Expr, values: Mapping[str, float]) -> float:
    """Evaluate an expression against parameter values. Returns a float."""
    if isinstance(expr, int | float):
        return float(expr)
    text = expr.strip()
    if not text:
        raise ExpressionError("empty expression")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"invalid expression {text!r}: {exc.msg}") from exc
    result = _eval_node(tree.body, text, values)
    if isinstance(result, bool) or not isinstance(result, int | float):
        raise ExpressionError(f"expression {text!r} did not produce a number")
    value = float(result)
    if value != value or value in (float("inf"), float("-inf")):  # NaN/inf guard
        raise ExpressionError(f"expression {text!r} produced a non-finite value")
    return value


def _eval_node(node: ast.expr, source: str, values: Mapping[str, float]) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise ExpressionError(f"non-numeric literal in {source!r}")
        return float(node.value)

    if isinstance(node, ast.Name):
        if node.id in values:
            return float(values[node.id])
        raise ExpressionError(f"unknown parameter {node.id!r} in {source!r}")

    if isinstance(node, ast.BinOp) and isinstance(node.op, _ALLOWED_BINOPS):
        left = _eval_node(node.left, source, values)
        right = _eval_node(node.right, source, values)
        try:
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
            return float(left**right)
        except ZeroDivisionError as exc:
            raise ExpressionError(f"division by zero in {source!r}") from exc
        except (OverflowError, ValueError) as exc:
            # float pow can overflow or go complex (negative base, frac. exp)
            raise ExpressionError(f"arithmetic error in {source!r}: {exc}") from exc

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ALLOWED_UNARYOPS):
        operand = _eval_node(node.operand, source, values)
        return -operand if isinstance(node.op, ast.USub) else operand

    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in _ALLOWED_FUNCS
            and not node.keywords
        ):
            args = [_eval_node(arg, source, values) for arg in node.args]
            if not args:
                raise ExpressionError(f"{node.func.id}() needs arguments in {source!r}")
            try:
                if node.func.id == "round" and len(args) == 2:
                    return float(round(args[0], int(args[1])))
                func = _ALLOWED_FUNCS[node.func.id]
                return float(func(*args))  # type: ignore[operator]
            except TypeError as exc:
                raise ExpressionError(f"bad arguments to {node.func.id}() in {source!r}") from exc
        raise ExpressionError(f"function not allowed in {source!r}")

    raise ExpressionError(f"disallowed syntax in {source!r}: {type(node).__name__}")
