#!/usr/bin/env python3
"""Manufacturing cost model + batch economics (brief sections 12-15).

Reads products/generated/<stem>.analysis.json (run generate.py first) and
config/costs.json. Writes documentation/costs/cost-report.md and
products/generated/<stem>.cost.json.

ALL outputs are manufacturing ESTIMATES. Suggested retail ranges come from the
configured price bands and a cost floor; they do NOT predict or guarantee demand.

  python scripts/cost.py                 # cost report
  python scripts/cost.py --calibrate     # compare research/print-log.csv to estimates
"""
from __future__ import annotations

import argparse
import csv
import math

import _common as C
from cad.core import config
from cad.core.model import TOOLS


def unit_cost(a: dict, product_meta: dict, scenario: str, batch_units: int) -> dict:
    cc = config.costs()
    sc = cc["scenarios"][scenario]
    price = cc["filament_price_per_kg"]
    mats = config.materials()
    row = next(r for r in a["batch"]["rows"] if r["units"] == batch_units)

    def price_g(material):
        return price[mats[material]["price_key"]] / 1000.0 * sc["filament_price_multiplier"]

    material = sum(a["per_tool"][t]["grams"] * price_g(a["per_tool"][t]["material"]) for t in TOOLS)
    # purge is split across the tools switched INTO (the tool that primes)
    into = a["tool_changes"]["switches_into_tool"]
    n_sw = max(sum(into.values()), 1)
    purge_g_unit = row["purge_per_unit_g"]
    purge = sum(purge_g_unit * into[t] / n_sw * price_g(a["per_tool"][t]["material"]) for t in TOOLS)
    hours_unit = row["time_per_unit_min"] / 60
    el = cc["electricity"]
    electricity = hours_unit * el["printer_avg_power_kw"] * el["price_per_kwh"]
    hardware = sum(cc["hardware"].get(h, 0.0) for h in product_meta["hardware"])
    packaging = cc["packaging"][product_meta["packaging"]] * sc["packaging_multiplier"]
    lab = cc["labour"]
    labour_min = (lab["plate_handling_min_per_batch"] / batch_units + product_meta["post_process_minutes"]
                  + product_meta["assembly_time_minutes"])
    labour = labour_min / 60 * lab["rate_per_hour"] * sc["labour_rate_multiplier"]
    fail = sc["failed_print_allowance"]
    failure = (material + purge + electricity) * fail
    total = material + purge + electricity + hardware + packaging + labour + failure
    band = cc["price_bands"][product_meta["tier"]]
    floor = total * sc["retail_markup_on_cost"]
    lo, hi = max(band[0], math.ceil(floor)), max(band[1], math.ceil(floor))
    mid = (lo + hi) / 2
    gst = 1 / 11  # AU GST included in shelf price
    ex_gst = mid * (1 - gst)
    return {
        "scenario": scenario, "batch_units": batch_units,
        "material": round(material, 3), "purge": round(purge, 3), "electricity": round(electricity, 3),
        "hardware": round(hardware, 3), "packaging": round(packaging, 3), "labour": round(labour, 3),
        "labour_minutes": round(labour_min, 2), "failure_allowance": round(failure, 3),
        "total_cost": round(total, 2),
        "suggested_retail_range": [lo, hi], "cost_floor_retail": round(floor, 2),
        "gross_margin_at_mid_ex_gst": round((ex_gst - total) / ex_gst, 3) if ex_gst else None,
    }


def product_meta(pid, size):
    p = C.build(pid, size)
    return p, {"hardware": p.hardware, "packaging": p.packaging, "tier": p.tier,
               "post_process_minutes": p.post_process_minutes, "assembly_time_minutes": p.assembly_time_minutes}


def run_costs():
    results = {}
    for pid, (_, sizes, _) in C.REGISTRY.items():
        for size in sizes:
            p, meta = product_meta(pid, size)
            a = C.load_json(C.analysis_path(p.file_stem))
            rec = a["batch"]["recommended_batch"]
            res = {"stem": p.file_stem, "id": pid, "name": p.name, "size": size, "tier": p.tier,
                   "recommended_batch": rec,
                   "single_unit": {s: unit_cost(a, meta, s, 1) for s in config.costs()["scenarios"]},
                   "batch": {s: unit_cost(a, meta, s, rec) for s in config.costs()["scenarios"]}}
            C.save_json(res, C.GEN / f"{p.file_stem}.cost.json")
            results[p.file_stem] = (res, a)
    write_report(results)
    return results


