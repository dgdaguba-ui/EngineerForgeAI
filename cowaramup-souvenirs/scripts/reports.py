#!/usr/bin/env python3
"""Compile the product database, product sheets, print-settings sheets and the
internal manufacturing opportunity score.

Run after generate.py, validate.py and cost.py. Writes:
  products/products.json                       product DB (brief section 32) + concept catalogue
  documentation/product-sheets/<stem>.md       one sheet per prototype
  documentation/print-settings/<stem>.md       slicer set-up sheet per prototype
  documentation/opportunity-score.md           INTERNAL development ranking (not a sales forecast)
"""
from __future__ import annotations

import _common as C
from cad.core import config
from cad.core.model import TOOLS

# Design-team judgement (1 = poor, 5 = excellent; packaging_ease: 5 = trivial).
# Subjective, to be revised after physical prototypes. NOT market research.
RATINGS = {
    "CRW-001": {"durability": 5, "visual_appeal": 4, "differentiation": 4, "packaging_ease": 5},
    "CRW-002": {"durability": 5, "visual_appeal": 5, "differentiation": 4, "packaging_ease": 5},
    "CRW-003": {"durability": 4, "visual_appeal": 4, "differentiation": 5, "packaging_ease": 3},
    "CRW-004": {"durability": 5, "visual_appeal": 3, "differentiation": 4, "packaging_ease": 3},
    "CRW-005": {"durability": 3, "visual_appeal": 4, "differentiation": 5, "packaging_ease": 3},
}
WEIGHTS = {"print_time": 0.15, "material_cost": 0.10, "purge": 0.15, "assembly": 0.10,
           "durability": 0.15, "visual_appeal": 0.15, "differentiation": 0.15, "packaging_ease": 0.05}


def scale_inverse(x, best, worst):
    """Map a 'lower is better' metric to 0-5."""
    if worst == best:
        return 5.0
    return max(0.0, min(5.0, 5.0 * (worst - x) / (worst - best)))


def record(product, a, cost, qc_rows):
    stem = product.file_stem
    tools = a["effective_tools"]
    n = cost["batch"]["NORMAL"]
    worst = "PASS"
    order = ["PASS", "INFO", "SETUP", "WARN", "FAIL"]
    for r in qc_rows:
        if r["product"] == stem and order.index(r["status"]) > order.index(worst):
            worst = r["status"]
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "description": product.description,
        "size": product.size,
        "dimensions_mm": dict(zip(("x", "y", "z"), a["plate_bbox_mm"])),
        "toolheads": {t: f"{tools[t]['material']} {tools[t]['colour_name']} - {product.tool_roles.get(t, 'unused')}"
                      for t in TOOLS},
        "materials": sorted({tools[t]["material"] for t in product.tools_used()}),
        "colours": [tools[t]["colour_name"] for t in product.tools_used()],
        "parts": [{"name": p.name, "tool": p.tool, "feature": p.feature, "object": p.object_group} for p in product.parts],
        "estimated_print_time_minutes": a["print_time_min"],
        "estimated_filament_g": {t: a["per_tool"][t]["grams"] for t in TOOLS},
        "estimated_purge_g": a["purge_g"],
        "tool_changes": a["tool_changes"]["tool_changes"],
        "assembly_time_minutes": product.assembly_time_minutes,
        "estimated_cost_aud": n["total_cost"],
        "recommended_retail_range_aud": f"{n['suggested_retail_range'][0]}-{n['suggested_retail_range'][1]}",
        "supports_required": any(v["steep_overhang_area_mm2"] > 5 for v in a["overhangs"].values()),
        "status": f"prototype - generated, QC {worst}, awaiting physical print test",
        "stl_files": a["files"]["stl"] + a["files"]["stl_parts"],
        "three_mf_files": a["files"]["3mf"],
        "scad_files": a["files"]["scad"],
        "step_files": [],
        "recommended_batch": a["batch"]["recommended_batch"],
        "manufacturing_strategy": product.strategy,
        "print_orientation": product.print_orientation,
        "hardware": product.hardware,
        "setup_issues": [i["msg"] for i in a["setup_issues"]],
    }


def opportunity(rows):
    times = [r["time_per_unit"] for r in rows]
    mats = [r["material_cost"] for r in rows]
    purges = [r["purge_frac"] for r in rows]
    asm = [r["assembly"] for r in rows]
    for r in rows:
        s = {"print_time": scale_inverse(r["time_per_unit"], min(times), max(times)),
             "material_cost": scale_inverse(r["material_cost"], min(mats), max(mats)),
             "purge": scale_inverse(r["purge_frac"], min(purges), max(purges)),
             "assembly": scale_inverse(r["assembly"], min(asm), max(asm)),
             **RATINGS[r["id"]]}
        r["subscores"] = {k: round(v, 1) for k, v in s.items()}
        r["score"] = round(sum(WEIGHTS[k] * s[k] for k in WEIGHTS) * 20, 1)  # 0-100
    return sorted(rows, key=lambda r: -r["score"])


