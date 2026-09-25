#!/usr/bin/env python3
"""Render assembly diagrams (PNG) for DOCUMENTATION/assembly/img/.

Uses OpenSCAD's preview renderer (colours preserved) through xvfb-run.
Build-step images are made by rendering growing subsets of assembly items
(the `only` list parameter of every ASSEMBLIES/*.scad file).
"""
import json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
from png import tile, render as render_stl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "DOCUMENTATION", "assembly", "img")
ISO = "0,0,0,62,0,35,0"


def items(asm, defines):
    with tempfile.NamedTemporaryFile(suffix=".echo", delete=False) as t:
        f = t.name
    args = ["openscad", "-o", f] + sum([["-D", d] for d in defines], []) + ["-D", 'only="__none__"', os.path.join(ROOT, "ASSEMBLIES", asm + ".scad")]
    subprocess.run(args, capture_output=True, check=True)
    out = []
    for line in open(f):
        if line.startswith('ECHO: "ITEM"'):
            out.append(json.loads("[" + line[5:].strip() + "]")[1])
    os.unlink(f)
    return list(dict.fromkeys(out))


def shot(asm, defines, png, only=None, camera=ISO, size=(900, 700)):
    args = ["xvfb-run", "-a", "openscad", "-o", png, "--imgsize=%d,%d" % size, "--viewall", "--autocenter",
            "--colorscheme=Tomorrow", "--camera=" + camera]
    for d in defines:
        args += ["-D", d]
    if only is not None:
        args += ["-D", "only=[%s]" % ",".join('"%s"' % n for n in only)]
    args.append(os.path.join(ROOT, "ASSEMBLIES", asm + ".scad"))
    subprocess.run(args, capture_output=True, check=True)
    return png


def steps(asm, defines, groups, out, labels, camera=ISO, cols=3):
    allv = items(asm, defines)
    tmp = tempfile.mkdtemp()
    jobs, shown = [], []
    for k, g in enumerate(groups):
        shown += [n for n in allv if any(n.startswith(p) for p in g)]
        jobs.append((os.path.join(tmp, "%d.png" % k), list(shown)))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda j: shot(asm, defines, j[0], j[1], camera, (600, 470)), jobs))
    tile([j[0] for j in jobs], labels, out, cols)


def main():
    os.makedirs(IMG, exist_ok=True)
    P = lambda n: os.path.join(IMG, n)
    tmp = tempfile.mkdtemp()
    # --- single views
    solo = [
        ("solar_vehicle", ['version="B"'], P("solar_vehicle_B.png"), None, ISO),
        ("dynamo_generator", ["ratio=8", "guard=false", "crank=30"], P("dynamo_8.png"), None, "0,0,0,62,0,215,0"),
        ("dynamo_generator", ["ratio=8", "crank=30"], P("dynamo_guard.png"), None, "0,0,0,62,0,215,0"),
        ("wind_turbine", ["blades=3", "pitch=20"], P("wind_turbine.png"), None, "0,0,0,75,0,200,0"),
        ("pulley_lab", [], P("pulley_lab.png"), None, "0,0,0,60,0,305,0"),
    ]
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda s: shot(s[0], s[1], s[2], s[3], s[4]), solo))
    # --- overview
    ov = [("solar_vehicle", ['version="B"'], ISO), ("dynamo_generator", ["ratio=8", "guard=false", "crank=30"], "0,0,0,62,0,215,0"),
          ("wind_turbine", ["pitch=20"], "0,0,0,75,0,200,0"), ("pulley_lab", [], "0,0,0,60,0,305,0"),
          ("linkage_fourbar", ["crank=60"], "0,0,0,40,0,20,0")]
    ovp = [os.path.join(tmp, "ov%d.png" % i) for i in range(len(ov))]
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda i: shot(ov[i][0], ov[i][1], ovp[i], None, ov[i][2], (600, 470)), range(len(ov))))
    tile(ovp, ["Solar vehicle", "Hand-crank dynamo 8:1", "Wind turbine", "Pulley lab 3:1", "Four-bar linkage"], P("overview.png"), 3)
    # --- solar steps + versions
    steps("solar_vehicle", ['version="B"'],
          [["chassis", "rear_axle_mount", "front_axle_mount"], ["motor"], ["pinion"], ["rear_axle", "front_axle", "axle_gear"],
           ["wheel"], ["pillar", "panel_frame", "solar_panel"]],
          P("solar_vehicle_steps.png"),
          ["1  axle mounts", "2  motor mount + motor", "3  pinion on motor", "4  axles + 20T gear", "5  wheels", "6  pillars + panel"])
    vp = []
    for v in "ABCD":
        f = os.path.join(tmp, "v%s.png" % v)
        allv = items("solar_vehicle", ['version="%s"' % v])
        keep = [n for n in allv if not n.startswith(("pillar", "panel", "solar_panel", "front", "wheel_L_145", "wheel_R_145"))]
        vp.append(f)
        shot("solar_vehicle", ['version="%s"' % v], f, keep, "0,0,0,35,0,340,0", (600, 470))
    tile(vp, ["A  1:1 (10T/10T)", "B  2:1 reduction (10T/20T)", "C  1:2 overdrive (20T/10T)", "D  two motors (10T+10T/20T)"],
         P("solar_vehicle_versions.png"), 2)
    # --- dynamo steps + ratios
    steps("dynamo_generator", ["ratio=8", "guard=false"],
          [["base_plate", "plate_A", "plate_B", "pillar"], ["bracket"], ["shaft_S", "S0_", "S1_", "S2_"],
           ["generator", "coupler", "shaft_G", "G_", "gen_nut"], ["crank"], ["guard"]],
          P("dynamo_steps.png"),
          ["1  frame: plates + pillars", "2  corner connectors", "3  shafts + gear train (8:1)", "4  generator + coupler + pinion",
           "5  crank + knob", "6  guard (see below)"], camera="0,0,0,62,0,215,0")
    rp = []
    for r in (1, 2, 4, 8):
        f = os.path.join(tmp, "r%d.png" % r)
        allv = items("dynamo_generator", ["ratio=%d" % r, "guard=false"])
        keep = [n for n in allv if n not in ("plate_A", "guard", "bracket_10", "bracket_90", "crank", "crank_knob", "base_plate")]
        shot("dynamo_generator", ["ratio=%d" % r, "guard=false"], f, keep, "0,0,0,80,0,5,0", (600, 520))
        rp.append(f)
    tile(rp, ["1:1  10T -> 10T", "2:1  20T -> 10T", "4:1  40T -> 10T (3-4-5 diagonal)", "8:1  (20T -> 10T) x 3"],
         P("dynamo_ratios.png"), 2)
    # --- linkage positions
    lp = []
    for c in (0, 90, 180, 270):
        f = os.path.join(tmp, "l%d.png" % c)
        shot("linkage_fourbar", ["crank=%d" % c], f, None, "0,0,0,0,0,0,0", (500, 420))
        lp.append(f)
    tile(lp, ["crank 0°", "crank 90°", "crank 180°", "crank 270°"], P("linkage.png"), 2)
    # --- tolerance test
    render_stl(os.path.join(ROOT, "STL", "common", "STEM_TOLERANCE_TEST.stl"), P("tolerance_test.png"), (900, 650), "0,0,0,50,0,20,0")
    print("images written to", IMG)


if __name__ == "__main__":
    main()
