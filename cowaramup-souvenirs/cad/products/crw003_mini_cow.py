"""CRW-003 v2 - 'Cowa' Mini Collectible (Cowaramup Cow Collection No. 01 - Classic).

Redesign (see DESIGN_AUDIT.md): the sculpted Cowa character in a sitting,
head-turned pose - replaces the ellipsoid lying cow.

Editions
  STANDARD  3 colours (T1 body, T2 markings, T3 muzzle/ears); no base.
            ~60 mm; looks complete on its own.
  DELUXE    4 colours + story: collar, bell and ear tag in the tool-4 accent,
            standing on the 'Cowaramup Paddock' base (grass tufts, whitewashed
            fence, COWARAMUP inlaid in the front, COW TOWN WA on the back,
            series number under the base).

Support-free: the SDF model is passed through a 45-degree closure, so every
overhang (chin, ears, bell) gets a moulded fillet instead of needing supports.
"""
from __future__ import annotations

import numpy as np

from ..accessories.bases import paddock_base
from ..core import config, geom, sdf
from ..core.model import Product
from ..core.sculpt import sculpt_parts
from ..cows.character import CowaParams, fields

ID, SLUG = "CRW-003", "mini-cow-classic"
H = 0.33   # voxel size (mm) - 0.4 mm nozzle resolves ~0.4 mm, so this is enough


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    deluxe = size == "DELUXE"
    hb = 7.0 if deluxe else 0.0
    if deluxe:
        g = sdf.Grid((-41, -29, 0), (41, 29, hb + 64), H)
    else:
        g = sdf.Grid((-24, -28, 0), (24, 28, 64), H)
    P = CowaParams(zb=hb, collar=deluxe, bell=deluxe, ear_tag=deluxe)
    if deluxe:
        # sit the cow slightly forward-right so the fence frames it
        pass
    F = fields(g, P)
    env, layers, cuts = F["env"], list(F["layers"]), []
    if deluxe:
        B = paddock_base(g, under_lines=("01  CLASSIC", "COWARAMUP  WA", "CRW-003"))
        env = np.minimum(env, B["env"])
        env = sdf.smin(env, B["env"], 1.2)
        plinth_sel = B["plinth"] if B["grass"] is None else np.minimum(B["plinth"], B["grass"])
        layers = [("tool_4", plinth_sel - 0.4, "paddock base + grass")] + layers
        layers.append(("tool_1", B["fence"] - 0.5, "timber fence"))
        layers.append(("tool_1", B["text_inlay"] - 0.05, "COWARAMUP lettering"))
        cuts = B["cuts"]
    parts, env_m = sculpt_parts(g, env, layers, post_cut=cuts,
                                decimate_env=140_000, decimate_layer=45_000)
    bb = env_m.bounding_box()
    tools = sorted({p.tool for p in parts})
    return Product(
        id=ID, slug=SLUG, name="Cowa Mini Collectible - No.01 Classic" + (" (Deluxe)" if deluxe else ""),
        category="A/B - Mini collectible (Cowaramup Cow Collection)",
        description=("Sculpted sitting Cowa: head turned to camera, relaxed lids, lopsided smile, split hooves, "
                     "raised organic patches. " + ("On the Cowaramup Paddock base with fence, grass, collar, bell "
                                                    "and ear tag; COWARAMUP inlaid in the base front, series number "
                                                    "underneath." if deluxe else "Stands on its own; 3 colours.")),
        size=size, parts=parts,
        tool_roles={"tool_1": "body, horns, eyelids, highlights" + (", fence, base lettering" if deluxe else ""),
                    "tool_2": "raised patches, forelock, pupils, nostrils, smile, hooves, tail tuft",
                    "tool_3": "muzzle, inner ears",
                    **({"tool_4": "paddock base + grass, collar, bell, ear tag"} if deluxe else {})},
        requirements={"tool_4": {"flexible": False, "strict": True, "preferred_material": "PLA",
                                 "why": "the base is structural and the bell/tag are small - rigid only"}} if deluxe else {},
        print_orientation="Upright as displayed. No supports (45-degree closure is built into the model).",
        strategy="A - one multi-colour model (sculpted 3D colour volumes)",
        hardware=[], packaging="collectible_box" if deluxe else "small_gift_card_and_bag",
        tier="COLLECTIBLE" if deluxe else "SMALL_GIFT",
        assembly_time_minutes=0.0, post_process_minutes=1.5 if deluxe else 1.0,
        envelope=env_m,
        checks={"envelope_mm": (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]), "target_height": (50.0, 80.0),
                "edition": "DELUXE" if deluxe else "STANDARD", "tools": tools},
        notes=["Chin, ear and bell overhangs carry moulded 45-degree fillets from the support-free closure.",
               "Eye highlights are >= 1 mm radius at every size (3.4 mm^2 islands)."],
        self_critique={
            "character": "Head turn + roll, relaxed lids, lopsided smile, asymmetric ears -> reads as a personality.",
            "exploits_4_tools": "Deluxe: 4 colours used for storytelling (paddock/collar/bell/tag) not decoration.",
            "still_to_improve": "Patch edges are procedural-organic; a hand-drawn patch set per series cow would add "
                                "more individuality. Back view is simpler than the front.",
        },
    )
