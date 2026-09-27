"""COWARAMUP cow coaster set — multi-colour, 3D-printable.

Builds six 100 x 100 mm, 2 mm cup coasters (Front Face, Winking, Tongue Out,
Eyes Closed, Side Peek, Back Pattern) plus a U-cradle holder, and writes:

  * one multi-colour 3MF per coaster (one object per colour, FlashPrint /
    Orca / Bambu compatible) via the engine's `write_3mf`,
  * one STL per colour per coaster (for slicers that assemble colours from
    separate STLs — load them together, they share an origin),
  * the holder as STL + 3MF,
  * top-down PNG previews and a contact sheet.

Layer stack (printed face-up, 0.2 mm layers):

    z 0.0 – 1.0   white base (full silhouette)
    z 1.0 – 1.6   artwork inlay, flush — black / cream / pink / white
    z 1.6 – 2.0   raised black drip-lip on the rim (also the stacking rest)

so every colour change happens in the top 5 layers only.

Run from the repo root:

    uv run --project apps/engine python examples/cowaramup-coaster/generate.py
"""

from __future__ import annotations

import argparse
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from engineerforge_engine.services.threemf import Part3MF, write_3mf

# ---------------------------------------------------------------- parameters

BASE = 1.0  # white base thickness
INLAY = 0.6  # flush colour artwork layer
LIP = 0.4  # raised rim lip above the artwork
TOP = BASE + INLAY
R = 49.0  # coaster disc radius (head/ears extend the silhouette to ~100 x 100)
RIM_W = 2.5  # black rim ring width
OUTLINE = 1.1  # black outline width around head / muzzle / horns

COLORS = {
    "white": "#F4F1EA",
    "black": "#1A1A1A",
    "cream": "#F2D2B0",
    "pink": "#E8707E",
}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

Shape2D = Callable[[float], cq.Workplane]  # grow (mm) -> prism in the inlay layer


# ------------------------------------------------------------- 2D primitives
# Every primitive is a prism spanning the inlay layer [BASE, TOP]; `g` grows
# the shape outward by ~g mm so outlines are "same shape, grown, painted first".


def _wp() -> cq.Workplane:
    return cq.Workplane("XY", origin=(0, 0, BASE))


def ellipse(x: float, y: float, a: float, b: float, rot: float = 0.0) -> Shape2D:
    def f(g: float = 0.0) -> cq.Workplane:
        wp = _wp().transformed(offset=(x, y, 0), rotate=(0, 0, rot))
        return wp.ellipse(a + g, b + g).extrude(INLAY)

    return f


def circle(x: float, y: float, r: float) -> Shape2D:
    def f(g: float = 0.0) -> cq.Workplane:
        return _wp().center(x, y).circle(r + g).extrude(INLAY)

    return f


def slot(x: float, y: float, length: float, h: float, rot: float = 0.0) -> Shape2D:
    def f(g: float = 0.0) -> cq.Workplane:
        wp = _wp().transformed(offset=(x, y, 0), rotate=(0, 0, rot))
        return wp.slot2D(length + 2 * g, h + 2 * g).extrude(INLAY)

    return f


def polygon(pts: list[tuple[float, float]]) -> cq.Workplane:
    return _wp().polyline(pts).close().extrude(INLAY)


def arc_band(x: float, y: float, r: float, w: float, upper: bool) -> cq.Workplane:
    """Half-annulus (∩ if upper, ∪ if not) with round caps — eyelids, smiles."""
    ring = _wp().center(x, y).circle(r + w / 2).circle(r - w / 2).extrude(INLAY)
    box_y = y + (r + w) / 2 if upper else y - (r + w) / 2
    half = _wp().center(x, box_y).rect(2 * (r + w), r + w).extrude(INLAY)
    band = ring.intersect(half)
    for sx in (-1, 1):
        band = band.union(_wp().center(x + sx * r, y).circle(w / 2).extrude(INLAY))
    return band


def union_all(shapes: list[cq.Workplane]) -> cq.Workplane:
    out = shapes[0]
    for s in shapes[1:]:
        out = out.union(s)
    return out


