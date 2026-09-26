#!/usr/bin/env python3
"""Preview images (brief section 25) + packaging / display mock-ups (26-27).

Per product, previews/<stem>/:
  1-single-colour.png      the same geometry in one colour (what a 1-tool printer gives)
  2-four-colour.png        PRIMARY MARKETING CONCEPT (classic variant)
  3-multi-material.png     rigid parts greyed, flexible (TPU) parts highlighted
  4-dimensions.png         orthographic views with overall dimensions
  5-print-orientation.png  as placed on the bed, build direction
  variants.png             every exported colour variant (same geometry)
  tool-layers.png          which toolhead prints on which layer (tool-change map)
Plus previews/collection-overview.png, previews/packaging-card-keyring.png,
previews/market-display-sign.png.
"""
from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import _common as C  # noqa: E402
from cad.core import config, geom, render  # noqa: E402
from cad.core.model import TOOLS  # noqa: E402
from cad.core.tools import effective_tools  # noqa: E402

BG = (236, 240, 244)
INK = (34, 38, 46)
MUTED = (110, 116, 128)
DISPLAY_ROT = {"CRW-002": [90, 0, 0], "CRW-004": [90, 0, 0], "CRW-005": [90, 0, 0]}   # printed on their side
VIEW = {"CRW-001": (-32, 16), "CRW-002": (-22, 12), "CRW-003": (-32, 16), "CRW-004": (-35, 18), "CRW-005": (-30, 12)}


def meshes(product, tools, rot=None, groups=None, colour=None, grey_rigid=False):
    out = []
    mats = config.materials()
    for p in product.parts:
        if groups and p.object_group not in groups:
            continue
        s = p.solid.rotate(rot) if rot else p.solid
        v, f = geom.mesh_arrays(s)
        rgb = render.hex_rgb(tools[p.tool]["hex"])
        if colour is not None:
            rgb = np.array(colour, float)
        if grey_rigid:
            flexible = mats[tools[p.tool]["material"]]["flexible"]
            rgb = np.array([238, 120, 40.0]) if flexible else np.array([205, 208, 214.0])
        out.append((v, f, rgb))
    return out


def _pad(img, size):
    c = Image.new("RGB", size, (250, 250, 249))
    c.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    return c


def before_after(pid, stem):
    """Side-by-side of the archived phase-1 render and the redesigned product photo."""
    before = C.ROOT / "previews" / "archive" / "before-redesign" / stem / "2-four-colour.png"
    after = C.ROOT / "previews" / stem / "photo-3q.png"
    if not (before.exists() and after.exists()):
        return
    a = Image.open(before).convert("RGB")
    b = Image.open(after).convert("RGB")
    h = 620
    a = a.resize((int(a.width * h / a.height), h))
    b = b.resize((int(b.width * h / b.height), h))
    sheet = Image.new("RGB", (a.width + b.width + 60, h + 80), (255, 255, 255))
    sheet.paste(a, (20, 60))
    sheet.paste(b, (a.width + 40, 60))
    render.label(sheet, "BEFORE (phase 1)", (24, 16), 26, (150, 60, 60))
    render.label(sheet, "AFTER (redesign)", (a.width + 44, 16), 26, (30, 110, 60))
    sheet.save(C.ROOT / "previews" / stem / "before-after.png")


def caption(img, title, sub=None):
    render.label(img, title, (18, 12), 24, INK)
    if sub:
        render.label(img, sub, (18, 44), 16, MUTED, bold=False)
    return img


def main_groups(product):
    g = list(product.groups())
    return [x for x in g if not x.startswith("pad_")] or g


