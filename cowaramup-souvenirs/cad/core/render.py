"""Dependency-light preview renderer (orthographic, painter-sorted, Lambert shaded).

No OpenGL / display required - works in headless CI. Triangles are small, so
centroid depth sorting gives correct-looking occlusion for these products.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib

FONT_PATH = Path(matplotlib.get_data_path()) / "fonts/ttf/DejaVuSans.ttf"
FONT_BOLD_PATH = Path(matplotlib.get_data_path()) / "fonts/ttf/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD_PATH if bold else FONT_PATH), size)


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def view_matrix(azim_deg: float, elev_deg: float) -> np.ndarray:
    """Rows = camera right, up, towards-viewer. azim 0 looks from -Y toward +Y (front)."""
    a, e = math.radians(azim_deg), math.radians(elev_deg)
    fwd = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])  # to viewer
    up0 = np.array([0, 0, 1.0])
    right = np.cross(up0, fwd)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0, 0])
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    return np.vstack([right, up, fwd])


try:
    from numba import njit
except ImportError:  # pragma: no cover - numba is optional but ~100x faster
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


@njit(cache=True)
def _raster(xy, z, cols, W, H, bg):
    img = np.empty((H, W, 3), np.uint8)
    for c in range(3):
        img[:, :, c] = bg[c]
    zb = np.full((H, W), -1e30)
    for i in range(xy.shape[0]):
        x0, y0 = xy[i, 0, 0], xy[i, 0, 1]
        x1, y1 = xy[i, 1, 0], xy[i, 1, 1]
        x2, y2 = xy[i, 2, 0], xy[i, 2, 1]
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-12:
            continue
        minx = max(int(min(x0, x1, x2)), 0)
        maxx = min(int(max(x0, x1, x2)) + 1, W - 1)
        miny = max(int(min(y0, y1, y2)), 0)
        maxy = min(int(max(y0, y1, y2)) + 1, H - 1)
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                fx, fy = px + 0.5, py + 0.5
                a = ((y1 - y2) * (fx - x2) + (x2 - x1) * (fy - y2)) / den
                b = ((y2 - y0) * (fx - x2) + (x0 - x2) * (fy - y2)) / den
                c = 1.0 - a - b
                if a < -1e-6 or b < -1e-6 or c < -1e-6:
                    continue
                zz = a * z[i, 0] + b * z[i, 1] + c * z[i, 2]
                if zz > zb[py, px]:
                    zb[py, px] = zz
                    img[py, px, 0] = cols[i, 0]
                    img[py, px, 1] = cols[i, 1]
                    img[py, px, 2] = cols[i, 2]
    return img


def render(meshes, azim=-35, elev=25, size=(900, 700), bg=(255, 255, 255), margin=0.08,
           ssaa=2, light=(-0.4, -0.6, 0.9), frame=None, return_transform=False):
    """meshes: list of (vertices Nx3, faces Mx3, rgb 0-255). Z-buffered, returns PIL image."""
    R = view_matrix(azim, elev)
    L = np.asarray(light, float)
    L = L / np.linalg.norm(L)
    Lc = R @ L
    tris, cols, allpts = [], [], []
    for v, f, rgb in meshes:
        if len(f) == 0:
            continue
        vc = v @ R.T
        allpts.append(vc)
        t = vc[f]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        nn = np.linalg.norm(n, axis=1)
        ok = nn > 1e-12
        n[ok] /= nn[ok, None]
        vis = ok & (n[:, 2] > 0)
        t, n = t[vis], n[vis]
        diff = np.clip(n @ Lc, 0, 1)
        half = Lc + np.array([0, 0, 1.0])
        half /= np.linalg.norm(half)
        spec = np.clip(n @ half, 0, 1) ** 40
        c = np.asarray(rgb, float)[None, :] * (0.42 + 0.58 * diff[:, None]) + 45 * spec[:, None]
        tris.append(t)
        cols.append(np.clip(c, 0, 255))
    W, H = size[0] * ssaa, size[1] * ssaa
    if not tris:
        return Image.new("RGB", size, bg)
    T = np.concatenate(tris)
    C = np.concatenate(cols).astype(np.uint8)
    P = np.concatenate(allpts)
    lo, hi = (P[:, :2].min(0), P[:, :2].max(0)) if frame is None else frame
    span = np.maximum(hi - lo, 1e-6)
    s = min(W * (1 - 2 * margin) / span[0], H * (1 - 2 * margin) / span[1])
    off = np.array([W / 2, H / 2]) - s * (lo + hi) / 2
    XY = T[:, :, :2] * s + off
    XY[:, :, 1] = H - XY[:, :, 1]
    arr = _raster(np.ascontiguousarray(XY), np.ascontiguousarray(T[:, :, 2]), C, W, H,
                  np.asarray(bg, np.uint8))
    img = Image.fromarray(arr).resize(size, Image.LANCZOS)
    if return_transform:
        return img, (R, s / ssaa, off / ssaa, size)
    return img


def project(points, transform):
    R, s, off, size = transform
    pc = np.asarray(points, float) @ R.T
    xy = pc[:, :2] * s + off
    xy[:, 1] = size[1] - xy[:, 1]
    return xy


def label(img, text, xy=(16, 12), size=22, colour=(30, 30, 30), bold=True):
    d = ImageDraw.Draw(img)
    d.text(xy, text, font=font(size, bold), fill=colour)
    return img


def grid(images, cols, pad=10, bg=(255, 255, 255)):
    w = max(i.width for i in images)
    h = max(i.height for i in images)
    rows = math.ceil(len(images) / cols)
    out = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * h + (rows + 1) * pad), bg)
    for k, im in enumerate(images):
        r, c = divmod(k, cols)
        out.paste(im, (pad + c * (w + pad), pad + r * (h + pad)))
    return out
