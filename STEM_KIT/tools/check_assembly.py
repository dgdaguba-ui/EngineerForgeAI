#!/usr/bin/env python3
"""Virtual assembly verification for STEM_KIT.

For an assembly .scad file (see ASSEMBLIES/), this tool
  1. asks OpenSCAD for the item list (echo "ITEM"), gear meshes
     (echo "MESH") and allowed press-fit interferences (echo "ALLOW");
  2. renders every item to its own STL, in world coordinates;
  3. checks every pair of items for solid interference (exact mesh
     booleans with manifold3d) — touching faces are fine, overlap is not;
  4. for every gear mesh: slices both gears at the gear mid-plane and
     rotates them through one full tooth pitch at the correct ratio,
     checking (a) no tooth overlap, (b) the flank gap stays small
     (the gears really engage), (c) the pair locks if backlash is removed.

usage: check_assembly.py ASSEMBLIES/x.scad [-D name=value ...] [--label L]
Exit status 1 if anything fails. Writes a JSON report to build/qc/.
"""
import hashlib, json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import trimesh
import manifold3d as m3d
from shapely import affinity
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "build", "cache")
VOL_TOL = 0.05          # mm^3: numerical noise from coplanar contact
os.makedirs(CACHE, exist_ok=True)


def scad(args, out):
    r = subprocess.run(["openscad", "-o", out] + args, capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stderr:
        raise RuntimeError(r.stderr[-2000:])
    return r.stderr


def parse_echo(text):
    items, meshes, allow = [], [], {}
    for line in text.splitlines():
        if not line.startswith("ECHO:"):
            continue
        body = line[5:].strip()
        try:
            vals = json.loads("[" + body.replace("undef", "null") + "]")
        except json.JSONDecodeError:
            continue
        if vals[0] == "ITEM":
            items.append(vals[1])
        elif vals[0] == "MESH":
            meshes.append(vals[1:])
        elif vals[0] == "ALLOW":
            allow[tuple(sorted(vals[1:3]))] = vals[3]
    return list(dict.fromkeys(items)), meshes, allow


def render_item(path, defines, name):
    """Render one item; cached by the CSG tree (so static items are reused)."""
    args = sum([["-D", d] for d in defines], []) + ["-D", 'only="%s"' % name, path]
    with tempfile.NamedTemporaryFile(suffix=".csg", delete=False) as t:
        csg = t.name
    scad(args, csg)
    txt = open(csg).read()
    os.unlink(csg)
    # drop the echo/colour noise, keep geometry + transforms
    txt = re.sub(r"color\([^)]*\)", "", txt)
    txt = re.sub(r"(?m)^\s*group\(\);\s*$", "", txt)          # empty groups from other items
    txt = re.sub(r"\n\s*\n", "\n", txt)                         # and the blank lines they leave
    key = hashlib.sha1(txt.encode()).hexdigest()
    stl = os.path.join(CACHE, key + ".stl")
    if not os.path.exists(stl):
        scad(args, stl)
    return stl


def to_manifold(mesh):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                                 tri_verts=np.asarray(mesh.faces, np.uint32)))


def section_xz(mesh, y):
    s = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None:
        return None
    # to_2D with an explicit frame: world X -> u, world Z -> v
    T = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, y], [0, 0, 0, 1]], float)
    p2, M = s.to_2D(to_2D=T)
    return unary_union(list(p2.polygons_full))


