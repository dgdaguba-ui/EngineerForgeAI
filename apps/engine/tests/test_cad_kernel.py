"""CadQuery kernel golden tests.

The strongest correctness proof available for a CAD compiler: compiled
B-rep volumes must match closed-form analytic solutions.
"""

from __future__ import annotations

import base64
import math

import numpy as np
import pytest
import trimesh
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel, GeometryError
from engineerforge_engine.domain.feature_program import (
    CircleProfile,
    ExtrudeFeature,
    FeatureProgram,
    HoleFeature,
    Parameter,
    RawMesh,
    RectProfile,
    SketchFeature,
)
from engineerforge_engine.templates.bracket_l import build as build_bracket

from helpers import bracket_volume

kernel = CadQueryKernel()


def mesh_as_trimesh(mesh: RawMesh) -> trimesh.Trimesh:
    """Decode the transport mesh, merging duplicate vertices.

    OCP tessellation duplicates vertices along face boundaries (intentional —
    it gives correct flat shading in the viewport). Merging makes the soup
    topologically closed so watertightness can be asserted.
    """
    positions = np.frombuffer(base64.b64decode(mesh.positions_b64), dtype="<f4").reshape(-1, 3)
    indices = np.frombuffer(base64.b64decode(mesh.indices_b64), dtype="<u4").reshape(-1, 3)
    merged = trimesh.Trimesh(vertices=positions, faces=indices, process=True)
    merged.merge_vertices()
    return merged


class TestPrimitives:
    def test_rect_extrude_volume_exact(self) -> None:
        program = FeatureProgram(
            name="plate",
            parameters=[
                Parameter(id="W", label="w", value=20),
                Parameter(id="H", label="h", value=30),
                Parameter(id="T", label="t", value=5),
            ],
            features=[
                SketchFeature(
                    id="s", plane="XY", profile=RectProfile(width="W", height="H")
                ),
                ExtrudeFeature(id="e", of="s", distance="T"),
            ],
        )
        compiled, _ = kernel.compile(program)
        assert compiled.mass_props.volume_mm3 == pytest.approx(20 * 30 * 5, rel=1e-9)
        assert compiled.mass_props.bbox_mm == {"x": 20, "y": 30, "z": 5}

    def test_cylinder_volume_exact(self) -> None:
        program = FeatureProgram(
            name="disc",
            parameters=[Parameter(id="D", label="d", value=30)],
            features=[
                SketchFeature(id="s", plane="XY", profile=CircleProfile(diameter="D")),
                ExtrudeFeature(id="e", of="s", distance=8),
            ],
        )
        compiled, _ = kernel.compile(program)
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            math.pi * 15**2 * 8, rel=1e-6
        )

    def test_hole_removes_exact_cylinder(self) -> None:
        program = FeatureProgram(
            name="plate+hole",
            parameters=[],
            features=[
                SketchFeature(
                    id="s", plane="XY", profile=RectProfile(width=40, height=40)
                ),
                ExtrudeFeature(id="e", of="s", distance=6),
                HoleFeature(id="h", axis="Z", u=0, v=0, diameter=10),
            ],
        )
        compiled, _ = kernel.compile(program)
        expected = 40 * 40 * 6 - math.pi * 25 * 6
        assert compiled.mass_props.volume_mm3 == pytest.approx(expected, rel=1e-6)

    def test_hole_row_count_and_spacing(self) -> None:
        def volume_with(count: float) -> float:
            program = FeatureProgram(
                name="row",
                parameters=[Parameter(id="N", label="n", value=count, integer=True)],
                features=[
                    SketchFeature(
                        id="s", plane="XY", profile=RectProfile(width=100, height=20)
                    ),
                    ExtrudeFeature(id="e", of="s", distance=5),
                    HoleFeature(
                        id="h",
                        axis="Z",
                        u=0,
                        v=0,
                        diameter=6,
                        count="N",
                        spacing=20,
                        spread_axis="X",
                    ),
                ],
            )
            compiled, _ = kernel.compile(program)
            return compiled.mass_props.volume_mm3

        hole = math.pi * 9 * 5
        assert volume_with(1) == pytest.approx(100 * 20 * 5 - hole, rel=1e-6)
        assert volume_with(3) == pytest.approx(100 * 20 * 5 - 3 * hole, rel=1e-6)


