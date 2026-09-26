"""Product / part data model and the colour 'painter'.

A product is a set of Parts. Each Part is one watertight solid assigned to ONE
tool role (tool_1..tool_4). Parts inside the same `object_group` are printed
fused together (a multi-part object in the 3MF); different groups are separate
objects on the plate (e.g. TPU inserts printed next to the body).

Colour regions are resolved with a painter's algorithm: later layers win and
every region is clipped to the envelope, so parts never overlap and together
exactly fill the product envelope. This is what makes tool assignment reliable
in any slicer that accepts multi-part objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapely.ops import unary_union

from . import geom

TOOLS = ("tool_1", "tool_2", "tool_3", "tool_4")


@dataclass
class Part:
    name: str
    tool: str
    solid: geom.Manifold
    feature: str = ""                 # what this colour region represents
    object_group: str = "main"        # parts in one group are fused/printed as one object
    requires: dict = field(default_factory=dict)  # e.g. {"flexible": True}
    quantity: int = 1

    def __post_init__(self):
        assert self.tool in TOOLS, self.tool


@dataclass
class FaceRegion:
    """A visible 2D colour region on a planar face (used for min-feature QC)."""
    face: str
    tool: str
    shape: Any


@dataclass
class Product:
    id: str
    slug: str
    name: str
    category: str
    description: str
    size: str
    parts: list[Part]
    tool_roles: dict               # tool -> human description of use in THIS product
    requirements: dict             # tool -> {"flexible": bool, "strict": bool, "why": str}
    print_orientation: str
    strategy: str                  # A..E manufacturing strategy from the brief
    hardware: list[str] = field(default_factory=list)
    packaging: str = "impulse_backing_card"
    tier: str = "IMPULSE"
    assembly_time_minutes: float = 0.0
    post_process_minutes: float = 0.5
    supports_required: bool = False
    face_regions: list[FaceRegion] = field(default_factory=list)
    checks: dict = field(default_factory=dict)   # product-specific QC data (holes, joints...)
    notes: list[str] = field(default_factory=list)
    self_critique: dict = field(default_factory=dict)
    envelope: Any = None   # optional exact single-colour solid (else: union of parts)

    @property
    def file_stem(self) -> str:
        suffix = "" if self.size == "STANDARD" else f"-{self.size.lower()}"
        return f"{self.id}-{self.slug}{suffix}"

    def tools_used(self) -> list[str]:
        return sorted({p.tool for p in self.parts if not p.solid.is_empty()})

    def groups(self) -> dict[str, list[Part]]:
        out: dict[str, list[Part]] = {}
        for p in self.parts:
            out.setdefault(p.object_group, []).append(p)
        return out


class Painter2D:
    """Painter's-algorithm colour layout for flat (2.5D) designs."""

    def __init__(self):
        self.layers: list[tuple[str, Any, str]] = []

    def paint(self, tool: str, shape, feature: str):
        assert tool in TOOLS
        if shape is not None and not shape.is_empty:
            self.layers.append((tool, shape, feature))
        return self

    def envelope(self):
        return geom.clean(unary_union([s for _, s, _ in self.layers]))

    def resolve(self, envelope=None) -> dict[str, dict[str, Any]]:
        """-> {tool: {"shape": visible region, "features": [...]}}, disjoint, inside envelope."""
        env = self.envelope() if envelope is None else envelope
        out: dict[str, dict[str, Any]] = {}
        covered = None
        for tool, shape, feature in reversed(self.layers):
            vis = shape.intersection(env)
            if covered is not None:
                vis = vis.difference(covered)
            covered = shape if covered is None else covered.union(shape)
            if vis.is_empty or vis.area < 1e-3:
                continue
            slot = out.setdefault(tool, {"shape": vis, "features": []})
            if feature not in slot["features"]:
                slot["features"].append(feature)
            if slot["shape"] is not vis:
                slot["shape"] = slot["shape"].union(vis)
        return out


class Painter3D:
    """Painter's algorithm for true 3D colour volumes (later volumes win)."""

    def __init__(self):
        self.layers: list[tuple[str, geom.Manifold, str]] = []

    def paint(self, tool: str, solid: geom.Manifold, feature: str):
        assert tool in TOOLS
        if solid is not None and not solid.is_empty():
            self.layers.append((tool, solid, feature))
        return self

    def resolve(self, envelope: geom.Manifold | None = None) -> dict[str, dict[str, Any]]:
        env = envelope if envelope is not None else geom.union(s for _, s, _ in self.layers)
        out: dict[str, dict[str, Any]] = {}
        covered = geom.Manifold()
        for tool, solid, feature in reversed(self.layers):
            vis = (solid ^ env) - covered
            covered = covered + solid
            if vis.is_empty() or vis.volume() < 1e-3:
                continue
            slot = out.setdefault(tool, {"solid": geom.Manifold(), "features": []})
            slot["solid"] = slot["solid"] + vis
            if feature not in slot["features"]:
                slot["features"].append(feature)
        return out