def product_previews(pid, size="STANDARD"):
    product = C.build(pid, size)
    stem = product.file_stem
    out = C.ROOT / "previews" / stem
    out.mkdir(parents=True, exist_ok=True)
    a = C.load_json(C.analysis_path(stem))
    tools, _ = effective_tools(product, C.DEFAULT_VARIANT)
    rot = DISPLAY_ROT.get(pid)
    az, el = VIEW[pid]
    mg = main_groups(product)
    size_px = (900, 700)

    img = render.render_photo(meshes(product, tools, rot, mg, colour=(214, 214, 210)), az, max(el, 12), (900, 900)).resize(size_px[::-1][::-1] if False else (700, 700))
    img = _pad(img, size_px)
    caption(img, "1  Single-colour version", "same geometry, one toolhead - no markings")
    img.save(out / "1-single-colour.png")

    img = render.render_photo(meshes(product, tools, rot, mg), az, max(el, 12), (1000, 1000))
    img.save(out / "photo-3q.png")                       # simulated product photo (primary marketing)
    hero = img.resize(size_px[::-1] if False else (int(1000 * size_px[1] / 1000 * 1.0), size_px[1]))
    canvas = Image.new("RGB", size_px, (250, 250, 249))
    canvas.paste(hero, ((size_px[0] - hero.width) // 2, 0))
    caption(canvas, f"{product.id}  {product.name}", "4-colour (Classic) - colour printed, not painted")
    canvas.save(out / "2-four-colour.png")

    tiles = []
    for name, (va, ve) in {"front 3/4": (az, 15), "side": (-90, 4), "back": (155, 18), "top": (0, 89)}.items():
        t = render.render_photo(meshes(product, tools, rot, mg), va, ve, (560, 560), shadow=name != "top")
        render.label(t, name, (14, 10), 20, INK)
        tiles.append(t)
    render.grid(tiles, 4, bg=(255, 255, 255)).save(out / "views.png")

    img = render.render(meshes(product, tools, rot, None if pid == "CRW-004" else mg, grey_rigid=True),
                        az, el, size_px, BG)
    flex = [p for p in product.parts if config.materials()[tools[p.tool]["material"]]["flexible"]]
    sub = ("orange = flexible TPU: " + ", ".join(sorted({p.feature for p in flex}))[:90]) if flex \
        else "no flexible material in this product (tool 4 used as a rigid colour)"
    caption(img, "3  Multi-material map", sub)
    img.save(out / "3-multi-material.png")

    dims_img(product, tools, rot, mg, a).save(out / "4-dimensions.png")

    img = render.render(meshes(product, tools, None, None) + [bed_plate(product)], -30, 30, size_px, BG)
    caption(img, "5  Print orientation", product.print_orientation[:95])
    img.save(out / "5-print-orientation.png")

    variants = C.REGISTRY[pid][2]
    tiles = []
    for v in variants:
        vt, _ = effective_tools(product, v)
        t = render.render(meshes(product, vt, rot, mg), az, el, (420, 340), BG)
        caption(t, config.variants()[v]["name"])
        tiles.append(t)
    render.grid(tiles, min(3, len(tiles)), bg=(255, 255, 255)).save(out / "variants.png")

    layer_chart(product, a, tools, out / "tool-layers.png")
    before_after(pid, stem)
    return out / "photo-3q.png"


def bed_plate(product):
    bb = geom.union(p.solid for p in product.parts).bounding_box()
    m = 12
    plate = geom.Manifold.cube([bb[3] - bb[0] + 2 * m, bb[4] - bb[1] + 2 * m, 1.0]).translate([bb[0] - m, bb[1] - m, -1.0])
    v, f = geom.mesh_arrays(plate)
    return (v, f, np.array([60, 64, 72.0]))


def dims_img(product, tools, rot, groups, a):
    solid = geom.union(p.solid for p in product.parts if p.object_group in groups)
    if rot:
        solid = solid.rotate(rot)
    bb = solid.bounding_box()
    W, D, H = bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]
    ms = meshes(product, tools, rot, groups)
    front, tf = render.render(ms, 0, 0, (560, 460), (255, 255, 255), margin=0.22, return_transform=True)
    top, tt = render.render(ms, 0, 89.9, (560, 460), (255, 255, 255), margin=0.22, return_transform=True)
    for img, tr, (p0, p1, txt_w), (q0, q1, txt_h) in (
            (front, tf, ((bb[0], bb[1], bb[2]), (bb[3], bb[1], bb[2]), f"{W:.1f} mm"),
             ((bb[0], bb[1], bb[2]), (bb[0], bb[1], bb[5]), f"{H:.1f} mm")),
            (top, tt, ((bb[0], bb[1], bb[5]), (bb[3], bb[1], bb[5]), f"{W:.1f} mm"),
             ((bb[3], bb[1], bb[5]), (bb[3], bb[4], bb[5]), f"{D:.1f} mm"))):
        d = ImageDraw.Draw(img)
        a0, a1 = render.project([p0, p1], tr)
        b0, b1 = render.project([q0, q1], tr)
        off = 22
        d.line([(a0[0], a0[1] + off), (a1[0], a1[1] + off)], fill=INK, width=2)
        for x in (a0[0], a1[0]):
            d.line([(x, a0[1] + off - 7), (x, a0[1] + off + 7)], fill=INK, width=2)
        d.text(((a0[0] + a1[0]) / 2 - 30, a0[1] + off + 6), txt_w, font=render.font(17, True), fill=INK)
        sgn = -1 if img is front else 1
        bx0, bx1 = b0[0] + sgn * off, b1[0] + sgn * off
        d.line([(bx0, b0[1]), (bx1, b1[1])], fill=INK, width=2)
        for y in (b0[1], b1[1]):
            d.line([(bx0 - 7, y), (bx0 + 7, y)], fill=INK, width=2)
        d.text((bx0 + (10 if sgn > 0 else -10), (b0[1] + b1[1]) / 2), txt_h, font=render.font(17, True), fill=INK, anchor="lm" if sgn > 0 else "rm")
    render.label(front, "Front", (14, 10), 18, MUTED)
    render.label(top, "Top", (14, 10), 18, MUTED)
    sheet = Image.new("RGB", (1140, 560), (255, 255, 255))
    sheet.paste(front, (10, 80))
    sheet.paste(top, (570, 80))
    render.label(sheet, f"4  Dimensions - {product.id} ({product.size})", (18, 12), 24, INK)
    render.label(sheet, f"overall {W:.1f} x {D:.1f} x {H:.1f} mm (as displayed)", (18, 44), 16, MUTED, bold=False)
    return sheet


def layer_chart(product, a, tools, path):
    """Strip chart: rows = toolheads, x = layer, filled where the tool prints."""
    rows = a["layer_tools"]
    n = len(rows)
    M = np.array([[c != "." for c in r] for r in rows])
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9, 3.6), height_ratios=[4, 1.3], sharex=True,
                                  gridspec_kw={"hspace": 0.12})
    for i, t in enumerate(TOOLS):
        xs = np.where(M[:, i])[0]
        col = tools[t]["hex"]
        ax.broken_barh([(x, 1) for x in xs], (3 - i + 0.14, 0.72), facecolors=col, edgecolors="#2a2e36", linewidth=0.25)
    ax.set_yticks([3.5 - i for i in range(4)])
    ax.set_yticklabels([f"T{i + 1} {tools[t]['material']} {tools[t]['colour_name']}" for i, t in enumerate(TOOLS)],
                       fontsize=8, color="#22262e")
    ax.set_ylim(0, 4)
    ax.set_title(f"{product.id} - toolheads active per layer  ({a['tool_changes']['tool_changes']} tool changes, "
                 f"{a['tool_changes']['layers_with_changes']}/{n} layers with changes)", fontsize=9, loc="left", color="#22262e")
    k = M.sum(1)
    ax2.bar(np.arange(n) + 0.5, np.maximum(k - 1, 0), width=0.8, color="#6e7480")
    ax2.set_ylabel("changes\n(min)", fontsize=7, color="#6e7480")
    ax2.set_xlabel("layer (0.2 mm)", fontsize=8, color="#6e7480")
    for axis in (ax, ax2):
        for s in ("top", "right"):
            axis.spines[s].set_visible(False)
        axis.tick_params(colors="#6e7480", labelsize=7)
    ax.set_facecolor("#f4f5f7")
    fig.savefig(path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def overview(heroes):
    tiles = []
    for pid, path in heroes:
        im = Image.open(path).resize((440, 440), Image.LANCZOS)
        tiles.append(im)
    sheet = render.grid(tiles, 3, bg=(255, 255, 255))
    canvas = Image.new("RGB", (sheet.width, sheet.height + 70), (255, 255, 255))
    canvas.paste(sheet, (0, 70))
    render.label(canvas, "Cowaramup Cow Collection - prototype set (Classic colours)", (18, 16), 26, INK)
    canvas.save(C.ROOT / "previews" / "collection-overview.png")


def packaging_card():
    """Keyring backing card mock-up (60 x 100 mm card, rendered at 6 px/mm)."""
    pal = config.palette()
    k = 6
    W, H = 60 * k, 100 * k
    green = tuple(int(c) for c in render.hex_rgb(pal["australian_green"]["hex"]))
    card = Image.new("RGB", (W, H), (236, 240, 244))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=4 * k, fill=green)
    d.ellipse([W / 2 - 3.5 * k, 5 * k, W / 2 + 3.5 * k, 12 * k], fill=(236, 240, 244))  # hang hole
    d.rounded_rectangle([4 * k, 16 * k, W - 4 * k, 76 * k], radius=3 * k, fill=(244, 241, 232))
    product = C.build("CRW-001")
    tools, _ = effective_tools(product, "classic")
    hero = render.render(meshes(product, tools), -20, 40, (int(W - 10 * k), int(58 * k)), (244, 241, 232), margin=0.05)
    card.paste(hero, (5 * k, 17 * k))
    gold = (255, 205, 0)
    d.text((W / 2, 81 * k), "COWARAMUP", font=render.font(int(6.2 * k), True), fill=gold, anchor="mm")
    d.text((W / 2, 88 * k), "COW TOWN  WA", font=render.font(int(3.6 * k), True), fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, 94 * k), "4-Colour 3D Printed Souvenir", font=render.font(int(2.6 * k)), fill=(255, 255, 255), anchor="mm")
    card.save(C.ROOT / "previews" / "packaging-card-keyring.png")


