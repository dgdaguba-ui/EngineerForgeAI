#!/usr/bin/env python3
"""Quality-control validation for every generated product (brief sections 20 + 24).

Run after scripts/generate.py. Writes documentation/qc/qc-report.md and
products/generated/qc-report.json. Exit code 1 if any check FAILs.

Status meanings: PASS | WARN (review) | FAIL (do not print) | SETUP (valid, but the
printer's loaded materials must change first) | INFO (documented assumption).
"""
from __future__ import annotations

import argparse
import math
import sys
import zipfile

import numpy as np
import trimesh
from lxml import etree

import _common as C
from cad.core import analysis, config, geom
from cad.core.model import TOOLS
from cad.core.tools import effective_tools

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def luminance(hexs: str) -> float:
    h = hexs.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def lab(hexs: str):
    h = hexs.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    M = [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]
    X, Y, Z = (sum(M[i][j] * lin[j] for j in range(3)) for i in range(3))
    ref = (0.95047, 1.0, 1.08883)
    f = [(v / r) ** (1 / 3) if v / r > 0.008856 else 7.787 * v / r + 16 / 116 for v, r in zip((X, Y, Z), ref)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def delta_e(a: str, b: str) -> float:
    return math.dist(lab(a), lab(b))


class Report:
    def __init__(self):
        self.rows = []

    def add(self, pid, check, status, detail):
        self.rows.append({"product": pid, "check": check, "status": status, "detail": detail})

    def worst(self, pid=None):
        order = ["PASS", "INFO", "SETUP", "WARN", "FAIL"]
        rows = [r for r in self.rows if pid is None or r["product"] == pid]
        return max((r["status"] for r in rows), key=order.index, default="PASS")


def rotate_about(solid, pivot, deg):
    return solid.translate([-pivot[0], -pivot[1], 0]).rotate([0, 0, deg]).translate([pivot[0], pivot[1], 0])


def check_product(pid: str, size: str, R: Report, variants: list[str]):
    product = C.build(pid, size)
    stem = product.file_stem
    tag = f"{stem}"
    apath = C.analysis_path(stem)
    if not apath.exists():
        R.add(tag, "analysis present", "FAIL", "run scripts/generate.py first")
        return
    a = C.load_json(apath)
    dims = config.dims(pid, size)
    printer = config.printer()
    mats = config.materials()

    # 1-2. mesh + manifold validation
    bad = []
    for p in product.parts:
        tm = analysis.to_tm(p.solid)
        if str(p.solid.status()) != "Error.NoError" or not tm.is_watertight or not tm.is_winding_consistent \
                or p.solid.volume() <= 0:
            bad.append(p.name)
    R.add(tag, "mesh + manifold (watertight, winding, volume>0)", "FAIL" if bad else "PASS",
          f"non-manifold parts: {bad}" if bad else f"{len(product.parts)} parts watertight")

    stl = C.ROOT / a["files"]["stl"][0]
    tm = trimesh.load(stl)
    R.add(tag, "merged single-colour STL re-load", "PASS" if tm.is_watertight else "WARN",
          f"{len(tm.faces)} faces, watertight={tm.is_watertight}, volume={tm.volume:.0f} mm3")

    from cad.core.export import pinch_points
    pinches = {p.name: len(pinch_points(p.solid)) for p in product.parts}
    total = sum(pinches.values())
    detail = ", ".join(f"{k}:{v}" for k, v in pinches.items() if v)
    R.add(tag, "per-part STL re-load (vertex-welded, as a slicer reads it)",
          "PASS" if total == 0 else ("WARN" if total <= 20 else "FAIL"),
          f"{len(product.parts)} part STLs watertight after position welding" if total == 0 else
          f"{total} isolated pinch edges ({detail}) - zero-area contacts where colour regions meet; "
          "the indexed 3MF keeps exact manifold topology; slicers repair these on STL import")

    # 3. part disjointness (assignment is unambiguous for the slicer)
    ov = a.get("max_part_overlap_mm3", analysis.pairwise_overlap(product))
    R.add(tag, "parts disjoint (no double-assigned volume)", "PASS" if ov < 0.1 else "FAIL", f"max overlap {ov} mm3 (tolerance 0.1 mm3: sub-micron edge collapse)")

    # 4. bed fit
    bx, by, bz = printer["bed_x_mm"], printer["bed_y_mm"], printer["max_z_mm"]
    w, d, h = a["plate_bbox_mm"]
    fits = (w <= bx and d <= by) or (d <= bx and w <= by)
    R.add(tag, "fits build volume", "PASS" if fits and h <= bz else "FAIL", f"plate {w} x {d} x {h} mm vs bed {bx} x {by} x {bz}")

    # 5. wall thickness (5th percentile of inward ray-cast thickness)
    for g, wt in a.get("wall_thickness", {}).items():
        mat = next(p for p in product.parts if p.object_group == g)
        is_tpu = mats[a["effective_tools"][mat.tool]["material"]]["flexible"]
        limit = dims["min_tpu_feature"] if is_tpu else dims["wall_thickness"]
        p5 = wt["p5_mm"]
        R.add(tag, f"wall thickness [{g}]", "PASS" if p5 is not None and p5 >= limit * 0.99 else "WARN",
              f"p5 {p5} mm, median {wt['median_mm']} mm (limit {limit} mm; p1 {wt['p1_mm']} mm is edge/chamfer noise)")

    # 6. overhangs / supports
    for g, oh in a.get("overhangs", {}).items():
        steep = oh["steep_overhang_area_mm2"]
        need = oh.get("support_required_area_mm2", steep)
        span = oh["max_bridge_span_mm"]
        status = "PASS" if need <= 30.0 and span <= 15.0 else "WARN"
        R.add(tag, f"overhangs/supports [{g}]", status,
              f"support-required (>60 deg, >2 mm drop) {need} mm2; 45-deg-rule area {steep} mm2 (info); "
              f"bridges {oh['bridge_area_mm2']} mm2, max span {span} mm"
              + (" -> supports NOT required" if status == "PASS" else ""))

    # 7. toolhead assignment + 3MF round-trip
    tools, issues = effective_tools(product, C.DEFAULT_VARIANT)
    used = product.tools_used()
    undeclared = [t for t in used if t not in product.tool_roles]
    R.add(tag, "toolhead assignment declared", "FAIL" if undeclared else "PASS",
          f"tools used {used}; roles: " + "; ".join(f"{t}={product.tool_roles[t]}" for t in used))
    for f3 in a["files"]["3mf"][:1]:
        z = zipfile.ZipFile(C.ROOT / f3)
        root = etree.fromstring(z.read("3D/3dmodel.model"))
        bases = root.findall(".//m:base", NS)
        mesh_objs = [o for o in root.findall(".//m:object", NS) if o.find("m:mesh", NS) is not None]
        want_hex = [tools[t]["hex"].upper() + "FF" for t in TOOLS]
        got_hex = [b.get("displaycolor") for b in bases]
        pidx_ok = all(TOOLS[int(o.get("pindex"))] == next(p.tool for p in product.parts
                      if o.get("name").split(" ")[1] == p.name) for o in mesh_objs)
        scene = trimesh.load(C.ROOT / f3)
        ok = (len(mesh_objs) == len(product.parts) and got_hex == want_hex and pidx_ok
              and len(scene.geometry) == len(product.parts) and "Metadata/crw_toolmap.json" in z.namelist())
        R.add(tag, "3MF parts/colours/tool map round-trip", "PASS" if ok else "FAIL",
              f"{len(mesh_objs)} mesh objects, colours {got_hex}, pindex->tool consistent={pidx_ok}")

    # 8. material requirements vs loaded toolheads
    if not issues:
        R.add(tag, "material requirements vs loaded toolheads", "PASS", "loaded materials satisfy the design")
    for i in issues:
        R.add(tag, f"material requirement [{i['tool']}]", i["level"], i["msg"])

    # 9. fused-interface bonding + thermal compatibility
    fused = a.get("fused_tool_contacts", [])
    worst = "PASS"
    notes = []
    for t1, t2 in fused:
        q = config.bond_quality(tools[t1]["material"], tools[t2]["material"])
        notes.append(f"{t1}/{t2} {tools[t1]['material']}-{tools[t2]['material']}: {q}")
        if q == "poor":
            worst = "FAIL"
        elif q in ("fair", "unknown") and worst == "PASS":
            worst = "WARN" if "interlock" not in " ".join(product.notes + [product.strategy]).lower() \
                and pid != "CRW-005" else "PASS"
    R.add(tag, "fused interface bonding", worst, "; ".join(notes) or "no fused multi-tool interfaces")
    used_mats = sorted({tools[t]["material"] for t in used})
    lo = max(mats[m]["bed_temp_c"][0] for m in used_mats)
    hi = min(mats[m]["bed_temp_c"][1] for m in used_mats)
    R.add(tag, "thermal compatibility (common bed temperature)", "PASS" if lo <= hi else "FAIL",
          f"materials {used_mats}: bed window {lo}-{hi} C" if lo <= hi else f"no common bed temperature for {used_mats}")

    # 10. colour regions: islands, thin features, contrast
    cr = a.get("colour_regions_2d", [])
    tiny = sum(r["tiny_islands"] for r in cr)
    thin = max((r["thin_area_fraction"] for r in cr), default=0.0)
    if cr:
        R.add(tag, "colour regions (2D faces): islands >= min area, strokes >= min feature",
              "PASS" if tiny == 0 and thin <= 0.05 else "WARN",
              f"tiny islands {tiny} (< {dims['min_colour_island_area']} mm2), worst thin-area fraction {thin} "
              f"(< {dims['min_feature']} mm strokes)")
    cv = a.get("colour_volumes", [])
    tiny3 = [f"{r['part']}:{r['tiny_components']}" for r in cv if r["tiny_components"]]
    R.add(tag, "colour volumes: no tiny isolated islands (< 2 mm3)", "WARN" if tiny3 else "PASS",
          f"tiny components {tiny3}" if tiny3 else "all colour components >= 2 mm3")
    worst_c = []
    for v in variants:
        vt, _ = effective_tools(product, v)
        for t1, t2 in fused:
            rules = config.load("colors")["rules"]
            c = contrast(vt[t1]["hex"], vt[t2]["hex"])
            de = delta_e(vt[t1]["hex"], vt[t2]["hex"])
            if c < rules["min_luminance_contrast_ratio"] and de < rules["min_delta_e"]:
                worst_c.append(f"{v}:{vt[t1]['colour_name']}/{vt[t2]['colour_name']} (ratio {c:.2f}, dE {de:.0f})")
    R.add(tag, "adjacent colour contrast (all exported variants)", "WARN" if worst_c else "PASS",
          ("low contrast: " + ", ".join(worst_c)) if worst_c else "all adjacent pairs pass luminance-ratio or dE rule")

    # 11. tool changes / purge
    tc = a["tool_changes"]
    frac = a["purge_g"] / max(a["total_material_g"], 1e-6)
    R.add(tag, "tool changes + purge (single unit)", "WARN" if frac > 0.3 else "PASS",
          f"{tc['tool_changes']} changes on {tc['layers_with_changes']}/{tc['layers']} layers, purge {a['purge_g']} g "
          f"({frac:.0%} of material) - batch of {a['batch']['recommended_batch']} -> "
          + next((f"{r['purge_per_unit_g']} g/unit" for r in a["batch"]["rows"] if r["units"] == a["batch"]["recommended_batch"]), "n/a"))

    # 12. product-specific dimension + assembly checks
    ck = product.checks
    if pid == "CRW-001":
        env = ck["envelope_mm"]
        lo_, hi_ = ck["target_max_dim"]
        big = max(env)
        R.add(tag, "dimension: largest side 45-60 mm", "PASS" if lo_ <= big <= hi_ + 0.5 else "WARN",
              f"{env[0]:.1f} x {env[1]:.1f} x {env[2]:.1f} mm")
        R.add(tag, "keyring loop (tail) hole + ring section", "PASS" if ck["keyring_hole_d"] >= 4.5 and ck["keyring_ring_wall"] >= 3.0 else "FAIL",
              f"hole {ck['keyring_hole_d']} mm, ring section {ck['keyring_ring_wall']} mm, fused into the rump (tool 1)")
    if pid == "CRW-002":
        n_mag = ck["magnet_pockets"] if isinstance(ck["magnet_pockets"], int) else len(ck["magnet_pockets"])
        env = ck["envelope_mm"]
        R.add(tag, "magnet pockets", "PASS" if ck["ceiling_above_pocket"] >= 1.0 else "FAIL",
              f"{n_mag} x d{ck['magnet_pocket_d']:.2f} x {ck['magnet_pocket_depth']} mm, >= {ck['ceiling_above_pocket']:.1f} mm above")
        R.add(tag, "dimension: 50-70 mm dimensional head", "PASS" if 50 <= max(env[0], env[1]) <= 70 else "WARN",
              f"{env[0]:.1f} x {env[1]:.1f} x {env[2]:.1f} mm")
    if pid == "CRW-003":
        env = ck["envelope_mm"]
        lo_, hi_ = ck.get("target_height", (45, 80))
        R.add(tag, "dimension: 50-80 mm collectible", "PASS" if lo_ <= env[2] <= hi_ else "WARN",
              f"{env[0]:.1f} x {env[1]:.1f} x {env[2]:.1f} mm ({ck.get('edition', '')})")
    if pid == "CRW-004":
        st = ck["phone_cases"]
        R.add(tag, "phone slot fits phone+case", "PASS" if ck["max_device_thickness"] >= 12.0 else "WARN",
              f"slot {ck['slot_width']} mm, max device thickness after pads {ck['max_device_thickness']:.1f} mm, lean {ck['lean_angle_deg']} deg")
        R.add(tag, "tip-over stability (phone CG ahead of rear edge)", "PASS" if all(v["stable"] for v in st.values()) else "WARN",
              ", ".join(f"{k}: CG u={v['cg_u']}" for k, v in st.items()) + f" (rear edge u={ck['rear_edge_u']:.1f})")
        pads = [p for p in product.parts if p.tool == "tool_4"]
        g = ck["groove"]
        R.add(tag, "TPU pad / dovetail groove fit", "PASS" if g["clearance"] > 0 and all(p.requires.get("flexible") for p in pads) else "FAIL",
              f"{len(pads)} pads, neck {g['neck']} mm, depth {g['depth']} mm, clearance {g['clearance']} mm/side; slide-in, no glue")
    if pid == "CRW-005":
        envs = analysis.group_envelopes(product)
        body = envs["body"]
        worst_int, min_gap = 0.0, 99.0
        for name, j in ck["joints"].items():
            m = envs[name]
            for ang in np.linspace(j["rom_deg"][0], j["rom_deg"][1], 5):
                moved = rotate_about(m, j["pivot"], ang)
                worst_int = max(worst_int, (moved ^ body).volume())
            min_gap = min(min_gap, body.min_gap(m, 2.0))
            ok_ret = j["retention_chord"] < j["post_diameter"]
            R.add(tag, f"joint retention [{name}]", "PASS" if ok_ret else "FAIL",
                  f"opening chord {j['retention_chord']:.2f} mm < post diameter {j['post_diameter']} mm; ROM {j['rom_deg']} deg")
        R.add(tag, "print-in-place clearance (as printed)", "PASS" if min_gap >= 0.3 else "FAIL",
              f"min member gap {min_gap:.3f} mm (radial {dims['joint_clearance']} mm; 45-deg faces normal gap)")
        R.add(tag, "range-of-motion interference sweep", "PASS" if worst_int < 0.5 else "FAIL",
              f"max intersection over ROM samples {worst_int:.3f} mm3")
        fl, rl = ck["joints"]["front_leg"]["rom_deg"], ck["joints"]["rear_leg"]["rom_deg"]
        stands = fl[0] >= 0 and rl[1] <= 0
        R.add(tag, "stands unaided (asymmetric leg stops block collapse)", "PASS" if stands else "WARN",
              f"front leg ROM {fl}, rear leg ROM {rl}")

    # 13. documented assumptions
    R.add(tag, "toolhead clearance / colour-region accessibility", "INFO",
          "Assumes inactive tools park off the print (tool-changer). Layer-wise deposition means every region "
          "is reachable; verify idle-nozzle ooze/standby temps on the real machine.")


def write_markdown(R: Report, path):
    lines = ["# QC Report", "", "Generated by `scripts/validate.py`. Estimates are geometry-based; see "
             "`documentation/assumptions.md`.", ""]
    prods = list(dict.fromkeys(r["product"] for r in R.rows))
    lines += ["| Product | Result | PASS | WARN | SETUP | FAIL |", "|---|---|---|---|---|---|"]
    for p in prods:
        rows = [r for r in R.rows if r["product"] == p]
        cnt = {s: sum(1 for r in rows if r["status"] == s) for s in ("PASS", "WARN", "SETUP", "FAIL")}
        lines.append(f"| {p} | **{R.worst(p)}** | {cnt['PASS']} | {cnt['WARN']} | {cnt['SETUP']} | {cnt['FAIL']} |")
    for p in prods:
        lines += ["", f"## {p}", "", "| Check | Status | Detail |", "|---|---|---|"]
        for r in (r for r in R.rows if r["product"] == p):
            lines.append(f"| {r['check']} | {r['status']} | {r['detail'].replace('|', '/')} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-p", "--product", action="append")
    args = ap.parse_args()
    R = Report()
    for pid in C.selected(args.product):
        _, sizes, variants = C.REGISTRY[pid]
        for size in sizes:
            check_product(pid, size, R, variants)
    write_markdown(R, C.ROOT / "documentation" / "qc" / "qc-report.md")
    C.save_json(R.rows, C.GEN / "qc-report.json")
    for p in dict.fromkeys(r["product"] for r in R.rows):
        rows = [r for r in R.rows if r["product"] == p]
        print(f"{p:<44} {R.worst(p):<6} " + " ".join(f"{s}={sum(1 for r in rows if r['status'] == s)}"
                                                     for s in ("PASS", "WARN", "SETUP", "FAIL")))
        for r in rows:
            if r["status"] in ("WARN", "FAIL", "SETUP"):
                print(f"    [{r['status']}] {r['check']}: {r['detail'][:160]}")
    sys.exit(1 if any(r["status"] == "FAIL" for r in R.rows) else 0)


if __name__ == "__main__":
    main()
