"""CadQueryKernel — compiles Feature Program IR via CadQuery/OpenCascade.

Notes:
  * `cadquery` is imported lazily inside methods: the import costs ~8s on
    first use and must not slow engine boot or non-CAD requests.
  * All coordinates are CAD-frame millimetres, Z-up. Named-plane extrusion
    normals follow CadQuery: XY→+Z, YZ→+X, XZ→−Y.
  * Volume/CoG come from the exact B-rep (not the tessellation).
"""

from __future__ import annotations

import base64
from typing import Any

import numpy as np

from ...domain.errors import EngineError
from ...domain.expressions import evaluate
from ...domain.feature_program import (
    CompiledPart,
    ExtrudeFeature,
    FeatureProgram,
    FilletFeature,
    GearProfile,
    HoleFeature,
    MassProps,
    RawMesh,
    ShellFeature,
    SketchFeature,
)
from ...ports.cad_kernel import CadKernelPort

TESSELLATION_TOLERANCE = 0.1  # mm — good display quality at printer scale
_GEAR_FLANK_SAMPLES = 12  # involute points per flank
_GEAR_ROOT_SAMPLES = 4  # arc points along the root land between teeth


class GeometryError(EngineError):
    code = "GEOMETRY_ERROR"
    http_status = 422


def gear_outline(module: float, teeth: int, pressure_angle_deg: float) -> list[tuple[float, float]]:
    """Closed involute spur-gear outline as (x, y) points, CCW about the origin.

    Standard full-depth proportions: pitch radius r = m·z/2, base radius
    rb = r·cos(α), addendum ra = r + m, dedendum (root) rf = r − 1.25·m. Each
    tooth flank is an involute of the base circle, sized so the tooth thickness
    at the pitch circle is exactly half the circular pitch. Flanks below the
    base circle drop radially to the root; adjacent teeth are joined by a root
    arc, giving one closed wire the kernel can extrude.
    """
    if teeth < 4:
        raise GeometryError(f"gear needs ≥ 4 teeth (got {teeth})")
    if module <= 0:
        raise GeometryError(f"gear module must be > 0 (got {module})")
    alpha = np.radians(pressure_angle_deg)
    if not 0 < alpha < np.pi / 2:
        raise GeometryError(f"gear pressure angle must be in (0, 90)° (got {pressure_angle_deg})")

    r = module * teeth / 2.0
    rb = r * np.cos(alpha)
    ra = r + module
    rf = max(r - 1.25 * module, 0.1)
    inv_a = np.tan(alpha) - alpha  # involute function at the pressure angle
    half_base = np.pi / (2 * teeth) + inv_a  # half tooth angle at the base circle

    # roll-angle range: from the flank start radius (max of root, base) to tip
    r_start = max(rf, rb)
    u_start = float(np.sqrt(max((r_start / rb) ** 2 - 1.0, 0.0)))
    u_tip = float(np.sqrt((ra / rb) ** 2 - 1.0))
    us = np.linspace(u_start, u_tip, _GEAR_FLANK_SAMPLES)

    def flank(u: float, sign: float) -> tuple[float, float]:
        radius = rb * np.sqrt(1.0 + u * u)
        inv_u = u - np.arctan(u)
        ang = sign * (half_base - inv_u)
        return radius * np.cos(ang), radius * np.sin(ang)

    tooth_pitch = 2 * np.pi / teeth
    points: list[tuple[float, float]] = []
    for k in range(teeth):
        # one tooth built in a tooth-local frame (centreline at angle 0), then
        # rotated into place — avoids a per-iteration closure over the rotation.
        local: list[tuple[float, float]] = []
        if rf < rb:  # root below the base circle: drop the flank in radially
            local.append((rf * np.cos(-half_base), rf * np.sin(-half_base)))
        local.extend(flank(u, -1.0) for u in us)  # left flank: root → tip
        local.extend(flank(u, +1.0) for u in reversed(us))  # right flank: tip → root
        if rf < rb:
            local.append((rf * np.cos(half_base), rf * np.sin(half_base)))
        # root land: arc along rf from this tooth's right root to the next left root
        for j in range(1, _GEAR_ROOT_SAMPLES):
            a = half_base + (tooth_pitch - 2 * half_base) * j / _GEAR_ROOT_SAMPLES
            local.append((rf * np.cos(a), rf * np.sin(a)))

        phi = k * tooth_pitch
        cos_p, sin_p = np.cos(phi), np.sin(phi)
        for x, y in local:
            points.append((float(cos_p * x - sin_p * y), float(sin_p * x + cos_p * y)))
    return points


