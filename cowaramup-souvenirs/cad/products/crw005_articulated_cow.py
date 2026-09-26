"""CRW-005 - Articulated Cow (Prototype 5, flagship) - print-in-place.

Strategy A + C: one plate, five members, four bicone print-in-place joints,
optional TPU tail fused to the body.

  * Printed LYING ON ITS SIDE: the cow's lateral axis is the print Z axis, so
    every joint axis is vertical and every member starts on the bed. No member
    is printed over an air gap (the usual failure of print-in-place toys).
  * Moving: head (nod +/-20 deg), front legs (0..+25 deg forward), rear legs
    (-25..0 deg back). The ASYMMETRIC leg stops block the parallelogram
    'collapse' mode, so the cow stands on its own with legs vertical.
  * Tail: TPU (tool 4), fused to the rump through a keyhole anchor, only in the
    bottom 6 mm -> flexible swishing tail, TPU on ~30 layers only.
  * Decoration: 0.6 mm skin inlays on both flanks (cow's right side carries the
    signature eye patch). Core layers are tool 1 only.
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

from ..core import config, geom, sdf
from ..core.sculpt import sculpt_parts
from ..core.model import FaceRegion, Part, Product
from ..cows.side import cow_head_side
from ..mechanisms.joints import hinge, sweep2d

ID, SLUG = "CRW-005", "articulated-cow"


def pillow_member(name, outline, T, deco, head=None, h=0.3, under_text=None):
    """Pillow-rounded, sculpted member (SDF): 3.2 mm rounded top edge, 45-degree bottom
    chamfer (prints on the bed), raised patches, and on the head a sculpted face on the
    display side. Colour regions wrap onto the edges (hooves are black all round)."""
    minx, miny, maxx, maxy = outline.bounds
    g = sdf.Grid((minx - 2, miny - 2, -0.5), (maxx + 2, maxy + 2, T + 3.0), h)
    X, Y, Z = g.P
    xs, ys, _ = g.axes
    d2 = sdf.polygon_sdf2d(outline, xs, ys)[:, :, None]
    r, c = 3.2, 1.4
    q1, q2 = d2 + r, Z - (T - r)
    env = np.sqrt(np.maximum(q1, 0) ** 2 + np.maximum(q2, 0) ** 2) + np.minimum(np.maximum(q1, q2), 0) - r
    env = np.maximum(env, -Z)
    env = np.maximum(env, (d2 + c - Z) * 0.7071)
    band = lambda f, depth=0.9: np.maximum(f, -(env + depth))
    layers = []
    top_half = T * 0.5 - Z
    for tool, shape, feat in (deco or []):
        prism = sdf.polygon_sdf2d(shape, xs, ys)[:, :, None]
        if tool == "tool_2" and "patch" in feat:          # tactile raised patch (display side), never wider
            env = np.minimum(env, np.maximum(np.maximum(env - 0.4, d2), np.maximum(prism, top_half)))
        layers.append((tool, band(prism - 0.2 + 0 * Z, 1.2), feat))
    if head is not None:
        cen = lambda sh: (sh.centroid.x, sh.centroid.y)
        mx, my = cen(head["muzzle"])
        b = head["muzzle"].bounds
        env = sdf.smin(env, sdf.ellipsoid(X, Y, Z, (mx, my, T - 1.4), ((b[2] - b[0]) * 0.46, (b[3] - b[1]) * 0.46, 3.2)), 1.6)
        ex, ey = cen(head["eye"])
        env = sdf.sub(env, sdf.ellipsoid(X, Y, Z, (ex, ey, T + 0.2), (3.4, 4.0, 1.5)), 0.5)
        pupil = sdf.ellipsoid(X, Y, Z, (ex, ey, T - 0.5), (2.6, 3.2, 1.55))
        env = np.minimum(env, pupil)
        lid = sdf.ellipsoid(X, Y, Z, (ex - 0.3, ey + 2.6, T + 0.2), (3.3, 1.5, 1.2))
        env = sdf.smin(env, lid, 0.8)
        hl = sdf.sphere(X, Y, Z, (ex + 1.0, ey + 0.1, T + 0.75), 1.05)   # clear of the lid
        nx, ny = cen(head["nostril"])
        nos = sdf.ellipsoid(X, Y, Z, (nx, ny, T + 1.9), (1.5, 1.9, 1.7))
        env = sdf.sub(env, nos, 0.4)
        patch = sdf.polygon_sdf2d(head["patch"], xs, ys)[:, :, None] if head["patch"] is not None else None
        if patch is not None:
            env = np.minimum(env, np.maximum(np.maximum(env - 0.4, d2), np.maximum(patch, np.maximum(top_half, 1.6 - pupil))))
        prism = lambda sh, grow=0.2: sdf.polygon_sdf2d(sh, xs, ys)[:, :, None] - grow
        layers += [("tool_3", band(prism(head["inner_ear"]), 1.2), "inner ear")]
        if patch is not None:
            layers += [("tool_2", band(patch - 0.2, 1.2), "eye patch"),
                       ("tool_1", sdf.ellipsoid(X, Y, Z, (ex, ey, T), (4.3, 5.0, 3.0)), "eye ring")]
        layers += [("tool_3", band(prism(head["muzzle"], 0.3), 1.6), "muzzle"),
                   ("tool_1", lid - 0.35, "eyelid"),
                   ("tool_2", pupil - 0.3, "eye"), ("tool_2", nos - 0.35, "nostril"),
                   ("tool_1", hl - 0.35, "eye highlight")]
    cuts = []
    if under_text:   # hidden detail: debossed into the bed-side flank
        from ..core.text import text_shape
        txt = geom.mirror_x(text_shape(under_text[0], under_text[1], under_text[2], under_text[3], min_counter=1.2),
                            under_text[2])
        t2 = sdf.polygon_sdf2d(txt, xs, ys)[:, :, None]
        cuts.append(np.maximum(np.maximum(t2, Z - 0.6), -Z - 1.0))
    parts, _ = sculpt_parts(g, env, layers, closure=True, group=name, decimate_env=70_000, decimate_layer=25_000,
                            post_cut=cuts)
    for p in parts:
        p.name = f"{name}_{p.tool}"
    return parts


def _layout(d):
    ground = box(-50, 0, 250, 200)
    torso = unary_union([geom.ellipse(52, 50, 34, 16), geom.ellipse(24, 52, 12, 14),
                         geom.ellipse(58, 36, 8, 5.5),
                         geom.tapered_stroke([(76, 57), (88, 63)], 10, 8, 10)])
    head = cow_head_side(106, 75, 34, 1, patch=True)       # v2: bigger, more characterful head
    head_b = cow_head_side(106, 75, 34, 1, patch=False)
    head_arm = geom.tapered_stroke([(91, 64), (100, 71)], 6.5, 7.5, 8)
    front_leg = unary_union([geom.tapered_stroke([(72, 44), (73, 6)], 6.5, 5.8, 12),
                             geom.rounded_rect(73, 4.5, 13, 9, 3)]).intersection(ground)
    rear_leg = unary_union([geom.tapered_stroke(geom.bezier((30, 46), (24, 27), (30, 6), 12), 7.0, 5.8, 16),
                            geom.rounded_rect(30, 4.5, 13, 9, 3)]).intersection(ground)
    tail = unary_union([geom.tapered_stroke(geom.bezier((17, 60), (5, 57), (6, 30), 12), 2.0, 1.8, 16),
                        geom.ellipse(6, 25, 3.6, 5.5)])
    anchor = unary_union([geom.tapered_stroke([(15, 60), (21, 59)], 2.0, 2.0, 4), geom.circle(22.5, 59, 3.2)])
    return torso, head, head_b, head_arm, front_leg, rear_leg, tail, anchor


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    T = d["thickness"]
    c = d["joint_clearance"]
    inlay = d["inlay_depth"]
    r_max, taper, wall = d["joint_post_r_max"], d["joint_post_taper"], d["joint_ring_wall"]
    torso, head, head_b, head_arm, front_leg, rear_leg, tail2d, anchor2d = _layout(d)

    J = {
        "head": hinge((91, 64), T, r_max, taper, c, wall, (-1.0, -0.55), 3.6, 13, (-d["head_swing_deg"], d["head_swing_deg"])),
        "front_leg": hinge((72, 44), T, r_max, taper, c, wall, (0.0, 1.0), 3.6, 12, (0.0, d["leg_swing_deg"])),
        "rear_leg": hinge((30, 46), T, r_max, taper, c, wall, (0.05, 1.0), 3.6, 12, (-d["leg_swing_deg"], 0.0)),
    }
    members2d = {
        "head": unary_union([head["outline"], head_arm, J["head"]["ring"]]),
        "front_leg": unary_union([front_leg, J["front_leg"]["ring"]]),
        "rear_leg": unary_union([rear_leg, J["rear_leg"]["ring"]]),
    }
    # moving members: remove the neck-sweep opening
    for k in members2d:
        members2d[k] = geom.clean(members2d[k].difference(J[k]["opening"]))
    # fixed body: remove everything the moving members can sweep through (+ clearance)
    body2d = torso
    for k, m in members2d.items():
        body2d = body2d.difference(sweep2d(m, J[k]["pivot"], J[k]["rom_deg"]).buffer(c, quad_segs=6))
    # necks tie each post back to the fixed body (full thickness)
    necks = unary_union([j["neck"] for j in J.values()])
    # morphological opening removes slivers < 1.4 mm left where sweep cuts meet the outline
    body2d = body2d.buffer(-0.7, quad_segs=8).buffer(0.7, quad_segs=8)
    body2d = geom.clean(unary_union([body2d, necks]))

    body_deco = [("tool_2", geom.blob([(40, 58, 9), (50, 55, 7), (32, 53, 6)], smooth=2), "flank patch"),
                 ("tool_2", geom.blob([(70, 53, 7), (77, 58, 5)], smooth=2), "shoulder patch"),
                 ("tool_3", geom.ellipse(58, 36, 7, 4.6), "udder")]
    hoof = box(-50, -1, 250, 8.5)

    parts: list[Part] = []
    specs = {"body": (body2d, body_deco), "head": (members2d["head"], None),
             "front_leg": (members2d["front_leg"], [("tool_2", hoof, "hoof")]),
             "rear_leg": (members2d["rear_leg"], [("tool_2", hoof, "hoof")])}
    for name, (outline, deco) in specs.items():
        ps = pillow_member(name, outline, T, deco, head if name == "head" else None,
                           under_text=("COWARAMUP  CRW-005", 4.0, 50.0, 47.0) if name == "body" else None)
        if name in J:
            for p in ps:
                p.solid = p.solid - J[name]["hole"]
        parts += ps
    face_regions: list[FaceRegion] = []
    # Exact clean-up: sculpting (smoothed outlines, relief) must never eat the joint clearance.
    for p in parts:
        if p.object_group in members2d:
            p.solid = p.solid ^ geom.extrude(members2d[p.object_group].buffer(-0.08), -2, T + 6)  # 0.08 off the wall: no coincident faces
        elif p.object_group == "body":
            for k, m in members2d.items():
                p.solid = p.solid - geom.extrude(sweep2d(m, J[k]["pivot"], J[k]["rom_deg"]).buffer(c + 0.08, quad_segs=6)
                                                 .difference(J[k]["neck"]), -2, T + 6)

    # Bicone posts join the fixed body core (colour regions keep priority).
    body_core = next(p for p in parts if p.name == "body_tool_1")
    body_colour = geom.union(p.solid for p in parts if p.object_group == "body" and p is not body_core)
    body_core.solid = (body_core.solid + geom.union(j["post"] for j in J.values())) - body_colour

    # TPU tail fused to the rump through a keyhole anchor, bottom tail_thickness only.
    tt = d["tail_thickness"]
    tail_solid = geom.extrude(unary_union([tail2d, anchor2d]), 0, tt)
    for p in parts:
        if p.object_group == "body":
            p.solid = p.solid - tail_solid
    # keep the tail clear of the rear leg sweep
    tail_solid = tail_solid - geom.extrude(sweep2d(members2d["rear_leg"], J["rear_leg"]["pivot"],
                                                   J["rear_leg"]["rom_deg"]).buffer(c), -1, T + 1)
    parts.append(Part("tail_tool_4", "tool_4", tail_solid, "flexible tail + tuft (TPU)", "body",
                      requires={"flexible": True}))

    bb = geom.union(p.solid for p in parts).bounding_box()
    checks = {
        "joints": {k: {kk: (list(v) if isinstance(v, tuple) else v) for kk, v in j.items()
                       if kk in ("pivot", "r_min", "r_max", "r_out", "clearance", "rom_deg",
                                 "retention_chord", "post_diameter")} for k, j in J.items()},
        "members": ["body", "head", "front_leg", "rear_leg"],
        "thickness": T,
        "envelope_mm": (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]),
        "standing_height": bb[4] - bb[1],
    }
    return Product(
        id=ID, slug=SLUG, name="Articulated Cow - Walking Cowa", category="F - Kids / interactive (flagship)",
        description="Print-in-place articulated mascot: nodding head, posable front and rear legs with "
                    "built-in stops (stands unaided), flexible TPU tail, 4-colour skins on both flanks. "
                    "No glue, no assembly.",
        size=size, parts=parts,
        tool_roles={"tool_1": "all structural members, joint posts/rings, eye highlights",
                    "tool_2": "patches, eye, nostril, hooves",
                    "tool_3": "muzzle, inner ear, udder",
                    "tool_4": "flexible tail (TPU)"},
        requirements={"tool_4": {"flexible": True, "strict": False, "preferred_material": "TPU",
                                 "why": "TPU tail flexes instead of snapping; a rigid tail still prints "
                                        "(6 mm thick) but is more fragile"}},
        print_orientation="Lying on its (left) side, joints vertical. No supports. Break joints free "
                          "gently after printing.",
        strategy="A - one multi-material print-in-place model (+ fused TPU tail)",
        hardware=[], packaging="premium_box", tier="PREMIUM",
        assembly_time_minutes=0.0, post_process_minutes=3.0,
        face_regions=face_regions, checks=checks,
        notes=["Joint friction depends on real clearance: 0.5 mm radial (0.35 mm normal on the 45-degree "
               "faces) is a starting point - print the joint test coupon first.",
               "Legs appear as one leg per pair in side view (the pair is one 18 mm member)."],
        self_critique={
            "exploits_4_tools": "Yes - colour skins + a flexible tail in a single print-in-place job; the "
                                "single-colour equivalent needs painting and a separate rubber tail.",
            "reliability": "Every member starts on the bed; all overhangs <= 45 deg; stops are geometric.",
            "tool_change_reduction": "Colour only in 6 skin layers + TPU in the bottom 30 layers.",
            "suitcase_durability": "No part thinner than 3.6 mm except the TPU tail, which bends.",
        },
    )
