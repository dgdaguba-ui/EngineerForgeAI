"""Integration tests against a REAL local Blender installation.

Skipped automatically when Blender is not present (CI without Blender);
they run on developer machines with Blender installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import trimesh
from engineerforge_engine.adapters.blender.local import LocalBlenderAdapter

adapter = LocalBlenderAdapter()
BLENDER = adapter.detect()

requires_blender = pytest.mark.skipif(
    BLENDER is None, reason="no local Blender installation detected"
)


@requires_blender
def test_detects_real_blender() -> None:
    assert BLENDER is not None
    assert Path(BLENDER.executable).exists()
    assert BLENDER.version != "unknown"


@requires_blender
def test_run_script_round_trips_efc_result() -> None:
    result = adapter.run_script(
        "import bpy, json\n"
        'print("EFC_RESULT " + json.dumps({"blender": bpy.app.version_string}))\n',
        timeout_sec=240,
    )
    assert result.ok, result.stderr
    assert result.result is not None
    assert "blender" in result.result


@requires_blender
def test_real_stl_to_fbx_conversion(tmp_path: Path) -> None:
    src = tmp_path / "cube.stl"
    trimesh.creation.box(extents=(10.0, 10.0, 10.0)).export(str(src))
    dst = tmp_path / "cube.fbx"

    result = adapter.convert(str(src), str(dst), timeout_sec=300)
    assert result.ok, f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    assert result.result is not None and result.result.get("ok") is True
    assert dst.exists() and dst.stat().st_size > 0
