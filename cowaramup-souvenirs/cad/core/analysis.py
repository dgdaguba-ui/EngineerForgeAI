"""Slicer-independent manufacturing analysis.

Every number here is an ESTIMATE from geometry + config assumptions. Replace
with slicer output / real print data as soon as it exists (research/print-log.csv
and scripts/cost.py --calibrate).
"""
from __future__ import annotations

import math
from itertools import combinations

import numpy as np
import trimesh
from shapely.geometry import Polygon

from . import config, geom
from .model import TOOLS, Product


# ------------------------------------------------------------------ material
def part_mass_g(solid: geom.Manifold, material: str, est: dict) -> tuple[float, float]:
    """-> (grams, extruded mm^3). Shell + sparse infill model."""
    mats = config.materials()
    V = solid.volume()
    A = solid.surface_area()
    shell = min(V, A * est["shell_thickness_mm"])
    extruded = shell + est["infill_fraction"] * (V - shell)
    extruded *= est.get("mass_calibration", 1.0)
    return extruded * mats[material]["density_g_cm3"] / 1000.0, extruded


# ------------------------------------------------------------------ layers
def layer_presence(product: Product, layer_h: float) -> tuple[np.ndarray, list[str]]:
    """Boolean matrix [layer, tool] - does tool t print anything on layer i?"""
    zmax = max(p.solid.bounding_box()[5] for p in product.parts)
    zmin = min(p.solid.bounding_box()[2] for p in product.parts)
    n = int(math.ceil((zmax - zmin) / layer_h - 1e-6))
    mids = zmin + (np.arange(n) + 0.5) * layer_h
    M = np.zeros((n, 4), bool)
    for p in product.parts:
        if p.solid.is_empty():
            continue
        v, f = geom.mesh_arrays(p.solid)
        tz = v[f][:, :, 2]
        lo, hi = tz.min(1), tz.max(1)
        order = np.argsort(lo)
        lo_s, hi_s = lo[order], hi[order]
        hi_cummax = np.maximum.accumulate(hi_s)
        # a plane at z cuts the part iff some triangle has lo < z < hi
        idx = np.searchsorted(lo_s, mids, side="left")  # triangles with lo < z are [0, idx)
        present = np.zeros(n, bool)
        ok = idx > 0
        present[ok] = hi_cummax[idx[ok] - 1] > mids[ok]
        M[:, TOOLS.index(p.tool)] |= present
    return M, list(TOOLS)


def simulate_toolchanges(M: np.ndarray) -> dict:
    """Greedy per-layer tool ordering: keep the current tool first, finish on a tool
    that is also needed on the next layer. Returns counts + switches into each tool."""
    cur = None
    changes = 0
    into = np.zeros(4, int)
    layers_with_change = 0
    n = len(M)
    for i in range(n):
        S = [t for t in range(4) if M[i, t]]
        if not S:
            continue
        nxt = {t for t in range(4) if i + 1 < n and M[i + 1, t]}
        keep = cur in S
        rest = [t for t in S if t != cur]
        rest.sort(key=lambda t: t in nxt)  # tools needed next layer go last
        order = ([cur] if keep else []) + rest
        switches = order[1:] if (keep or cur is None) else order
        if switches:
            layers_with_change += 1
        for t in switches:
            into[t] += 1
        changes += len(switches)
        cur = order[-1]
    return {"tool_changes": int(changes), "layers": int(n), "layers_with_changes": int(layers_with_change),
            "switches_into_tool": {TOOLS[i]: int(into[i]) for i in range(4)}}


# ------------------------------------------------------------------ geometry QC
def group_envelopes(product: Product) -> dict[str, geom.Manifold]:
    return {g: geom.union(p.solid for p in parts) for g, parts in product.groups().items()}