def write_report(results):
    L = ["# Cost & Batch Report", "",
         "> **Manufacturing estimates only.** Mass/time come from a slicer-free geometry model "
         "(`cad/core/analysis.py`) with the assumptions in `config/*.json`. Retail ranges are the configured "
         "price bands raised to a cost floor; they are **not** a prediction of market demand.", "",
         "## Toolhead utilisation (per unit, STANDARD sizes)", "",
         "| Product | T1 | T2 | T3 | T4 | Purge (1 unit) | Total | Tool changes | Est. time |",
         "|---|---|---|---|---|---|---|---|---|"]
    for stem, (res, a) in results.items():
        if res["size"] != "STANDARD":
            continue
        cells = [f"{a['per_tool'][t]['grams']:.1f} g {a['per_tool'][t]['material']}" if a['per_tool'][t]['grams'] > 0 else "-"
                 for t in TOOLS]
        L.append(f"| {stem} | " + " | ".join(cells) + f" | {a['purge_g']:.2f} g | {a['total_material_g']:.1f} g | "
                 f"{a['tool_changes']['tool_changes']} | {a['print_time_min']:.0f} min |")
    L += ["", "## Batch plans", ""]
    for stem, (res, a) in results.items():
        b = a["batch"]
        L += [f"### {stem}", "", f"Max units on a {b['bed_mm'][0]}x{b['bed_mm'][1]} mm bed: **{b['max_units_on_bed']}** "
              f"(spacing {b['spacing_mm']} mm). Recommended batch: **{b['recommended_batch']}**.", "",
              "| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |",
              "|---|---|---|---|---|---|---|---|"]
        for r in b["rows"]:
            L.append(f"| {r['units']} | {'yes' if r['fits_bed'] else 'no'} | {r['batch_time_h']} h | {r['time_per_unit_min']} min | "
                     f"{r['material_per_batch_g']} g | {r['purge_per_batch_g']} g | {r['purge_per_unit_g']} g | {r['waste_fraction']:.1%} |")
        L.append("")
    L += ["## Unit economics (AUD)", "",
          "Batch = recommended batch size. Margin = gross margin at the middle of the suggested range, ex-GST.", "",
          "| Product | Scenario | Batch | Material | Purge | Power | HW | Pack | Labour | Fail | **Cost** | Suggested retail | Margin |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for stem, (res, a) in results.items():
        for s, u in res["batch"].items():
            L.append(f"| {stem} | {s} | {u['batch_units']} | {u['material']:.2f} | {u['purge']:.2f} | {u['electricity']:.2f} | "
                     f"{u['hardware']:.2f} | {u['packaging']:.2f} | {u['labour']:.2f} | {u['failure_allowance']:.2f} | "
                     f"**{u['total_cost']:.2f}** | ${u['suggested_retail_range'][0]}-{u['suggested_retail_range'][1]} | "
                     f"{u['gross_margin_at_mid_ex_gst']:.0%} |")
    L += ["", "## Single-unit vs batch (NORMAL scenario)", "",
          "| Product | Cost @1 | Cost @batch | Purge/unit @1 | Purge/unit @batch |", "|---|---|---|---|---|"]
    for stem, (res, a) in results.items():
        r1 = next(r for r in a["batch"]["rows"] if r["units"] == 1)
        rb = next(r for r in a["batch"]["rows"] if r["units"] == res["recommended_batch"])
        L.append(f"| {stem} | {res['single_unit']['NORMAL']['total_cost']:.2f} | {res['batch']['NORMAL']['total_cost']:.2f} | "
                 f"{r1['purge_per_unit_g']} g | {rb['purge_per_unit_g']} g |")
    path = C.ROOT / "documentation" / "costs" / "cost-report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def calibrate():
    """Compare real prints (research/print-log.csv) with estimates -> suggested calibration factors."""
    path = C.ROOT / "research" / "print-log.csv"
    rows = [r for r in csv.DictReader(open(path, encoding="utf-8")) if r.get("actual_filament_g")]
    if not rows:
        print("No completed rows in research/print-log.csv yet - print the prototypes first.")
        return
    mass_r, time_r = [], []
    for r in rows:
        a = C.load_json(C.analysis_path(r["stem"]))
        units = float(r.get("units") or 1)
        est_mass = a["total_part_g"] * units
        est_time = next(x for x in a["batch"]["rows"] if x["units"] == int(units))["batch_time_h"] * 60 \
            if any(x["units"] == int(units) for x in a["batch"]["rows"]) else a["print_time_min"] * units
        mass_r.append(float(r["actual_filament_g"]) / est_mass)
        if r.get("actual_print_time_min"):
            time_r.append(float(r["actual_print_time_min"]) / est_time)
        print(f"{r['stem']}: mass x{mass_r[-1]:.2f}" + (f", time x{time_r[-1]:.2f}" if time_r else ""))
    est = config.costs()["estimation"]
    if mass_r:
        print(f"suggested mass_calibration = {est['mass_calibration'] * sum(mass_r) / len(mass_r):.3f}")
    if time_r:
        print(f"suggested time_calibration = {est['time_calibration'] * sum(time_r) / len(time_r):.3f}")
    print("Edit config/costs.json -> estimation to apply, then re-run generate.py + cost.py.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args()
    if args.calibrate:
        calibrate()
        return
    results = run_costs()
    for stem, (res, a) in results.items():
        n = res["batch"]["NORMAL"]
        print(f"{stem:<44} batch {res['recommended_batch']:>2}  cost ${n['total_cost']:>6.2f}  "
              f"retail ${n['suggested_retail_range'][0]}-{n['suggested_retail_range'][1]}  margin {n['gross_margin_at_mid_ex_gst']:.0%}")


if __name__ == "__main__":
    main()
