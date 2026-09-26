"""Geometry kernel helpers.

All solid modelling goes through manifold3d (guaranteed-manifold CSG) and all
2D design work goes through shapely (offsets, unions, minimum-feature checks).
Units are millimetres. Print coordinates: +Z is the build direction.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

import manifold3d as m3d
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

SEGMENTS = 72          # circle resolution for spheres / cylinders
SHAPE_RES = 48         # shapely buffer resolution (quad_segs = SHAPE_RES / 4)
SIMPLIFY_TOL = 0.0     # mm; per-shape simplification OFF - coverage simplification is used instead

Manifold = m3d.Manifold
CrossSection = m3d.CrossSection


# --------------------------------------------------------------------------- 2D
def circle(cx: float, cy: float, r: float) -> Polygon:
    return Point(cx, cy).buffer(r, quad_segs=SHAPE_RES // 4)


def ellipse(cx: float, cy: float, rx: float, ry: float, angle_deg: float = 0.0) -> Polygon:
    e = affinity.scale(Point(0, 0).buffer(1.0, quad_segs=SHAPE_RES // 4), rx, ry)
    if angle_deg:
        e = affinity.rotate(e, angle_deg, origin=(0, 0))
    return affinity.translate(e, cx, cy)


def rounded_rect(cx: float, cy: float, w: float, h: float, r: float) -> Polygon:
    r = min(r, w / 2 - 1e-3, h / 2 - 1e-3)
    core = Polygon([(-w / 2 + r, -h / 2 + r), (w / 2 - r, -h / 2 + r),
                    (w / 2 - r, h / 2 - r), (-w / 2 + r, h / 2 - r)])
    return affinity.translate(core.buffer(r, quad_segs=SHAPE_RES // 4), cx, cy)


def blob(circles: Iterable[Sequence[float]], smooth: float = 0.0) -> Polygon:
    """Organic patch: union of (x, y, r) circles, optionally rounded (closing)."""
    shape = unary_union([circle(x, y, r) for x, y, r in circles])
    if smooth > 0:
        shape = shape.buffer(smooth, quad_segs=SHAPE_RES // 4).buffer(-smooth, quad_segs=SHAPE_RES // 4)
    # fill enclosed holes: a pin-hole of body colour inside a patch is an unprintable island
    return unary_union([Polygon(p.exterior) for p in polygons_of(shape)])


def tapered_stroke(points: Sequence[Sequence[float]], r0: float, r1: float, n: int = 24) -> Polygon:
    """A smooth tapered stroke along a polyline (horns, tails)."""
    pts = np.asarray(points, float)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    ts = np.linspace(0, seg[-1], n)
    xs = np.interp(ts, seg, pts[:, 0])
    ys = np.interp(ts, seg, pts[:, 1])
    rs = np.linspace(r0, r1, n)
    discs = [circle(x, y, r) for x, y, r in zip(xs, ys, rs)]
    return unary_union([discs[i].union(discs[i + 1]).convex_hull for i in range(n - 1)])


def bezier(p0, p1, p2, n: int = 16) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(p, float) for p in (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def mirror_x(shape, x0: float = 0.0):
    return affinity.scale(shape, -1, 1, origin=(x0, 0))


def mirror_about_own_centre(shape):
    c = shape.centroid
    return affinity.scale(shape, -1, 1, origin=(c.x, c.y))


def clean(shape, eps: float = 1e-4):
    """Remove slivers and invalid rings produced by boolean chains."""
    if shape.is_empty:
        return shape
    return shape.buffer(eps, quad_segs=2).buffer(-eps, quad_segs=2)


def depinch(shape, eps: float = 0.01, close: bool = False):
    """Remove point contacts (pinches) and hair-line slivers.
    Opening (erode, dilate) separates lobes touching at a point; closing joins them."""
    if shape is None or shape.is_empty:
        return shape
    if close:
        return shape.buffer(eps, quad_segs=4, join_style="mitre").buffer(-eps, quad_segs=4, join_style="mitre")
    return shape.buffer(-eps, quad_segs=4, join_style="mitre").buffer(eps, quad_segs=4, join_style="mitre")


def pinch_points(shape) -> list:
    """Points where a region touches itself (hole touches shell, or two member
    polygons touch) at a single point. Each becomes a non-manifold edge on extrusion."""
    from itertools import combinations
    from shapely.geometry import Point as _P

    def pts(g):
        if g.is_empty:
            return []
        if g.geom_type == "Point":
            return [g]
        if g.geom_type in ("MultiPoint", "GeometryCollection"):
            return [x for x in g.geoms if x.geom_type == "Point"]
        return []
    out = []
    polys = polygons_of(shape)
    for p in polys:
        rings = [p.exterior] + list(p.interiors)
        for ring in rings:  # ring touching itself (repeated vertex)
            c = np.asarray(ring.coords)[:-1].round(9)
            u, cnt = np.unique(c, axis=0, return_counts=True)
            out += [_P(*xy) for xy in u[cnt > 1]]
        for a, b in combinations(rings, 2):
            out += pts(a.intersection(b))
    for a, b in combinations(polys, 2):
        out += pts(a.boundary.intersection(b.boundary))
    return [_P(round(q.x, 9), round(q.y, 9)) for q in out]


def polygons_of(shape) -> list[Polygon]:
    if shape is None or shape.is_empty:
        return []
    if isinstance(shape, Polygon):
        return [shape]
    if isinstance(shape, MultiPolygon):
        return list(shape.geoms)
    out = []
    for g in getattr(shape, "geoms", []):   # GeometryCollection: keep polygonal members only
        out += polygons_of(g)
    return out


def polyonly(shape):
    """Drop lines/points that boolean or precision ops can leave in a collection."""
    ps = [p for p in polygons_of(shape) if p.area > 0]
    if not ps:
        return Polygon()
    return ps[0] if len(ps) == 1 else MultiPolygon(ps)


def to_cross_section(shape) -> CrossSection:
    contours = []
    if SIMPLIFY_TOL > 0:
        shape = shape.simplify(SIMPLIFY_TOL, preserve_topology=True)
    for p in polygons_of(shape):
        if p.area < 1e-6:
            continue
        p = orient(p, 1.0)
        contours.append(np.asarray(p.exterior.coords)[:-1])
        for ring in p.interiors:
            contours.append(np.asarray(ring.coords)[:-1])
    return CrossSection(contours, m3d.FillRule.EvenOdd)


# --------------------------------------------------------------------------- 3D
def empty() -> Manifold:
    return Manifold()


def extrude(shape, z0: float, z1: float) -> Manifold:
    """Extrude a shapely (Multi)Polygon between z0 and z1."""
    if shape is None or shape.is_empty or z1 <= z0:
        return Manifold()
    return Manifold.extrude(to_cross_section(shape), z1 - z0).translate([0, 0, z0])


def union(parts: Iterable[Manifold]) -> Manifold:
    parts = [p for p in parts if p is not None and not p.is_empty()]
    if not parts:
        return Manifold()
    return Manifold.batch_boolean(parts, m3d.OpType.Add)


def ellipsoid(c, r, segments: int = SEGMENTS) -> Manifold:
    return Manifold.sphere(1.0, segments).scale(list(r)).translate(list(c))


def teardrop(c, r, floor: float | None = None, segments: int = SEGMENTS) -> Manifold:
    """Ellipsoid with a 45-degree 'keel' underneath so it prints without support.

    For an ellipse with semi-axes a (horizontal) and c (vertical), the apex of the
    45-degree tangent cone lies sqrt(a^2 + c^2) below the centre. Using the larger
    horizontal semi-axis makes every side at least 45 degrees.
    """
    cx, cy, cz = c
    rx, ry, rz = r
    depth = math.sqrt(rz ** 2 + max(rx, ry) ** 2)
    e = ellipsoid(c, r, segments)
    tip = Manifold.sphere(0.05, 8).translate([cx, cy, cz - depth])
    shape = Manifold.batch_hull([e, tip])
    if floor is not None:
        shape = shape.trim_by_plane([0, 0, 1], floor)
    return shape


def capsule(p0, p1, r0: float, r1: float | None = None, segments: int = 48) -> Manifold:
    r1 = r0 if r1 is None else r1
    a = Manifold.sphere(r0, segments).translate(list(p0))
    b = Manifold.sphere(r1, segments).translate(list(p1))
    return Manifold.batch_hull([a, b])


def teardrop_capsule(p0, p1, r: float, segments: int = 48) -> Manifold:
    """Capsule whose underside is made self-supporting by 45-degree keels at both ends."""
    a = teardrop(p0, (r, r, r), segments=segments)
    b = teardrop(p1, (r, r, r), segments=segments)
    return Manifold.batch_hull([a, b])


def cylinder_z(cx: float, cy: float, z0: float, z1: float, r: float, segments: int = SEGMENTS) -> Manifold:
    return Manifold.cylinder(z1 - z0, r, r, segments).translate([cx, cy, z0])


def revolve_profile(rz: Sequence[Sequence[float]], cx: float, cy: float, segments: int = SEGMENTS) -> Manifold:
    """Revolve an (r, z) polyline profile (closed against the axis) about a vertical axis."""
    pts = [(max(r, 0.0), z) for r, z in rz]
    cs = CrossSection([np.asarray(pts, float)], m3d.FillRule.Positive)
    return Manifold.revolve(cs, segments).translate([cx, cy, 0])


def floor_trim(m: Manifold, z: float = 0.0) -> Manifold:
    return m.trim_by_plane([0, 0, 1], z)


def mesh_arrays(m: Manifold):
    """(vertices Nx3 float64, faces Mx3 int64) of a manifold."""
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    f = np.asarray(mesh.tri_verts, dtype=np.int64)
    return v, f