def overhang_report(solid: geom.Manifold, max_deg: float = 45.0, tol_deg: float = 1.5) -> dict:
    v, f = geom.mesh_arrays(solid)
    t = v[f]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    area2 = np.linalg.norm(n, axis=1)
    ok = area2 > 1e-12
    n[ok] /= area2[ok, None]
    area = area2 / 2
    zmin = v[:, 2].min()
    zc = t[:, :, 2].mean(1)
    down = -n[:, 2]
    on_bed = zc < zmin + 0.6   # first 3 layers: bed-supported (mesh facets at the bottom edge)
    limit = math.cos(math.radians(max_deg - tol_deg))
    bridge = (down > 0.999) & ~on_bed
    steep = (down > limit) & ~bridge & ~on_bed
    # ignore tiny ledges (raised-patch edges, relief steps): only count faces with > 0.8 mm
    # of free fall below them - those are the ones that would actually need support
    if steep.any():
        idx = np.where(steep)[0]
        mesh = trimesh.Trimesh(v, f, process=False)
        origins = t[idx].mean(1) - np.array([0, 0, 1e-3])
        loc, ray_i, _ = mesh.ray.intersects_location(origins, np.tile([0, 0, -1.0], (len(idx), 1)), multiple_hits=False)
        drop = np.full(len(idx), np.inf)
        drop[ray_i] = origins[ray_i, 2] - loc[:, 2]
        drop = np.minimum(drop, origins[:, 2] - zmin)
        real = np.zeros(len(area), bool)
        real[idx[drop > 0.8]] = True
        # support-required: steeper than 60 degrees from vertical with > 2 mm of free fall
        need = np.zeros(len(area), bool)
        need[idx[(drop > 2.0) & (down[idx] > math.cos(math.radians(30)))]] = True
        steep = real
    else:
        need = steep
    return {"steep_overhang_area_mm2": round(float(area[steep].sum()), 2),
            "support_required_area_mm2": round(float(area[need].sum()), 2),
            "bridge_area_mm2": round(float(area[bridge].sum()), 2),
            "max_bridge_span_mm": round(_max_bridge_span(t[bridge]), 2) if bridge.any() else 0.0}


def _max_bridge_span(tris: np.ndarray) -> float:
    """Largest inscribed-circle diameter over connected horizontal bridge regions (approx)."""
    from shapely.ops import unary_union
    if len(tris) == 0:
        return 0.0
    polys = [Polygon(t[:, :2]) for t in tris if Polygon(t[:, :2]).area > 1e-9]
    if not polys:
        return 0.0
    region = unary_union([p.buffer(1e-4) for p in polys])
    best = 0.0
    for g in geom.polygons_of(region):
        # binary search the largest erosion that keeps area
        lo, hi = 0.0, max(g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1])
        for _ in range(18):
            mid = (lo + hi) / 2
            if g.buffer(-mid).is_empty:
                hi = mid
            else:
                lo = mid
        best = max(best, 2 * lo)
    return best


def wall_thickness(solid: geom.Manifold, samples: int = 3000, seed: int = 1) -> dict:
    """Inward ray-cast thickness at random surface points (percentiles, mm)."""
    v, f = geom.mesh_arrays(solid)
    mesh = trimesh.Trimesh(v, f, process=False)
    rng = np.random.default_rng(seed)
    pts, fid = trimesh.sample.sample_surface(mesh, samples, seed=int(rng.integers(1 << 30)))
    normals = mesh.face_normals[fid]
    origins = pts - normals * 1e-3
    loc, ray_idx, _ = mesh.ray.intersects_location(origins, -normals, multiple_hits=False)
    d = np.full(samples, np.nan)
    d[ray_idx] = np.linalg.norm(loc - origins[ray_idx], axis=1)
    d = d[~np.isnan(d)]
    if len(d) == 0:
        return {"p1_mm": None, "p5_mm": None, "median_mm": None}
    return {"p1_mm": round(float(np.percentile(d, 1)), 2), "p5_mm": round(float(np.percentile(d, 5)), 2),
            "median_mm": round(float(np.median(d)), 2)}


def colour_region_report(product: Product, min_feature: float, min_island: float) -> list[dict]:
    """2D face-region QC: tiny islands and features thinner than min_feature."""
    out = []
    for fr in product.face_regions:
        shape = fr.shape.buffer(-0.02, quad_segs=4).buffer(0.02, quad_segs=4)  # drop boolean slivers
        if shape.is_empty:
            continue
        fr = type(fr)(fr.face, fr.tool, shape)
        polys = [p for p in geom.polygons_of(fr.shape) if p.area >= 0.05]  # < 0.05 mm2 = numerical dust
        tiny = [p.area for p in polys if p.area < min_island]
        opened = fr.shape.buffer(-min_feature / 2, quad_segs=8).buffer(min_feature / 2, quad_segs=8)
        lost = fr.shape.difference(opened).area
        frac = lost / fr.shape.area if fr.shape.area else 0.0
        out.append({"face": fr.face, "tool": fr.tool, "islands": len(polys),
                    "tiny_islands": len(tiny), "min_island_mm2": round(min((p.area for p in polys), default=0), 2),
                    "thin_area_fraction": round(frac, 3)})
    return out


