"""V-belt pulley template golden + API tests.

The revolved-notch volume has no simple closed form, so it is checked against
Pappus's theorem (V = 2π · r̄ · A) computed independently from the same
cross-section polygon the template revolves.
"""

from __future__ import annotations

import math

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.domain.expressions import evaluate
from engineerforge_engine.templates.v_pulley import build as build_pulley
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def _pappus_volume(values: dict[str, float]) -> float:
    """Full-360° revolve volume of the pulley section via Pappus's theorem.

    Uses the same expressions the template does, evaluated against `values`, so
    it is an independent check of the revolved geometry.
    """
    section = [
        ("0", "B/2"),
        ("W", "B/2"),
        ("W", "OD/2"),
        ("W/2 + GW/2", "OD/2"),
        ("W/2", "OD/2 - GD"),
        ("W/2 - GW/2", "OD/2"),
        ("0", "OD/2"),
    ]
    pts = [(evaluate(u, values), evaluate(v, values)) for u, v in section]
    n = len(pts)
    area2 = 0.0  # 2·signed area
    cy6a = 0.0  # 6·A·centroid_v accumulator
    for i in range(n):
        u0, v0 = pts[i]
        u1, v1 = pts[(i + 1) % n]
        cross = u0 * v1 - u1 * v0
        area2 += cross
        cy6a += (v0 + v1) * cross
    area = abs(area2) / 2.0
    centroid_v = cy6a / (3.0 * area2)  # signed area cancels the sign
    return 2 * math.pi * centroid_v * area


def _defaults() -> dict[str, float]:
    return {p.id: p.value for p in build_pulley({}).parameters}


def test_default_matches_pappus_volume() -> None:
    compiled, _ = kernel.compile(build_pulley({}))
    assert compiled.mass_props.volume_mm3 == pytest.approx(_pappus_volume(_defaults()), rel=2e-3)
    # widest across the rim (OD = 40); axial length = face width W = 12
    bbox = compiled.mass_props.bbox_mm
    assert max(bbox.values()) == pytest.approx(40, abs=0.2)


@pytest.mark.parametrize("overrides", [{"OD": 60}, {"GD": 9, "GW": 10}, {"W": 16, "B": 12}])
def test_parametric_rebuild_tracks_pappus(overrides: dict[str, float]) -> None:
    compiled, _ = kernel.compile(build_pulley(overrides))
    values = {**_defaults(), **overrides}
    assert compiled.mass_props.volume_mm3 == pytest.approx(_pappus_volume(values), rel=2e-3)


def test_deeper_groove_removes_material() -> None:
    shallow, _ = kernel.compile(build_pulley({"GD": 3}))
    deep, _ = kernel.compile(build_pulley({"GD": 9}))
    assert deep.mass_props.volume_mm3 < shallow.mass_props.volume_mm3


def test_listed_and_created_over_api(client: TestClient) -> None:
    templates = client.get("/api/v1/templates").json()
    assert "v-pulley" in {t["id"] for t in templates}
    created = client.post("/api/v1/parts/from-template", json={"templateId": "v-pulley"})
    assert created.status_code == 200
    assert created.json()["templateId"] == "v-pulley"