def coverage(silhouette, regions: dict, tol: float = 0.02, min_area: float = 0.05) -> dict:
    """Turn painter regions into an edge-matched polygon COVERAGE of the silhouette.

    * colour regions are de-pinched (0.01 mm opening) so no two lobes touch at a
      point (a point contact becomes a non-manifold edge once a slicer welds
      vertices by position);
    * tool_1 = silhouette minus all colours (exact shared edges);
    * GEOS coverage simplification keeps shared edges identical, so extruded
      parts meet face-to-face with no slivers or coincident duplicate vertices.
    """
    import shapely
    R = 0.08  # radius of the disc re-assigned at each pinch point (mm)
    G = 0.001  # snap grid (mm): nearly-coincident boundaries become exactly coincident
    S = 0.03   # hairline slivers narrower than 2*S (mm) are removed from every region
    silhouette = shapely.set_precision(silhouette, G)
    others = {}
    for t, r in regions.items():
        if t == "tool_1":
            continue
        shp = shapely.set_precision(r["shape"], G).intersection(silhouette)
        shp = shapely.set_precision(shp.buffer(-S, join_style="mitre").buffer(S, join_style="mitre"), G)
        shp = unary_union([p for p in geom.polygons_of(shp) if p.area >= min_area])
        for q in geom.pinch_points(shp):          # colour touching itself -> give disc to tool_1
            shp = shp.difference(q.buffer(R, quad_segs=4))
        if not shp.is_empty:
            others[t] = shp
    for _ in range(3):
        t1 = silhouette.difference(unary_union(list(others.values()))) if others else silhouette
        t1 = shapely.set_precision(t1, G)
        pins = geom.pinch_points(t1)
        if not pins:
            break
        for q in pins:                            # tool_1 touching itself -> give disc to a neighbour
            near = min(others, key=lambda t: others[t].distance(q))
            others[near] = shapely.set_precision(others[near].union(q.buffer(R, quad_segs=4).intersection(silhouette)), G)
    # tool_1 hairlines (e.g. a white wedge ending microns from the outline) -> nearest colour
    if others:
        t1_open = shapely.set_precision(t1.buffer(-S, join_style="mitre").buffer(S, join_style="mitre"), G).intersection(t1)
        for piece in geom.polygons_of(shapely.set_precision(t1.difference(t1_open), G)):
            near = min(others, key=lambda t: others[t].distance(piece))
            others[near] = shapely.set_precision(others[near].union(piece), G)
        t1 = shapely.set_precision(silhouette.difference(unary_union(list(others.values()))), G)
    names = ["tool_1"] + list(others)
    cov = [geom.polyonly(g) for g in [t1] + [others[t] for t in others]]
    # outer boundary is NOT simplified here: it must stay identical for both faces and the core band
    simp = shapely.coverage_simplify(cov, tol, simplify_boundary=False)
    simp = [geom.polyonly(shapely.set_precision(g, G)) for g in simp]
    # simplification can create new point contacts: repair them with exact booleans
    for _ in range(3):
        fixed = False
        for i, g in enumerate(simp):
            for q in geom.pinch_points(g):
                disc = shapely.set_precision(q.buffer(R, quad_segs=4).intersection(silhouette), G)
                j = min((k for k in range(len(simp)) if k != i), key=lambda k: simp[k].distance(q), default=None)
                if j is None:
                    continue
                simp[i] = geom.polyonly(shapely.set_precision(simp[i].difference(disc), G))
                simp[j] = geom.polyonly(shapely.set_precision(simp[j].union(disc), G))
                fixed = True
        if not fixed:
            break
    return {n: g for n, g in zip(names, simp) if not g.is_empty}


def sandwich_parts(silhouette, regions: dict, thickness: float, inlay_depth: float,
                   top: bool = True, bottom: bool = True, bottom_regions: dict | None = None,
                   group: str = "main", prefix: str = "", return_coverage: bool = False):
    """Build 'sandwich inlay' parts for a flat product.

    The core is a single tool (tool_1); every other colour lives only in the top
    and/or bottom `inlay_depth`. That confines tool changes to a handful of layers
    per face - the central waste-reduction rule of this project.
    `regions` are the resolved Painter2D regions for the top face;
    `bottom_regions` (default: same as top) for the bed face.
    All parts are pure extrusions of one edge-matched coverage per face.
    """
    import shapely
    bottom_regions = regions if bottom_regions is None else bottom_regions
    silhouette = geom.depinch(silhouette, close=True).simplify(0.02, preserve_topology=True)
    silhouette = shapely.set_precision(silhouette, 0.001)
    cov_top = coverage(silhouette, regions) if top else {"tool_1": silhouette}
    cov_bot = coverage(silhouette, bottom_regions) if bottom else {"tool_1": silhouette}
    # the middle band uses the (simplified) outer boundary shared by both faces
    band = silhouette
    z0 = inlay_depth if bottom else 0.0
    z1 = thickness - inlay_depth if top else thickness
    parts: list[Part] = []
    for tool in TOOLS:
        solids, feats = [], []
        if top and tool in cov_top:
            solids.append(geom.extrude(cov_top[tool], z1, thickness))
            feats += regions.get(tool, {}).get("features", [])
        if bottom and tool in cov_bot:
            solids.append(geom.extrude(cov_bot[tool], 0.0, z0))
            feats += [f for f in bottom_regions.get(tool, {}).get("features", []) if f not in feats]
        if tool == "tool_1":
            solids.append(geom.extrude(band, z0, z1))
            feats = ["core body"] + feats
        solid = geom.union(solids)
        if not solid.is_empty():
            parts.append(Part(f"{prefix}{tool}", tool, solid, ", ".join(feats), group))
    if return_coverage:
        return parts, cov_top, cov_bot, silhouette
    return parts