def colour_volume_islands(product: Product, min_volume: float = 2.0) -> list[dict]:
    out = []
    for p in product.parts:
        comps = p.solid.decompose()
        vols = sorted(c.volume() for c in comps)
        out.append({"part": p.name, "tool": p.tool, "components": len(comps),
                    "tiny_components": int(sum(1 for x in vols if x < min_volume)),
                    "min_component_mm3": round(vols[0], 2) if vols else 0.0})
    return out


def pairwise_overlap(product: Product) -> float:
    """Max overlap volume between any two parts (should be ~0)."""
    worst = 0.0
    parts = [p for p in product.parts if not p.solid.is_empty()]
    for a, b in combinations(parts, 2):
        ba, bb = a.solid.bounding_box(), b.solid.bounding_box()
        if any(ba[i] > bb[i + 3] or bb[i] > ba[i + 3] for i in range(3)):
            continue
        worst = max(worst, (a.solid ^ b.solid).volume())
    return worst


def contacts(product: Product, tol: float = 0.02) -> list[tuple[str, str]]:
    """Pairs of TOOLS whose parts touch inside the same object group (fused interfaces)."""
    pairs = set()
    for g, parts in product.groups().items():
        for a, b in combinations(parts, 2):
            if a.tool == b.tool:
                continue
            if a.solid.min_gap(b.solid, tol * 2) <= tol:
                pairs.add(tuple(sorted((a.tool, b.tool))))
    return sorted(pairs)


# ------------------------------------------------------------------ top level
def analyse(product: Product, deep: bool = True, tools: dict | None = None) -> dict:
    """tools = effective tool map (cad.core.tools.effective_tools); default = loaded config."""
    cfg_p = config.printer()
    est = config.costs()["estimation"]
    th = tools or config.tool_assignment(None)
    mats = config.materials()
    h = cfg_p["layer_height_mm"]

    per_tool = {t: {"material": th[t]["material"], "grams": 0.0, "extruded_mm3": 0.0, "volume_mm3": 0.0}
                for t in TOOLS}
    for p in product.parts:
        g, ext = part_mass_g(p.solid, th[p.tool]["material"], est)
        per_tool[p.tool]["grams"] += g * p.quantity
        per_tool[p.tool]["extruded_mm3"] += ext * p.quantity
        per_tool[p.tool]["volume_mm3"] += p.solid.volume() * p.quantity
    for t in per_tool.values():
        t["grams"] = round(t["grams"], 2)
        t["extruded_mm3"] = round(t["extruded_mm3"], 1)
        t["volume_mm3"] = round(t["volume_mm3"], 1)

    M, _ = layer_presence(product, h)
    tc = simulate_toolchanges(M)
    purge_g = tc["tool_changes"] * cfg_p["purge_per_toolchange_g"]
    tower_g = (tc["layers_with_changes"] * cfg_p["prime_tower_g_per_layer_with_change"]) if cfg_p["prime_tower"] else 0.0

    extrude_s = sum(per_tool[t]["extruded_mm3"] / mats[per_tool[t]["material"]]["effective_flow_mm3_s"]
                    for t in TOOLS)
    n_objects = len(product.groups())
    time_s = (extrude_s + tc["layers"] * (est["layer_overhead_s"] + est["per_object_per_layer_overhead_s"] * n_objects)
              + tc["tool_changes"] * cfg_p["toolchange_time_s"] + est["heatup_s"]) * est.get("time_calibration", 1.0)

    envs = group_envelopes(product)
    bb = geom.union(envs.values()).bounding_box()
    res = {
        "id": product.id, "stem": product.file_stem, "size": product.size,
        "tools_used": product.tools_used(),
        "per_tool": per_tool,
        "total_part_g": round(sum(t["grams"] for t in per_tool.values()), 2),
        "tool_changes": tc,
        "layer_presence": M,
        "purge_g": round(purge_g, 2),
        "prime_tower_g": round(tower_g, 2),
        "total_material_g": round(sum(t["grams"] for t in per_tool.values()) + purge_g + tower_g, 2),
        "print_time_min": round(time_s / 60, 1),
        "time_breakdown_min": {"extrusion": round(extrude_s / 60, 1),
                               "layer_overhead": round(tc["layers"] * est["layer_overhead_s"] / 60, 1),
                               "tool_changes": round(tc["tool_changes"] * cfg_p["toolchange_time_s"] / 60, 1),
                               "heatup": round(est["heatup_s"] / 60, 1)},
        "plate_bbox_mm": [round(bb[3] - bb[0], 2), round(bb[4] - bb[1], 2), round(bb[5] - bb[2], 2)],
        "object_groups": list(envs),
    }
    if deep:
        dims = config.dims(product.id, product.size)
        res["overhangs"] = {g: overhang_report(e, dims["max_overhang_deg"]) for g, e in envs.items()}
        res["wall_thickness"] = {g: wall_thickness(e) for g, e in envs.items()}
        res["colour_regions_2d"] = colour_region_report(product, dims["min_feature"], dims["min_colour_island_area"])
        res["colour_volumes"] = colour_volume_islands(product)
        res["max_part_overlap_mm3"] = round(pairwise_overlap(product), 4)
        res["watertight"] = {p.name: bool(to_tm(p.solid).is_watertight) for p in product.parts}
        res["fused_tool_contacts"] = contacts(product)
    return res


