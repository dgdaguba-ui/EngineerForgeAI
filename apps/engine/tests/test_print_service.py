from __future__ import annotations

from pathlib import Path

import pytest
import trimesh
from engineerforge_engine.application.print_service import (
    WALL_OVERHEAD_FRACTION,
    estimate_purge,
    estimate_usage,
    fits_build_volume,
)
from engineerforge_engine.domain.errors import InvalidRequestError
from engineerforge_engine.domain.materials import BuildVolume


@pytest.fixture
def cube_20mm(tmp_path: Path) -> Path:
    """A 20mm cube: volume exactly 8 cm³."""
    target = tmp_path / "cube20.stl"
    trimesh.creation.box(extents=(20.0, 20.0, 20.0)).export(str(target))
    return target


class TestUsageEstimate:
    def test_mass_and_cost_math(self, cube_20mm: Path) -> None:
        est = estimate_usage(str(cube_20mm), "pla", infill=0.2)
        assert est.volume_cm3 == pytest.approx(8.0, rel=1e-3)
        expected_solid = 8.0 * (0.2 + WALL_OVERHEAD_FRACTION * 0.8)
        assert est.solid_volume_cm3 == pytest.approx(expected_solid, rel=1e-3)
        expected_mass = expected_solid * 1.24
        assert est.mass_g == pytest.approx(expected_mass, rel=1e-2)
        assert est.cost == pytest.approx(expected_mass / 1000 * 20, abs=0.01)
        assert est.watertight is True
        assert any("wall/shell overhead" in a for a in est.assumptions)

    def test_full_infill_caps_at_solid(self, cube_20mm: Path) -> None:
        est = estimate_usage(str(cube_20mm), "pla", infill=1.0)
        assert est.solid_volume_cm3 == pytest.approx(8.0, rel=1e-3)

    def test_fit_check_against_printer(self, cube_20mm: Path) -> None:
        est = estimate_usage(str(cube_20mm), "petg", printer_id="flashforge-ad5x")
        assert est.fits_printer is True
        assert est.printer_id == "flashforge-ad5x"

    def test_oversized_part_does_not_fit(self, tmp_path: Path) -> None:
        big = tmp_path / "big.stl"
        trimesh.creation.box(extents=(250.0, 100.0, 100.0)).export(str(big))
        # 250 > 220 in X but fits the 300x250 Guider 3 after rotation logic
        est_small = estimate_usage(str(big), "pla", printer_id="flashforge-ad5x")
        assert est_small.fits_printer is False
        est_big = estimate_usage(str(big), "pla", printer_id="flashforge-guider-3")
        assert est_big.fits_printer is True

    def test_invalid_inputs(self, cube_20mm: Path) -> None:
        with pytest.raises(InvalidRequestError):
            estimate_usage(str(cube_20mm), "pla", infill=1.5)
        with pytest.raises(InvalidRequestError):
            estimate_usage(str(cube_20mm), "nope")
        with pytest.raises(InvalidRequestError):
            estimate_usage(str(cube_20mm), "pla", printer_id="nope")


class TestFitsBuildVolume:
    def test_rotation_about_z_allowed(self) -> None:
        volume = BuildVolume(x=200, y=148, z=150)
        assert fits_build_volume({"x": 140, "y": 190, "z": 100}, volume) is True
        assert fits_build_volume({"x": 190, "y": 190, "z": 100}, volume) is False
        assert fits_build_volume({"x": 50, "y": 50, "z": 151}, volume) is False


class TestPurgeEstimate:
    def test_single_material_is_zero(self) -> None:
        est = estimate_purge("flashforge-ad5x", ["pla"], height_mm=50)
        assert est.tool_changes == 0
        assert est.purge_mass_g == 0

    def test_single_material_printer_is_zero(self) -> None:
        est = estimate_purge(
            "flashforge-adventurer-5m-pro", ["pla", "petg"], height_mm=50
        )
        assert est.tool_changes == 0

    def test_filament_switching_math(self) -> None:
        # 40mm at 0.2mm = 200 layers; 2 materials → 200 × 1 × 0.5 = 100 changes
        est = estimate_purge(
            "flashforge-ad5x", ["pla", "pva"], height_mm=40, layer_height_mm=0.2
        )
        assert est.tool_changes == 100
        assert est.purge_volume_mm3 == pytest.approx(100 * 300)
        avg_density = (1.24 + 1.23) / 2
        assert est.purge_mass_g == pytest.approx(30_000 / 1000 * avg_density, rel=1e-3)

    def test_explicit_tool_changes_override(self) -> None:
        est = estimate_purge(
            "flashforge-ad5x",
            ["pla", "petg"],
            height_mm=40,
            tool_changes_override=12,
        )
        assert est.tool_changes == 12
        assert est.purge_volume_mm3 == pytest.approx(12 * 300)

    def test_idex_purges_less(self) -> None:
        switching = estimate_purge("flashforge-ad5x", ["abs", "hips"], height_mm=40)
        idex = estimate_purge("flashforge-creator-pro-2", ["abs", "hips"], height_mm=40)
        assert idex.purge_volume_mm3 < switching.purge_volume_mm3

    def test_invalid_inputs(self) -> None:
        with pytest.raises(InvalidRequestError):
            estimate_purge("nope", ["pla", "petg"], height_mm=10)
        with pytest.raises(InvalidRequestError):
            estimate_purge("flashforge-ad5x", ["pla", "petg"], height_mm=0)
