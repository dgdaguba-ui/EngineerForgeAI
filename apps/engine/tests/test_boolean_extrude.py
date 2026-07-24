"""Boolean extrude modes: cut and intersect against the running solid."""

from __future__ import annotations

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel, GeometryError
from engineerforge_engine.domain.feature_program import (
    ExtrudeFeature,
    FeatureProgram,
    Parameter,
    RectProfile,
    SketchFeature,
)
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def _sketch(fid: str, w: str, h: str) -> SketchFeature:
    return SketchFeature(id=fid, plane="XY", profile=RectProfile(width=w, height=h))


def test_cut_removes_a_pocket() -> None:
    # 40×40×20 base, then cut a 20×20 tool spanning z=10..30 → removes 20×20×10
    prog = FeatureProgram(
        name="Pocketed",
        parameters=[Parameter(id="Z", label="Z", value=0)],
        features=[
            _sketch("base_s", "40", "40"),
            ExtrudeFeature(id="base", of="base_s", distance="20"),
            _sketch("tool_s", "20", "20"),
            ExtrudeFeature(id="pocket", of="tool_s", distance="20", offset="10", mode="cut"),
        ],
    )
    compiled, _ = kernel.compile(prog)
    assert compiled.mass_props.volume_mm3 == pytest.approx(40 * 40 * 20 - 20 * 20 * 10, rel=1e-5)


def test_intersect_keeps_the_overlap() -> None:
    # 40×40×20 ∩ 20×20×40 (both from z=0) → 20×20×20 overlap
    prog = FeatureProgram(
        name="Intersection",
        parameters=[Parameter(id="Z", label="Z", value=0)],
        features=[
            _sketch("a_s", "40", "40"),
            ExtrudeFeature(id="a", of="a_s", distance="20"),
            _sketch("b_s", "20", "20"),
            ExtrudeFeature(id="b", of="b_s", distance="40", mode="intersect"),
        ],
    )
    compiled, _ = kernel.compile(prog)
    assert compiled.mass_props.volume_mm3 == pytest.approx(20 * 20 * 20, rel=1e-5)


def test_first_extrude_cannot_be_cut() -> None:
    prog = FeatureProgram(
        name="Bad",
        parameters=[Parameter(id="Z", label="Z", value=0)],
        features=[
            _sketch("s", "10", "10"),
            ExtrudeFeature(id="e", of="s", distance="10", mode="cut"),
        ],
    )
    with pytest.raises(GeometryError, match="first extrude"):
        kernel.compile(prog)


def test_cut_that_removes_everything_fails() -> None:
    prog = FeatureProgram(
        name="Erased",
        parameters=[Parameter(id="Z", label="Z", value=0)],
        features=[
            _sketch("s", "20", "20"),
            ExtrudeFeature(id="e", of="s", distance="20"),
            _sketch("t", "40", "40"),
            ExtrudeFeature(id="cut", of="t", distance="40", offset="-10", mode="cut"),
        ],
    )
    with pytest.raises(GeometryError, match="empty solid"):
        kernel.compile(prog)


def test_boolean_extrude_over_compile_api(client: TestClient) -> None:
    prog = FeatureProgram(
        name="API Pocket",
        parameters=[Parameter(id="Z", label="Z", value=0)],
        features=[
            _sketch("base_s", "40", "40"),
            ExtrudeFeature(id="base", of="base_s", distance="20"),
            _sketch("tool_s", "20", "20"),
            ExtrudeFeature(id="pocket", of="tool_s", distance="20", offset="10", mode="cut"),
        ],
    )
    resp = client.post("/api/v1/parts/compile", json={"program": prog.model_dump(by_alias=True)})
    assert resp.status_code == 200
    assert resp.json()["compiled"]["massProps"]["volumeMm3"] == pytest.approx(28000, rel=1e-4)