def inlay_slab() -> cq.Workplane:
    return _wp().rect(400, 400).extrude(INLAY)


# ------------------------------------------------------------------- artwork


@dataclass
class Art:
    """Painter's-algorithm artwork: later layers cover earlier ones."""

    silhouette: list[cq.Workplane]
    layers: list[tuple[str, cq.Workplane]]
    lip_exclude: list[cq.Workplane]


def curved_text(
    text: str, cy: float, size: float, bend_r: float, font: str | None
) -> cq.Workplane:
    """Letters laid on a convex arc of radius `bend_r` whose apex is at y = cy."""
    kw = {"fontPath": font} if font else {"font": "Sans"}
    glyphs = [
        cq.Workplane("XY", origin=(0, 0, BASE)).text(
            ch, size, INLAY, kind="bold", halign="center", valign="center", **kw
        )
        for ch in text
    ]
    widths = [gl.val().BoundingBox().xlen for gl in glyphs]
    gap = size * 0.08
    total = sum(widths) + gap * (len(text) - 1)
    s = -total / 2
    out: cq.Workplane | None = None
    for gl, w in zip(glyphs, widths, strict=True):
        s_mid = s + w / 2
        s += w + gap
        theta = s_mid / bend_r  # radians along the arc
        px = bend_r * math.sin(theta)
        py = cy - bend_r * (1 - math.cos(theta))
        placed = gl.rotate((0, 0, 0), (0, 0, 1), -math.degrees(theta)).translate(
            (px, py, 0)
        )
        out = placed if out is None else out.union(placed)
    assert out is not None
    return out


def farm_logo(cx: float, cy: float, k: float = 1.0) -> cq.Workplane:
    """Two pine trees on rolling fields — the COWARAMUP mark."""
    parts: list[cq.Workplane] = []
    for tx, th in ((-2.6 * k, 7.5 * k), (2.6 * k, 8.5 * k)):
        x0, y0 = cx + tx, cy
        w = th * 0.42
        parts.append(
            polygon([(x0 - w, y0 + 1.2 * k), (x0 + w, y0 + 1.2 * k), (x0, y0 + th)])
        )
        parts.append(
            polygon(
                [
                    (x0 - w * 0.8, y0 + th * 0.5),
                    (x0 + w * 0.8, y0 + th * 0.5),
                    (x0, y0 + th * 1.2),
                ]
            )
        )
        parts.append(
            _wp().center(x0, y0 + 0.4 * k).rect(1.2 * k, 2.2 * k).extrude(INLAY)
        )
    for i, length in enumerate((30.0, 22.0, 13.0)):
        parts.append(slot(cx, cy - (1.6 + 3.4 * i) * k, length * k, 1.7 * k)(0))
    return union_all(parts)


def cow_spots() -> list[cq.Workplane]:
    # laid out on a unit-radius disc, scaled to R
    blobs = [
        [(-0.92, 0.26, 0.14), (-0.84, 0.12, 0.10), (-0.97, 0.06, 0.08)],
        [(0.92, 0.30, 0.12), (0.97, 0.17, 0.08)],
        [(-0.80, -0.56, 0.12), (-0.70, -0.66, 0.09)],
        [(0.84, -0.50, 0.12), (0.76, -0.62, 0.08)],
        [(-0.30, -0.92, 0.12), (-0.16, -0.97, 0.08)],
        [(0.40, -0.88, 0.10), (0.50, -0.80, 0.07)],
    ]
    inner = _wp().circle(R - RIM_W).extrude(INLAY)
    return [
        union_all([circle(x * R, y * R, r * R)(0) for x, y, r in b]).intersect(inner)
        for b in blobs
    ]


