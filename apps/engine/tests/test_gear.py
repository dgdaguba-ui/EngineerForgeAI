"""Involute spur-gear template + outline generator tests.

A gear has no simple closed-form volume, so the golden checks bound the
compiled B-rep volume between the root and addendum cylinders (less the bore)
and assert the exact key radii and tooth count of the generated outline.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import (
    CadQueryKernel,
    GeometryError,
    gear_outline,
)
from engineerforge_engine.templates.gear import build as build_gear

kernel = CadQueryKernel()


def _radii(points: list[tuple[float, float]]) -> np.ndarray:
    arr = np.array(points)
    return np.hypot(arr[:, 0], arr[:, 1])


class TestGearOutline:
    @pytest.mark.parametrize("teeth", [17, 20, 40, 60])
    def test_key_radii_and_tooth_count(self, teeth: int) -> None:
        module = 2.0
        pts = gear_outline(module, teeth, 20.0)
        r = module * teeth / 2
        ra = r + module
        rf = r - 1.25 * module
        radii = _radii(pts)
        # outer points reach the addendum circle, inner reach the root circle
        assert radii.max() == pytest.approx(ra, abs=1e-6)
        assert radii.min() == pytest.approx(rf, abs=1e-6)
        # one tip run per tooth
        tip = radii > (ra - 1e-3)
        runs = int(np.sum((tip.astype(int)[1:] - tip.astype(int)[:-1]) == 1))
        assert runs == teeth
        # closed, non-trivial outline
        assert len(pts) > teeth * 4

    def test_rejects_degenerate_parameters(self) -> None:
        with pytest.raises(GeometryError):
            gear_outline(2.0, 3, 20.0)  # too few teeth
        with pytest.raises(GeometryError):
            gear_outline(0.0, 20, 20.0)  # zero module
        with pytest.raises(GeometryError):
            gear_outline(2.0, 20, 95.0)  # impossible pressure angle


class TestGearTemplate:
    def test_default_volume_within_root_and_addendum_cylinders(self) -> None:
        compiled, _ = kernel.compile(build_gear({}))
        m, z, t, b = 2.0, 20, 6.0, 6.0
        r = m * z / 2
        add_cyl = math.pi * (r + m) ** 2 * t
        root_cyl = math.pi * (r - 1.25 * m) ** 2 * t
        bore = math.pi * (b / 2) ** 2 * t
        vol = compiled.mass_props.volume_mm3
        assert root_cyl - bore < vol < add_cyl - bore
        # bbox spans the addendum circle; face width sets Z
        assert compiled.mass_props.bbox_mm["x"] == pytest.approx(2 * (r + m), abs=0.05)
        assert compiled.mass_props.bbox_mm["z"] == pytest.approx(t, abs=1e-6)

    def test_tooth_count_changes_with_Z(self) -> None:
        small, _ = kernel.compile(build_gear({"Z": 12}))
        large, _ = kernel.compile(build_gear({"Z": 48}))
        # more teeth (same module) → larger gear → more volume
        assert large.mass_props.volume_mm3 > small.mass_props.volume_mm3
        assert large.mass_props.bbox_mm["x"] > small.mass_props.bbox_mm["x"]

    def test_determinism(self) -> None:
        a, _ = kernel.compile(build_gear({}))
        b, _ = kernel.compile(build_gear({}))
        assert a.mesh.positions_b64 == b.mesh.positions_b64

    def test_bore_too_large_fails(self) -> None:
        # a bore past the tooth roots removes the whole body
        with pytest.raises(GeometryError):
            kernel.compile(build_gear({"Z": 12, "M": 2, "B": 60}))
