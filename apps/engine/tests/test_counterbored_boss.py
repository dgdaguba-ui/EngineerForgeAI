"""Counterbored boss template golden + API tests (boolean-cut recess)."""

from __future__ import annotations

import math

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.templates.counterbored_boss import build as build_boss
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def boss_volume(od: float, h: float, b: float, cb: float, cd: float) -> float:
    return math.pi / 4 * (od**2 * h - b**2 * h - (cb**2 - b**2) * cd)


def test_default_matches_analytic_volume() -> None:
    compiled, _ = kernel.compile(build_boss({}))
    assert compiled.mass_props.volume_mm3 == pytest.approx(
        boss_volume(16, 14, 3.4, 6.5, 3.5), rel=1e-4
    )
    assert compiled.mass_props.bbox_mm["z"] == pytest.approx(14, abs=1e-6)
    assert compiled.mass_props.bbox_mm["x"] == pytest.approx(16, abs=0.05)


@pytest.mark.parametrize(
    "overrides",
    [{"CB": 8, "CD": 5}, {"OD": 20, "B": 5}, {"H": 20}],
)
def test_parametric_rebuild_tracks_volume(overrides: dict[str, float]) -> None:
    compiled, _ = kernel.compile(build_boss(overrides))
    a = {"OD": 16, "H": 14, "B": 3.4, "CB": 6.5, "CD": 3.5, **overrides}
    assert compiled.mass_props.volume_mm3 == pytest.approx(
        boss_volume(a["OD"], a["H"], a["B"], a["CB"], a["CD"]), rel=1e-4
    )


def test_counterbore_is_a_blind_recess_not_a_through_hole() -> None:
    # material must remain beneath the counterbore: volume > a full CB through-bore case
    compiled, _ = kernel.compile(build_boss({}))
    through = math.pi / 4 * (16**2 * 14 - 6.5**2 * 14)  # if CB went all the way
    assert compiled.mass_props.volume_mm3 > through


def test_listed_and_created_over_api(client: TestClient) -> None:
    templates = client.get("/api/v1/templates").json()
    assert "counterbored-boss" in {t["id"] for t in templates}
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "counterbored-boss"}
    )
    assert created.status_code == 200
    assert created.json()["templateId"] == "counterbored-boss"
