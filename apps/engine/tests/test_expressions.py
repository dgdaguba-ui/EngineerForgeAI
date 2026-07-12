from __future__ import annotations

import pytest
from engineerforge_engine.domain.expressions import ExpressionError, evaluate

VALUES = {"W": 40.0, "H": 60.0, "T": 4.0, "HC": 2.0}


class TestEvaluate:
    def test_numbers_pass_through(self) -> None:
        assert evaluate(5, {}) == 5.0
        assert evaluate(2.5, {}) == 2.5

    def test_arithmetic(self) -> None:
        assert evaluate("W / 2", VALUES) == 20.0
        assert evaluate("H - 2 * T", VALUES) == 52.0
        assert evaluate("(W + H) * 2", VALUES) == 200.0
        assert evaluate("2 ** 3", {}) == 8.0
        assert evaluate("7 // 2", {}) == 3.0
        assert evaluate("7 % 2", {}) == 1.0
        assert evaluate("-T", VALUES) == -4.0

    def test_functions(self) -> None:
        assert evaluate("max(HC - 1, 1)", VALUES) == 1.0
        assert evaluate("min(W, H)", VALUES) == 40.0
        assert evaluate("abs(0 - T)", VALUES) == 4.0
        assert evaluate("round(W / 3, 1)", VALUES) == 13.3

    def test_bracket_spacing_expression(self) -> None:
        # the actual template expression must be valid for HC=1 and HC>1
        expr = "(W - 4 * HD) / max(HC - 1, 1)"
        assert evaluate(expr, {**VALUES, "HD": 5.0}) == 20.0
        assert evaluate(expr, {**VALUES, "HD": 5.0, "HC": 1.0}) == 20.0  # no div-by-zero

    def test_unknown_parameter(self) -> None:
        with pytest.raises(ExpressionError, match="unknown parameter"):
            evaluate("W + Q", VALUES)

    def test_syntax_error(self) -> None:
        with pytest.raises(ExpressionError):
            evaluate("W +", VALUES)

    def test_division_by_zero(self) -> None:
        with pytest.raises(ExpressionError, match="division by zero"):
            evaluate("1 / (HC - 2)", VALUES)

    @pytest.mark.parametrize(
        "malicious",
        [
            "__import__('os')",
            "(1).__class__",
            "[1,2][0]",
            "'a' + 'b'",
            "lambda: 1",
            "W if H else T",
            "open('x')",
            "min()",
        ],
    )
    def test_disallowed_constructs_rejected(self, malicious: str) -> None:
        with pytest.raises(ExpressionError):
            evaluate(malicious, VALUES)

    def test_non_finite_rejected(self) -> None:
        with pytest.raises(ExpressionError):
            evaluate("10 ** 10 ** 10", {})  # overflows to inf
