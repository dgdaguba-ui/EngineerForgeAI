# Changelog

## 0.1.0 - 2026-09-26 - Phase 1: manufacturing system + 5 prototypes

### Added
- Configuration system: `config/toolheads.json`, `colors.json`, `materials.json`, `dimensions.json`, `costs.json`,
  `variants.json`.
- Geometry library (`cad/`): manifold3d + shapely kernel helpers, text outlines, colour painters (2D/3D),
  edge-matched colour coverage, sandwich-inlay builder, bicone print-in-place hinge, pegs/sockets/snaps,
  accessories (keyring loop, magnet pocket, phone slot, dovetail TPU pad, sign, collector base).
- Mascot "Cowa" (front / side / 3D) and 9 colour themes.
- Prototypes CRW-001 keyring, CRW-002 magnet, CRW-003 mini cow, CRW-004 phone stand, CRW-005 articulated cow.
- Exporters: STL (merged + per tool), 3MF (core spec, basematerials, multi-part objects, tool-map metadata),
  OpenSCAD colour assemblies.
- Pipeline scripts: generate, validate, cost (+ calibrate), previews, reports, run_all. 28 pytest tests.
- Documentation: QC report, cost report, product sheets, print settings, assembly, packaging, market display,
  assumptions, mascot, toolhead system, test protocol; product DB with 48 concepts.

### Engineering notes (lessons worth keeping)
- Independent simplification of adjacent colour regions + boolean subtraction created micron slivers and
  coincident vertices; STL readers (which weld vertices by position) then saw non-manifold edges. Fixed by building
  each face as an edge-matched **coverage** (1 um snap grid, pinch-point repair, sliver removal, GEOS
  `coverage_simplify` with the outer boundary preserved) and assembling parts by extrusion only.
- float32 STL precision at bed-centre coordinates (~125 mm) welded distinct vertices; exports now stay near the
  origin and the 3MF positions the plate with a build transform.
- 3D figure: painting the plinth last (instead of first) removed coplanar pocket floors inside the plinth.
- Validator caught and drove fixes for: TPU dovetail flare > 45 degrees, tiny letter counters in knock-out text,
  white pin-holes inside blob patches, eye highlights below 3 mm^2 at SMALL size, patches enlarging the silhouette.
