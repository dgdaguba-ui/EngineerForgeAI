"""Plane-offset extrude: stacked/flanged multi-body parts.

A second sketch+extrude with a non-zero offset begins where the first body ends,
so unioning them produces a stepped solid — the basis for lids and shouldered
standoffs without a dedicated boolean feature.
"""

from __future__ import annotations

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.domain.feature_program import (
    ExtrudeFeature,
    FeatureProgram,
    Parameter,
    RectProfile,
    SketchFeature,
)
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def _stacked() -> FeatureProgram:
    # 40×40×5 base, then a 20×20×10 shaft stacked on top (offset = base height)
    return FeatureProgram(
        name="Shouldered Post",
        parameters=[
            Parameter(id="BW", label="Base width", value=40),
            Parameter(id="BH", label="Base height", value=5),
            Parameter(id="SW", label="Shaft width", value=20),
            Parameter(id="SH", label="Shaft height", value=10),
        ],
        features=[
            SketchFeature(id="base_s", plane="XY", profile=RectProfile(width="BW", height="BW")),
            ExtrudeFeature(id="base", of="base_s", distance="BH"),
            SketchFeature(id="shaft_s", plane="XY", profile=RectProfile(width="SW", height="SW")),
            ExtrudeFeature(id="shaft", of="shaft_s", distance="SH", offset="BH"),
        ],
    )


def test_offset_extrude_stacks_bodies() -> None:
    compiled, _ = kernel.compile(_stacked())
    props = compiled.mass_props
    expected = 40 * 40 * 5 + 20 * 20 * 10  # 12000 mm³
    assert props.volume_mm3 == pytest.approx(expected, rel=1e-6)
    assert props.bbox_mm == {"x": 40.0, "y": 40.0, "z": 15.0}


def test_offset_defaults_to_zero() -> None:
    # without an offset the two bodies overlap from z=0 → union is just the larger
    prog = FeatureProgram(
        name="Overlap",
        parameters=[Parameter(id="A", label="A", value=20)],
        features=[
            SketchFeature(id="s1", plane="XY", profile=RectProfile(width="A", height="A")),
            ExtrudeFeature(id="e1", of="s1", distance="A"),
            SketchFeature(id="s2", plane="XY", profile=RectProfile(width="A", height="A")),
            ExtrudeFeature(id="e2", of="s2", distance="A"),  # offset defaults to 0
        ],
    )
    compiled, _ = kernel.compile(prog)
    assert compiled.mass_props.volume_mm3 == pytest.approx(20**3, rel=1e-6)


def test_offset_extrude_over_compile_api(client: TestClient) -> None:
    program = _stacked().model_dump(by_alias=True)
    resp = client.post("/api/v1/parts/compile", json={"program": program})
    assert resp.status_code == 200
    assert resp.json()["compiled"]["massProps"]["bboxMm"]["z"] == 15.0
