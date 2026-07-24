"""Tapered spacer template golden + API tests (revolve-based)."""

from __future__ import annotations

import math

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.templates.tapered_spacer import build as build_spacer
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def spacer_volume(r1: float, r2: float, h: float, b: float) -> float:
    frustum = math.pi * h * (r1**2 + r1 * r2 + r2**2) / 3
    bore = math.pi * (b / 2) ** 2 * h
    return frustum - bore


def test_default_matches_analytic_volume() -> None:
    compiled, _ = kernel.compile(build_spacer({}))
    assert compiled.mass_props.volume_mm3 == pytest.approx(
        spacer_volume(15, 10, 12, 6), rel=1e-3
    )
    # widest across the base diameter (2·R1 = 30); axial length H along the revolve axis
    assert max(compiled.mass_props.bbox_mm.values()) == pytest.approx(30, abs=0.1)


@pytest.mark.parametrize(
    "overrides",
    [{"R1": 20}, {"R2": 6, "H": 18}, {"B": 8}],
)
def test_parametric_rebuild_tracks_volume(overrides: dict[str, float]) -> None:
    compiled, _ = kernel.compile(build_spacer(overrides))
    a = {"R1": 15, "R2": 10, "H": 12, "B": 6, **overrides}
    assert compiled.mass_props.volume_mm3 == pytest.approx(
        spacer_volume(a["R1"], a["R2"], a["H"], a["B"]), rel=1e-3
    )


def test_listed_and_created_over_api(client: TestClient) -> None:
    templates = client.get("/api/v1/templates").json()
    assert "tapered-spacer" in {t["id"] for t in templates}
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "tapered-spacer", "materialId": "petg"}
    )
    assert created.status_code == 200
    assert created.json()["templateId"] == "tapered-spacer"
