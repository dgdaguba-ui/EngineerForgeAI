"""Print preparation estimates — first-order, assumption-transparent.

These are planning numbers, not slicer output: every response carries an
`assumptions` list so the user can judge the confidence. Slicer-grade
estimates arrive with slicer profile integration (roadmap Phase 4/8).
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from ..domain.errors import InvalidRequestError
from ..domain.materials import BuildVolume
from ..services.catalog import material_by_id, printer_by_id
from ..services.mesh_io import load_mesh

# Walls/top/bottom shells consume roughly this solid fraction on top of infill.
WALL_OVERHEAD_FRACTION = 0.15


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UsageEstimate(_CamelModel):
    material_id: str
    volume_cm3: float
    solid_volume_cm3: float
    mass_g: float
    cost: float
    currency: str = "EUR"
    bbox_mm: dict[str, float]
    watertight: bool
    fits_printer: bool | None = None
    printer_id: str | None = None
    orientation_hint: str = ""
    assumptions: list[str]


class PurgeEstimate(_CamelModel):
    printer_id: str
    tool_changes: int
    purge_volume_mm3: float
    purge_mass_g: float
    purge_cost: float
    assumptions: list[str]


def fits_build_volume(bbox_mm: dict[str, float], volume: BuildVolume) -> bool:
    """Axis-aligned fit allowing 90° rotation around Z (swap X/Y)."""
    x, y, z = bbox_mm["x"], bbox_mm["y"], bbox_mm["z"]
    return z <= volume.z and (
        (x <= volume.x and y <= volume.y) or (x <= volume.y and y <= volume.x)
    )


def orientation_hint(bbox_mm: dict[str, float]) -> str:
    """First-order bed-orientation heuristic: lay the flattest side down.

    Larger bed contact and lower height generally mean better adhesion and
    less support. A bbox heuristic cannot see overhang geometry — the slicer
    has the final word (full orientation optimisation is roadmap Phase 5).
    """
    smallest_axis = min(bbox_mm, key=lambda k: bbox_mm[k])
    if smallest_axis == "z":
        return (
            f"Orientation OK: the flattest extent is already the height "
            f"({bbox_mm['z']} mm) — good bed contact."
        )
    return (
        f"Lay flat: rotate so the {smallest_axis.upper()} extent "
        f"({bbox_mm[smallest_axis]} mm) becomes the height — more bed contact, "
        "lower profile, typically less support."
    )


def estimate_from_metrics(
    volume_mm3: float,
    bbox_mm: dict[str, float],
    watertight: bool,
    material_id: str,
    infill: float = 0.2,
    printer_id: str | None = None,
) -> UsageEstimate:
    """Core estimate math over pre-computed geometry metrics.

    Used for mesh files (via :func:`estimate_usage`) and for parametric parts,
    whose exact B-rep volume/bbox come straight from the CAD kernel.
    """
    if not 0.0 <= infill <= 1.0:
        raise InvalidRequestError("infill must be between 0 and 1")
    material = material_by_id(material_id)
    if material is None:
        raise InvalidRequestError(f"unknown material id: {material_id}")

    volume_cm3 = volume_mm3 / 1000.0
    solid_fraction = min(1.0, infill + WALL_OVERHEAD_FRACTION * (1.0 - infill))
    solid_volume_cm3 = volume_cm3 * solid_fraction
    mass_g = solid_volume_cm3 * material.density_g_cm3
    cost = mass_g / 1000.0 * material.cost_per_kg

    assumptions = [
        f"solid fraction = infill ({infill:.0%}) "
        f"+ {WALL_OVERHEAD_FRACTION:.0%} wall/shell overhead",
        "no support material included",
        f"material density {material.density_g_cm3} g/cm³, cost {material.cost_per_kg}/kg",
        "orientation hint is a bounding-box heuristic; the slicer has the final word",
    ]
    if not watertight:
        assumptions.append(
            "mesh is NOT watertight — volume taken from the convex hull (upper bound); "
            "run mesh repair (roadmap Phase 3) for accurate volume"
        )

    fits: bool | None = None
    resolved_printer_id: str | None = None
    if printer_id is not None:
        printer = printer_by_id(printer_id)
        if printer is None:
            raise InvalidRequestError(f"unknown printer id: {printer_id}")
        fits = fits_build_volume(bbox_mm, printer.build_volume)
        resolved_printer_id = printer.id
        assumptions.append("fit check allows rotation about Z only (flat on the bed)")

    return UsageEstimate(
        material_id=material.id,
        volume_cm3=round(volume_cm3, 3),
        solid_volume_cm3=round(solid_volume_cm3, 3),
        mass_g=round(mass_g, 2),
        cost=round(cost, 2),
        bbox_mm=bbox_mm,
        watertight=watertight,
        fits_printer=fits,
        printer_id=resolved_printer_id,
        orientation_hint=orientation_hint(bbox_mm),
        assumptions=assumptions,
    )


def estimate_usage(
    mesh_path: str,
    material_id: str,
    infill: float = 0.2,
    printer_id: str | None = None,
) -> UsageEstimate:
    mesh = load_mesh(mesh_path)
    watertight = bool(mesh.is_watertight)
    volume_mm3 = float(abs(mesh.volume)) if watertight else float(mesh.convex_hull.volume)
    extents = mesh.bounding_box.extents
    bbox = {
        "x": round(float(extents[0]), 2),
        "y": round(float(extents[1]), 2),
        "z": round(float(extents[2]), 2),
    }
    return estimate_from_metrics(
        volume_mm3, bbox, watertight, material_id, infill=infill, printer_id=printer_id
    )


def estimate_purge(
    printer_id: str,
    material_ids: list[str],
    height_mm: float,
    layer_height_mm: float = 0.2,
    changes_per_layer_factor: float = 0.5,
    tool_changes_override: int | None = None,
) -> PurgeEstimate:
    printer = printer_by_id(printer_id)
    if printer is None:
        raise InvalidRequestError(f"unknown printer id: {printer_id}")
    if printer.multi_material_system == "none" or len(set(material_ids)) < 2:
        return PurgeEstimate(
            printer_id=printer.id,
            tool_changes=0,
            purge_volume_mm3=0.0,
            purge_mass_g=0.0,
            purge_cost=0.0,
            assumptions=["single-material job — no purge waste"],
        )
    if height_mm <= 0 or layer_height_mm <= 0:
        raise InvalidRequestError("height_mm and layer_height_mm must be positive")

    materials = []
    for material_id in dict.fromkeys(material_ids):
        material = material_by_id(material_id)
        if material is None:
            raise InvalidRequestError(f"unknown material id: {material_id}")
        materials.append(material)

    if tool_changes_override is not None:
        tool_changes = max(0, tool_changes_override)
        change_assumption = "tool changes provided by caller"
    else:
        layers = math.ceil(height_mm / layer_height_mm)
        tool_changes = math.ceil(layers * (len(materials) - 1) * changes_per_layer_factor)
        change_assumption = (
            f"{layers} layers × ({len(materials)}−1) materials × "
            f"{changes_per_layer_factor} changes/layer factor"
        )

    purge_volume = tool_changes * printer.purge_per_change_mm3
    avg_density = sum(m.density_g_cm3 for m in materials) / len(materials)
    avg_cost_per_kg = sum(m.cost_per_kg for m in materials) / len(materials)
    purge_mass = purge_volume / 1000.0 * avg_density
    purge_cost = purge_mass / 1000.0 * avg_cost_per_kg

    return PurgeEstimate(
        printer_id=printer.id,
        tool_changes=tool_changes,
        purge_volume_mm3=round(purge_volume, 1),
        purge_mass_g=round(purge_mass, 2),
        purge_cost=round(purge_cost, 2),
        assumptions=[
            change_assumption,
            f"{printer.purge_per_change_mm3} mm³ purge per change "
            f"({printer.multi_material_system} system)",
            "mass/cost use the average of the active materials",
            "first-order estimate — the slicer's purge/prime tower will refine this",
        ],
    )
