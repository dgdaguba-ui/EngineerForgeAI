"""Static-guard tests for the freeform (text-to-CAD) path.

The guard is the first line of defence before any generated code runs, so the
rejection cases matter as much as the accept case.
"""

from __future__ import annotations

import pytest
from engineerforge_engine.domain.script_guard import ScriptSecurityError, validate_script

SAFE = "import cadquery as cq\nresult = cq.Workplane('XY').box(10, 10, 5)"


class TestAccepts:
    def test_a_normal_cadquery_script(self) -> None:
        validate_script(SAFE)  # no raise

    def test_allowed_imports_and_math(self) -> None:
        validate_script(
            "import cadquery as cq\nimport math\nimport numpy as np\n"
            "result = cq.Workplane('XY').circle(math.pi).extrude(np.float64(3))"
        )

    def test_from_import_within_allowlist(self) -> None:
        validate_script("from cadquery import Workplane\nresult = Workplane('XY').box(1, 2, 3)")


class TestRejects:
    def test_empty(self) -> None:
        with pytest.raises(ScriptSecurityError):
            validate_script("   ")

    def test_syntax_error(self) -> None:
        with pytest.raises(ScriptSecurityError, match="syntax"):
            validate_script("result = (")

    def test_missing_result_assignment(self) -> None:
        with pytest.raises(ScriptSecurityError, match="result"):
            validate_script("import cadquery as cq\nx = cq.Workplane('XY').box(1, 1, 1)")

    @pytest.mark.parametrize(
        "code",
        [
            "import os\nresult = 1",
            "import subprocess\nresult = 1",
            "import sys\nresult = 1",
            "from os import path\nresult = 1",
            "import socket\nresult = 1",
            "import requests\nresult = 1",
        ],
    )
    def test_forbidden_imports(self, code: str) -> None:
        with pytest.raises(ScriptSecurityError, match="import"):
            validate_script(code)

    @pytest.mark.parametrize(
        "code",
        [
            "result = ().__class__.__bases__[0].__subclasses__()",
            "result = (42).__class__",
            "result = object.__subclasses__",
        ],
    )
    def test_dunder_attribute_access(self, code: str) -> None:
        with pytest.raises(ScriptSecurityError, match="dunder"):
            validate_script(code)

    @pytest.mark.parametrize(
        "code",
        [
            "result = open('/etc/passwd').read()",
            "result = eval('1+1')",
            "result = exec('x=1')",
            "result = __import__('os')",
            "result = getattr(cq, 'exporters')",
            "result = globals()",
        ],
    )
    def test_forbidden_names(self, code: str) -> None:
        with pytest.raises(ScriptSecurityError, match="not allowed"):
            validate_script(code)
