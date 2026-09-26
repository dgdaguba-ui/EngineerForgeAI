"""'Cowa' mascot, SIDE view (2D), for extruded-profile products (phone stand,
articulated cow). Same design language as the front view: oversized pink
muzzle, big eye with highlight, leaf ear, short thick horn, patch over the
cow's right eye.
"""
from __future__ import annotations

from shapely import affinity
from shapely.ops import unary_union

from ..core import geom


def cow_head_side(cx: float, cy: float, s: float, facing: int = 1, patch: bool = True) -> dict:
    """Head in side view. s = head height scale (mm). facing +1 = nose toward +u."""
    def P(shape):
        shape = affinity.scale(shape, s * facing, s, origin=(0, 0))
        return affinity.translate(shape, cx, cy)

    skull = geom.ellipse(0, 0, 0.45, 0.42)
    muzzle = geom.ellipse(0.40, -0.20, 0.31, 0.27, -8)
    ear = geom.ellipse(-0.30, 0.28, 0.26, 0.11, 28)
    inner = geom.ellipse(-0.33, 0.29, 0.16, 0.055, 28)
    horn = geom.tapered_stroke(geom.bezier((-0.06, 0.34), (0.02, 0.50), (0.10, 0.62), 10), 0.085, 0.055, 16)
    eye = geom.ellipse(0.14, 0.10, 0.075, 0.095)
    hl = geom.circle(0.165, 0.135, 0.038)
    nostril = geom.ellipse(0.62, -0.13, 0.055, 0.075, -15)
    head_patch = geom.blob([(0.08, 0.13, 0.20), (-0.10, 0.22, 0.16)], smooth=0.03)
    out = dict(skull=P(skull), muzzle=P(muzzle), ear=P(ear), inner_ear=P(inner), horn=P(horn),
               eye=P(eye), highlight=P(hl), nostril=P(nostril),
               eye_ring=P(eye.buffer(0.036)))
    out["outline"] = unary_union([out["skull"], out["muzzle"], out["ear"], out["horn"]])
    out["patch"] = P(head_patch).intersection(out["skull"]) if patch else None
    return out
