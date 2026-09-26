# PROJECT STATUS

**Phase:** 2 - commercial design overhaul (in progress). Mascot + 4 of 5 products redesigned; phone stand next.
**Gate:** still no physical prints. Do not expand the collection; print-test the redesigned set first.
**Last updated:** 2026-09-26

## Phase 2 summary (see `DESIGN_AUDIT.md`, `documentation/redesign/BEFORE_AFTER.md`)

| ID | Status | T1 | T2 | T3 | T4 | Purge (1 / at batch) | Tool changes | Batch | Cost @batch | QC |
|---|---|---|---|---|---|---|---|---|---|---|
| Mascot "Cowa" v2 | redesigned (SDF character) | - | - | - | - | - | - | - | - | - |
| CRW-003 mini Standard | redesigned | 10.5 g | 5.1 g | 1.4 g | - | 21.8 / 1.37 g | 364 | 16 | $1.92 | WARN |
| CRW-003 mini Deluxe | NEW edition | 15.7 g | 5.2 g | 1.4 g | 11.5 g PLA | 30.1 / 3.77 g | 502 | 8 | $4.01 | FAIL (34 pinch edges) + SETUP |
| CRW-001 keyring | redesigned (3D, tail loop) | 6.3 g | 3.2 g | 0.9 g | 0.02 g | 19.1 / 0.64 g | 318 | 30 | $1.51 | WARN |
| CRW-002 magnet | redesigned (bas-relief bust) | 4.3 g | 1.5 g | 1.7 g | 3.1 g | 7.4 / 0.62 g | 124 | 12 | $2.06 | FAIL (21 pinch edges) |
| CRW-005 articulated | redesigned (pillow members) | 33.7 g | 5.9 g | 3.2 g | 1.3 g TPU | 13.7 / 6.9 g | 229 | 2 | $6.99 | WARN |
| CRW-004 phone stand | **v1, next to redesign** | 79.0 g | 2.3 g | 0.4 g | 4.5 g TPU | 1.7 g | 28 | 3 | $5.94 | WARN |

QC FAIL items are both mesh-export pinch edges (see Known problems #1); the 3MF production files are topologically
exact. 29/29 tests pass (sculpted products are held to documented regression ceilings).

## Phase 1 record

### Prototype summary (phase 1) (STANDARD size, Classic colours, single unit unless noted - ESTIMATES)

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

## Open issues / known problems (phase 2 first)

1. **Pinch edges on sculpted meshes.** 5-34 isolated zero-area edges per sculpted product, where three colour regions meet
   tangentially (eye rims, fence feet, bust eye). STL readers weld them and slicers auto-repair them; the 3MF is exact. Fix next:
   make colour selectors transversal at eye rims, or repair at mesh level.
2. **Support-required overhang on ear rims.** 40-60 mm^2 per figure (> 60 deg, > 2 mm drop). The Deluxe also has its fence
   rails (bridges between posts). Fix: shape ear undersides at 45 deg.
3. **3D colour economics.** 124-502 tool changes per plate. Batch printing is mandatory; the real purge per change decides
   whether the Deluxe collectible is viable.
4. **Phone stand** is still the phase-1 extruded design.
5. **Articulated cow** still reads as a flexi toy: one leg member per pair, no on-product branding.

### Phase 1 issues (still relevant)


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

0. Redesign CRW-004 phone stand (sculpted resting Cowa, back cradles the phone, TPU saddle + feet, branded base).
0. Fix known problems #1 and #2 above, then print-test: mini Standard, mini Deluxe, keyring, magnet, articulated.


1. Print the 5 prototypes (single + recommended batch) following `research/test-protocol.md`; fill `research/print-log.csv`.
2. Measure the real printer: tool-change time, purge per change, bed size -> update `config/toolheads.json`;
   run `python3 scripts/cost.py --calibrate`.
3. Print a joint/clearance test coupon (bicone joint at 0.35 / 0.5 / 0.65 mm) and a magnet/dovetail fit coupon.
4. Fix what the prints reveal; re-run `scripts/run_all.py`; move passing prototypes to `production` stage.
5. Then (and only then) expand: CRW-006 tourist magnet, CRW-007 bottle opener, B-series collectibles on a shared base.
6. Native B-rep STEP for 2.5D products via CadQuery; optional vendor 3MF metadata once a target slicer is chosen.
