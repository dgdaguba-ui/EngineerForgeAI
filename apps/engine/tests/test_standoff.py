"""Standoff template golden tests."""

from __future__ import annotations

import math

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel, GeometryError
from engineerforge_engine.templates.standoff import build as build_standoff

kernel = CadQueryKernel()


def standoff_volume(od: float, idia: float, h: float) -> float:
    """Analytic tube volume: π/4 · (OD² − ID²) · H."""
    return math.pi / 4 * (od**2 - idia**2) * h


class TestStandoffGolden:
    def test_default_matches_analytic_volume(self) -> None:
        compiled, _ = kernel.compile(build_standoff({}))
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            standoff_volume(8, 3.4, 15), rel=1e-5
        )
        # bbox is the outer cylinder
        assert compiled.mass_props.bbox_mm["z"] == 15
        assert compiled.mass_props.bbox_mm["x"] == pytest.approx(8, abs=0.02)

    @pytest.mark.parametrize(
        ("overrides", "expected_args"),
        [
            ({"OD": 12}, (12, 3.4, 15)),
            ({"ID": 5, "H": 25}, (8, 5, 25)),
            ({"OD": 10, "ID": 6}, (10, 6, 15)),
        ],
    )
    def test_parametric_rebuild_tracks_analytic_volume(
        self, overrides: dict[str, float], expected_args: tuple[float, ...]
    ) -> None:
        compiled, _ = kernel.compile(build_standoff(overrides))
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            standoff_volume(*expected_args), rel=1e-4
        )

    def test_bore_larger_than_body_fails(self) -> None:
        # ID > OD → nothing left → kernel guards non-positive volume
        with pytest.raises(GeometryError):
            kernel.compile(build_standoff({"OD": 6, "ID": 10}))

    def test_determinism(self) -> None:
        a, _ = kernel.compile(build_standoff({}))
        b, _ = kernel.compile(build_standoff({}))
        assert a.mesh.positions_b64 == b.mesh.positions_b64
