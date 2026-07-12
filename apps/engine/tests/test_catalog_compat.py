from __future__ import annotations

import pytest
from engineerforge_engine.application.compat_service import analyze
from engineerforge_engine.domain.errors import InvalidRequestError
from engineerforge_engine.services.catalog import (
    load_materials,
    load_printers,
    material_by_id,
    printer_by_id,
)


class TestCatalog:
    def test_materials_load_and_validate(self) -> None:
        materials = load_materials()
        ids = {m.id for m in materials}
        assert {"pla", "petg", "abs", "asa", "pa", "pa-cf", "tpu95a", "pc", "pva", "hips"} <= ids
        pla = material_by_id("pla")
        assert pla is not None
        assert pla.density_g_cm3 == pytest.approx(1.24)
        assert pla.print_temp_min_c < pla.print_temp_max_c

    def test_printers_load_with_flashforge_multimaterial(self) -> None:
        printers = load_printers()
        ad5x = printer_by_id("flashforge-ad5x")
        assert ad5x is not None
        assert ad5x.material_slots == 4
        assert ad5x.multi_material_system == "filament-switching"
        assert ad5x.purge_per_change_mm3 > 0
        assert all(p.brand == "Flashforge" for p in printers)

    def test_unknown_lookups_return_none(self) -> None:
        assert material_by_id("unobtainium") is None
        assert printer_by_id("prusa-mk4") is None


class TestCompatibility:
    def test_pla_pva_is_soluble_support_pairing(self) -> None:
        report = analyze(["pla", "pva"])
        assert report.worst == "ok"
        assert "soluble support" in report.pairs[0].reasons[0].lower()

    def test_pla_abs_incompatible(self) -> None:
        report = analyze(["pla", "abs"])
        assert report.worst == "incompatible"

    def test_pva_degrades_with_hot_materials(self) -> None:
        report = analyze(["abs", "pva"])
        assert report.worst == "incompatible"
        assert any("degrades" in r for r in report.pairs[0].reasons)

    def test_abs_asa_same_family_ok(self) -> None:
        report = analyze(["abs", "asa"])
        assert report.worst == "ok"

    def test_hips_supports_abs(self) -> None:
        report = analyze(["abs", "hips"])
        assert report.worst == "ok"

    def test_petg_tpu_good_adhesion(self) -> None:
        report = analyze(["petg", "tpu95a"])
        assert report.worst in ("ok", "caution")
        pair = report.pairs[0]
        assert pair.nozzle_temp_overlap_c > 0

    def test_four_material_ad5x_scenario(self) -> None:
        # a realistic AD5X 4-slot loadout
        report = analyze(["pla", "pla", "petg", "pva"])
        # duplicates collapse; 3 distinct → 3 pairs
        assert len(report.pairs) == 3
        assert report.worst == "caution"  # PLA–PETG adhesion caution

    def test_temp_window_escalation(self) -> None:
        # PLA (190-220) vs PC (260-290): no overlap → incompatible
        report = analyze(["pla", "pc"])
        pair = report.pairs[0]
        assert pair.nozzle_temp_overlap_c < 0
        assert pair.level == "incompatible"

    def test_requires_two_distinct_materials(self) -> None:
        with pytest.raises(InvalidRequestError):
            analyze(["pla", "pla"])
        with pytest.raises(InvalidRequestError):
            analyze(["pla", "made-up"])
