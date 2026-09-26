"""CRW-002 v2 - Cowa Head Magnet: a dimensional bas-relief bust (~64 mm).

Redesign (see DESIGN_AUDIT.md): replaces the flat face + rectangle banner.
  * The collectible's sculpted head, converted to BAS-RELIEF: depth compressed to
    45 % so the magnet stays ~14 mm thick while eyes, lids, muzzle, horns and ears
    keep their modelling.
  * A curved scroll ribbon hugs the chin; 'COWARAMUP' is RAISED in tool 1 and
    follows the arc (the flat rectangle banner is gone).
  * Printed face-up: every surface is a dome or a 45-degree fillet; decoration
    tool changes only happen where the relief is.
  * Two 12 x 3 mm magnet pockets in the flat back; 'CRW-002 COWARAMUP WA' debossed.
"""
from __future__ import annotations

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon

from ..accessories.accessories import magnet_cavity
from ..accessories.bases import _text_field
from ..core import config, geom, sdf
from ..core.model import Product
from ..core.sculpt import sculpt_parts
from ..core.text import text_shape
from ..cows.character import CowaParams, fields

ID, SLUG = "CRW-002", "cowaramup-magnet"
H = 0.3
COMPRESS = 0.45


def _arc_text(text, cap, R, vc, span_deg=100.0):
    """Text bent along an arc (smile-shaped: centre above at (0, vc), radius R)."""
    t = text_shape(text, cap, 0, 0)
    out = []
    for p in geom.polygons_of(t):
        def bend(ring):
            ring = np.asarray(affinity.affine_transform(ring, [1, 0, 0, 1, 0, 0]).segmentize(0.3).coords)
            th = ring[:, 0] / R
            r = R - ring[:, 1]
            return np.column_stack([r * np.sin(th), vc - r * np.cos(th)])
        out.append(Polygon(bend(p.exterior), [bend(i) for i in p.interiors]))
    from shapely.ops import unary_union
    return unary_union(out)


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    s = 1.38 * d["scale"]
    Hc = np.array([0.0, -6.5, 43.0]) * s          # head centre in character space (mm)
    w0 = -3.0 * s * COMPRESS                       # back plane (behind head centre)
    g = sdf.Grid((-34 * s / 1.38, -36 * s / 1.38, 0), (34 * s / 1.38, 36 * s / 1.38, 20), H)
    u, v, wz = g.P
    w = wz + w0
    # bust frame -> character space: u = x, v = z (up), w toward viewer = -y (compressed)
    X = u + 0 * v + 0 * wz
    Zc = Hc[2] + v + 0 * u + 0 * wz
    Yc = Hc[1] - w / COMPRESS + 0 * u + 0 * v
    P = CowaParams(scale=s, head_yaw=0.0, head_roll=4.0, head_pitch=6.0, collar=False, bell=False, ear_tag=True,
                   horn_r=1.15, ear_left=(14.0, 4.0), ear_right=(-4.0, 6.0))   # ears in the relief plane
    F = fields(g, P, xyz=(X, Yc, Zc))
    env = F["env"] * COMPRESS
    # keep the head only: a soft region round the head, flat back
    region = sdf.ellipsoid(u, v, w, (0, 7.5 * s, 0), (27.0 * s, 21.5 * s, 40.0))   # head only, ends behind the ribbon
    env = sdf.smax(env, region, 1.0)
    env = np.maximum(env, -wz)
    layers = [(t, np.maximum(f * COMPRESS, region), n) for t, f, n in F["layers"]]

    # scroll ribbon under the chin (tool 4) with raised arc lettering (tool 1)
    R, vc = 44.0 * s / 1.38, 18.5 * s / 1.38
    rr = np.sqrt(u ** 2 + (v - vc) ** 2)
    th = np.degrees(np.arctan2(u, -(v - vc)))
    band = np.maximum(np.abs(rr - R) - 5.6, np.abs(th) - 43.0 * 1.0)
    band = sdf.smax(band, np.maximum(wz - 5.2, -wz), 0.6)
    for sgn in (-1, 1):  # rolled ends
        a = np.radians(sgn * 43.0)
        ex, ey = R * np.sin(a), vc - R * np.cos(a)
        roll = sdf.capsule(u, v, wz, (ex, ey, 0.0), (ex, ey, 4.4), 3.4)
        band = np.minimum(band, np.maximum(roll, -wz))
    txt = _arc_text("COWARAMUP", 5.8, R, vc)
    xs, ys, zs = g.axes
    t2 = sdf.polygon_sdf2d(txt, xs, ys)[:, :, None]
    letters = np.maximum(np.maximum(t2, wz - 5.9), -wz)
    env = np.minimum(env, np.minimum(band, letters))
    layers = [("tool_4", band - 0.35, "COWARAMUP ribbon")] + layers + [("tool_1", np.maximum(t2 - 0.3, 4.4 - wz), "raised lettering")]

    # back: magnet pockets + hidden deboss
    pockets = []
    pocket_xy = [(-7.0 * s / 1.38, -8.5 * s / 1.38), (7.0 * s / 1.38, -8.5 * s / 1.38)]   # under the thick muzzle
    for x, y in pocket_xy:
        pockets.append(np.maximum(np.sqrt((u - x) ** 2 + (v - y) ** 2) - 6.15, np.maximum(wz - 3.2, -wz - 1.0)))
    tu = _text_field("CRW-002  COWARAMUP WA", 3.0, xs, ys, 0.0, -14.0, mirror=True, max_width=46)[:, :, None]
    pockets.append(np.maximum(np.maximum(tu, wz - 0.5), -wz - 1.0))
    parts, env_m, envc = sculpt_parts(g, env, layers, post_cut=pockets, decimate_env=150_000, decimate_layer=40_000,
                                      return_field=True)
    # measured (not assumed) material above each pocket: ray-cast the final mesh over the pocket disc
    import trimesh
    vv, ff = geom.mesh_arrays(env_m)
    tm = trimesh.Trimesh(vv, ff, process=False)
    ceilings = []
    for x, y in pocket_xy:
        rr_, aa_ = np.meshgrid(np.linspace(0, 6.1, 5), np.linspace(0, 2 * np.pi, 12, endpoint=False))
        pts = np.column_stack([x + (rr_ * np.cos(aa_)).ravel(), y + (rr_ * np.sin(aa_)).ravel(), np.full(rr_.size, 60.0)])
        loc, ri, _ = tm.ray.intersects_location(pts, np.tile([0, 0, -1.0], (len(pts), 1)), multiple_hits=False)
        ceilings.append(float(loc[:, 2].min() - 3.2) if len(loc) >= 0.8 * len(pts) else 0.0)
    bb = env_m.bounding_box()
    return Product(
        id=ID, slug=SLUG, name="Cowa Head Magnet", category="A - Multi-colour impulse",
        description="Dimensional bas-relief Cowa head (~64 mm) with sculpted eyes, lids, muzzle, horns and ears; "
                    "curved scroll ribbon with raised COWARAMUP lettering; two 12x3 mm magnets in the back.",
        size=size, parts=parts,
        tool_roles={"tool_1": "head, horns, eyelids, highlights, raised lettering",
                    "tool_2": "patches, forelock, pupils, nostrils, smile",
                    "tool_3": "muzzle, inner ears", "tool_4": "scroll ribbon, ear tag"},
        requirements={"tool_4": {"flexible": False, "strict": False, "preferred_material": "PLA",
                                 "why": "ribbon should be rigid and crisp"}},
        print_orientation="Face up, flat back on the bed (magnet pockets on the bed face).",
        strategy="E - printed + hardware (magnets)", hardware=["neodymium_disc_12x3", "neodymium_disc_12x3"],
        packaging="impulse_backing_card", tier="IMPULSE", assembly_time_minutes=0.6, post_process_minutes=0.4,
        envelope=env_m,
        checks={"envelope_mm": (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]), "magnet_pockets": 2,
                "magnet_pocket_d": 12.3, "magnet_pocket_depth": 3.2, "ceiling_above_pocket": round(min(ceilings), 2)},
        notes=["Bas-relief compression 45 %: reads as full 3D from the front 3/4, ~14 mm deep.",
               "Letters cap 5.8 mm, raised 0.7 mm on the ribbon (top layers only)."],
        self_critique={"character": "Same face as the collection; the ribbon now frames it instead of a label.",
                       "still_to_improve": "Pockets sit under the muzzle (thickest area); ceiling is measured "
                                           "from the geometry in checks.ceiling_above_pocket."},
    )