def check_mesh(m1, m2, z1, z2, c1, c2, y, backlash_expect):
    A, B = section_xz(m1, y), section_xz(m2, y)
    if A is None or B is None:
        return {"ok": False, "why": "no section at y=%.2f" % y}
    cd = float(np.hypot(c2[0] - c1[0], c2[1] - c1[1]))
    worst, gmin, gmax = 0.0, 1e9, 0.0
    for k in range(48):
        a = (360.0 / z1) * k / 48
        PA = affinity.rotate(A, a, origin=tuple(c1))
        PB = affinity.rotate(B, -a * z1 / z2, origin=tuple(c2))
        worst = max(worst, PA.intersection(PB).area)
        g = PA.distance(PB)
        gmin, gmax = min(gmin, g), max(gmax, g)
    # engagement: take up the backlash + 0.1 mm -> teeth must collide
    lock = 0.0
    for sgn in (1, -1):
        dth = sgn * np.degrees((backlash_expect + 0.1) / (z2 * 1.0))  # driven gear, pitch radius = z (m=2)
        PB = affinity.rotate(B, dth, origin=tuple(c2))
        lock = max(lock, A.intersection(PB).area)
    ok = worst < 1e-3 and gmax < 0.35 and lock > 1e-3
    return {"ok": ok, "centre_distance": round(cd, 3), "overlap_mm2": round(worst, 5),
            "flank_gap_min": round(gmin, 3), "flank_gap_max": round(gmax, 3), "locks_without_backlash": lock > 1e-3}


def main():
    argv = sys.argv[1:]
    path = argv.pop(0)
    defines, label = [], None
    while argv:
        a = argv.pop(0)
        if a == "-D":
            defines.append(argv.pop(0))
        elif a == "--label":
            label = argv.pop(0)
    label = label or os.path.basename(path)[:-5] + ("_" + "_".join(d.replace('"', "") for d in defines) if defines else "")
    with tempfile.NamedTemporaryFile(suffix=".echo", delete=False) as t:
        echo_file = t.name
    scad(sum([["-D", d] for d in defines], []) + ["-D", 'only="__none__"', path], echo_file)
    items, meshes, allow = parse_echo(open(echo_file).read())
    os.unlink(echo_file)

    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        stls = dict(zip(items, ex.map(lambda n: render_item(path, defines, n), items)))
    meshes_tm, mans = {}, {}
    for n, f in stls.items():
        m = trimesh.load(f, force="mesh")
        if len(m.faces) == 0:
            continue
        meshes_tm[n] = m
        mans[n] = to_manifold(m)

    report = {"assembly": label, "items": len(meshes_tm), "interference": [], "gear_meshes": [], "ok": True}
    names = list(meshes_tm)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            ba, bb = meshes_tm[a].bounds, meshes_tm[b].bounds
            if np.any(ba[1] < bb[0]) or np.any(bb[1] < ba[0]):
                continue
            v = (mans[a] ^ mans[b]).volume()
            lim = allow.get(tuple(sorted((a, b))), VOL_TOL)
            if v > VOL_TOL:
                entry = {"a": a, "b": b, "volume_mm3": round(v, 3), "allowed": v <= lim}
                report["interference"].append(entry)
                if v > lim:
                    report["ok"] = False
    bl = 0.30
    for mdef in meshes:
        n1, n2, z1, z2, c1, c2, y = mdef[:7]
        r = check_mesh(meshes_tm[n1], meshes_tm[n2], z1, z2, c1, c2, y, bl)
        r.update({"pair": "%s(%dT) - %s(%dT)" % (n1, z1, n2, z2), "ratio": "%g:1" % (z1 / z2 if z1 > z2 else z2 / z1)})
        report["gear_meshes"].append(r)
        if not r["ok"]:
            report["ok"] = False

    os.makedirs(os.path.join(ROOT, "build", "qc"), exist_ok=True)
    with open(os.path.join(ROOT, "build", "qc", label + ".json"), "w") as f:
        json.dump(report, f, indent=1)
    print("== %s: %d items, %s" % (label, report["items"], "PASS" if report["ok"] else "FAIL"))
    for e in report["interference"]:
        print("   %s  %-22s x %-22s %.3f mm3" % ("allowed" if e["allowed"] else "CLASH  ", e["a"], e["b"], e["volume_mm3"]))
    for g in report["gear_meshes"]:
        print("   mesh %-40s CD %-6s overlap %.4f gap %.3f..%.3f lock %s %s" % (
            g.get("pair"), g.get("centre_distance"), g.get("overlap_mm2", -1), g.get("flank_gap_min", -1),
            g.get("flank_gap_max", -1), g.get("locks_without_backlash"), "ok" if g["ok"] else "FAIL"))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
