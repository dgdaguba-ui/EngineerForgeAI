"""Mechanisms: print-in-place hinge, pegs/sockets, snap joints.

hinge() - the 'bicone ring' print-in-place joint used by the articulated cow:
  * Both members span the FULL print thickness and start on the bed - no
    member is ever printed over an air gap (no floating layers, no bridges).
  * The post (on member A) is a bicone: narrow at the bed, widening at 45 deg to
    r_max, narrowing again at the top. The ring (member B) has the matching
    hole + radial clearance. 45-degree faces are self-supporting and trap the
    ring vertically; the ring wraps > 180 deg to trap it in-plane.
  * The post is tied to member A by a 'neck' that passes through an opening in
    the ring. The opening is the neck swept over the range of motion, so the
    neck doubles as a HARD STOP at both ends of travel.
"""
from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from ..core import geom


def sweep2d(shape, pivot, rom_deg, step: float = 2.5):
    """Union of `shape` rotated about pivot over [rom0, rom1] degrees."""
    a0, a1 = rom_deg
    n = max(2, int(math.ceil(abs(a1 - a0) / step)) + 1)
    return unary_union([affinity.rotate(shape, a, origin=tuple(pivot)) for a in np.linspace(a0, a1, n)])


def bicone_profile(r_min: float, r_max: float, T: float, grow: float = 0.0):
    taper = r_max - r_min
    return [(0, 0), (r_min + grow, 0), (r_max + grow, taper), (r_max + grow, T - taper),
            (r_min + grow, T), (0, T)]


def hinge(pivot, T: float, r_max: float, taper: float, clearance: float, ring_wall: float,
          neck_dir, neck_w: float, neck_len: float, rom_deg):
    """Build a bicone print-in-place joint at `pivot` (2D, profile plane).

    Member A (fixed) receives: post (3D), neck (2D, full thickness).
    Member B (moving) receives: ring disc (2D, add), hole (3D, subtract),
    opening (2D, subtract). `rom_deg` = motion of B relative to A (CCW +).
    """
    px, py = pivot
    r_min = r_max - taper
    c = clearance
    post = geom.revolve_profile(bicone_profile(r_min, r_max, T), px, py, 96)
    hole = geom.revolve_profile(bicone_profile(r_min, r_max, T, grow=c), px, py, 96)
    # widen the hole slightly beyond the part on both faces so it is always open
    hole = hole + geom.cylinder_z(px, py, -0.5, 0.01, r_min + c, 96) + geom.cylinder_z(px, py, T - 0.01, T + 0.5, r_min + c, 96)
    r_out = r_max + c + ring_wall
    ring = geom.circle(px, py, r_out)
    dx, dy = np.asarray(neck_dir, float) / np.linalg.norm(neck_dir)
    nx, ny = -dy, dx
    L = neck_len
    hw = neck_w / 2
    neck = Polygon([(px + nx * hw, py + ny * hw), (px + nx * hw + dx * L, py + ny * hw + dy * L),
                    (px - nx * hw + dx * L, py - ny * hw + dy * L), (px - nx * hw, py - ny * hw)])
    # B rotates by +a relative to A  ==  A's neck rotates by -a in B's frame
    opening = sweep2d(neck.buffer(c, quad_segs=4), pivot, (-rom_deg[1], -rom_deg[0]))
    # in-plane retention: chord of the opening at the ring's inner radius < post diameter
    r_in = r_max + c
    ring_band = geom.circle(px, py, r_in + 0.05).difference(geom.circle(px, py, r_in - 0.05))
    chord = ring_band.intersection(opening)
    chord_len = 0.0
    if not chord.is_empty:
        pts = np.asarray(chord.envelope.exterior.coords) if chord.geom_type != "Point" else np.zeros((1, 2))
        chord_len = float(max(np.linalg.norm(a - b) for a in pts for b in pts))
    return {
        "pivot": (px, py), "post": post, "hole": hole, "ring": ring, "neck": neck, "opening": opening,
        "r_min": r_min, "r_max": r_max, "r_out": r_out, "clearance": c, "rom_deg": tuple(rom_deg),
        "retention_chord": chord_len, "post_diameter": 2 * r_max,
    }


def peg(d: float, h: float, chamfer: float = 0.4):
    """Chamfered cylindrical peg (bed at z=0) - for modular Build-a-Cow parts."""
    body = geom.cylinder_z(0, 0, 0, h - chamfer, d / 2, 64)
    tip = geom.Manifold.cylinder(chamfer, d / 2, d / 2 - chamfer, 64).translate([0, 0, h - chamfer])
    return body + tip


def socket(d: float, h: float, clearance: float = 0.15):
    """Matching socket (to subtract): diameter d + 2*clearance, depth h + 0.3."""
    return geom.cylinder_z(0, 0, -0.01, h + 0.3, d / 2 + clearance, 64)


def snap_joint(length: float = 8.0, thickness: float = 1.6, hook: float = 0.8, width: float = 5.0):
    """Cantilever snap hook, profile in XZ extruded along Y, printed standing
    (arm vertical) so the flex is across layers' strong direction."""
    prof = Polygon([(0, 0), (thickness, 0), (thickness, length - 1.6), (thickness + hook, length - 1.0),
                    (thickness, length), (0, length)])
    solid = geom.extrude(prof, 0, width).rotate([90, 0, 0])
    bb = solid.bounding_box()
    return solid.translate([0, -bb[1], -bb[2]])