def product_sheet(product, a, cost, rec):
    stem = product.file_stem
    tools = a["effective_tools"]
    L = [f"# {product.id} - {product.name}", "", f"*{product.category} - {product.size} - tier {product.tier}*", "",
         product.description, "", f"![four-colour](../../previews/{stem}/2-four-colour.png)", "",
         "## Manufacturing", "",
         f"- **Strategy:** {product.strategy}", f"- **Print orientation:** {product.print_orientation}",
         f"- **Plate footprint:** {a['plate_bbox_mm'][0]} x {a['plate_bbox_mm'][1]} x {a['plate_bbox_mm'][2]} mm",
         f"- **Supports:** {'required' if rec['supports_required'] else 'none (all overhangs <= 45 deg, bridges short)'}",
         f"- **Hardware:** {', '.join(product.hardware) or 'none'}",
         f"- **Recommended batch:** {a['batch']['recommended_batch']} per plate", "",
         "## Toolhead utilisation (per unit, estimate)", "", "| Tool | Material / colour | Used for | Grams |", "|---|---|---|---|"]
    for t in TOOLS:
        L.append(f"| {t} | {tools[t]['material']} {tools[t]['colour_name']} | {product.tool_roles.get(t, '-')} | "
                 f"{a['per_tool'][t]['grams']:.2f} |")
    tc = a["tool_changes"]
    L += ["", f"- Purge (single unit): **{a['purge_g']} g** from **{tc['tool_changes']}** tool changes on "
              f"{tc['layers_with_changes']}/{tc['layers']} layers",
          f"- Total material (single unit incl. purge): **{a['total_material_g']} g**",
          f"- Estimated print time (single unit): **{a['print_time_min']} min** "
          f"(extrusion {a['time_breakdown_min']['extrusion']}, tool changes {a['time_breakdown_min']['tool_changes']}, "
          f"layers {a['time_breakdown_min']['layer_overhead']}, heat-up {a['time_breakdown_min']['heatup']})", "",
          f"![tool layers](../../previews/{stem}/tool-layers.png)", "",
          "## Economics (NORMAL scenario, recommended batch) - estimate only", "",
          f"- Unit cost **${cost['batch']['NORMAL']['total_cost']:.2f}**; suggested retail "
          f"**${rec['recommended_retail_range_aud']}** (price band / cost floor - not a demand forecast)",
          "", "## Self-critique", ""]
    for k, v in product.self_critique.items():
        L.append(f"- **{k.replace('_', ' ')}:** {v}")
    L += ["", "## Notes / known risks", ""] + [f"- {n}" for n in product.notes]
    if a["setup_issues"]:
        L += ["", "## Toolhead set-up issues", ""] + [f"- [{i['level']}] {i['msg']}" for i in a["setup_issues"]]
    L += ["", "## Files", ""] + [f"- `{f}`" for f in a["files"]["3mf"] + a["files"]["stl"] + a["files"]["scad"]]
    L += ["- STEP: not generated (see documentation/assumptions.md)", "",
          f"Previews: `previews/{stem}/` (single-colour, four-colour, multi-material, dimensions, print orientation, variants)"]
    return "\n".join(L) + "\n"


