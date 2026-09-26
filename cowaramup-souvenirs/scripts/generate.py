#!/usr/bin/env python3
"""Generate geometry + production files for the prototype products.

For every product/size:
  stl/<stage>/<stem>.stl                      single-colour geometry (all parts merged)
  stl/<stage>/<stem>/<stem>__<part>.stl       one STL per toolhead region (geometry interchange)
  stl/<stage>/<stem>/<stem>.scad              OpenSCAD colour assembly of the per-part STLs
  3mf/<stage>/<stem>.3mf                      PRODUCTION file: multi-part, colours, tool map
  3mf/<stage>/variants/<stem>--<variant>.3mf  colour variants (same geometry)
  products/generated/<stem>.analysis.json     material / tool-change / QC analysis

Usage:
  python scripts/generate.py                 # all products, all registered sizes
  python scripts/generate.py -p CRW-001 --variant aussie
  python scripts/generate.py --fast          # skip deep QC analysis (wall thickness etc.)
"""
from __future__ import annotations

import argparse
import time

import _common as C
from cad.core import analysis, config, export, geom
from cad.core.tools import effective_tools


def layer_strings(M):
    return ["".join(str(i + 1) if row[i] else "." for i in range(4)) for row in M]


def generate(pid: str, size: str, variants: list[str], deep: bool = True) -> dict:
    t0 = time.time()
    product = C.build(pid, size)
    stem = product.file_stem
    printer = config.printer()
    offset = export.plate_offset(product, (printer["bed_x_mm"], printer["bed_y_mm"]))
    stl_dir = C.ROOT / "stl" / C.STAGE
    part_dir = stl_dir / stem
    files = {"stl": [], "stl_parts": [], "3mf": [], "scad": []}

    merged = export.clean_mesh(product.envelope if product.envelope is not None
                               else geom.union(p.solid for p in product.parts), collapse=1e-3)
    export.write_stl(merged, stl_dir / f"{stem}.stl", offset)
    files["stl"].append(C.rel(stl_dir / f"{stem}.stl"))
    part_files = {}
    for p in product.parts:
        path = part_dir / f"{stem}__{p.name}.stl"
        export.write_stl(p.solid, path, offset)
        part_files[p.name] = path.name
        files["stl_parts"].append(C.rel(path))

    tools, issues = effective_tools(product, C.DEFAULT_VARIANT)
    scad = part_dir / f"{stem}.scad"
    export.write_scad(product, scad, part_files, tools)
    files["scad"].append(C.rel(scad))

    for v in variants:
        vt, _ = effective_tools(product, v)
        if v == C.DEFAULT_VARIANT:
            path = C.ROOT / "3mf" / C.STAGE / f"{stem}.3mf"
        else:
            path = C.ROOT / "3mf" / C.STAGE / "variants" / f"{stem}--{v}.3mf"
        export.write_3mf(product, path, vt, offset, variant=v, bed_xy=(printer["bed_x_mm"], printer["bed_y_mm"]))
        files["3mf"].append(C.rel(path))

    a = analysis.analyse(product, deep=deep, tools=tools)
    a["layer_tools"] = layer_strings(a.pop("layer_presence"))
    a["batch"] = analysis.batch_plan(product, a)
    a["files"] = files
    a["setup_issues"] = issues
    a["effective_tools"] = tools
    a["plate_offset"] = offset.tolist()
    a["name"] = product.name
    a["generated_in_s"] = round(time.time() - t0, 1)
    C.save_json(a, C.analysis_path(stem))
    return a


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--product", action="append", help="product id (repeatable); default all")
    ap.add_argument("--size", action="append", help="size preset(s); default = registry")
    ap.add_argument("--variant", action="append", help="colour variant(s); default = registry")
    ap.add_argument("--fast", action="store_true", help="skip deep QC analysis")
    args = ap.parse_args()
    for pid in C.selected(args.product):
        _, sizes, variants = C.REGISTRY[pid]
        for size in args.size or sizes:
            a = generate(pid, size, args.variant or variants, deep=not args.fast)
            tc = a["tool_changes"]
            print(f"{a['stem']:<44} {a['total_part_g']:>7.1f} g  purge {a['purge_g']:>5.2f} g  "
                  f"{tc['tool_changes']:>4} tool changes  {a['print_time_min']:>6.1f} min  "
                  f"({a['generated_in_s']} s)")
            for i in a["setup_issues"]:
                print(f"    [{i['level']}] {i['msg']}")


if __name__ == "__main__":
    main()