# (u, v) position axes per drill axis; third component is the drill direction.
_HOLE_FRAME: dict[str, tuple[str, str]] = {"X": ("y", "z"), "Y": ("x", "z"), "Z": ("x", "y")}
_AXIS_VECTORS = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}
# FaceRef → CadQuery face selector string.
_FACE_SELECTOR = {
    "+X": ">X",
    "-X": "<X",
    "+Y": ">Y",
    "-Y": "<Y",
    "+Z": ">Z",
    "-Z": "<Z",
}


class CadQueryKernel(CadKernelPort):
    def compile(self, program: FeatureProgram) -> tuple[CompiledPart, Any]:
        import cadquery as cq  # lazy: heavy import

        values = program.parameter_values()
        sketches: dict[str, SketchFeature] = {}
        solid: Any = None
        warnings: list[str] = []

        for feature in program.features:
            try:
                if isinstance(feature, SketchFeature):
                    sketches[feature.id] = feature
                elif isinstance(feature, ExtrudeFeature):
                    solid = self._extrude(cq, sketches, feature, values, solid)
                elif isinstance(feature, HoleFeature):
                    solid = self._hole(cq, feature, values, solid)
                elif isinstance(feature, FilletFeature):
                    solid, skip_note = self._fillet(cq, feature, values, solid)
                    if skip_note:
                        warnings.append(skip_note)
                elif isinstance(feature, ShellFeature):
                    solid = self._shell(feature, values, solid)
            except GeometryError:
                raise
            except Exception as exc:
                raise GeometryError(
                    f"feature {feature.id!r} ({feature.op}) failed: {exc}"
                ) from exc

        if solid is None:
            raise GeometryError("program produced no solid (needs sketch + extrude)")

        shape = solid.val()
        volume = float(shape.Volume())
        if volume <= 0:
            raise GeometryError("compiled solid has non-positive volume")
        center = shape.Center()
        bb = shape.BoundingBox()

        mesh = self._tessellate(shape)
        compiled = CompiledPart(
            mesh=mesh,
            mass_props=MassProps(
                volume_mm3=round(volume, 3),
                volume_cm3=round(volume / 1000.0, 4),
                cog_mm=(round(center.x, 3), round(center.y, 3), round(center.z, 3)),
                bbox_mm={
                    "x": round(bb.xlen, 3),
                    "y": round(bb.ylen, 3),
                    "z": round(bb.zlen, 3),
                },
            ),
            warnings=warnings,
        )
        return compiled, solid

    # ── feature executors ─────────────────────────────────────────────────────

    def _extrude(
        self,
        cq: Any,
        sketches: dict[str, SketchFeature],
        feature: ExtrudeFeature,
        values: dict[str, float],
        solid: Any,
    ) -> Any:
        sketch = sketches[feature.of]
        wp = cq.Workplane(sketch.plane)
        profile = sketch.profile
        if profile.kind == "rect":
            wp = wp.rect(evaluate(profile.width, values), evaluate(profile.height, values))
        elif profile.kind == "circle":
            wp = wp.circle(evaluate(profile.diameter, values) / 2.0)
        elif profile.kind == "gear":
            wp = wp.polyline(self._gear_points(profile, values)).close()
        else:  # polygon
            points = [
                (evaluate(u, values), evaluate(v, values)) for u, v in profile.points
            ]
            wp = wp.polyline(points).close()
        distance = evaluate(feature.distance, values)
        if distance <= 0:
            raise GeometryError(f"extrude {feature.id}: distance must be > 0")
        body = wp.extrude(distance)
        return body if solid is None else solid.union(body)

    def _gear_points(
        self, profile: GearProfile, values: dict[str, float]
    ) -> list[tuple[float, float]]:
        module = evaluate(profile.module, values)
        teeth = int(round(evaluate(profile.teeth, values)))
        pressure_angle = evaluate(profile.pressure_angle, values)
        return gear_outline(module, teeth, pressure_angle)

    def _hole(
        self, cq: Any, feature: HoleFeature, values: dict[str, float], solid: Any
    ) -> Any:
        if solid is None:
            raise GeometryError(f"hole {feature.id}: no solid to cut yet")
        diameter = evaluate(feature.diameter, values)
        if diameter <= 0:
            raise GeometryError(f"hole {feature.id}: diameter must be > 0")
        count = int(round(evaluate(feature.count, values)))
        if count < 1:
            raise GeometryError(f"hole {feature.id}: count must be ≥ 1")
        spacing = evaluate(feature.spacing, values)
        u = evaluate(feature.u, values)
        v = evaluate(feature.v, values)

        bb = solid.val().BoundingBox()
        axis = feature.axis
        span = {"X": bb.xlen, "Y": bb.ylen, "Z": bb.zlen}[axis] + 2.0
        start = {"X": bb.xmin, "Y": bb.ymin, "Z": bb.zmin}[axis] - 1.0

        u_name, v_name = _HOLE_FRAME[axis]
        # spread axis is always perpendicular to the drill axis (validated),
        # i.e. one of the two position axes; default to the first.
        spread_name = (feature.spread_axis or u_name.upper()).lower()

        for i in range(count):
            offset = (i - (count - 1) / 2.0) * spacing
            coords = {u_name: u, v_name: v, axis.lower(): start}
            coords[spread_name] += offset
            cylinder = cq.Solid.makeCylinder(
                diameter / 2.0,
                span,
                cq.Vector(coords["x"], coords["y"], coords["z"]),
                cq.Vector(*_AXIS_VECTORS[axis]),
            )
            solid = solid.cut(cylinder)
        return solid

    def _fillet(
        self, cq: Any, feature: FilletFeature, values: dict[str, float], solid: Any
    ) -> tuple[Any, str | None]:
        if solid is None:
            raise GeometryError(f"fillet {feature.id}: no solid to fillet yet")
        radius = evaluate(feature.radius, values)
        if radius <= 0:
            return solid, f"fillet {feature.id} skipped (radius ≤ 0)"
        try:
            return solid.edges(f"|{feature.axis}").fillet(radius), None
        except Exception as exc:
            raise GeometryError(
                f"fillet {feature.id} failed at radius {radius}: the radius is too "
                "large for an adjacent wall — opposing edges on a face of thickness t "
                f"allow r < t/2. Reduce the fillet radius. ({exc})"
            ) from exc

    def _shell(
        self, feature: ShellFeature, values: dict[str, float], solid: Any
    ) -> Any:
        if solid is None:
            raise GeometryError(f"shell {feature.id}: no solid to shell yet")
        thickness = evaluate(feature.thickness, values)
        if thickness <= 0:
            raise GeometryError(f"shell {feature.id}: thickness must be > 0")
        before = float(solid.val().Volume())
        selectors = [_FACE_SELECTOR[f] for f in feature.open_faces]
        try:
            if selectors:
                wp = solid.faces(selectors[0])
                for sel in selectors[1:]:
                    wp = wp.add(solid.faces(sel))
                result = wp.shell(-thickness)
            else:
                result = solid.shell(-thickness)
        except Exception as exc:
            raise GeometryError(
                f"shell {feature.id} failed at thickness {thickness}: the wall is likely "
                "too thick for the part's smallest dimension. Reduce the wall thickness. "
                f"({exc})"
            ) from exc
        # CadQuery may silently return the un-hollowed solid when the wall is
        # too thick — guard against that wrong-but-valid result.
        if float(result.val().Volume()) >= before - 1e-6:
            raise GeometryError(
                f"shell {feature.id}: wall thickness {thickness} is too large — no cavity "
                "was produced. Reduce the wall thickness relative to the part's dimensions."
            )
        return result

    # ── output ────────────────────────────────────────────────────────────────

    def _tessellate(self, shape: Any) -> RawMesh:
        vertices, triangles = shape.tessellate(TESSELLATION_TOLERANCE)
        positions = np.asarray(
            [(v.x, v.y, v.z) for v in vertices], dtype="<f4"
        ).reshape(-1)
        indices = np.asarray(triangles, dtype="<u4").reshape(-1)
        return RawMesh(
            positions_b64=base64.b64encode(positions.tobytes()).decode("ascii"),
            indices_b64=base64.b64encode(indices.tobytes()).decode("ascii"),
            vertex_count=len(vertices),
            triangle_count=len(triangles),
        )

    def export_solid(self, native_solid: Any, dst_path: str) -> None:
        import cadquery as cq  # lazy

        cq.exporters.export(native_solid, dst_path)