def print_settings(product, a):
    tools = a["effective_tools"]
    mats = config.materials()
    pr = config.printer()
    L = [f"# Print settings - {product.id} {product.name}", "",
         "Slicer-agnostic set-up sheet. Values are starting points from generic material data - "
         "tune on the real machine and record results in `research/print-log.csv`.", "",
         "## Load", "", f"- Production file: `{a['files']['3mf'][0]}` (parts named `T1..T4 ...`, colours embedded)",
         "- If the slicer asks 'multi-part object?' answer **yes** (keep parts together).",
         "- Assign extruders by part-name prefix: T1 -> tool 1, T2 -> tool 2, T3 -> tool 3, T4 -> tool 4.", "",
         "## Tools", "", "| Tool | Material | Colour | Nozzle C | Bed C | Role |", "|---|---|---|---|---|---|"]
    for t in product.tools_used():
        m = mats[tools[t]["material"]]
        L.append(f"| {t} | {tools[t]['material']} | {tools[t]['colour_name']} | {m['nozzle_temp_c'][0]}-{m['nozzle_temp_c'][1]} | "
                 f"{m['bed_temp_c'][0]}-{m['bed_temp_c'][1]} | {product.tool_roles.get(t, '')} |")
    used = sorted({tools[t]["material"] for t in product.tools_used()})
    lo = max(mats[m]["bed_temp_c"][0] for m in used)
    hi = min(mats[m]["bed_temp_c"][1] for m in used)
    L += ["", "## Process", "",
          f"- Layer height {pr['layer_height_mm']} mm (inlay depth 0.6 mm = exactly 3 layers - keep 0.2 mm or 0.15/0.3 "
          "multiples so colour boundaries fall on layer boundaries)",
          f"- Bed temperature: common window {lo}-{hi} C for {', '.join(used)}",
          "- Walls 2 perimeters (0.9 mm), top/bottom 4 layers, infill 15 % (estimates assume this)",
          f"- Orientation: {product.print_orientation}",
          "- Supports: none", "- Prime/wipe: use the machine's standard tool-change prime; prime tower off unless ooze is seen "
          "(if enabled, set `prime_tower: true` in config/toolheads.json to cost it)",
          "- Standby temperature on idle tools: ~40 C below print temp to limit ooze (verify)"]
    if any(mats[tools[t]["material"]]["flexible"] for t in product.tools_used()):
        L.append("- TPU: print slowly (<= 25 mm/s), retraction minimal, no fan limitation needed for pads")
    L += ["", "## Record after printing", "", "Add a row to `research/print-log.csv`: actual time, filament, purge, tool changes, "
          "failures, weak points, assembly time, surface and colour quality."]
    return "\n".join(L) + "\n"


def main():
    qc = C.load_json(C.GEN / "qc-report.json") if (C.GEN / "qc-report.json").exists() else []
    records, opp = [], []
    for pid, (_, sizes, _) in C.REGISTRY.items():
        for size in sizes:
            product = C.build(pid, size)
            stem = product.file_stem
            a = C.load_json(C.analysis_path(stem))
            cost = C.load_json(C.GEN / f"{stem}.cost.json")
            rec = record(product, a, cost, qc)
            records.append(rec)
            if size == "STANDARD":
                (C.ROOT / "documentation" / "product-sheets").mkdir(parents=True, exist_ok=True)
                (C.ROOT / "documentation" / "product-sheets" / f"{stem}.md").write_text(product_sheet(product, a, cost, rec))
                (C.ROOT / "documentation" / "print-settings").mkdir(parents=True, exist_ok=True)
                (C.ROOT / "documentation" / "print-settings" / f"{stem}.md").write_text(print_settings(product, a))
                row = next(r for r in a["batch"]["rows"] if r["units"] == a["batch"]["recommended_batch"])
                opp.append({"id": pid, "stem": stem, "time_per_unit": row["time_per_unit_min"],
                            "material_cost": cost["batch"]["NORMAL"]["material"],
                            "purge_frac": row["purge_per_unit_g"] / max(a["total_part_g"], 1e-6),
                            "assembly": product.assembly_time_minutes + product.post_process_minutes})
    concepts = C.load_json(C.ROOT / "products" / "concepts.json")["concepts"]
    C.save_json({"_about": "Product database. 'products' = implemented prototypes (generated); 'concepts' = "
                           "catalogue from products/concepts.json. All numbers are estimates.",
                 "products": records, "concepts": concepts}, C.ROOT / "products" / "products.json")
    ranked = opportunity(opp)
    L = ["# Manufacturing opportunity score (INTERNAL)", "",
         "> For internal product-development prioritisation ONLY. It ranks how easy/robust/distinctive a design is "
         "to manufacture with this printer. It does **not** predict sales or demand.", "",
         "Score 0-100 = weighted sub-scores (0-5): " + ", ".join(f"{k} {int(v * 100)}%" for k, v in WEIGHTS.items()) + ".",
         "Measured sub-scores (print time, material cost, purge fraction, assembly) are relative across the prototype set "
         "at recommended batch size; durability / visual appeal / differentiation / packaging ease are design-team "
         "ratings in `scripts/reports.py` to be revised after physical tests.", "",
         "| Rank | Product | Score | Time/unit | Purge/unit vs part | " + " | ".join(WEIGHTS) + " |",
         "|---|---|---|---|---|" + "---|" * len(WEIGHTS)]
    for i, r in enumerate(ranked, 1):
        L.append(f"| {i} | {r['stem']} | **{r['score']}** | {r['time_per_unit']} min | {r['purge_frac']:.1%} | "
                 + " | ".join(str(r["subscores"][k]) for k in WEIGHTS) + " |")
    (C.ROOT / "documentation" / "opportunity-score.md").write_text("\n".join(L) + "\n")
    for r in ranked:
        print(f"{r['stem']:<40} score {r['score']}")
    print(f"products.json: {len(records)} prototype records, {len(concepts)} concepts")


if __name__ == "__main__":
    main()
