"""Chamfer feature golden + API tests.

A 45° chamfer of length c on each of the four vertical (Z-parallel) edges of a
W×L×H box removes a right-triangular prism (legs c×c, area c²/2) of height H —
so the chamfered volume is  W·L·H − 4·(c²/2)·H = W·L·H − 2·c²·H.
"""

from __future__ import annotations

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel, GeometryError
from engineerforge_engine.domain.feature_program import (
    ChamferFeature,
    ExtrudeFeature,
    FeatureProgram,
    Parameter,
    RectProfile,
    SketchFeature,
)
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def _box_with_chamfer(w: float, length: float, h: float, c: float) -> FeatureProgram:
    return FeatureProgram(
        name="Chamfered Box",
        parameters=[
            Parameter(id="W", label="W", value=w),
            Parameter(id="L", label="L", value=length),
            Parameter(id="H", label="H", value=h),
            Parameter(id="C", label="C", value=c),
        ],
        features=[
            SketchFeature(id="s", plane="XY", profile=RectProfile(width="W", height="L")),
            ExtrudeFeature(id="body", of="s", distance="H"),
            ChamferFeature(id="edges", axis="Z", length="C"),
        ],
    )


def test_chamfer_removes_expected_volume() -> None:
    w, length, h, c = 40.0, 30.0, 10.0, 3.0
    compiled, _ = kernel.compile(_box_with_chamfer(w, length, h, c))
    expected = w * length * h - 2 * c**2 * h
    assert compiled.mass_props.volume_mm3 == pytest.approx(expected, rel=1e-5)


def test_zero_length_is_a_noop_with_warning() -> None:
    compiled, _ = kernel.compile(_box_with_chamfer(40, 30, 10, 0))
    assert compiled.mass_props.volume_mm3 == pytest.approx(40 * 30 * 10, rel=1e-6)
    assert any("chamfer" in w and "skipped" in w for w in compiled.warnings)


def test_oversize_chamfer_fails() -> None:
    # length ≥ half the smallest side → opposing chamfers collide
    with pytest.raises(GeometryError):
        kernel.compile(_box_with_chamfer(40, 30, 10, 16))


def test_chamfer_over_compile_api(client: TestClient) -> None:
    program = _box_with_chamfer(40, 30, 10, 2).model_dump(by_alias=True)
    resp = client.post("/api/v1/parts/compile", json={"program": program})
    assert resp.status_code == 200
    body = resp.json()
    feature_ops = [f["op"] for f in body["program"]["features"]]
    assert "chamfer" in feature_ops
    assert body["compiled"]["massProps"]["volumeMm3"] == pytest.approx(
        40 * 30 * 10 - 2 * 2**2 * 10, rel=1e-4
    )
