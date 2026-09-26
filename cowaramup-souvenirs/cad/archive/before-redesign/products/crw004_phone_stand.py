"""CRW-004 - Cow Phone Stand (Prototype 4) - multi-material.

Strategy D (inserted TPU components) + A (sandwich inlay decoration):
  * The stand is a 'resting cow' side profile EXTRUDED to 64 mm and printed ON
    ITS SIDE. Every functional feature (slot, dovetail grooves, lip) is in the
    profile plane -> zero supports, and layer lines run along the load path.
  * The phone leans back at 68 deg in a 15 mm slot (fits phone + case up to
    ~12.6 mm after pads). Works in portrait and landscape.
  * Four identical slide-in TPU pads (tool 4): rear-wall contact, front-lip
    contact and two non-slip feet. They are printed as SEPARATE objects on the
    same plate (only 9 layers tall), then slid into dovetail grooves - no glue,
    no fused PLA/TPU interface to fail, replaceable.
  * Decoration (both side faces, 0.6 mm inlays): patches, eye, nostril, hoof,
    muzzle, inner ear and a COWARAMUP band with knocked-out lettering.
"""
from __future__ import annotations

import math

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

from ..accessories.accessories import dovetail_groove_profile, phone_slot, tpu_pad
from ..core import config, geom
from ..core.model import FaceRegion, Painter2D, Part, Product, sandwich_parts
from ..core.text import text_shape
from ..cows.side import cow_head_side

ID, SLUG = "CRW-004", "cow-phone-stand"
GROOVE_NECK, GROOVE_DEPTH, GROOVE_CLEAR = 3.2, 2.0, 0.15


