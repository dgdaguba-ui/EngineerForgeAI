"""'Cowa' mascot as true 3D components (for figurines).

Every rounded component is a `teardrop` (ellipsoid + 45-degree keel) so the
assembled figure prints WITHOUT supports. Frame: +x = the cow's nose direction,
+y = cow's left, z up, z = zb is the top of the plinth.

All functions take the plinth-top height `zb` and a scale `k` (1.0 = 50 mm mini).
"""
from __future__ import annotations

from ..core import geom


def _p(k, zb, x, y, z):
    return (x * k, y * k, zb + z * k)


def _r(k, *r):
    return tuple(v * k for v in r)


def cow_body(k: float, zb: float):
    """Resting (lying) body + hind-leg hip bulges. Lying = no belly overhang,
    no thin legs to snap in a suitcase."""
    body = geom.teardrop(_p(k, zb, -4, 0, 8.5), _r(k, 19, 11.5, 9.5), floor=zb - 0.4)
    hips = [geom.teardrop(_p(k, zb, -12, s * 8.5, 5.5), _r(k, 8.0, 4.5, 5.0), floor=zb - 0.4) for s in (-1, 1)]
    return geom.union([body, *hips])


def _grounded(m, zb):
    """Hull a lying capsule with its own shadow so its underside is vertical (no undercut)."""
    return geom.Manifold.batch_hull([m, m.translate([0, 0, -4.0])]).trim_by_plane([0, 0, 1], zb - 0.4)


def cow_leg(k: float, zb: float):
    """Folded front legs lying on the plinth (x-forward capsules)."""
    return geom.union(_grounded(geom.capsule(_p(k, zb, 5, s * 6.2, 3.0), _p(k, zb, 15.5, s * 6.8, 2.9), 3.0 * k), zb)
                      for s in (-1, 1))


def cow_hooves(k: float, zb: float):
    front = [geom.teardrop(_p(k, zb, 17.2, s * 6.8, 2.8), _r(k, 2.6, 2.9, 2.8), floor=zb - 0.4) for s in (-1, 1)]
    hind = [geom.teardrop(_p(k, zb, -2.8, s * 11.3, 2.6), _r(k, 2.6, 2.2, 2.4), floor=zb - 0.4) for s in (-1, 1)]
    return geom.union(front + hind)


def cow_head(k: float, zb: float):
    return geom.teardrop(_p(k, zb, 15.5, 0, 13.8), _r(k, 7.8, 8.2, 8.0), floor=zb - 0.4)


def cow_nose(k: float, zb: float):
    """-> (muzzle, nostril dimples to SUBTRACT). Nostrils are geometry, not colour:
    shadows read as nostrils and save ~20 tool changes."""
    muzzle = geom.teardrop(_p(k, zb, 22.0, 0, 9.6), _r(k, 5.4, 7.0, 5.0), floor=zb - 0.4)
    dimples = geom.union(geom.ellipsoid(_p(k, zb, 27.1, s * 2.7, 10.6), _r(k, 0.9, 1.1, 1.3), 24) for s in (-1, 1))
    return muzzle, dimples


def cow_ear(k: float, zb: float):
    return geom.union(geom.teardrop(_p(k, zb, 13.0, s * 9.6, 16.8), _r(k, 2.2, 3.8, 1.8), floor=zb - 0.4)
                      for s in (-1, 1))


def cow_horn(k: float, zb: float):
    return geom.union(geom.capsule(_p(k, zb, 13.3, s * 4.2, 19.8), _p(k, zb, 12.7, s * 6.4, 24.3), 1.9 * k, 1.25 * k)
                      for s in (-1, 1))


def cow_eye(k: float, zb: float):
    """-> (eyes, white ring for the eye inside the patch). Centred on the head surface
    so the painter clips them flush."""
    eyes = geom.union(geom.ellipsoid(_p(k, zb, 21.1, s * 4.9, 15.3), _r(k, 1.6, 1.5, 2.0), 32) for s in (-1, 1))
    ring = geom.ellipsoid(_p(k, zb, 21.1, -4.9, 15.3), _r(k, 2.5, 2.4, 2.9), 32)
    return eyes, ring


def cow_spot(k: float, zb: float):
    """Signature patches: saddle over the back (occupies only the top layers), one hip
    patch, and the head patch over the cow's RIGHT eye (matches the flat mascot)."""
    saddle = geom.union([geom.ellipsoid(_p(k, zb, -6, 2, 19), _r(k, 8, 8, 4.5)),
                         geom.ellipsoid(_p(k, zb, -12, -3, 17.5), _r(k, 5.5, 6.5, 4.5))])
    hip = geom.ellipsoid(_p(k, zb, -15, 11.5, 9), _r(k, 5.5, 3.5, 5.0))
    head = geom.union([geom.ellipsoid(_p(k, zb, 19.0, -6.5, 16.3), _r(k, 5.4, 4.6, 5.2)),
                       geom.ellipsoid(_p(k, zb, 14.0, -9.6, 17.1), _r(k, 3.2, 4.4, 3.0))])
    return geom.union([saddle, hip, head])


def cow_tail(k: float, zb: float):
    """-> (tail, tuft). Tail lies on the plinth (fully supported)."""
    pts = [(-21.5, 1.5, 6.5), (-24.0, 6.0, 2.2), (-21.0, 11.5, 1.8)]
    tail = geom.union([geom.teardrop_capsule(_p(k, zb, *pts[0]), _p(k, zb, *pts[1]), 1.5 * k),
                       _grounded(geom.capsule(_p(k, zb, *pts[1]), _p(k, zb, *pts[2]), 1.5 * k), zb)]).trim_by_plane([0, 0, 1], zb - 0.4)
    tuft = geom.teardrop(_p(k, zb, -18.8, 13.2, 2.0), _r(k, 2.8, 2.4, 2.0), floor=zb - 0.4)
    return tail, tuft
