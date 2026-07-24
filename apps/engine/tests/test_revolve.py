"""Revolve feature golden + API tests.

A rectangle in local (u, v) spanning u∈[0,H], v∈[RI,RO] revolved 360° around the
u-axis is a tube (axial length H along u, radii RI..RO):
    V = π · (RO² − RI²) · H
A partial angle θ scales the volume by θ/360.
"""

from __future__ import annotations

import math

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel, GeometryError
from engineerforge_engine.domain.feature_program import (
    FeatureProgram,
    Parameter,
    PolygonProfile,
    RevolveFeature,
    SketchFeature,
)
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def _tube_program(ri: float, ro: float, h: float, angle: str = "360") -> FeatureProgram:
    return FeatureProgram(
        name="Revolved Tube",
        parameters=[Parameter(id="P", label="P", value=0)],
        features=[
            SketchFeature(
                id="s",
                plane="XY",
                profile=PolygonProfile(
                    points=[
                        ("0", str(ri)),
                        (str(h), str(ri)),
                        (str(h), str(ro)),
                        ("0", str(ro)),
                    ]
                ),
            ),
            RevolveFeature(id="rev", of="s", angle=angle, axis="u"),
        ],
    )


def test_full_revolve_makes_a_tube() -> None:
    compiled, _ = kernel.compile(_tube_program(5, 10, 8))
    assert compiled.mass_props.volume_mm3 == pytest.approx(math.pi * (100 - 25) * 8, rel=1e-4)
    # revolved around u (local X) → axial length along X, diameter 2·RO across Y/Z
    assert compiled.mass_props.bbox_mm == pytest.approx({"x": 8.0, "y": 20.0, "z": 20.0}, abs=0.05)


def test_partial_revolve_scales_volume() -> None:
    compiled, _ = kernel.compile(_tube_program(5, 10, 8, angle="90"))
    assert compiled.mass_props.volume_mm3 == pytest.approx(math.pi * 75 * 8 * 90 / 360, rel=1e-4)


def test_bad_angle_rejected() -> None:
    with pytest.raises(GeometryError, match="angle"):
        kernel.compile(_tube_program(5, 10, 8, angle="0"))
    with pytest.raises(GeometryError, match="angle"):
        kernel.compile(_tube_program(5, 10, 8, angle="400"))


def test_profile_crossing_axis_is_reported() -> None:
    # a rectangle spanning v=-5..5 crosses the u-axis → self-intersecting revolve
    prog = FeatureProgram(
        name="Crosses",
        parameters=[Parameter(id="P", label="P", value=0)],
        features=[
            SketchFeature(
                id="s",
                plane="XY",
                profile=PolygonProfile(
                    points=[("0", "-5"), ("8", "-5"), ("8", "5"), ("0", "5")]
                ),
            ),
            RevolveFeature(id="rev", of="s", angle="360", axis="u"),
        ],
    )
    with pytest.raises(GeometryError):
        kernel.compile(prog)


def test_revolve_over_compile_api(client: TestClient) -> None:
    program = _tube_program(5, 10, 8).model_dump(by_alias=True)
    resp = client.post("/api/v1/parts/compile", json={"program": program})
    assert resp.status_code == 200
    body = resp.json()
    assert "revolve" in [f["op"] for f in body["program"]["features"]]
    assert body["compiled"]["massProps"]["volumeMm3"] == pytest.approx(
        math.pi * 75 * 8, rel=1e-4
    )
