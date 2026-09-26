# CLAUDE.md - Cowaramup 3D Souvenir Factory

Working agreement for any agent (or human) continuing this project.

## Session start checklist (always, in order)

1. Read this file, `PROJECT_STATUS.md`, `CHANGELOG.md`.
2. Skim `cad/` (library + products) and `documentation/assumptions.md`.
3. Run the pipeline: `python3 scripts/run_all.py` (generate -> validate -> cost -> previews -> reports -> pytest, ~1 min).
4. Read `documentation/qc/qc-report.md` - any FAIL is the first job.
5. Check `research/print-log.csv` - real print data beats every estimate; calibrate with `python3 scripts/cost.py --calibrate`.
6. Pick the next highest-value task from `PROJECT_STATUS.md` -> "Next steps". Never restart the project.

## Phase gate (brief section 30)

The collection is **frozen at the 5 prototypes** until they have been physically printed and the print log
contains real time / filament / purge / tool-change / failure data. Do not generate further products
before that; concepts live in `products/concepts.json` only.

## Architecture (one-way data flow)

```
config/*.json  ->  cad/ (python geometry, manifold3d + shapely)  ->  scripts/generate.py
   toolheads       core/   geom, text, model(Part, Painter, coverage, sandwich_parts),
   colors          |       analysis, export(STL/3MF/SCAD), render, tools(effective_tools)
   materials       cows/   face (front 2D), side (side 2D), solid (3D)  = the mascot
   dimensions      accessories/ keyring_loop, magnet_cavity, phone_slot, tpu_pad, cow_sign, cow_base
   costs           mechanisms/  hinge (bicone print-in-place), peg, socket, snap_joint
   variants        products/    crwNNN_*.py  -> build(size) -> Product(parts...)
                                     |
            stl/ 3mf/ previews/ products/generated/*.json -> validate/cost/reports -> documentation/
```

## Rules that keep the system working

- **Products never hard-code materials or colours.** They declare a ROLE per tool (`tool_roles`) and optional
  `requirements` (`flexible`, `strict`, `preferred_material`). Colours come from `config/variants.json`,
  materials from `config/toolheads.json`. `tests/test_config.py` enforces this.
- **Each Part = one tool.** Parts in one `object_group` are fused; different groups are separate objects on the plate.
- **Flat products use `sandwich_parts()`** (colour only in the outer 0.6 mm = 3 layers). Colour regions go through
  `coverage()`: de-pinch, snap to a 1 um grid, GEOS coverage simplification. Do not bypass it - independent
  simplification or boolean-subtraction of colours re-introduces non-manifold slivers (see CHANGELOG 0.1.0 notes).
- **3D figures use `Painter3D`** + `teardrop()` shapes (45-degree keels) so they print without supports.
  Paint the plinth LAST so body parts end on its top face instead of carving pockets.
- **Exports:** vertices stay near the origin (float32 STL precision); the 3MF places the plate with a build
  transform. Merged single-colour STL uses `Product.envelope` when provided.
- **Minimum features:** colour strokes >= 0.8 mm, colour islands >= 3 mm^2 (use geometry - dimples, deboss -
  for anything smaller), TPU features >= 1.2 mm where possible, text knock-outs use `min_counter`.
- **Honesty:** estimates are labelled as estimates; never claim demand; never fabricate a file format
  (STEP is deliberately not produced - see assumptions). Packaging claims must be literally true.

## Commands

```bash
python3 scripts/run_all.py                         # everything
python3 scripts/generate.py -p CRW-001 --variant aussie
python3 scripts/validate.py -p CRW-005
python3 scripts/cost.py --calibrate                # after real prints
python3 -m pytest -q tests
```

## Adding a product (after the phase gate)

1. `cad/products/crwNNN_slug.py` with `build(size) -> Product`, reusing library components.
2. Register it in `scripts/_common.py` `REGISTRY` and ratings in `scripts/reports.py`.
3. Add product-specific checks to `Product.checks` + `scripts/validate.py` section 12, and a test.
4. Run the pipeline; fix every FAIL; answer the self-critique questions in the Product definition.
