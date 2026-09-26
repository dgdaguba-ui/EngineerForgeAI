"""Configuration system: every file loads, cross-references resolve, products are not hard-coded."""
from cad.core import config
from cad.core.model import TOOLS


def test_all_config_files_load():
    for name in ("colors", "materials", "toolheads", "dimensions", "costs", "variants"):
        assert config.load(name)


def test_toolheads_reference_known_materials_and_colours():
    th, mats, pal = config.toolheads(), config.materials(), config.palette()
    for t in TOOLS:
        assert th[t]["material"] in mats
        assert th[t]["colour"] in pal


def test_variants_reference_palette():
    pal = config.palette()
    for name, v in config.variants().items():
        for t in TOOLS:
            assert v[t] in pal, (name, t)


def test_palette_entries_complete():
    for key, c in config.palette().items():
        assert c["hex"].startswith("#") and len(c["hex"]) == 7
        assert c["suggested_tool"] in TOOLS
        assert set(c["materials"]) >= {"PLA", "PETG", "TPU"}
        for other in c["contrast_with"]:
            assert other in config.palette(), (key, other)


def test_every_material_has_a_price_and_bonding_rows():
    prices = config.costs()["filament_price_per_kg"]
    mats = config.materials()
    for m, spec in mats.items():
        assert spec["price_key"] in prices
        assert config.bond_quality(m, m) != "unknown"
    assert config.bond_quality("PLA", "TPU") == config.bond_quality("TPU", "PLA")


def test_product_sources_do_not_hardcode_materials():
    """Products declare tool ROLES; materials/colours must come from config."""
    from pathlib import Path
    for f in (Path(__file__).resolve().parents[1] / "cad" / "products").glob("crw*.py"):
        src = f.read_text()
        for colour in config.palette():
            assert f'"{colour}"' not in src, (f.name, colour)
