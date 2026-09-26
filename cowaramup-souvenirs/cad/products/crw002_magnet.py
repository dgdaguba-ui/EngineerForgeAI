"""CRW-002 - Cowaramup Cow Head Magnet (Prototype 2).

Strategy E (printed part + hardware), single-sided:
  * Face printed UP; decoration only in the top layers (inlay + raised relief).
  * Raised 3D muzzle (tool 3) with flush black nostril plugs -> tactile, premium.
  * 'COWARAMUP' banner in tool 4 with the lettering KNOCKED OUT so the white
    core shows through: legible text with zero additional tool changes.
  * Two press-fit magnet pockets open on the bed face (short circular bridge
    ceilings, no supports). A drop of CA glue is optional.
"""
from __future__ import annotations

from shapely.ops import unary_union

from ..accessories.accessories import cow_sign, magnet_cavity
from ..core import config, geom
from ..core.model import FaceRegion, Part, Product, sandwich_parts
from ..cows import face

ID, SLUG = "CRW-002", "cowaramup-magnet"


def build(size: str = "STANDARD") -> Product:
    d = config.dims(ID, size)
    k = d["scale"]
    W = d["head_width"] * k
    T = d["thickness"]
    inlay = d["inlay_depth"]
    relief = d["muzzle_relief"]

    painter = face.face_painter(W)
    banner_cy = -0.66 * W
    board, txt = cow_sign(d["banner_text"], d["banner_width"] * k, d["banner_height"] * k,
                          d["banner_text_height"] * k, 0.0, banner_cy, min_counter=d["min_colour_island_area"])
    painter.paint("tool_4", board.difference(txt), "banner")
    painter.paint("tool_1", txt, "banner lettering (knock-out)")

    env = painter.envelope()
    regions = painter.resolve(env)
    parts, cov, _, sil = sandwich_parts(env, regions, T, inlay, top=True, bottom=False, return_coverage=True)

    # Relief outlines are taken FROM the top coverage so they meet the inlay face-to-face.
    muzzle, nostrils = face.cow_nose(W)
    core_muzzle = muzzle.difference(board).buffer(-0.5)
    pick = lambda shape, test: unary_union([p for p in geom.polygons_of(shape) if p.intersects(test)])
    raised_pink = geom.extrude(pick(cov["tool_3"], core_muzzle), T, T + relief)
    nostril_plugs = geom.extrude(pick(cov["tool_2"], nostrils.buffer(-0.3)), T, T + relief)
    by_tool = {p.tool: p for p in parts}
    by_tool["tool_3"].solid = by_tool["tool_3"].solid + raised_pink
    by_tool["tool_3"].feature += ", raised muzzle relief"
    by_tool["tool_2"].solid = by_tool["tool_2"].solid + nostril_plugs

    # Magnet pockets in the bed face, placed under the forehead/cheeks (thickest flat area).
    n_mag = int(d["magnet_count"])
    xs = [0.0] if n_mag == 1 else [-0.22 * W, 0.22 * W]
    pockets = geom.union(magnet_cavity(x, 0.02 * W, d["magnet_diameter"], d["magnet_depth"],
                                       d["magnet_fit_clearance"]) for x in xs)
    for p in parts:
        p.solid = p.solid - pockets
    envelope = (geom.extrude(sil, 0, T) + raised_pink + nostril_plugs) - pockets

    minx, miny, maxx, maxy = env.bounds
    face_regions = [FaceRegion("top", t, g) for t, g in cov.items()]   # what is actually printed
    pocket_top = d["magnet_depth"] + 0.2
    return Product(
        id=ID, slug=SLUG, name="Cowaramup Cow Head Magnet", category="A - Multi-colour impulse",
        description="4-colour fridge magnet: mascot head with raised pink muzzle and a COWARAMUP banner "
                    "whose lettering is knocked out to the white core. Two press-fit 12x3 mm magnets.",
        size=size, parts=parts,
        tool_roles={"tool_1": "core body, knocked-out banner lettering, eye highlights",
                    "tool_2": "patches, eyes, nostril plugs",
                    "tool_3": "raised muzzle, inner ears",
                    "tool_4": "horns, banner"},
        requirements={"tool_4": {"flexible": False, "strict": False, "preferred_material": "PLA",
                                 "why": "banner should be rigid; TPU works but reads less crisp"}},
        print_orientation="Face up, magnet pockets on the bed face.",
        strategy="E - hybrid printed + hardware (magnets)",
        hardware=["neodymium_disc_12x3"] * n_mag,
        packaging="impulse_backing_card", tier="IMPULSE",
        assembly_time_minutes=0.6, post_process_minutes=0.3,
        face_regions=face_regions, envelope=envelope,
        checks={"magnet_pockets": [(x, 0.02 * W) for x in xs],
                "magnet_pocket_d": d["magnet_diameter"] + 2 * d["magnet_fit_clearance"],
                "magnet_pocket_depth": pocket_top,
                "ceiling_above_pocket": T - inlay - pocket_top,
                "envelope_mm": (maxx - minx, maxy - miny, T + relief)},
        notes=["Magnets are pressed in after printing (no mid-print pause needed).",
               "Pocket fit (0.15 mm radial clearance) must be confirmed on the real printer; adjust "
               "magnet_fit_clearance in config/dimensions.json."],
        self_critique={
            "exploits_4_tools": "Yes - four colours plus 3D relief and knocked-out text in one print.",
            "every_colour_has_purpose": "Tool 4 doubles as horns AND banner so the brand line costs no extra tool.",
            "tool_change_reduction": "Colour only in the top 9 layers; bottom 22 layers single-tool.",
            "single_colour_alternative": "A single-colour print would need the banner text embossed and the "
                                         "face hand-painted - far less legible at market distance.",
        },
    )