def to_tm(solid):
    v, f = geom.mesh_arrays(solid)
    return trimesh.Trimesh(v, f, process=False)


# ------------------------------------------------------------------ batch
def batch_plan(product: Product, a: dict) -> dict:
    cfg_p = config.printer()
    est = config.costs()["estimation"]
    batch_cfg = config.costs()["batch"]
    w, d = a["plate_bbox_mm"][0], a["plate_bbox_mm"][1]
    s = cfg_p["object_spacing_mm"]
    bx, by = cfg_p["bed_x_mm"], cfg_p["bed_y_mm"]
    best_fit = 0
    for (pw, pd) in ((w, d), (d, w)):  # allow 90-degree rotation of the plate footprint
        nx = int((bx + s) // (pw + s))
        ny = int((by + s) // (pd + s))
        best_fit = max(best_fit, nx * ny)
    mats = config.materials()
    extrude_s_unit = sum(a["per_tool"][t]["extruded_mm3"] / mats[a["per_tool"][t]["material"]]["effective_flow_mm3_s"]
                         for t in TOOLS)
    n_obj_unit = len(a["object_groups"])
    tc = a["tool_changes"]["tool_changes"]
    layers = a["tool_changes"]["layers"]
    rows = []
    for n in sorted(set(batch_cfg["candidate_sizes"]) | ({best_fit} if best_fit else set())):
        fits = n <= best_fit
        t_s = (extrude_s_unit * n + layers * (est["layer_overhead_s"] + est["per_object_per_layer_overhead_s"] * n_obj_unit * n)
               + tc * config.printer()["toolchange_time_s"] + est["heatup_s"]) * est.get("time_calibration", 1.0)
        purge = a["purge_g"] + a["prime_tower_g"]
        rows.append({"units": n, "fits_bed": fits, "batch_time_h": round(t_s / 3600, 2),
                     "time_per_unit_min": round(t_s / 60 / n, 1),
                     "material_per_batch_g": round(a["total_part_g"] * n + purge, 1),
                     "purge_per_batch_g": round(purge, 2), "purge_per_unit_g": round(purge / n, 3),
                     "waste_fraction": round(purge / (a["total_part_g"] * n + purge), 3)})
    ok = [r for r in rows if r["fits_bed"] and r["batch_time_h"] <= batch_cfg["max_batch_hours"]]
    rec = max(ok, key=lambda r: r["units"])["units"] if ok else 1
    return {"max_units_on_bed": best_fit, "rows": rows, "recommended_batch": rec,
            "bed_mm": [bx, by], "spacing_mm": s}