def cow_head(
    variant: str, peek: bool = False
) -> tuple[list[cq.Workplane], list[tuple[str, cq.Workplane]]]:
    """Head silhouette pieces + paint layers, in coaster coordinates.

    `peek` drops the paws and the left ear so the head can be tilted in
    from the upper-left edge (Side Peek).
    """
    hx, hy = 0.0, 28.0
    head = ellipse(hx, hy, 23.0, 17.5)
    ear_sides = (1,) if peek else (-1, 1)
    ears = [ellipse(sx * 29.5, hy + 10.0, 10.0, 5.4, sx * 26) for sx in ear_sides]
    ear_in = [ellipse(sx * 30.0, hy + 9.7, 6.4, 2.7, sx * 26) for sx in ear_sides]
    horns = [ellipse(sx * 14.0, hy + 19.0, 2.6, 5.0, sx * -22) for sx in (-1, 1)]
    tuft = [
        circle(-9, hy + 15.5, 5.0),
        circle(-1.5, hy + 17.5, 5.2),
        circle(6, hy + 15.8, 4.2),
    ]
    hair = ellipse(-13.5, hy + 6.0, 10.0, 9.5, 20)
    muzzle = ellipse(hx, hy - 7.0, 14.5, 8.5)
    paw_sides = () if peek else (-1, 1)
    paws = [ellipse(sx * 20.5, hy - 17.0, 6.2, 4.6, sx * -8) for sx in paw_sides]

    black, cream, white, pink = "black", "cream", "white", "pink"
    L: list[tuple[str, cq.Workplane]] = []
    L += [(black, e(OUTLINE)) for e in ears]
    L += [(cream, e(0)) for e in ear_in]
    L += [(black, h(OUTLINE)) for h in horns]
    L += [(cream, h(0)) for h in horns]
    L += [(black, head(OUTLINE)), (white, head(0))]
    L += [(black, hair(0).intersect(head(0)))]
    L += [(black, t(0)) for t in tuft]
    L += [(black, muzzle(OUTLINE * 0.8)), (cream, muzzle(0))]
    for sx in (-1, 1):  # nostrils
        L.append((black, ellipse(sx * 4.8, hy - 5.0, 1.7, 1.1)(0)))
    L.append((black, arc_band(hx, hy - 7.5, 5.2, 1.3, upper=False)))  # smile

    eye_y, eye_dx = hy + 3.5, 9.5
    for sx in (-1, 1):  # white eye patch so the eye reads on the black hair
        L.append((white, ellipse(sx * eye_dx, eye_y, 5.4, 6.0)(0).intersect(head(0))))

    def open_eye(sx: int) -> None:
        L.append((black, ellipse(sx * eye_dx, eye_y, 3.6, 4.2)(0)))
        L.append((white, circle(sx * eye_dx + 1.2, eye_y + 1.5, 1.2)(0)))

    def closed_eye(sx: int) -> None:
        L.append((black, arc_band(sx * eye_dx, eye_y - 1.5, 3.0, 1.3, upper=True)))

    if variant == "eyes-closed":
        closed_eye(-1)
        closed_eye(1)
    elif variant == "winking":
        open_eye(-1)
        closed_eye(1)
    else:
        open_eye(-1)
        open_eye(1)

    if variant == "tongue-out":
        tongue = ellipse(hx + 1.5, hy - 13.2, 2.8, 3.4, -10)
        L += [(black, tongue(0.8)), (pink, tongue(0))]
        L.append(
            (black, arc_band(hx, hy - 7.5, 5.2, 1.3, upper=False))
        )  # redraw smile over

    for p in paws:
        L += [(black, p(0))]
    for sx in paw_sides:  # toe splits
        for d in (-1.8, 1.8):
            L.append((white, slot(sx * 20.5 + d, hy - 18.4, 3.2, 0.7, 90 + sx * -8)(0)))

    silhouette = (
        [head(OUTLINE)]
        + [e(OUTLINE) for e in ears]
        + [h(OUTLINE) for h in horns]
        + [t(0) for t in tuft]
    )
    return silhouette, L


