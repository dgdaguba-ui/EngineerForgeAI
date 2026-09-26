"""Exporters: STL (geometry interchange), 3MF (production: parts + colours +
tool map), OpenSCAD assembly (.scad viewer that colours the per-tool STLs).

3MF is written by hand against the 3MF Core Specification (2015/02) with a
<basematerials> group so every part carries its colour. Each object group
becomes ONE multi-part object (<components>), which is how slicers keep
per-part extruder assignments aligned. The tool map is also stored as
Metadata/crw_toolmap.json inside the package.

What is NOT written: slicer-specific project settings (e.g. per-volume
extruder numbers in PrusaSlicer/Orca/Bambu config XML). Those formats are
undocumented/vendor-specific and could not be verified here, so the operator
maps the four named parts to extruders once in the slicer (names start with
T1..T4).
"""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import trimesh

from . import geom
from .model import TOOLS, Product

NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"


def tidy(solid: geom.Manifold, min_volume: float = 0.01) -> geom.Manifold:
    """Drop zero-volume slivers left by boolean chains."""
    comps = solid.decompose()
    keep = [c for c in comps if c.volume() >= min_volume]
    if len(keep) == len(comps):
        return solid
    return geom.Manifold.compose(keep) if keep else geom.Manifold()


def clean_mesh(solid: geom.Manifold, collapse: float = 0.0) -> geom.Manifold:
    """Final export cleanup: drop zero-volume shells and optionally collapse
    sub-`collapse` mm edges (used for merged single-colour meshes, where fused
    colour interfaces leave micron-scale edges that vertex-welding readers
    would turn into non-manifold edges). Parts are left exact so they stay
    perfectly disjoint."""
    solid = tidy(solid)
    if collapse > 0:
        solid = solid.simplify(collapse)
    # weld only meshes that actually need it: welding moves vertices, which would break the
    # exactly-shared boundaries of the edge-matched (sandwich) products
    return weld(solid) if len(pinch_points(solid)) else solid


