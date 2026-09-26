# PROJECT STATUS

**Phase:** 1 - manufacturing system + 5 prototypes (software-validated).
**Gate:** STOP expanding the collection. Next work is the physical print/test loop.
**Last updated:** 2026-09-26

## Prototype summary (STANDARD size, Classic colours, single unit unless noted - ESTIMATES)

| ID | T1 | T2 | T3 | T4 | Purge | Total | Tool changes | Time | Batch/plate | Purge/unit @batch | Cost @batch (NORMAL) | QC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRW-001 keyring | 5.0 g PLA | 0.5 g | 0.8 g | 0.2 g TPU* | 1.08 g | 7.5 g | 18 | 23 min | 12 | 0.09 g | $1.41 | WARN (0 FAIL) |
| CRW-002 magnet | 8.4 g PLA | 0.4 g | 1.0 g | 0.6 g TPU* | 0.90 g | 11.3 g | 15 | 33 min | 9 | 0.10 g | $2.00 | WARN (0 FAIL) |
| CRW-003 mini cow | 5.8 g PLA | 1.0 g | 0.6 g | 4.7 g PLA** | 11.94 g | 24.0 g | 199 | 63 min | 24 | 0.50 g | $1.66 | WARN + SETUP |
| CRW-004 phone stand | 79.0 g PLA | 2.3 g | 0.4 g | 4.5 g TPU | 1.68 g | 87.9 g | 28 | 235 min | 3 | 0.56 g | $5.94 | WARN (0 FAIL) |
| CRW-005 articulated | 33.0 g PLA | 1.3 g | 0.5 g | 1.3 g TPU | 2.52 g | 38.7 g | 42 | 101 min | 2 | 1.26 g | $6.53 | PASS |

\* TPU is what `config/toolheads.json` loads in tool 4; PLA preferred for these (WARN).
\** Mini cow requires rigid tool 4 (SETUP) - costed as PLA.
Sizes also generated: CRW-001 and CRW-002 SMALL + LARGE. Full numbers: `documentation/costs/cost-report.md`.

## Done

- Project structure, CLAUDE.md, configuration system (toolheads / colours / materials / dimensions / costs / variants).
- Mascot "Cowa" (front, side, 3D) + 9 colour themes (Classic, Aussie, Farmer, Surfer, Wine Country, Christmas,
  Camping, Beach, Jersey).
- Component library (all 19 functions from the brief).
- 5 prototypes -> STL (merged + per tool), 3MF (colours + tool map), SCAD assemblies; 3MF colour variants.
- QC (`scripts/validate.py`): mesh/manifold, vertex-weld STL reload, part disjointness, bed fit, wall thickness,
  overhang/bridges, tool assignment + 3MF round-trip, material requirements, bonding, thermal window, colour
  islands/thin strokes, contrast (all variants), purge, product-specific (keyring loop, magnet pockets, phone
  stability/slot, joint retention, ROM sweep, standing stops). **Result: 0 FAIL on all 9 builds.**
- Cost model (3 scenarios), batch planner, toolhead utilisation, opportunity score (internal), product DB
  (`products/products.json`: 9 prototype records + 48 concepts), product sheets, print-settings sheets,
  packaging card + market display mock-ups, previews (5 views + variants + tool-layer map per product).
- 28 automated tests (`python3 -m pytest -q tests`) - all pass.

## Open issues / known problems

1. **Nothing has been physically printed.** All mass/time/purge numbers are model estimates; clearances
   (joints 0.5 mm, magnet 0.15 mm, dovetail 0.15 mm) are untested starting values.
2. **Mini cow purge:** ~199 tool changes -> purge = 50 % of a single unit's material. Only sensible batch-printed
   (24/plate -> 0.5 g/unit). Real purge per change on the actual printer decides whether this product is viable.
3. **Tool 4 setup conflict:** keyring/magnet/mini want a rigid accent in tool 4, stand/articulated want TPU.
   Plan production in two set-ups (see `documentation/assumptions.md`).
4. **TPU dovetail key wings** are ~0.7 mm (below the 1.2 mm TPU guideline) - WARN; verify pad printability/retention.
5. **3MF not tested in a slicer**; extruder mapping by part name is manual (vendor project metadata not written).
6. **STEP not produced** (mesh kernel; faceted conversion impractical).
7. **Mini cow LARGE** not exported: merged single-colour mesh has a tangency at 1.25x (parts themselves validate).
8. Contrast WARNs: Beach variant (white/sand horns), mini cow black patch next to earth-brown hooves (Classic/Jersey).
9. Phone stand has no charging-cable channel (portrait charging while docked not supported).
10. Articulated cow legs are one member per pair (side-profile "flexi" style); joint friction unknown.
11. Mini cow muzzle keel (45-degree support-free wedge) is visible as a "chin" - cosmetic.

## Next steps (in priority order)

1. Print the 5 prototypes (single + recommended batch) following `research/test-protocol.md`; fill `research/print-log.csv`.
2. Measure the real printer: tool-change time, purge per change, bed size -> update `config/toolheads.json`;
   run `python3 scripts/cost.py --calibrate`.
3. Print a joint/clearance test coupon (bicone joint at 0.35 / 0.5 / 0.65 mm) and a magnet/dovetail fit coupon.
4. Fix what the prints reveal; re-run `scripts/run_all.py`; move passing prototypes to `production` stage.
5. Then (and only then) expand: CRW-006 tourist magnet, CRW-007 bottle opener, B-series collectibles on a shared base.
6. Native B-rep STEP for 2.5D products via CadQuery; optional vendor 3MF metadata once a target slicer is chosen.
