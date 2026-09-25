#!/usr/bin/env python3
"""Render STL files to PNG with OpenSCAD (headless via xvfb) and tile them.

usage: png.py out.png file1.stl [file2.stl ...] [--size 600x450] [--cols 3]
"""
import subprocess, sys, os, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont

def render(stl, png, size=(600, 450), camera=None, color="Tomorrow"):
    with tempfile.NamedTemporaryFile("w", suffix=".scad", delete=False) as f:
        f.write('color([0.25,0.5,0.85]) import("%s");\n' % os.path.abspath(stl))
        scad = f.name
    cmd = ["xvfb-run", "-a", "openscad", "-o", png, "--imgsize=%d,%d" % size,
           "--autocenter", "--viewall", "--colorscheme=" + color, "--projection=p"]
    cmd += ["--camera=" + (camera or "0,0,0,55,0,30,0")]
    cmd.append(scad)
    subprocess.run(cmd, check=True, capture_output=True)
    os.unlink(scad)

def tile(pngs, labels, out, cols=3):
    ims = [Image.open(p) for p in pngs]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 24)), "white")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except OSError:
        font = None
    for i, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * w, (i // cols) * (h + 24)
        sheet.paste(im, (x, y + 24))
        d.text((x + 8, y + 4), lab, fill="black", font=font)
    sheet.save(out)

if __name__ == "__main__":
    args = sys.argv[1:]
    size, cols, cam = (600, 450), 3, None
    if "--size" in args:
        i = args.index("--size"); size = tuple(int(v) for v in args[i + 1].split("x")); del args[i:i + 2]
    if "--cols" in args:
        i = args.index("--cols"); cols = int(args[i + 1]); del args[i:i + 2]
    if "--camera" in args:
        i = args.index("--camera"); cam = args[i + 1]; del args[i:i + 2]
    out, stls = args[0], args[1:]
    tmp = tempfile.mkdtemp()
    pngs = []
    for k, s in enumerate(stls):
        p = os.path.join(tmp, "%d.png" % k); render(s, p, size, cam); pngs.append(p)
    tile(pngs, [os.path.basename(s)[:-4] for s in stls], out, cols)
    shutil.rmtree(tmp)
