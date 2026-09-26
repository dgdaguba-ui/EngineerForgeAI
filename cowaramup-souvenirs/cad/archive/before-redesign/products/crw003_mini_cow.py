"""CRW-003 - Mini Collectible Cow, 'Resting Cowa' (Prototype 3).

Strategy A (one multi-colour model), true 3D colour volumes.
  * Lying pose: no belly overhang, no thin standing legs -> support-free and
    suitcase-proof at 50 mm.
  * Vertical colour ZONING to limit tool changes:
      - plinth layers  : tool 4 (+ hooves, tail tuft on the same layers)
      - body layers    : tool 1 + hip patch
      - top layers     : saddle patch, head patch, eyes, horns
  * Nostrils are dimples (geometry) not colour; eye highlights omitted at this
    scale (sub-1 mm islands are unreliable).
  * Provenance text debossed into the underside (single colour, no tool change).
"""
from __future__ import annotations

from ..accessories.accessories import cow_base
from ..core import config, geom
from ..core.model import Painter3D, Part, Product
from ..cows import solid

ID, SLUG = "CRW-003", "mini-cow-classic"


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    k = d["scale"]
    zb = d["plinth_height"] * k
    plinth, text_cut = cow_base(d["plinth_length"] * k, d["plinth_width"] * k, zb,
                                d["underside_text"], d["underside_text_height"] * max(k, 1.0),
                                d["underside_text_depth"])

    body = solid.cow_body(k, zb)
    legs = solid.cow_leg(k, zb)
    hooves = solid.cow_hooves(k, zb)
    head = solid.cow_head(k, zb)
    muzzle, dimples = solid.cow_nose(k, zb)
    ears = solid.cow_ear(k, zb)
    horns = solid.cow_horn(k, zb)
    eyes, eye_ring = solid.cow_eye(k, zb)
    spots = solid.cow_spot(k, zb)
    tail, tuft = solid.cow_tail(k, zb)

    envelope = geom.union([plinth, body, legs, hooves, head, muzzle, ears, horns, tail, tuft]) - dimples - text_cut

    # Painter order = priority. The plinth is painted LAST so it owns its own volume:
    # body parts end exactly on the plinth top (a clean part interface) instead of
    # carving pockets into it.
    p = Painter3D()
    p.paint("tool_1", geom.union([body, legs, head, ears, tail, tuft]), "body, legs, head, ears, tail + tuft")
    p.paint("tool_2", spots, "patches")
    p.paint("tool_1", eye_ring, "eye ring")
    p.paint("tool_2", eyes, "eyes")
    p.paint("tool_3", muzzle, "muzzle")
    # (tail tuft is white: a black tuft on the plinth was low-contrast AND cost tool changes)
    p.paint("tool_4", hooves, "hooves")
    p.paint("tool_4", horns, "horns")
    p.paint("tool_4", plinth, "plinth")
    regions = p.resolve(envelope)
    parts = [Part(t, t, regions[t]["solid"], ", ".join(regions[t]["features"])) for t in sorted(regions)]

    bb = envelope.bounding_box()
    return Product(
        id=ID, slug=SLUG, name="Mini Collectible Cow - Resting Cowa", category="A - Multi-colour impulse",
        description="50 mm resting mascot cow on an oval plinth. Four colours as true 3D volumes, "
                    "support-free, underside debossed COWARAMUP WA.",
        size=size, parts=parts,
        tool_roles={"tool_1": "body, head, legs, ears, tail + tuft, eye ring",
                    "tool_2": "saddle/hip/head patches, eyes",
                    "tool_3": "muzzle",
                    "tool_4": "plinth, hooves, horns"},
        requirements={"tool_4": {"flexible": False, "strict": True, "preferred_material": "PLA",
                                 "why": "the plinth is structural and must be rigid (PLA/PETG). A TPU "
                                        "plinth would wobble and TPU horns under 3 mm are unreliable."}},
        print_orientation="Upright on the plinth (as displayed). No supports.",
        strategy="A - one multi-colour model (3D colour volumes, vertical zoning)",
        hardware=[], packaging="small_gift_card_and_bag", tier="SMALL_GIFT",
        assembly_time_minutes=0.0, post_process_minutes=1.0,
        checks={"envelope_mm": (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]), "target_length": 50.0,
                "plinth_height": zb},
        envelope=envelope,
        notes=["Tool 4 must be RIGID for this product (plinth). With TPU loaded in tool 4 use a 5th "
               "colour-swap job or move the plinth colour to tool 2 - validate.py flags this."],
        self_critique={
            "exploits_4_tools": "Yes - a painted-look figurine with no painting. Single-colour would need "
                                "hand-painting ~10 regions.",
            "tool_change_reduction": "Nostrils as dimples, no eye highlights, saddle patch on the top layers "
                                     "only; plinth layers are near single-tool.",
            "suitcase_durability": "Lying pose; the only protrusions are 2.5 mm horns (thick capsules).",
            "honest_weakness": "True 3D colour still needs tool changes on most layers - batch printing is "
                               "essential to amortise purge (see batch report).",
        },
    )