class TestBracketGolden:
    def test_default_bracket_matches_analytic_volume(self) -> None:
        program = build_bracket({"R": 0})
        compiled, _ = kernel.compile(program)
        expected = bracket_volume(40, 60, 40, 4, 5, 2)
        assert compiled.mass_props.volume_mm3 == pytest.approx(expected, rel=1e-6)
        assert compiled.mass_props.bbox_mm == {"x": 40, "y": 40, "z": 60}

    @pytest.mark.parametrize(
        ("overrides", "expected_args"),
        [
            ({"W": 60, "R": 0}, (60, 60, 40, 4, 5, 2)),
            ({"H": 80, "T": 6, "R": 0}, (40, 80, 40, 6, 5, 2)),
            ({"HC": 3, "R": 0}, (40, 60, 40, 4, 5, 3)),
            ({"HD": 8, "R": 0}, (40, 60, 40, 4, 8, 2)),
        ],
    )
    def test_parametric_rebuild_tracks_analytic_volume(
        self, overrides: dict[str, float], expected_args: tuple[float, ...]
    ) -> None:
        compiled, _ = kernel.compile(build_bracket(overrides))
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            bracket_volume(*expected_args), rel=1e-6
        )

    def test_fillet_changes_volume_and_stays_watertight(self) -> None:
        # opposing fillets share each leg's end face (thickness T=4),
        # so a feasible radius must stay below T/2
        flat, _ = kernel.compile(build_bracket({"R": 0}))
        filleted, _ = kernel.compile(build_bracket({"R": 1.5}))
        assert filleted.mass_props.volume_mm3 != pytest.approx(
            flat.mass_props.volume_mm3, rel=1e-6
        )
        mesh = mesh_as_trimesh(filleted.mesh)
        assert mesh.is_watertight
        assert mesh.volume == pytest.approx(filleted.mass_props.volume_mm3, rel=5e-3)

    def test_tessellation_is_watertight_and_consistent_with_brep(self) -> None:
        compiled, _ = kernel.compile(build_bracket({"R": 0}))
        mesh = mesh_as_trimesh(compiled.mesh)
        assert mesh.is_watertight
        # tessellation volume approximates the exact B-rep volume
        assert mesh.volume == pytest.approx(compiled.mass_props.volume_mm3, rel=5e-3)

    def test_determinism(self) -> None:
        a, _ = kernel.compile(build_bracket({}))
        b, _ = kernel.compile(build_bracket({}))
        assert a.mass_props.volume_mm3 == b.mass_props.volume_mm3
        assert a.mesh.vertex_count == b.mesh.vertex_count
        assert a.mesh.positions_b64 == b.mesh.positions_b64


class TestGeometryErrors:
    def test_oversized_fillet_raises_geometry_error(self) -> None:
        program = build_bracket({"R": 10, "T": 2})  # fillet ≫ thickness
        with pytest.raises(GeometryError, match="fillet"):
            kernel.compile(program)

    def test_program_without_solid(self) -> None:
        program = FeatureProgram(name="empty", parameters=[], features=[])
        with pytest.raises(GeometryError, match="no solid"):
            kernel.compile(program)

    def test_step_export_produces_iso_10303(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        _, solid = kernel.compile(build_bracket({}))
        dst = tmp_path / "bracket.step"
        kernel.export_solid(solid, str(dst))
        head = dst.read_text(encoding="utf-8", errors="ignore")[:200]
        assert "ISO-10303-21" in head
