"""CRW-001 v2 - Cowa Keyring: a miniature 3D sitting Cowa (~48 mm).

Redesign (see DESIGN_AUDIT.md): replaces the flat face cut-out.
  * Same sculpted character as the collectible, scaled 0.8, with thicker and
    shorter horns (keyrings get dropped and sat on).
  * The TAIL curls up into the key loop: 5.2 mm hole, 3.9 mm solid ring,
    fused into the rump - no separate tab to snap off.
  * 4 colours: body, markings (T2), muzzle/ears (T3), ear tag (T4 accent).
  * Hidden detail: 'COWARAMUP WA' debossed under the base of the figure.
Absolute feature sizes (grooves, highlights, loop) do not scale down.
"""
from __future__ import annotations

import numpy as np

from ..accessories.bases import _text_field
from ..core import config, sdf
from ..core.model import Product
from ..core.sculpt import sculpt_parts
from ..cows.character import CowaParams, fields

ID, SLUG = "CRW-001", "cowaramup-keyring-classic"
H = 0.28


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    k = 0.8 * d["scale"]
    g = sdf.Grid((-20 * k / 0.8, -23 * k / 0.8, 0), (20 * k / 0.8, 24 * k / 0.8, 52 * k / 0.8), H)
    P = CowaParams(scale=k, tail="loop", collar=False, bell=False, ear_tag=True,
                   horn_len=0.78, horn_r=1.25, head_yaw=-12.0)
    F = fields(g, P)
    xs, ys, zs = g.axes
    under = []
    for i, (line, cap) in enumerate((("COWARAMUP", 3.2), ("WA", 3.2))):
        t = _text_field(line, cap, xs, ys, 0.0, 9.0 * k - i * 5.0, mirror=True, max_width=24 * k)[:, :, None]
        under.append(np.maximum(np.maximum(t, g.z - 0.5), -g.z - 1.0))
    parts, env_m = sculpt_parts(g, F["env"], F["layers"], post_cut=under,
                                decimate_env=110_000, decimate_layer=35_000)
    bb = env_m.bounding_box()
    return Product(
        id=ID, slug=SLUG, name="Cowa Keyring - Classic", category="A - Multi-colour impulse",
        description="Miniature sculpted sitting Cowa (~48 mm) whose tail curls into a reinforced key loop. "
                    "4 colours incl. a tool-4 ear tag; COWARAMUP WA debossed underneath.",
        size=size, parts=parts,
        tool_roles={"tool_1": "body, horns, eyelids, highlights, tail loop",
                    "tool_2": "raised patches, forelock, pupils, nostrils, smile, hooves, tail tuft",
                    "tool_3": "muzzle, inner ears", "tool_4": "ear tag (accent / series colour)"},
        requirements={"tool_4": {"flexible": None, "strict": False, "preferred_material": "PLA",
                                 "why": "tag only; TPU tag also works"}},
        print_orientation="Upright, sitting on its flat base. No supports.",
        strategy="A - one multi-colour model (sculpted)",
        hardware=["split_ring_25mm", "keyring_chain_link"],
        packaging="impulse_backing_card", tier="IMPULSE",
        assembly_time_minutes=0.5, post_process_minutes=0.5,
        envelope=env_m,
        checks={"envelope_mm": (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]), "target_max_dim": (45.0, 60.0),
                "keyring_hole_d": 5.2, "keyring_ring_wall": 3.9, "thickness": bb[5] - bb[2],
                "hole_centre": (0.0, 21.0 * k)},
        notes=["The key loop is the tail: hole 5.2 mm, ring section 3.9 mm, fused into the rump.",
               "Horns shortened (x0.78) and thickened (x1.25) versus the collectible for pocket durability."],
        self_critique={
            "character": "Same face and pose as the collectible -> collection consistency at impulse price.",
            "durability": "No thin protrusions except horns (>= 2.3 mm tip dia) and ears (>= 3.5 mm thick).",
            "still_to_improve": "Needs a physical drop test; tag is small (4 x 3.6 mm).",
        },
    )
