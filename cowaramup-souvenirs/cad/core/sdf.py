"""Signed-distance-field (SDF) sculpting engine.

Why: CSG of ellipsoids gives a "primitive toy" look (visible joins, no fillets).
SDF modelling gives sculpted, blended forms: smooth unions (organic necks, fillets
at every join), grooves (smiles, hoof splits), sockets (eyes) and relief, and an
exact "support-free closure" pass for FDM.

Convention: negative inside, units mm, z up. Fields are evaluated on a regular
grid (numpy, vectorised) and meshed with marching cubes; the result is converted
to a manifold3d Manifold for exact colour booleans and export.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import manifold3d as m3d
import numpy as np
from scipy import ndimage


# ------------------------------------------------------------------ grid
@dataclass
class Grid:
    lo: np.ndarray
    hi: np.ndarray
    h: float

    def __post_init__(self):
        self.lo = np.asarray(self.lo, float)
        self.hi = np.asarray(self.hi, float)
        n = np.ceil((self.hi - self.lo) / self.h).astype(int) + 1
        self.shape = tuple(int(v) for v in n)
        ax = [self.lo[i] + np.arange(n[i], dtype=np.float32) * self.h for i in range(3)]
        self.x, self.y, self.z = np.meshgrid(*ax, indexing="ij", sparse=True)
        self.axes = ax

    @property
    def P(self):
        return self.x, self.y, self.z


# ------------------------------------------------------------------ transforms
def rot(axis: str, deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
            "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axis]


class Frame:
    """Local coordinate frame: world point -> local coords (for posing parts)."""

    def __init__(self, origin=(0, 0, 0), R=None):
        self.o = np.asarray(origin, float)
        self.R = np.eye(3) if R is None else np.asarray(R, float)

    def local(self, x, y, z):
        dx, dy, dz = x - self.o[0], y - self.o[1], z - self.o[2]
        Rt = self.R.T  # inverse rotation
        return (Rt[0, 0] * dx + Rt[0, 1] * dy + Rt[0, 2] * dz,
                Rt[1, 0] * dx + Rt[1, 1] * dy + Rt[1, 2] * dz,
                Rt[2, 0] * dx + Rt[2, 1] * dy + Rt[2, 2] * dz)

    def world(self, p):
        return self.o + self.R @ np.asarray(p, float)


# ------------------------------------------------------------------ primitives (x, y, z are arrays)
def sphere(x, y, z, c, r):
    return np.sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2 + (z - c[2]) ** 2) - r


def ellipsoid(x, y, z, c, r):
    """Good-quality ellipsoid SDF approximation (Quilez)."""
    px, py, pz = (x - c[0]) / r[0], (y - c[1]) / r[1], (z - c[2]) / r[2]
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def capsule(x, y, z, a, b, ra, rb=None):
    """Round cone between a (radius ra) and b (radius rb)."""
    rb = ra if rb is None else rb
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a
    L2 = float(ba @ ba)
    px, py, pz = x - a[0], y - a[1], z - a[2]
    t = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0, 1)
    dx, dy, dz = px - ba[0] * t, py - ba[1] * t, pz - ba[2] * t
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * t)


def tube(x, y, z, pts, r0, r1, k=0.6):
    """Tapered tube along a polyline (smoothly blended segments)."""
    pts = np.asarray(pts, float)
    n = len(pts) - 1
    rs = np.linspace(r0, r1, n + 1)
    d = None
    for i in range(n):
        s = capsule(x, y, z, pts[i], pts[i + 1], rs[i], rs[i + 1])
        d = s if d is None else smin(d, s, k)
    return d


def bezier_pts(p0, p1, p2, n=10):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(p, float) for p in (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def box(x, y, z, c, half, r=0.0):
    qx = np.abs(x - c[0]) - (half[0] - r)
    qy = np.abs(y - c[1]) - (half[1] - r)
    qz = np.abs(z - c[2]) - (half[2] - r)
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    return out + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - r


def torus(x, y, z, c, R, r, axis="z"):
    px, py, pz = x - c[0], y - c[1], z - c[2]
    if axis == "x":
        px, pz = pz, px
    elif axis == "y":
        py, pz = pz, py
    q = np.sqrt(px * px + py * py) - R
    return np.sqrt(q * q + pz * pz) - r


# ------------------------------------------------------------------ operators
def smin(a, b, k):
    """Polynomial smooth union (k = blend radius, mm)."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def union(*ds):
    out = ds[0]
    for d in ds[1:]:
        out = np.minimum(out, d)
    return out


