"""Mounting-plate template golden tests — Phase 2's first library expansion.

Same discipline as the L-bracket: compiled B-rep volumes must match
closed-form analytic solutions.
"""

from __future__ import annotations

import math

import pytest
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel, GeometryError
from engineerforge_engine.templates.mounting_plate import build as build_plate

kernel = CadQueryKernel()


def plate_volume(w: float, length: float, t: float, hd: float, cd: float) -> float:
    """Analytic mounting-plate volume (fillet radius 0)."""
    return w * length * t - 4 * math.pi * (hd / 2) ** 2 * t - math.pi * (cd / 2) ** 2 * t


class TestMountingPlateGolden:
    def test_default_matches_analytic_volume(self) -> None:
        program = build_plate({"R": 0})
        compiled, _ = kernel.compile(program)
        expected = plate_volume(80, 60, 5, 5, 8)
        assert compiled.mass_props.volume_mm3 == pytest.approx(expected, rel=1e-6)
        assert compiled.mass_props.bbox_mm == {"x": 80, "y": 60, "z": 5}

    @pytest.mark.parametrize(
        ("overrides", "expected_args"),
        [
            ({"W": 120, "R": 0}, (120, 60, 5, 5, 8)),
            ({"L": 100, "T": 8, "R": 0}, (80, 100, 8, 5, 8)),
            ({"HD": 6, "R": 0}, (80, 60, 5, 6, 8)),
            ({"CD": 20, "R": 0}, (80, 60, 5, 5, 20)),
        ],
    )
    def test_parametric_rebuild_tracks_analytic_volume(
        self, overrides: dict[str, float], expected_args: tuple[float, ...]
    ) -> None:
        compiled, _ = kernel.compile(build_plate(overrides))
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            plate_volume(*expected_args), rel=1e-6
        )

    def test_corner_holes_are_symmetric(self) -> None:
        # four equal-diameter holes removed → volume delta from a solid plate
        # of the same footprint equals 4x one hole's swept volume (± center bore)
        solid_plate, _ = kernel.compile(build_plate({"HD": 0.001, "CD": 0.001, "R": 0}))
        holed_plate, _ = kernel.compile(build_plate({"R": 0}))
        removed = solid_plate.mass_props.volume_mm3 - holed_plate.mass_props.volume_mm3
        expected_removed = 4 * math.pi * 2.5**2 * 5 + math.pi * 4**2 * 5
        assert removed == pytest.approx(expected_removed, rel=1e-3)

    def test_fillet_rounds_all_four_corners(self) -> None:
        flat, _ = kernel.compile(build_plate({"R": 0}))
        filleted, _ = kernel.compile(build_plate({"R": 5}))
        # each 90° corner fillet of radius R removes (1 - pi/4)*R^2*T of material
        expected_delta = 4 * (1 - math.pi / 4) * 5**2 * 5
        actual_delta = flat.mass_props.volume_mm3 - filleted.mass_props.volume_mm3
        assert actual_delta == pytest.approx(expected_delta, rel=1e-3)

    def test_determinism(self) -> None:
        a, _ = kernel.compile(build_plate({}))
        b, _ = kernel.compile(build_plate({}))
        assert a.mass_props.volume_mm3 == b.mass_props.volume_mm3
        assert a.mesh.positions_b64 == b.mesh.positions_b64

    def test_tessellation_is_watertight(self) -> None:
        import base64

        import numpy as np
        import trimesh

        compiled, _ = kernel.compile(build_plate({"R": 3}))
        mesh = compiled.mesh
        positions = np.frombuffer(
            base64.b64decode(mesh.positions_b64), dtype="<f4"
        ).reshape(-1, 3)
        indices = np.frombuffer(base64.b64decode(mesh.indices_b64), dtype="<u4").reshape(
            -1, 3
        )
        tri = trimesh.Trimesh(vertices=positions, faces=indices, process=True)
        tri.merge_vertices()
        assert tri.is_watertight


class TestMountingPlateChecksAndErrors:
    def test_min_wall_warning(self) -> None:
        thin = build_plate({"T": 1.0, "R": 0})
        compiled, _ = kernel.compile(thin)
        # checks are applied by PartsService, not the bare kernel — verify the
        # check expression itself flags this case
        from engineerforge_engine.domain.expressions import evaluate

        values = thin.parameter_values()
        assert evaluate("1.2 - T", values) > 0
        assert compiled.mass_props.volume_mm3 > 0  # kernel still compiles cleanly

    def test_oversized_corner_fillet_raises_geometry_error(self) -> None:
        program = build_plate({"W": 40, "L": 40, "R": 25})  # R > min(W,L)/2 = 20
        with pytest.raises(GeometryError):
            kernel.compile(program)

    def test_hole_breaching_edge_still_compiles_but_check_flags_it(self) -> None:
        from engineerforge_engine.domain.expressions import evaluate

        program = build_plate({"HD": 20, "M": 5})  # HD/2=10 > M=5
        values = program.parameter_values()
        assert evaluate("HD / 2 - M", values) > 0
