"""'Cowa' - the Cowaramup cow mascot, FRONT view (2D, for flat products).

Design language (applies to every product in the family):
  * Broad rounded forehead flowing into an OVERSIZED pink muzzle (the muzzle is
    ~45 % of face height - reads from 3 m away and is the key cuteness cue).
  * Sideways 'leaf' ears with pink inner ear.
  * Short, thick, up-curled horns in the tool-4 accent colour.
  * Signature asymmetric black patch over the cow's RIGHT eye (viewer's left)
    that takes the whole ear on that side, plus one small forehead spot on the
    other side.
  * Big oval eyes with a single highlight; the eye inside the patch gets a white
    ring so it stays readable.
  * No outlines, no thin lines: every region is a large contiguous colour block.

All coordinates are in head-width units (W = 1.0) and scaled by the caller.
Origin = head centre, +y up.
"""
from __future__ import annotations

from shapely import affinity
from shapely.ops import unary_union

from ..core import geom
from ..core.model import Painter2D

# ---- proportions (head-width units) ---------------------------------------
FOREHEAD = dict(c=(0.0, 0.12), r=(0.50, 0.42))
MUZZLE = dict(c=(0.0, -0.33), r=(0.46, 0.28))
EAR = dict(c=(0.62, 0.20), r=(0.23, 0.115), angle=-14.0)
EYE = dict(c=(0.21, 0.07), r=(0.080, 0.100))
NOSTRIL = dict(c=(0.15, -0.35), r=(0.065, 0.085), angle=18.0)


def _s(shape, W):
    return affinity.scale(shape, W, W, origin=(0, 0))


def cow_head(W: float):
    """Head outline (forehead + muzzle, convex hull) -> 2D."""
    fh = geom.ellipse(*FOREHEAD["c"], *FOREHEAD["r"])
    mz = geom.ellipse(*MUZZLE["c"], *MUZZLE["r"])
    return _s(unary_union([fh, mz]).convex_hull, W)


def cow_nose(W: float):
    """-> (muzzle, nostrils)."""
    mz = geom.ellipse(*MUZZLE["c"], *MUZZLE["r"])
    nx, ny = NOSTRIL["c"]
    rx, ry = NOSTRIL["r"]
    a = NOSTRIL["angle"]
    nostrils = unary_union([geom.ellipse(-nx, ny, rx, ry, -a), geom.ellipse(nx, ny, rx, ry, a)])
    return _s(mz, W), _s(nostrils, W)


def cow_ear(W: float, side: int):
    """side = +1 (viewer's right) or -1 -> (ear, inner_ear)."""
    cx, cy = EAR["c"]
    rx, ry = EAR["r"]
    ear = geom.ellipse(side * cx, cy, rx, ry, side * EAR["angle"])
    inner = geom.ellipse(side * (cx + 0.035), cy - 0.005, rx * 0.62, ry * 0.52, side * EAR["angle"])
    return _s(ear, W), _s(inner, W)


def cow_horn(W: float, side: int):
    pts = geom.bezier((side * 0.26, 0.42), (side * 0.40, 0.50), (side * 0.40, 0.72), 12)
    return _s(geom.tapered_stroke(pts, 0.095, 0.060, 20), W)


def cow_eye(W: float, side: int):
    """-> (eye, highlight, white ring used when the eye sits inside a patch)."""
    cx, cy = EYE["c"]
    rx, ry = EYE["r"]
    eye = geom.ellipse(side * cx, cy, rx, ry)
    hl = geom.circle(side * cx + 0.025, cy + 0.035, max(0.032, 1.05 / W))  # >= 3.4 mm2 at any size
    ring = eye.buffer(0.036, quad_segs=12)
    return _s(eye, W), _s(hl, W), _s(ring, W)


def cow_spot(W: float):
    """-> (signature patch over viewer-left eye + ear, small forehead spot)."""
    patch = geom.blob([(-0.31, 0.17, 0.20), (-0.44, 0.06, 0.13), (-0.17, 0.33, 0.12),
                       (-0.60, 0.22, 0.13), (-0.72, 0.17, 0.10), (-0.57, 0.10, 0.10),
                       (-0.48, 0.30, 0.08), (-0.80, 0.16, 0.09)], smooth=0.06)
    spot = geom.blob([(0.27, 0.36, 0.075), (0.35, 0.31, 0.055)], smooth=0.02)
    return _s(patch, W), _s(spot, W)


def face_painter(W: float, horns: bool = True) -> Painter2D:
    """Full mascot face as a Painter2D (tool roles, painter order = z-order)."""
    p = Painter2D()
    if horns:
        for s in (-1, 1):
            p.paint("tool_4", cow_horn(W, s), "horns")
    for s in (-1, 1):
        ear, inner = cow_ear(W, s)
        p.paint("tool_1", ear, "ears")
    p.paint("tool_1", cow_head(W), "head")
    patch, spot = cow_spot(W)
    # Patches are skin markings: clipped to head + ears so they never change the silhouette.
    # The signature patch takes the WHOLE left ear (no white slivers along the ear edge).
    skin = unary_union([cow_head(W)] + [cow_ear(W, s)[0] for s in (-1, 1)])
    patch = patch.union(cow_ear(W, -1)[0]).intersection(skin)
    p.paint("tool_2", patch, "signature patch")
    p.paint("tool_2", spot, "forehead spot")
    for s in (-1, 1):
        _, inner = cow_ear(W, s)
        p.paint("tool_3", inner, "inner ears")
    muzzle, nostrils = cow_nose(W)
    p.paint("tool_3", muzzle, "muzzle")
    p.paint("tool_2", nostrils, "nostrils")
    for s in (-1, 1):
        eye, hl, ring = cow_eye(W, s)
        if s == -1:  # eye inside the signature patch gets a white ring
            p.paint("tool_1", ring, "eye ring")
        p.paint("tool_2", eye, "eyes")
        p.paint("tool_1", hl, "eye highlights")
    return p
