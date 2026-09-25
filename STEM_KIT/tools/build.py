#!/usr/bin/env python3
"""Render every catalogued part (tools/parts.py) to STL/<folder>/<id>.stl.

usage: build.py [id ...]        (no ids = everything)
OpenSCAD warnings are treated as errors: a part with an undefined
variable or a failed text/geometry op must not reach the STL folder.
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
from parts import PARTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(p):
    out = os.path.join(ROOT, "STL", p["stl"], p["id"] + ".stl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ["openscad", "-o", out]
    for d in p["defines"]:
        cmd += ["-D", d]
    cmd.append(os.path.join(ROOT, p["src"]))
    r = subprocess.run(cmd, capture_output=True, text=True)
    bad = [l for l in r.stderr.splitlines() if l.startswith(("WARNING", "ERROR"))]
    if r.returncode != 0 or bad:
        return p["id"], False, "\n".join(bad) or r.stderr[-800:]
    # OpenSCAD 2021 writes ASCII STL; store binary (≈ 5x smaller, identical geometry)
    import trimesh
    trimesh.load(out, force="mesh", process=False).export(out, file_type="stl")
    return p["id"], True, ""


def main():
    want = set(sys.argv[1:])
    todo = [p for p in PARTS if not want or p["id"] in want]
    ok = True
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        for pid, good, msg in ex.map(build, todo):
            print(("  ok   " if good else "  FAIL ") + pid)
            if not good:
                ok = False
                print("       " + msg.replace("\n", "\n       "))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