def display_sign():
    W, H = 1500, 700
    img = Image.new("RGB", (W, H), (0, 132, 61))
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 150, W, H], fill=(92, 64, 48))
    d.text((W / 2, 90), "THE COWARAMUP", font=render.font(84, True), fill=(255, 205, 0), anchor="mm")
    d.text((W / 2, 185), "COW COLLECTION", font=render.font(84, True), fill=(255, 255, 255), anchor="mm")
    x = 60
    for pid in ("CRW-001", "CRW-002", "CRW-003", "CRW-005"):
        p = C.build(pid)
        tools, _ = effective_tools(p, "classic")
        az, el = VIEW[pid]
        t = render.render(meshes(p, tools, DISPLAY_ROT.get(pid), main_groups(p)), az, el, (330, 300), (0, 132, 61), margin=0.04)
        img.paste(t, (x, 240))
        x += 350
    d.text((W / 2, H - 75), "COLLECT THEM ALL  -  original designs, 4-colour 3D printed", font=render.font(46, True),
           fill=(255, 255, 255), anchor="mm")
    img.save(C.ROOT / "previews" / "market-display-sign.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-p", "--product", action="append")
    args = ap.parse_args()
    heroes = []
    for pid in C.selected(args.product):
        for size in C.REGISTRY[pid][1]:
            hero = product_previews(pid, size)
            if size == "STANDARD" or pid == "CRW-003":
                heroes.append((pid, hero))
            print("previews:", pid, size)
    if not args.product:
        overview(heroes)
        packaging_card()
        display_sign()
        print("overview, packaging card, display sign")


if __name__ == "__main__":
    main()