def build_art(variant: str, font: str | None) -> Art:
    disc = _wp().circle(R).extrude(INLAY)
    rim = _wp().circle(R).circle(R - RIM_W).extrude(INLAY)
    layers: list[tuple[str, cq.Workplane]] = [("black", rim)]
    layers += [("black", s) for s in cow_spots()]
    silhouette = [disc]
    lip_exclude: list[cq.Workplane] = []

    if variant == "back-pattern":
        layers.append(("black", farm_logo(0, -2, k=1.6)))
        return Art(silhouette, layers, lip_exclude)

    layers.append(("black", curved_text("COWARAMUP", -4.0, 9.5, 110.0, font)))
    layers.append(("black", farm_logo(0, -21.5)))

    peek = variant == "side-peek"
    head_sil, head_layers = cow_head("front-face" if peek else variant, peek=peek)
    if peek:
        # tilt the head about its own centre and slide it to the upper-left
        def move(w: cq.Workplane) -> cq.Workplane:
            return w.rotate((0, 28, 0), (0, 28, 1), 22).translate((-14.0, -3.0, 0))

        head_sil = [move(s) for s in head_sil]
        head_layers = [(c, move(s)) for c, s in head_layers]

    silhouette += head_sil
    layers += head_layers
    lip_exclude += head_sil
    return Art(silhouette, layers, lip_exclude)


# -------------------------------------------------------------- solid build


def paint(art: Art) -> dict[str, cq.Workplane]:
    """Resolve painter's layers into disjoint per-colour solids."""
    outline = union_all(art.silhouette)
    regions: dict[str, cq.Workplane] = {}
    for color, solid in art.layers:
        solid = solid.intersect(outline)
        for c in list(regions):
            regions[c] = regions[c].cut(solid)
        regions[color] = solid if color not in regions else regions[color].union(solid)
    regions.pop("white", None)  # white = whatever is left
    colored = union_all(list(regions.values()))

    # base = the silhouette prism stacked down until it fills z 0..BASE
    steps = math.ceil(BASE / INLAY)
    base = union_all(
        [
            outline.translate((0, 0, -BASE + i * (BASE - INLAY) / max(steps - 1, 1)))
            for i in range(steps)
        ]
    )
    top_white = outline.cut(colored)
    bodies = {"white": base.union(top_white)}

    lip = (
        cq.Workplane("XY", origin=(0, 0, TOP)).circle(R).circle(R - RIM_W).extrude(LIP)
    )
    for ex in art.lip_exclude:
        lip = lip.cut(ex.translate((0, 0, INLAY)))
    bodies["black"] = regions["black"].union(lip)
    for c in ("cream", "pink"):
        if c in regions and regions[c].vals():
            bodies[c] = regions[c]
    return bodies


def build_holder(
    width: float = 110.0, height: float = 65.0, count: int = 6
) -> cq.Workplane:
    """U-cradle that holds `count` coasters on edge, faces forward.

    Inner width = coaster disc + 3 mm clearance; slot depth = count x (2 mm + 0.5 mm)
    + 2 mm play. Front/back walls are scooped so the cow faces show; the
    tall side cheeks match the 65 mm front-view height.
    """
    wall, floor, r_out = 3.0, 3.0, 6.0
    inner_w = 2 * R + 3.0  # coaster disc width + clearance
    slot = count * (TOP + LIP + 0.5) + 2.0
    depth = slot + 2 * wall + 14.0  # extra front/back meat for stability
    width = max(width, inner_w + 2 * wall)
    body = (
        cq.Workplane("XY").rect(width, depth).extrude(height).edges("|Z").fillet(r_out)
    )
    pocket = (
        cq.Workplane("XY", origin=(0, 0, floor))
        .rect(inner_w, slot)
        .extrude(height)
        .edges("|Z")
        .fillet(1.5)
    )
    body = body.cut(pocket)
    # scoop: cylinder along Y, lowest point 22 mm above the floor. r = 50
    # exits the top at x ~ +/-49 (inside the 50.5 mm pocket half-width) at a
    # clear angle, so the side cheeks keep full `height` and OCC gets no
    # tangent edge (a larger radius tessellates with open seams).
    low, scoop_r = floor + 22.0, 50.0
    scoop = (
        cq.Workplane("XZ", origin=(0, depth, 0))
        .center(0, low + scoop_r)
        .circle(scoop_r)
        .extrude(2 * depth)
    )
    body = body.cut(scoop)
    # thumb notch in the floor to push the stack up
    notch = cq.Workplane("XY").slot2D(40, 10).extrude(floor)
    body = body.cut(notch)
    # soften every edge
    try:
        body = body.edges().fillet(0.8)
    except Exception:  # noqa: BLE001 — cosmetic, OCC can refuse on tiny edges
        pass
    return body


