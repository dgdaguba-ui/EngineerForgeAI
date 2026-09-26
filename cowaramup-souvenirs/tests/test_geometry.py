"""Geometry QC on every prototype: manifold, disjoint parts, tool ids, dimensions."""
import trimesh

from cad.core import analysis, config, export, geom
from cad.core.model import TOOLS


def test_parts_are_manifold_and_positive(products):
    for pid, p in products.items():
        for part in p.parts:
            assert str(part.solid.status()) == "Error.NoError", (pid, part.name)
            assert part.solid.volume() > 0, (pid, part.name)
            assert part.tool in TOOLS


def test_parts_survive_vertex_welding(products, tmp_path):
    """STL readers weld vertices by position - parts must stay watertight."""
    for pid, p in products.items():
        for part in p.parts:
            f = tmp_path / f"{pid}-{part.name}.stl"
            export.to_trimesh(part.solid).export(f)
            assert trimesh.load(f).is_watertight, (pid, part.name)


def test_parts_do_not_overlap(products):
    for pid, p in products.items():
        assert analysis.pairwise_overlap(p) < 0.01, pid


def test_every_used_tool_has_a_declared_role(products):
    for pid, p in products.items():
        for t in p.tools_used():
            assert t in p.tool_roles, (pid, t)


def test_keyring_dimensions_and_loop(products):
    p = products["CRW-001"]
    w, h, t = p.checks["envelope_mm"]
    assert 45 <= max(w, h) <= 60
    assert p.checks["keyring_hole_d"] >= 4.5 and p.checks["keyring_ring_wall"] >= 3.0


def test_sandwich_inlays_confine_colour_to_face_layers(products):
    """Keyring: colour tools only on the 3 bottom + 3 top layers."""
    M, _ = analysis.layer_presence(products["CRW-001"], 0.2)
    colour_layers = [i for i, row in enumerate(M) if row[1:].any()]
    assert colour_layers == [0, 1, 2, len(M) - 3, len(M) - 2, len(M) - 1]


def test_magnet_pocket_ceiling(products):
    assert products["CRW-002"].checks["ceiling_above_pocket"] >= 1.0


def test_mini_cow_is_support_free(products):
    env = geom.union(pt.solid for pt in products["CRW-003"].parts)
    assert analysis.overhang_report(env)["steep_overhang_area_mm2"] <= 5.0


def test_phone_stand_pads_are_separate_flexible_objects(products):
    p = products["CRW-004"]
    pads = [pt for pt in p.parts if pt.tool == "tool_4"]
    assert len(pads) == 4
    assert all(pt.requires.get("flexible") and pt.object_group.startswith("pad_") for pt in pads)
    assert all(v["stable"] for v in p.checks["phone_cases"].values())
    assert p.checks["max_device_thickness"] >= 12.0


def test_everything_fits_the_bed(products):
    pr = config.printer()
    for pid, p in products.items():
        bb = geom.union(pt.solid for pt in p.parts).bounding_box()
        w, d, h = bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]
        assert (w <= pr["bed_x_mm"] and d <= pr["bed_y_mm"]) or (d <= pr["bed_x_mm"] and w <= pr["bed_y_mm"]), pid
        assert h <= pr["max_z_mm"]