def profile(d: dict):
    """Returns (silhouette, painter_top, painter_bottom, slot_info, grooves)."""
    body = geom.ellipse(52, 21, 50, 21).intersection(box(-10, 0, 200, 100))
    base = geom.rounded_rect(53, 5, 94, 10, 3).intersection(box(-10, 0, 200, 100))
    rump = geom.ellipse(22, 13, 19, 13).intersection(box(-10, 0, 200, 100))
    front_leg = geom.tapered_stroke([(76, 5.5), (100, 5.0)], 5.5, 5.0, 12).intersection(box(-10, 0, 200, 100))
    hoof = geom.ellipse(103, 5.0, 5.5, 5.0).intersection(box(-10, 0, 200, 100))
    head_top = cow_head_side(103, 29, 30, 1, patch=True)
    head_bot = cow_head_side(103, 29, 30, 1, patch=False)

    slot, sinfo = phone_slot(d["slot_floor_u"], d["slot_floor_v"], d["lean_angle_deg"],
                             d["phone_slot_width"], d["phone_slot_depth"])
    solid_outline = unary_union([body, base, rump, front_leg, hoof, head_top["outline"]])
    silhouette = geom.clean(solid_outline.difference(slot))

    # Dovetail grooves (profile plane). (point, inward, along)
    n, dvec = sinfo["normal"], sinfo["dir"]
    grooves = {
        "rear_wall": (sinfo["rear0"] + dvec * 19.0, -n, dvec),
        "front_lip": (sinfo["front0"] + dvec * 7.0, n, dvec),
        "foot_rear": (np.array([22.0, 0.0]), np.array([0, 1.0]), np.array([1.0, 0])),
        "foot_front": (np.array([88.0, 0.0]), np.array([0, 1.0]), np.array([1.0, 0])),
    }
    groove_polys = unary_union([dovetail_groove_profile(p, i, a, 0, GROOVE_DEPTH, GROOVE_NECK, GROOVE_CLEAR)
                                for p, i, a in grooves.values()])
    silhouette = geom.clean(silhouette.difference(groove_polys))

    def decorate(head, mirror_text: bool):
        p = Painter2D()
        p.paint("tool_1", silhouette, "body")
        band = geom.rounded_rect(56, 8.2, 84, 11.0, 4.0)
        txt = text_shape(d["flank_text"], 7.0, 56, 8.2, max_width=74, min_counter=d["min_colour_island_area"])
        if mirror_text:
            txt = geom.mirror_about_own_centre(txt)
        p.paint("tool_2", band.difference(txt), "COWARAMUP band")
        p.paint("tool_2", geom.blob([(24, 29, 9), (33, 33, 7), (16, 23, 6)], smooth=2), "rump patch")
        p.paint("tool_2", geom.blob([(80, 30, 7.5), (88, 27, 6), (74, 24, 5)], smooth=2), "shoulder patch")
        p.paint("tool_2", geom.tapered_stroke(geom.bezier((5, 26), (-1, 18), (6, 12), 10), 1.4, 1.0, 14), "tail")
        p.paint("tool_2", geom.ellipse(7, 11, 3.2, 2.6), "tail tuft")
        p.paint("tool_2", hoof, "hoof")
        p.paint("tool_1", head["outline"], "head")
        p.paint("tool_1", head["horn"], "horn")
        p.paint("tool_3", head["inner_ear"], "inner ear")
        if head["patch"] is not None:
            p.paint("tool_2", head["patch"], "eye patch")
            p.paint("tool_1", head["eye_ring"], "eye ring")
        p.paint("tool_3", head["muzzle"], "muzzle")
        p.paint("tool_2", head["nostril"], "nostril")
        p.paint("tool_2", head["eye"], "eye")
        p.paint("tool_1", head["highlight"], "eye highlight")
        return p

    return silhouette, decorate(head_top, False), decorate(head_bot, True), sinfo, grooves


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    Wd = d["width"]
    inlay = d["inlay_depth"]
    pad_t = d["pad_thickness"]
    silhouette, ptop, pbot, sinfo, grooves = profile(d)
    top = ptop.resolve(silhouette)
    bottom = pbot.resolve(silhouette)
    parts, cov_top, _, _ = sandwich_parts(silhouette, top, Wd, inlay, bottom_regions=bottom, group="stand",
                                          return_coverage=True)

    # Four slide-in TPU pads laid out beside the stand (print orientation: face down).
    minx, miny, maxx, maxy = silhouette.bounds
    pad_len = Wd - 1.0
    for i, name in enumerate(grooves):
        pad = tpu_pad(pad_len, d["pad_width"], pad_t, GROOVE_NECK, GROOVE_DEPTH)
        pad = pad.translate([maxx + 12 + i * (d["pad_width"] + 8), miny, 0])
        parts.append(Part(f"tpu_pad_{name}", "tool_4", pad, f"TPU pad ({name.replace('_', ' ')})",
                          object_group=f"pad_{name}", requires={"flexible": True}))

    # Stability: phone CG vs. rear edge (tipping backwards), in profile coordinates.
    a = math.radians(d["lean_angle_deg"])
    floor = sinfo["floor"]
    rear_edge_u = minx
    checks = {"lean_angle_deg": d["lean_angle_deg"], "slot_width": d["phone_slot_width"],
              "max_device_thickness": d["phone_slot_width"] - 2 * pad_t,
              "slot_floor": tuple(floor), "rear_edge_u": rear_edge_u,
              "phone_cases": {}}
    for label, h in (("portrait_small_140mm", 140), ("portrait_large_170mm", 170),
                     ("landscape_75mm", 75), ("tablet_portrait_250mm", 250)):
        cg_u = floor[0] - math.cos(a) * h / 2
        checks["phone_cases"][label] = {"cg_u": round(cg_u, 1), "stable": bool(cg_u > rear_edge_u + 5)}
    checks["envelope_profile_mm"] = (maxx - minx, maxy - miny)
    checks["width"] = Wd
    checks["groove"] = {"neck": GROOVE_NECK, "depth": GROOVE_DEPTH, "clearance": GROOVE_CLEAR}

    face_regions = [FaceRegion("side_top", t, g) for t, g in cov_top.items()]   # what is actually printed
    return Product(
        id=ID, slug=SLUG, name="Cow Phone Stand - Resting Cowa", category="C - Multi-material functional",
        description="Resting-cow profile phone stand (portrait + landscape, case-compatible up to ~12.6 mm) "
                    "with four slide-in TPU pads (two contact pads, two non-slip feet) and 4-colour flank "
                    "artwork on both sides.",
        size=size, parts=parts,
        tool_roles={"tool_1": "structural stand body, knocked-out lettering, horn, highlights",
                    "tool_2": "patches, COWARAMUP band, eye, nostril, hoof, tail",
                    "tool_3": "muzzle, inner ear",
                    "tool_4": "TPU contact pads + non-slip feet (functional)"},
        requirements={"tool_4": {"flexible": True, "strict": True, "preferred_material": "TPU",
                                 "why": "pads must be flexible for grip and to protect the phone"}},
        print_orientation="On its side (profile on the bed); TPU pads face-down beside it.",
        strategy="D - inserted TPU components (+A sandwich inlay artwork)",
        hardware=[], packaging="small_gift_card_and_bag", tier="SMALL_GIFT",
        assembly_time_minutes=1.5, post_process_minutes=1.0,
        face_regions=face_regions, checks=checks,
        notes=["TPU pads slide in from either side; a tight fit is intended. If loose, reduce "
               "GROOVE_CLEAR or add a dab of CA at one end.",
               "No charging-cable channel in this prototype (profile-extruded design). Candidate for v2: "
               "a 12 mm notch in the slot floor at mid-width (requires a bridged cut)."],
        self_critique={
            "exploits_4_tools": "Yes - 3 decorative colours + a functional flexible material in one plate.",
            "multi_material_purpose": "TPU = grip + phone protection + non-slip feet. PLA = stiffness.",
            "tool_change_reduction": "TPU pads are only 9 layers tall and share layers with the bottom inlay; "
                                     "the 300+ core layers are single-tool.",
            "single_colour_alternative": "Possible, but would need glued rubber feet and painted artwork.",
        },
    )
