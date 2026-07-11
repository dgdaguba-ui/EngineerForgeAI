"""Native 3MF (3D Manufacturing Format) reader/writer — core spec.

Implements the parts of the 3MF core specification needed for print
preparation and FlashPrint-compatible export:

  * one or more mesh objects (vertices + triangles),
  * per-object display color / material name via a `basematerials` group,
  * millimetre units, build items for every object.

Scope notes (documented limitations, not placeholders): object `components`
(instancing), beam lattices, slice extensions, and production-extension UUIDs
are not implemented; readers here reject nothing — unknown elements are
ignored per spec guidance. Writing always produces a spec-valid archive.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
CONTENT_TYPES_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" '
    'ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)
RELS_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>"
)
MODEL_PATH = "3D/3dmodel.model"


@dataclass
class Part3MF:
    """One printable object: triangle mesh + optional material/color."""

    name: str
    vertices: list[tuple[float, float, float]]
    triangles: list[tuple[int, int, int]]
    color_hex: str | None = None  # "#RRGGBB"
    material_name: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


def _normalize_color(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip()
    if not v.startswith("#"):
        return None
    if len(v) == 9:  # #RRGGBBAA → drop alpha
        v = v[:7]
    if len(v) != 7:
        return None
    return v.lower()


def write_3mf(path: str | Path, parts: list[Part3MF], unit: str = "millimeter") -> None:
    if not parts:
        raise ValueError("write_3mf requires at least one part")
    for part in parts:
        if not part.vertices or not part.triangles:
            raise ValueError(f"part '{part.name}' has an empty mesh")

    ET.register_namespace("", CORE_NS)
    model = ET.Element(f"{{{CORE_NS}}}model", {"unit": unit, "xml:lang": "en-US"})
    resources = ET.SubElement(model, f"{{{CORE_NS}}}resources")

    # One basematerials group; each part with material/color gets a base entry.
    material_indices: dict[int, int] = {}  # part index → pindex
    colored = [
        (i, p) for i, p in enumerate(parts) if p.color_hex or p.material_name
    ]
    basematerials_id = 1
    if colored:
        group = ET.SubElement(
            resources, f"{{{CORE_NS}}}basematerials", {"id": str(basematerials_id)}
        )
        for pindex, (part_index, part) in enumerate(colored):
            ET.SubElement(
                group,
                f"{{{CORE_NS}}}base",
                {
                    "name": part.material_name or part.name,
                    "displaycolor": _normalize_color(part.color_hex) or "#b0b0b0",
                },
            )
            material_indices[part_index] = pindex

    first_object_id = 2
    for part_index, part in enumerate(parts):
        attrs = {
            "id": str(first_object_id + part_index),
            "type": "model",
            "name": part.name,
        }
        if part_index in material_indices:
            attrs["pid"] = str(basematerials_id)
            attrs["pindex"] = str(material_indices[part_index])
        obj = ET.SubElement(resources, f"{{{CORE_NS}}}object", attrs)
        mesh = ET.SubElement(obj, f"{{{CORE_NS}}}mesh")
        vertices_el = ET.SubElement(mesh, f"{{{CORE_NS}}}vertices")
        for x, y, z in part.vertices:
            ET.SubElement(
                vertices_el,
                f"{{{CORE_NS}}}vertex",
                {"x": f"{x:.6f}", "y": f"{y:.6f}", "z": f"{z:.6f}"},
            )
        triangles_el = ET.SubElement(mesh, f"{{{CORE_NS}}}triangles")
        for v1, v2, v3 in part.triangles:
            ET.SubElement(
                triangles_el,
                f"{{{CORE_NS}}}triangle",
                {"v1": str(v1), "v2": str(v2), "v3": str(v3)},
            )

    build = ET.SubElement(model, f"{{{CORE_NS}}}build")
    for part_index in range(len(parts)):
        ET.SubElement(
            build, f"{{{CORE_NS}}}item", {"objectid": str(first_object_id + part_index)}
        )

    model_xml = ET.tostring(model, encoding="unicode", xml_declaration=True)

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        archive.writestr("_rels/.rels", RELS_XML)
        archive.writestr(MODEL_PATH, model_xml)


def _find_model_path(archive: zipfile.ZipFile) -> str:
    """Resolve the start-part path from the package relationships."""
    try:
        rels = archive.read("_rels/.rels").decode("utf-8")
        root = ET.fromstring(rels)
        for rel in root.iter():
            if rel.tag.endswith("Relationship"):
                target = rel.attrib.get("Target", "")
                if target.lower().endswith(".model"):
                    return target.lstrip("/")
    except (KeyError, ET.ParseError):
        pass
    return MODEL_PATH


def read_3mf(path: str | Path) -> list[Part3MF]:
    """Read mesh objects (with basematerials colors) from a 3MF archive."""
    with zipfile.ZipFile(path, "r") as archive:
        model_xml = archive.read(_find_model_path(archive)).decode("utf-8")

    root = ET.fromstring(model_xml)
    ns = {"m": CORE_NS}

    # basematerials id → list of (name, color)
    materials: dict[str, list[tuple[str, str | None]]] = {}
    for group in root.findall(".//m:resources/m:basematerials", ns):
        bases: list[tuple[str, str | None]] = []
        for base in group.findall("m:base", ns):
            bases.append(
                (base.attrib.get("name", ""), _normalize_color(base.attrib.get("displaycolor")))
            )
        materials[group.attrib.get("id", "")] = bases

    parts: list[Part3MF] = []
    for obj in root.findall(".//m:resources/m:object", ns):
        mesh = obj.find("m:mesh", ns)
        if mesh is None:
            continue  # components-only objects are out of scope
        vertices: list[tuple[float, float, float]] = []
        for vertex in mesh.findall("m:vertices/m:vertex", ns):
            vertices.append(
                (
                    float(vertex.attrib.get("x", "0")),
                    float(vertex.attrib.get("y", "0")),
                    float(vertex.attrib.get("z", "0")),
                )
            )
        triangles: list[tuple[int, int, int]] = []
        for tri in mesh.findall("m:triangles/m:triangle", ns):
            triangles.append(
                (
                    int(tri.attrib.get("v1", "0")),
                    int(tri.attrib.get("v2", "0")),
                    int(tri.attrib.get("v3", "0")),
                )
            )
        color: str | None = None
        material_name: str | None = None
        pid = obj.attrib.get("pid")
        pindex = obj.attrib.get("pindex")
        if pid is not None and pindex is not None and pid in materials:
            bases = materials[pid]
            idx = int(pindex)
            if 0 <= idx < len(bases):
                material_name, color = bases[idx]
        parts.append(
            Part3MF(
                name=obj.attrib.get("name", f"object-{obj.attrib.get('id', '?')}"),
                vertices=vertices,
                triangles=triangles,
                color_hex=color,
                material_name=material_name,
            )
        )
    return parts
