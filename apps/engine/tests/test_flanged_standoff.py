"""Flanged standoff template golden + API tests (offset-extrude stacking)."""

from __future__ import annotations

import math

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.templates.flanged_standoff import build as build_flanged
from fastapi.testclient import TestClient

kernel = CadQueryKernel()


def flanged_volume(fd: float, fh: float, sd: float, sh: float, b: float) -> float:
    return math.pi / 4 * (fd**2 * fh + sd**2 * sh - b**2 * (fh + sh))


def test_default_matches_analytic_volume() -> None:
    compiled, _ = kernel.compile(build_flanged({}))
    assert compiled.mass_props.volume_mm3 == pytest.approx(
        flanged_volume(20, 4, 10, 16, 4.2), rel=1e-4
    )
    # bbox: widest is the flange; total height is FH + SH
    assert compiled.mass_props.bbox_mm["x"] == pytest.approx(20, abs=0.05)
    assert compiled.mass_props.bbox_mm["z"] == pytest.approx(20, abs=1e-6)


@pytest.mark.parametrize(
    "overrides",
    [{"FD": 30}, {"SH": 25, "B": 5}, {"FH": 6, "SD": 12}],
)
def test_parametric_rebuild_tracks_volume(overrides: dict[str, float]) -> None:
    compiled, _ = kernel.compile(build_flanged(overrides))
    args = {"FD": 20, "FH": 4, "SD": 10, "SH": 16, "B": 4.2, **overrides}
    assert compiled.mass_props.volume_mm3 == pytest.approx(
        flanged_volume(args["FD"], args["FH"], args["SD"], args["SH"], args["B"]), rel=1e-4
    )


def test_listed_and_created_over_api(client: TestClient) -> None:
    templates = client.get("/api/v1/templates").json()
    assert "flanged-standoff" in {t["id"] for t in templates}

    created = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "flanged-standoff", "materialId": "pla"},
    )
    assert created.status_code == 200
    assert created.json()["compiled"]["massProps"]["bboxMm"]["z"] == 20.0
