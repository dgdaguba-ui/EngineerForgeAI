# Cowaramup 3D Souvenir Factory

A parametric, code-driven product system for original Cowaramup (WA) souvenirs made on a **4-independent-toolhead
FFF printer**. Colour and material are designed into the geometry: every toolhead has a job, colour is confined to
the layers where it is cheap, and flexible TPU is used only where it does something.

![collection](previews/collection-overview.png)

## Status

Phase 1 (this repo state): manufacturing system + **5 prototypes**, generated and validated in software, **not yet
physically printed**. See `PROJECT_STATUS.md`. The rest of the collection (48 concepts in
`products/concepts.json`) is intentionally frozen until the physical testing loop is done.

| ID | Prototype | Key idea |
|---|---|---|
| CRW-001 | 4-colour keyring | double-sided flush "sandwich" inlays, colour on 6 of 21 layers |
| CRW-002 | 4-colour head magnet | raised pink muzzle, COWARAMUP lettering knocked out to the core colour (no extra tool) |
| CRW-003 | 50 mm mini collectible | true 3D colour volumes, support-free "teardrop" shapes, plinth-first vertical zoning |
| CRW-004 | phone stand (PLA + TPU) | printed on its side, 4 slide-in TPU dovetail pads (grip + feet), 4-colour flank art |
| CRW-005 | articulated cow (flagship) | print-in-place bicone joints, asymmetric leg stops so it stands, fused TPU tail |

## Quick start

```bash
pip install -r requirements.txt
python3 scripts/run_all.py        # generate -> validate -> cost -> previews -> reports -> tests (~1 min)
```

Change what is loaded in the printer: edit `config/toolheads.json`, re-run; `validate.py` reports which products
need a set-up change. Make a colour variant without touching geometry:

```bash
python3 scripts/generate.py -p CRW-003 --variant christmas
```

## Layout

```
config/        toolheads, colors (palette), materials, dimensions (SMALL/STANDARD/LARGE), costs, variants
cad/core/      geometry kernel helpers, colour painter + edge-matched coverage, analysis, exporters, renderer
cad/cows/      the mascot "Cowa": front (2D), side (2D), solid (3D) component library
cad/accessories/, cad/mechanisms/   keyring loop, magnet cavity, phone slot, TPU pad, sign, base; hinge, peg, socket, snap
cad/products/  one module per product: build(size) -> Product(parts per tool)
scripts/       generate, validate, cost, previews, reports, run_all
stl/ 3mf/      prototypes/ (generated), production/ (after physical sign-off)
previews/      per product: single-colour, four-colour, multi-material, dimensions, print orientation, variants, tool-layer map
documentation/ qc report, cost report, product sheets, print settings, assembly, packaging, assumptions, mascot
products/      products.json (database), concepts.json (catalogue), generated/ (analysis JSON)
research/      print-log.csv + test protocol for real prints
tests/         pytest: config, geometry, mechanisms, manufacturing
```

## Component library (brief section 17)

| Function | Where |
|---|---|
| `cow_head, cow_ear, cow_horn, cow_eye, cow_nose, cow_spot` | `cad/cows/face.py` (flat) and `cad/cows/solid.py` (3D) |
| `cow_body, cow_leg, cow_tail` | `cad/cows/solid.py`; side-profile head `cow_head_side` in `cad/cows/side.py` |
| `cow_base, cow_sign, keyring_loop, magnet_cavity, phone_slot, tpu_pad` | `cad/accessories/accessories.py` |
| `hinge, peg, socket, snap_joint` | `cad/mechanisms/joints.py` |

## Output formats

- `3mf/prototypes/<stem>.3mf` - **production file**: one part per toolhead, colours, tool map metadata.
- `stl/prototypes/<stem>.stl` (single-colour) and `stl/prototypes/<stem>/<stem>__<part>.stl` (per tool).
- `stl/prototypes/<stem>/<stem>.scad` - OpenSCAD colour assembly of the per-part STLs.
- `glb/<stem>.glb` - **for Blender / web viewers**: one named object per toolhead region with its colour
  material, true size (metres), standing as displayed. Blender: File > Import > glTF 2.0.
- STEP is **not** produced - see `documentation/assumptions.md`.

Tooling found in the build environment: Python 3.11, manifold3d, trimesh, shapely 2.1 (GEOS 3.13), numpy, matplotlib,
CadQuery 2.8 (installed, evaluated, not used), OpenSCAD 2021.01 (installed via apt). Not available: FreeCAD, Blender,
MeshLab, any slicer.
