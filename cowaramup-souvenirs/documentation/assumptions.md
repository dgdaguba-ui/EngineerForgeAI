# Assumptions & limitations

Everything below is an assumption made because the real hardware, filament and slicer were not available
in the development environment. Each has a place in `config/` where it can be corrected.

## Printer (config/toolheads.json -> printer)

| Item | Assumed | Why it matters |
|---|---|---|
| Machine | generic FFF, 4 independent tool heads (tool-changer style: idle tools park off the print) | tool-change time/purge, idle-nozzle collisions |
| Bed | 250 x 250 x 250 mm | batch layouts, max units per plate |
| Nozzle / layer | 0.4 mm / 0.2 mm | inlay depth 0.6 mm = exactly 3 layers |
| Tool change | 8 s, 0.06 g purge/prime per change, no prime tower | purge + time model (the dominant waste term for 3D colour) |

If the machine is a single-nozzle filament switcher instead of independent heads, purge per change is typically
an order of magnitude higher; set `purge_per_toolchange_g` accordingly and the reports re-rank everything.

## Material & process model (config/materials.json, config/costs.json -> estimation)

- Mass = density x (shell + 15 % infill x interior), shell = surface area x 0.9 mm. Not a slicer.
- Time = extruded volume / effective flow (PLA 6, TPU 2.5 mm^3/s) + 1.5 s/layer + 0.4 s/object/layer
  + tool changes x 8 s + 5 min heat-up. Not a slicer.
- Tool changes: per-layer tool sets from the geometry, greedy ordering (keep current tool, finish on a tool needed
  next layer). Real slicers may order differently.
- Calibration factors `mass_calibration`, `time_calibration` default to 1.0 - update from `research/print-log.csv`.
- Filament prices (AUD/kg): PLA 28, PETG 30, TPU 45, specialty 60. Electricity 0.32 AUD/kWh at 0.25 kW average.
  Labour 30 AUD/h. All editable.

## Toolhead loading

- `config/toolheads.json` loads **TPU in tool 4** (brief example). Consequences, all reported by `validate.py`:
  - CRW-003 mini cow needs a **rigid** tool 4 (structural plinth) -> SETUP flag; its costs are computed with PLA.
  - CRW-001/002 print with TPU horns/banner (allowed, but PLA preferred for crisp colour).
- Practical production plan: **Setup A** (tool 4 = rigid accent PLA) for CRW-001/002/003 and **Setup B**
  (tool 4 = TPU) for CRW-004/005. Batch by setup to avoid filament swaps.

## Formats

- **STL**: geometry interchange only; one merged single-colour STL + one STL per toolhead region.
- **3MF**: production format. Written to the 3MF Core spec (2015/02) with `<basematerials>` colours, one multi-part
  object per object group, and `Metadata/crw_toolmap.json`. Verified by re-loading with trimesh and XML parsing.
  **Not verified in a real slicer** (none installed). Vendor-specific extruder metadata (PrusaSlicer / Orca / Bambu
  project config) is deliberately NOT written - it is undocumented and could not be tested. Operators map parts
  T1..T4 to extruders by name once.
- **SCAD**: OpenSCAD colour assemblies importing the per-part STLs (viewer/re-export aid). Verified: OpenSCAD 2021.01
  renders them. The geometry source of truth is the Python in `cad/`, not the .scad.
- **STEP: not produced.** The kernel is mesh-based (manifold3d). A mesh-to-STEP conversion via CadQuery/OCP sewing was
  attempted and took > 10 min for a 2.9 k-triangle part and would only give faceted B-rep. A native B-rep path is
  feasible for the 2.5D products (their profiles are already 2D polygons) - listed as a next step.

## Geometry / QC method limits

- Wall thickness = inward ray casting; the 5th percentile is used because rays near 45-degree chamfers and edges
  read artificially thin.
- Overhang check flags faces steeper than 45 degrees (1.5 degree tolerance) excluding the bed face; horizontal
  down-facing faces are reported as bridges with an inscribed-span estimate.
- Colour contrast rule: luminance ratio >= 2.0 OR CIE76 dE >= 35 (hue contrast counts, e.g. pink on white).
- Print-in-place clearance (0.5 mm radial, 0.35 mm normal on 45-degree faces) is a typical starting value; the real
  value depends on the printer and must be tuned with a test coupon.
- Phone-stand stability uses the phone's centre of gravity at mid-height; case/phone mass distribution varies.

## Commercial

- Suggested retail ranges = configured price bands raised to a cost x markup floor. They are **not** a statement
  about demand, competitor prices or what tourists will pay.
- The opportunity score is an internal development ranking. It does not predict sales.
- "4-Colour 3D Printed Souvenir" is true for all five prototypes (each uses 4 tools). "Made in Cowaramup" may only
  be printed on packaging if production actually happens there.
