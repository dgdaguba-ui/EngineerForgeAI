"""CRW-001 - Cowaramup Cow Keyring (Prototype 1).

Strategy A (one multi-colour model), 'sandwich inlay':
  * Flat mascot face, printed flat, identical design on both faces.
  * Core (all middle layers) = tool 1 only.
  * Colour lives in the bottom 3 and top 3 layers (0.6 mm) -> tool changes
    happen on ~6 of 21 layers. Flush inlays cannot snag or chip in a pocket.
  * Keyring loop: absolute 3 mm ring wall around a 5 mm hole, full thickness,
    tool 1 (no colour boundary crosses the load path).
"""
from __future__ import annotations

from shapely.ops import unary_union

from ..accessories.accessories import keyring_loop
from ..core import config, geom
from ..core.model import FaceRegion, Product, sandwich_parts
from ..cows import face

ID, SLUG = "CRW-001", "cowaramup-keyring-classic"


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    W = d["head_width"] * d["scale"]
    T = d["thickness"]
    inlay = d["inlay_depth"]

    painter = face.face_painter(W)
    head_top = face.FOREHEAD["c"][1] * W + face.FOREHEAD["r"][1] * W
    hole_d = d["keyring_hole"]
    loop_cy = head_top + hole_d / 2 + 0.6
    loop, hole = keyring_loop(0.0, loop_cy, hole_d, d["keyring_ring_wall"])
    painter.layers.insert(0, ("tool_1", loop, "keyring loop"))

    silhouette = geom.clean(painter.envelope().difference(hole))
    top = painter.resolve(silhouette)
    # Bed face: mirror the whole design so a viewer on either side sees the same cow.
    bottom = {t: {"shape": geom.mirror_x(r["shape"]), "features": r["features"]} for t, r in top.items()}
    parts, cov_top, _, sil = sandwich_parts(silhouette, top, T, inlay, bottom_regions=bottom, return_coverage=True)

    minx, miny, maxx, maxy = silhouette.bounds
    face_regions = [FaceRegion("top", t, g) for t, g in cov_top.items()]   # what is actually printed

    return Product(
        id=ID, slug=SLUG, name="Cowaramup Cow Keyring", category="A - Multi-colour impulse",
        description="Flat 4-colour mascot keyring, identical face on both sides, flush sandwich inlays, "
                    "reinforced 5 mm keyring hole. No painting, no assembly beyond fitting the split ring.",
        size=size, parts=parts,
        tool_roles={"tool_1": "core body, keyring loop, eye highlights",
                    "tool_2": "signature patch, forehead spot, eyes, nostrils",
                    "tool_3": "muzzle, inner ears",
                    "tool_4": "horns"},
        requirements={"tool_4": {"flexible": None, "strict": False, "preferred_material": "PLA",
                                 "why": "any material; TPU gives bump-proof soft horns, PLA gives crisper colour"}},
        print_orientation="Flat, either face on the bed (design is mirrored so both faces match).",
        strategy="A - one multi-colour model (sandwich inlay)",
        hardware=["split_ring_25mm", "keyring_chain_link"],
        packaging="impulse_backing_card", tier="IMPULSE",
        assembly_time_minutes=0.5, post_process_minutes=0.3,
        face_regions=face_regions, envelope=geom.extrude(sil, 0, T),
        checks={"keyring_hole_d": hole_d, "keyring_ring_wall": d["keyring_ring_wall"],
                "hole_centre": (0.0, loop_cy), "thickness": T,
                "envelope_mm": (maxx - minx, maxy - miny, T), "target_max_dim": (45.0, 60.0)},
        notes=["Horn tips are the most exposed feature; if drop tests chip them, switch tool_4 to TPU "
               "(no geometry change needed)."],
        self_critique={
            "exploits_4_tools": "Yes - four colours in one print with zero painting; a single-colour printer "
                                "would need hand painting of 7 regions per side.",
            "every_colour_has_purpose": "White = body/structure, black = cow identity (patches/eyes), pink = "
                                        "muzzle (cuteness/readability), tool 4 = horns (silhouette cue).",
            "tool_change_reduction": "Colour confined to 6 of 21 layers; middle layers single-tool.",
            "suitcase_durability": "Flat, no thin cantilevers except horn tips (>= 4 mm wide).",
            "batch": "Flat and small -> 16-32 per plate; per-unit purge falls with batch size.",
        },
    )
