"""Reusable functional accessories: keyring loops, magnet pockets, phone slots,
TPU pads, signs and bases."""
from __future__ import annotations

import math

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon

from ..core import geom
from ..core.text import text_shape


def keyring_loop(cx: float, cy: float, hole_d: float, ring_wall: float):
    """-> (loop disc, hole). Ring wall is absolute (not scaled) for strength."""
    r_out = hole_d / 2 + ring_wall
    return geom.circle(cx, cy, r_out), geom.circle(cx, cy, hole_d / 2)


def magnet_cavity(cx: float, cy: float, diameter: float, depth: float, clearance: float,
                  z_open: float = 0.0, up: bool = True) -> geom.Manifold:
    """Press-fit magnet pocket opening on a planar face at z_open.

    Pocket is diameter + 2*clearance wide and depth + 0.2 deep (glue/tolerance
    room). Opening on the bed face means the pocket ceiling is a short circular
    bridge (< 13 mm), which every FFF printer handles without support.
    """
    r = diameter / 2 + clearance
    d = depth + 0.2
    z0, z1 = (z_open, z_open + d) if up else (z_open - d, z_open)
    return geom.cylinder_z(cx, cy, z0, z1, r, 64)


def cow_sign(text: str, w: float, h: float, cap: float, cx: float = 0.0, cy: float = 0.0,
             corner: float | None = None, min_counter: float = 0.0):
    """Banner/sign board + text. -> (board, text). Text is meant to be KNOCKED OUT
    of the board so it shows the core colour: zero extra tool changes for lettering."""
    corner = h * 0.35 if corner is None else corner
    board = geom.rounded_rect(cx, cy, w, h, corner)
    txt = text_shape(text, cap, cx, cy, max_width=w - 2 * max(2.0, h * 0.2), min_counter=min_counter)
    return board, txt


def cow_base(length: float, width: float, height: float, text: str | None = None,
             text_h: float = 5.0, text_depth: float = 0.6) -> tuple[geom.Manifold, geom.Manifold | None]:
    """Oval collectible plinth centred on the origin, sitting on z=0.

    Returns (plinth, underside_text_cut). Underside text is DEBOSSED into the
    bed face - single colour, zero tool changes, readable provenance mark.
    """
    oval = geom.ellipse(0, 0, length / 2, width / 2)
    chamfer = 0.8
    plinth = geom.union([
        geom.extrude(oval.buffer(-chamfer), 0, chamfer),
        geom.Manifold.batch_hull([geom.extrude(oval.buffer(-chamfer), 0, 0.01),
                                  geom.extrude(oval, chamfer, chamfer + 0.01)]),
        geom.extrude(oval, chamfer, height),
    ])
    cut = None
    if text:
        t = text_shape(text, text_h, 0, 0, max_width=length * 0.72)
        t = geom.mirror_x(t)  # read correctly when the piece is flipped over
        cut = geom.extrude(t, -0.01, text_depth)
    return plinth, cut


def phone_slot(floor_u: float, floor_v: float, lean_deg: float, width: float, depth: float):
    """2D slot (side profile) for a phone leaning back at lean_deg from horizontal.

    Returns (slot polygon, geometry dict). Profile frame: u = front(+)/back, v = up.
    """
    a = math.radians(lean_deg)
    d = np.array([-math.cos(a), math.sin(a)])      # up the lean (towards the back)
    n = np.array([math.sin(a), math.cos(a)])       # slot normal, towards the front
    f = np.array([floor_u, floor_v])
    L = depth + 60.0
    rear0, front0 = f - n * width / 2, f + n * width / 2
    slot = Polygon([rear0, front0, front0 + d * L, rear0 + d * L])
    return slot, {"floor": f, "dir": d, "normal": n, "rear0": rear0, "front0": front0}


def dovetail_dims(neck: float, depth: float) -> dict:
    """Shared dovetail geometry for groove (PLA) and key (TPU).

    neck height d0, flared foot up to d1 = depth with a 0.3 mm vertical land at
    the tip (no knife edges). The flare is limited to 40 deg from vertical so the
    TPU key prints face-down without support.
    """
    import math as _m
    d0, land = 0.8, 0.3
    flare = min(0.55 * depth, (depth - land - d0) * _m.tan(_m.radians(40)))
    return {"hn": neck / 2, "hf": neck / 2 + flare, "d0": d0, "d1": depth, "land": land}


def dovetail_groove_profile(p, inward, along, width: float, depth: float, neck: float, clearance: float = 0.0):
    """2D dovetail groove cut into a wall face at point p (profile plane).

    `inward` is the unit vector into the material, `along` the unit vector along
    the face. Neck (opening) is narrower than the foot -> the insert is captured.
    """
    p, inward, along = (np.asarray(v, float) for v in (p, inward, along))
    k = dovetail_dims(neck, depth)
    c = clearance
    hn, hf, d0, d1, land = k["hn"] + c, k["hf"] + c, k["d0"] + c, k["d1"] + c, k["land"]
    pts = [p + along * hn - inward * 0.3, p + along * hn + inward * d0, p + along * hf + inward * (d1 - land),
           p + along * hf + inward * d1, p - along * hf + inward * d1, p - along * hf + inward * (d1 - land),
           p - along * hn + inward * d0, p - along * hn - inward * 0.3]
    return Polygon(pts)


def tpu_pad(length: float, pad_w: float, pad_t: float, neck: float, groove_depth: float) -> geom.Manifold:
    """Slide-in TPU pad strip with a dovetail key, modelled in its PRINT orientation:
    pad face on the bed (z=0), key upward. Cross-section lies in the XZ plane,
    strip runs along Y.

      z=0 ........ pad face (contacts the phone / desk)
      pad_t ...... pad back (sits on the wall face)
      + key: 0.8 mm neck, then a foot flared at <= 40 deg (no support)
    """
    k = dovetail_dims(neck, groove_depth)
    hn, hf, d0, d1, land = k["hn"], k["hf"], k["d0"], k["d1"], k["land"]
    z_pad = pad_t
    poly = Polygon([(-pad_w / 2, 0), (pad_w / 2, 0), (pad_w / 2, z_pad), (hn, z_pad),
                    (hn, z_pad + d0), (hf, z_pad + d1 - land), (hf, z_pad + d1), (-hf, z_pad + d1),
                    (-hf, z_pad + d1 - land), (-hn, z_pad + d0), (-hn, z_pad), (-pad_w / 2, z_pad)])
    # extrude along Y: build in XY then rotate so profile lies in XZ
    solid = geom.extrude(poly, 0, length)                     # profile in XY, length along Z
    solid = solid.rotate([90, 0, 0])                          # Z -> -Y
    bb = solid.bounding_box()
    return solid.translate([0, -bb[1], -bb[2]])
