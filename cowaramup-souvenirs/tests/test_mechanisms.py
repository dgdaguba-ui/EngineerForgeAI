"""Print-in-place articulated cow: clearance, retention, range of motion."""
import numpy as np

from cad.core import analysis
from cad.mechanisms.joints import hinge, peg, socket, snap_joint


def rotate_about(solid, pivot, deg):
    return solid.translate([-pivot[0], -pivot[1], 0]).rotate([0, 0, deg]).translate([pivot[0], pivot[1], 0])


def test_members_are_separate_with_clearance(products):
    envs = analysis.group_envelopes(products["CRW-005"])
    body = envs.pop("body")
    for name, m in envs.items():
        assert (m ^ body).volume() < 1e-3, name
        assert body.min_gap(m, 2.0) >= 0.3, name


def test_range_of_motion_is_interference_free(products):
    p = products["CRW-005"]
    envs = analysis.group_envelopes(p)
    body = envs["body"]
    for name, j in p.checks["joints"].items():
        for ang in np.linspace(*j["rom_deg"], 7):
            assert (rotate_about(envs[name], j["pivot"], ang) ^ body).volume() < 0.5, (name, ang)


def test_joints_retain_their_members(products):
    for name, j in products["CRW-005"].checks["joints"].items():
        assert j["retention_chord"] < j["post_diameter"], name


def test_leg_stops_prevent_parallelogram_collapse(products):
    j = products["CRW-005"].checks["joints"]
    assert j["front_leg"]["rom_deg"][0] >= 0 and j["rear_leg"]["rom_deg"][1] <= 0


def test_hinge_hole_is_larger_than_post():
    h = hinge((0, 0), 18, 4.2, 1.6, 0.5, 2.8, (0, 1), 3.6, 12, (0, 25))
    assert h["hole"].volume() > h["post"].volume()
    assert (h["post"] - h["hole"]).is_empty()


def test_library_mechanisms_build():
    assert peg(5, 8).volume() > 0
    assert socket(5, 8).volume() > peg(5, 8).volume()
    assert snap_joint().volume() > 0
