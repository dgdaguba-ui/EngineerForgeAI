"""Premium collector base system (SDF): the 'Cowaramup Paddock'.

Every collectible sits on the same family of base so the range reads as one
collection on a shelf:

  * pebble-shaped paddock, flat front and back faces for lettering,
    rounded top edge, 45-degree bottom chamfer (no elephant-foot flare)
  * grass tufts (tool 4) round the rim - tactile, storytelling
  * optional whitewashed timber fence (tool 1): chunky posts and round rails
  * FRONT: 'COWARAMUP' inlaid flush in tool 1 (legible at shelf distance)
  * BACK: 'COW TOWN WA' engraved
  * UNDERSIDE (hidden, collectible): series number + name + 'COWARAMUP WA' debossed
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import box as sbox

from ..core import geom, sdf
from ..core.text import text_shape


def _text_field(text, cap, u, v, cu, cv, mirror=False, max_width=None):
    """2D signed field of text on a (u, v) raster (negative inside glyphs)."""
    shp = text_shape(text, cap, cu, cv, max_width=max_width, min_counter=1.2)
    if mirror:
        shp = geom.mirror_x(shp, cu)
    return sdf.polygon_sdf2d(shp, u, v)


def paddock_base(g: sdf.Grid, rx=38.0, ry=26.0, hb=7.0, front_text="COWARAMUP", back_text="COW TOWN WA",
                 under_lines=("01  CLASSIC", "COWARAMUP WA", "CRW-003"), fence=True, tufts=True,
                 seed=3):
    """Returns dict(env, text_inlay, grass, fence) fields (mm). Base top at z = hb."""
    X, Y, Z = g.P
    # footprint: ellipse with flat front/back (lettering faces)
    fy = ry * 0.72
    foot = geom.ellipse(0, 0, rx, ry).intersection(sbox(-rx - 1, -fy, rx + 1, fy))
    xs, ys, zs = g.axes
    d2 = sdf.polygon_sdf2d(foot, xs, ys)[:, :, None]
    r = 1.6
    q1, q2 = d2 + r, Z - (hb - r)
    f = np.sqrt(np.maximum(q1, 0) ** 2 + np.maximum(q2, 0) ** 2) + np.minimum(np.maximum(q1, q2), 0) - r
    f = np.maximum(f, -Z)
    f = np.maximum(f, (d2 + 0.7 - Z) * 0.7071)          # 45-degree bottom chamfer
    out = {}

    # FRONT lettering: flush inlay, 0.8 mm deep, tool 1
    tf = _text_field(front_text, 4.2, xs, zs, 0.0, hb * 0.46, max_width=2 * rx * 0.72)[:, None, :]   # clear of the top fillet
    out["text_inlay"] = np.maximum(np.maximum(tf, Y - (-fy + 0.8)), -(Y - (-fy - 1.0)))
    # BACK engraving (viewed from behind -> mirrored)
    tb = _text_field(back_text, 4.0, xs, zs, 0.0, hb * 0.5, mirror=True, max_width=2 * rx * 0.6)[:, None, :]
    cuts = [np.maximum(np.maximum(tb, (fy - 0.7) - Y), Y - (fy + 1.0))]
    # UNDERSIDE deboss (mirrored so it reads when flipped)
    for i, line in enumerate(under_lines):
        cap = 4.2 if i == 0 else 3.4
        tu = _text_field(line, cap, xs, ys, 0.0, 7.0 - i * 7.0, mirror=True, max_width=2 * rx * 0.7)[:, :, None]
        cuts.append(np.maximum(np.maximum(tu, Z - 0.6), -Z - 1.0))

    out["plinth"] = f.copy()
    grass = None
    if tufts:
        rng = np.random.default_rng(seed)
        for ang in np.linspace(0, 2 * np.pi, 11, endpoint=False) + 0.2:
            cx, cy = 0.84 * rx * np.cos(ang), 0.80 * ry * np.sin(ang)
            if abs(cy) > fy - 3.0:
                cy = np.sign(cy) * (fy - 3.0)
            for j in range(5):
                a2 = ang + rng.uniform(-1.6, 1.6)
                lean = rng.uniform(1.2, 2.4)
                tip = (cx + lean * np.cos(a2), cy + lean * np.sin(a2), hb + rng.uniform(2.4, 3.6))
                blade = sdf.capsule(X, Y, Z, (cx + 0.5 * np.cos(a2), cy + 0.5 * np.sin(a2), hb - 0.5), tip, 0.95, 0.5)
                grass = blade if grass is None else np.minimum(grass, blade)
        f = np.minimum(f, grass)
    out["grass"] = grass

    fz = None
    if fence:
        # two posts + two rails at the back-left, wood grain as shallow grooves along the rails
        posts = [(-rx * 0.62, fy - 5.0), (-rx * 0.12, fy - 3.2)]
        fz = None
        for px, py in posts:
            p = sdf.box(X, Y, Z, (px, py, hb + 7.5), (1.8, 1.8, 9.5), 0.6)   # sunk 2 mm into the base
            fz = p if fz is None else np.minimum(fz, p)
        (x0, y0), (x1, y1) = posts
        for zr in (hb + 6.0, hb + 12.5):
            rail = sdf.capsule(X, Y, Z, (x0, y0, zr), (x1, y1, zr), 1.35)
            fz = np.minimum(fz, rail)   # (no wood-grain grooves: < 0.5 mm is below nozzle resolution)
        f = np.minimum(f, fz)
    out["fence"] = fz
    out["env"] = f
    out["cuts"] = cuts          # apply AFTER the support-free closure
    return out
