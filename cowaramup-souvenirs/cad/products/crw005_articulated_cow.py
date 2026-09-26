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

from ..core import config, geom
from ..core.model import FaceRegion, Painter2D, Part, Product, sandwich_parts
from ..cows.side import cow_head_side
from ..mechanisms.joints import hinge, sweep2d

ID, SLUG = "CRW-005", "articulated-cow"


def _layout(d):
    ground = box(-50, 0, 250, 200)
    torso = unary_union([geom.ellipse(52, 50, 34, 16), geom.ellipse(24, 52, 12, 14),
                         geom.ellipse(58, 36, 8, 5.5),
                         geom.tapered_stroke([(76, 57), (88, 63)], 10, 8, 10)])
    head = cow_head_side(104, 74, 30, 1, patch=True)
    head_b = cow_head_side(104, 74, 30, 1, patch=False)
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

    def skins(outline, deco, mirror=False):
        p = Painter2D()
        p.paint("tool_1", outline, "core")
        for tool, shape, feat in deco:
            p.paint(tool, shape, feat)
        return p.resolve(outline)

    body_deco = [("tool_2", geom.blob([(40, 58, 9), (50, 55, 7), (32, 53, 6)], smooth=2), "flank patch"),
                 ("tool_2", geom.blob([(70, 53, 7), (77, 58, 5)], smooth=2), "shoulder patch"),
                 ("tool_3", geom.ellipse(58, 36, 7, 4.6), "udder")]

    def head_deco(h):
        out = [("tool_3", h["inner_ear"], "inner ear")]
        if h["patch"] is not None:
            out += [("tool_2", h["patch"], "eye patch"), ("tool_1", h["eye_ring"], "eye ring")]
        out += [("tool_3", h["muzzle"], "muzzle"), ("tool_2", h["nostril"], "nostril"),
                ("tool_2", h["eye"], "eye"), ("tool_1", h["highlight"], "eye highlight")]
        return out

    hoof = box(-50, -1, 250, 8.5)
    leg_deco = [("tool_2", hoof, "hoof")]

    parts: list[Part] = []
    face_regions: list[FaceRegion] = []
    specs = {
        "body": (body2d, body_deco, body_deco),
        "head": (members2d["head"], head_deco(head), head_deco(head_b)),
        "front_leg": (members2d["front_leg"], leg_deco, leg_deco),
        "rear_leg": (members2d["rear_leg"], leg_deco, leg_deco),
    }
    for name, (outline, deco_top, deco_bot) in specs.items():
        top = skins(outline, deco_top)
        bot = skins(outline, deco_bot)
        ps, cov_top, _, _ = sandwich_parts(outline, top, T, inlay, bottom_regions=bot, group=name,
                                           prefix=f"{name}_", return_coverage=True)
        if name in J:
            for p in ps:
                p.solid = p.solid - J[name]["hole"]
        parts += ps
        face_regions += [FaceRegion(f"{name}_top", t, g) for t, g in cov_top.items()]

    # Bicone posts join the fixed body core (colour skins keep priority).
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