def sub(a, b, k=0.0):
    return smax(a, -b, k) if k > 0 else np.maximum(a, -b)


def shell_band(d, depth):
    """Region within `depth` of the surface, inside."""
    return np.maximum(d, -(d + depth))


# ------------------------------------------------------------------ FDM
def support_free(d: np.ndarray, h: float, angle_deg: float = 40.0) -> np.ndarray:
    """Top-down 45-degree self-supporting closure of a field on a z-indexed grid.

    Each layer must lie within the layer below grown by h*tan(angle). Processing
    from the top, layer k is unioned with (layer k+1 shrunk by that amount); the
    added material forms smooth 45-degree fillets/skirts under every overhang, so
    the result prints without supports. (Holes become teardrops automatically.)
    Default 40 degrees from vertical leaves margin for mesh facets around the 45-degree limit.
    """
    out = d.copy()
    step = h * math.tan(math.radians(angle_deg))
    for k in range(out.shape[2] - 2, -1, -1):
        np.minimum(out[:, :, k], out[:, :, k + 1] + step, out=out[:, :, k])
    return out


# ------------------------------------------------------------------ 2D helpers
def polygon_sdf2d(shape, xs, ys):
    """Signed 2D distance (negative inside) of a shapely polygon on an (x, y) raster."""
    from matplotlib.path import Path as MPath
    from shapely.geometry import MultiPolygon, Polygon
    polys = [shape] if isinstance(shape, Polygon) else list(getattr(shape, "geoms", []))
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    pts = np.column_stack([X.ravel(), Y.ravel()])
    inside = np.zeros(len(pts), bool)
    for p in polys:
        m = MPath(np.asarray(p.exterior.coords)).contains_points(pts)
        for r in p.interiors:
            m &= ~MPath(np.asarray(r.coords)).contains_points(pts)
        inside |= m
    inside = inside.reshape(X.shape)
    h = float(xs[1] - xs[0])
    dout = ndimage.distance_transform_edt(~inside) * h
    din = ndimage.distance_transform_edt(inside) * h
    d = np.where(inside, -din + 0.5 * h, dout - 0.5 * h)
    return ndimage.gaussian_filter(d, 0.9).astype(np.float32)   # remove EDT terracing


# ------------------------------------------------------------------ meshing
def mesh(d: np.ndarray, grid: Grid, decimate_to: int | None = None) -> m3d.Manifold:
    """Marching cubes -> (optional quadric decimation) -> manifold3d Manifold."""
    from skimage import measure
    # light smoothing (sigma ~0.6 voxel) removes zero-thickness contacts that exact min/max
    # operations create - those become non-manifold "pinch" edges after vertex welding
    d = ndimage.gaussian_filter(d, 0.6, mode="nearest")   # 'nearest': keep the bed face flat
    pad = np.pad(d, 1, mode="constant", constant_values=max(float(d.max()), 1.0))
    verts, faces, _, _ = measure.marching_cubes(pad, level=0.0, spacing=(grid.h,) * 3)
    verts = verts - grid.h + grid.lo
    faces = faces[:, ::-1]  # skimage winds inward for negative-inside fields
    if decimate_to and len(faces) > decimate_to:
        import fast_simplification
        verts, faces = fast_simplification.simplify(verts.astype(np.float32), faces.astype(np.int64),
                                                    target_reduction=1 - decimate_to / len(faces))
    man = to_manifold(verts, faces)
    if man.volume() < 0:
        man = to_manifold(verts, faces[:, ::-1])
    return man


def to_manifold(verts, faces) -> m3d.Manifold:
    mg = m3d.Mesh(vert_properties=np.ascontiguousarray(verts, np.float32),
                  tri_verts=np.ascontiguousarray(faces, np.uint32))
    mg.merge()
    man = m3d.Manifold(mg)
    if str(man.status()) != "Error.NoError":
        import trimesh
        tm = trimesh.Trimesh(verts, faces, process=True)
        tm.merge_vertices()
        tm.update_faces(tm.nondegenerate_faces())
        tm.fix_normals()
        mg = m3d.Mesh(vert_properties=np.ascontiguousarray(tm.vertices, np.float32),
                      tri_verts=np.ascontiguousarray(tm.faces, np.uint32))
        mg.merge()
        man = m3d.Manifold(mg)
    if str(man.status()) != "Error.NoError":
        raise RuntimeError(f"SDF mesh is not manifold: {man.status()}")
    return man