# ------------------------------------------------------------------- export


def tessellate(w: cq.Workplane, tol: float = 0.02) -> tuple[list, list]:
    shape = cq.Compound.makeCompound([v for v in w.vals() if isinstance(v, cq.Shape)])
    verts, tris = shape.tessellate(tol, 0.2)
    return [(v.x, v.y, v.z) for v in verts], [tuple(t) for t in tris]


def preview_png(meshes: dict[str, tuple[list, list]], path: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    fig, ax = plt.subplots(figsize=(4, 4), dpi=150)
    polys = []
    for color, (v, t) in meshes.items():
        for a, b, c in t:
            z = max(v[a][2], v[b][2], v[c][2])
            polys.append((z, color, [v[a][:2], v[b][:2], v[c][:2]]))
    polys.sort(key=lambda p: p[0])
    pc = PolyCollection(
        [p[2] for p in polys],
        facecolors=[COLORS[p[1]] for p in polys],
        edgecolors="none",
        antialiased=False,
    )
    ax.add_collection(pc)
    ax.set_xlim(-55, 55)
    ax.set_ylim(-52, 58)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10)
    fig.savefig(path, bbox_inches="tight", facecolor="#DDE3EA")
    plt.close(fig)


VARIANTS = [
    ("1", "front-face", "Front Face"),
    ("2", "winking", "Winking"),
    ("3", "tongue-out", "Tongue Out"),
    ("4", "eyes-closed", "Eyes Closed"),
    ("5", "side-peek", "Side Peek"),
    ("6", "back-pattern", "Back Pattern"),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "output")
    ap.add_argument("--only", help="variant slug to build (default: all)")
    ap.add_argument("--no-stl", action="store_true", help="skip per-colour STLs")
    ap.add_argument("--font", help="TTF for the lettering (default: DejaVu Sans Bold)")
    args = ap.parse_args()

    font = args.font or next((f for f in FONT_CANDIDATES if Path(f).exists()), None)
    args.out.mkdir(parents=True, exist_ok=True)

    for num, slug, title in VARIANTS:
        if args.only and args.only != slug:
            continue
        print(f"building coaster {num} {title} ...", flush=True)
        bodies = paint(build_art(slug, font))
        meshes = {c: tessellate(b) for c, b in bodies.items()}
        stem = f"coaster_{num}_{slug}"
        write_3mf(
            args.out / f"{stem}.3mf",
            [
                Part3MF(
                    name=f"{stem}_{c}",
                    vertices=v,
                    triangles=t,
                    color_hex=COLORS[c],
                    material_name=f"PLA {c}",
                )
                for c, (v, t) in meshes.items()
            ],
        )
        if not args.no_stl:
            for c, b in bodies.items():
                cq.exporters.export(
                    b, str(args.out / f"{stem}_{c}.stl"), tolerance=0.02
                )
        bb = union_all(list(bodies.values())).val().BoundingBox()
        print(
            f"  size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.2f} mm; colours {list(bodies)}"
        )
        png = args.out / f"{stem}.png"
        preview_png(meshes, png, f"{num}. {title}")

    if not args.only or args.only == "holder":
        print("building holder ...", flush=True)
        holder = build_holder()
        cq.exporters.export(holder, str(args.out / "holder.stl"), tolerance=0.02)
        v, t = tessellate(holder)
        write_3mf(
            args.out / "holder.3mf",
            [Part3MF("holder", v, t, COLORS["black"], "PLA black")],
        )
        bb = holder.val().BoundingBox()
        print(f"  holder {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")

    previews = sorted(args.out.glob("coaster_*.png"))
    if len(previews) == len(VARIANTS):
        from PIL import Image

        imgs = [Image.open(p) for p in previews]
        w, h = imgs[0].size
        sheet = Image.new("RGB", (w * 3, h * 2), "#DDE3EA")
        for i, im in enumerate(imgs):
            sheet.paste(im.resize((w, h)), ((i % 3) * w, (i // 3) * h))
        sheet.save(args.out / "contact_sheet.png")


if __name__ == "__main__":
    main()