def weld(solid: geom.Manifold, q: float = 5e-4) -> geom.Manifold:
    """Merge vertices closer than q mm (KD-tree + union-find), drop collapsed triangles
    and re-verify manifoldness. Removes the micron edges booleans leave behind, which a
    float32 STL reader would otherwise weld into non-manifold edges. Falls back to the
    input if the welded mesh is not a valid manifold."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree

    from . import sdf as _sdf
    v, f = geom.mesh_arrays(solid)
    if len(f) == 0:
        return solid
    pairs = cKDTree(v).query_pairs(q, output_type="ndarray")
    if len(pairs) == 0:
        return solid
    n = len(v)
    graph = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    _, inv = connected_components(graph, directed=False)
    nv = np.zeros((inv.max() + 1, 3))
    np.add.at(nv, inv, v)
    nv /= np.bincount(inv)[:, None]
    nf = inv[f]
    ok = (nf[:, 0] != nf[:, 1]) & (nf[:, 1] != nf[:, 2]) & (nf[:, 0] != nf[:, 2])
    nf = nf[ok]
    # remove face pairs that became identical (opposite windings cancel)
    srt = np.sort(nf, axis=1)
    _, first, cnt = np.unique(srt, axis=0, return_index=True, return_counts=True)
    nf = nf[np.sort(first[cnt == 1])]
    try:
        out = _sdf.to_manifold(nv, nf)
    except Exception:
        return solid
    if abs(out.volume() - solid.volume()) > 1e-3 * max(abs(solid.volume()), 1.0):
        return solid
    return out


def plate_offset(product: Product, bed_xy=None) -> np.ndarray:
    """Translation that centres the plate on the XY origin with min z = 0.

    Vertices stay near the origin on purpose: STL stores float32, and at ~125 mm
    (a bed centre) float32 spacing is ~8 um, enough to weld distinct vertices into
    non-manifold edges. The 3MF places the plate on the bed with a build-item
    transform instead."""
    bb = geom.union(p.solid for p in product.parts).bounding_box()
    cx, cy = (bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2
    return np.array([-cx, -cy, -bb[2]])


def to_trimesh(solid: geom.Manifold, offset=None) -> trimesh.Trimesh:
    v, f = geom.mesh_arrays(solid)
    if offset is not None:
        v = v + offset
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


def write_stl(solid: geom.Manifold, path: Path, offset=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    to_trimesh(solid, offset).export(path, file_type="stl")


def part_label(part, tools: dict) -> str:
    t = tools[part.tool]
    n = TOOLS.index(part.tool) + 1
    return f"T{n} {part.name} [{t['material']} {t['colour_name']}] - {part.feature}"[:250]


def write_3mf(product: Product, path: Path, tools: dict, offset, variant: str | None = None, bed_xy=None):
    """tools = config.tool_assignment(variant). bed_xy -> build items placed at the bed centre."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = io.StringIO()
    w = out.write
    w('<?xml version="1.0" encoding="UTF-8"?>\n')
    w(f'<model unit="millimeter" xml:lang="en-US" xmlns="{NS}">\n')
    meta = {
        "Title": f"{product.id} {product.name}" + (f" ({variant})" if variant else ""),
        "Designer": "Cowaramup Souvenir Factory",
        "Description": product.description,
        "Application": "cowaramup-souvenirs/scripts/generate.py",
        "LicenseTerms": "Original design - all rights reserved",
    }
    for k, v in meta.items():
        w(f'  <metadata name="{k}">{escape(v)}</metadata>\n')
    w("  <resources>\n")
    w('    <basematerials id="1">\n')
    for t in TOOLS:
        info = tools[t]
        w(f'      <base name="{escape(t + " " + info["colour_name"] + " " + info["material"])}" '
          f'displaycolor="{info["hex"].upper()}FF"/>\n')
    w("    </basematerials>\n")
    next_id = 2
    group_ids = []
    toolmap = {"product": product.id, "variant": variant, "tools": tools, "objects": []}
    for group, parts in product.groups().items():
        comp_ids = []
        for part in parts:
            if part.solid.is_empty():
                continue
            v, f = geom.mesh_arrays(part.solid)
            v = v + offset
            oid = next_id
            next_id += 1
            comp_ids.append(oid)
            pindex = TOOLS.index(part.tool)
            w(f'    <object id="{oid}" type="model" name="{escape(part_label(part, tools))}" pid="1" pindex="{pindex}">\n')
            w("      <mesh>\n        <vertices>\n")
            w("".join(f'          <vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>\n' for x, y, z in v))
            w("        </vertices>\n        <triangles>\n")
            w("".join(f'          <triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in f))
            w("        </triangles>\n      </mesh>\n    </object>\n")
            toolmap["objects"].append({"id": oid, "group": group, "part": part.name, "tool": part.tool,
                                       "extruder": pindex + 1, "feature": part.feature,
                                       "requires": part.requires})
        gid = next_id
        next_id += 1
        group_ids.append(gid)
        w(f'    <object id="{gid}" type="model" name="{escape(product.id + " " + group)}">\n      <components>\n')
        for cid in comp_ids:
            w(f'        <component objectid="{cid}"/>\n')
        w("      </components>\n    </object>\n")
    w("  </resources>\n  <build>\n")
    tf = f' transform="1 0 0 0 1 0 0 0 1 {bed_xy[0] / 2:.3f} {bed_xy[1] / 2:.3f} 0"' if bed_xy else ""
    for gid in group_ids:
        w(f'    <item objectid="{gid}"{tf}/>\n')
    w("  </build>\n</model>\n")

    content_types = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                     '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                     '  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
                     '  <Default Extension="json" ContentType="application/json"/>\n'
                     '</Types>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            '</Relationships>\n')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", out.getvalue())
        z.writestr("Metadata/crw_toolmap.json", json.dumps(toolmap, indent=2, default=str))


def write_scad(product: Product, path: Path, part_files: dict, tools: dict):
    """OpenSCAD assembly: imports the per-tool STLs with preview colours.
    For viewing / re-exporting only - the geometry source of truth is Python."""
    lines = [f"// {product.id} {product.name}",
             "// Generated by scripts/generate.py - DO NOT EDIT (edit cad/products/*.py instead).",
             "// Each import() is one toolhead region; colours follow the default tool assignment.",
             "// Set SHOW_TOOL = 1..4 to isolate a single toolhead, 0 = all.",
             "SHOW_TOOL = 0;", ""]
    for part_name, rel in part_files.items():
        part = next(p for p in product.parts if p.name == part_name)
        n = TOOLS.index(part.tool) + 1
        hx = tools[part.tool]["hex"].lstrip("#")
        rgb = ", ".join(f"{int(hx[i:i + 2], 16) / 255:.3f}" for i in (0, 2, 4))
        lines.append(f"// T{n} {tools[part.tool]['material']} {tools[part.tool]['colour_name']}: {part.feature}")
        lines.append(f'if (SHOW_TOOL == 0 || SHOW_TOOL == {n}) color([{rgb}]) import("{rel}", convexity = 10);')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_glb(product: Product, path: Path, tools: dict, offset, rot=None):
    """glTF binary for Blender / web viewers: one named node per part, PBR colour per tool.
    glTF is metre-based, so millimetres are scaled by 0.001 (true size in Blender).
    `rot` (degrees, xyz) optionally stands the model in its display orientation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    scene = trimesh.Scene()
    for part in product.parts:
        solid = part.solid.translate(list(offset))
        if rot:
            solid = solid.rotate(rot)
        tm = to_trimesh(solid)
        tm.apply_scale(0.001)
        # model is Z-up; glTF is Y-up (Blender's importer converts back to Z-up)
        tm.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
        hx = tools[part.tool]["hex"].lstrip("#")
        rgba = [int(hx[i:i + 2], 16) for i in (0, 2, 4)] + [255]
        mat = trimesh.visual.material.PBRMaterial(
            name=f"T{TOOLS.index(part.tool) + 1}_{tools[part.tool]['material']}_{tools[part.tool]['colour']}",
            baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.6)
        tm.visual = trimesh.visual.TextureVisuals(material=mat)
        scene.add_geometry(tm, node_name=part_label(part, tools)[:60], geom_name=f"{part.object_group}_{part.name}")
    scene.export(path, file_type="glb")


def pinch_points(solid: geom.Manifold) -> np.ndarray:
    """Positions where a float32 / position-welded reader sees non-manifold edges."""
    v, f = geom.mesh_arrays(solid)
    v32 = v.astype(np.float32).astype(np.float64)
    key = np.round(v32 / 1e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    nf = inv.ravel()[f]
    e = np.sort(np.vstack([nf[:, [0, 1]], nf[:, [1, 2]], nf[:, [2, 0]]]), axis=1)
    u, idx, cnt = np.unique(e, axis=0, return_index=True, return_counts=True)
    bad = cnt != 2
    if not bad.any():
        return np.zeros((0, 3))
    edges_first = np.vstack([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])[idx[bad]]
    return (v[edges_first[:, 0]] + v[edges_first[:, 1]]) / 2


def repair_pinches(parts, radius: float = 0.22, rounds: int = 4):
    """Bridge every pinch (two lobes of one part touching along an edge) with a small
    ball of the SAME part, taken from its neighbours, then re-weld. A 0.2 mm bridge is
    below nozzle resolution - it only changes topology, not appearance."""
    for _ in range(rounds):
        changed = False
        for p in parts:
            pts = pinch_points(p.solid)
            if len(pts) == 0:
                continue
            keep = []
            for q in pts:
                if all(np.linalg.norm(q - k) > radius for k in keep):
                    keep.append(q)
            balls = geom.union(geom.Manifold.sphere(radius, 16).translate(list(q)) for q in keep)
            env = geom.union(o.solid for o in parts if o.object_group == p.object_group)
            balls = balls ^ env
            for o in parts:
                if o is not p and o.object_group == p.object_group:
                    o.solid = weld(o.solid - balls)
            p.solid = weld(p.solid + balls)
            changed = True
        if not changed:
            break
    return parts
