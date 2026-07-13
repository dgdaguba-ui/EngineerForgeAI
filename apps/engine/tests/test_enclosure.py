"""Shell IR feature + Enclosure template golden tests (M2.1 IR extension).

Same discipline as bracket/plate: compiled B-rep volumes match closed-form
analytic solutions.
"""

from __future__ import annotations

import base64

import numpy as np
import pytest
import trimesh
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel, GeometryError
from engineerforge_engine.domain.feature_program import (
    ExtrudeFeature,
    FeatureProgram,
    RectProfile,
    ShellFeature,
    SketchFeature,
)
from engineerforge_engine.templates.enclosure_box import build as build_enclosure

kernel = CadQueryKernel()


def enclosure_volume(w: float, length: float, h: float, t: float) -> float:
    """Analytic open-top hollow box: outer minus internal cavity."""
    return w * length * h - (w - 2 * t) * (length - 2 * t) * (h - t)


def _watertight(compiled_mesh: object) -> bool:
    positions = np.frombuffer(
        base64.b64decode(compiled_mesh.positions_b64), dtype="<f4"  # type: ignore[attr-defined]
    ).reshape(-1, 3)
    indices = np.frombuffer(
        base64.b64decode(compiled_mesh.indices_b64), dtype="<u4"  # type: ignore[attr-defined]
    ).reshape(-1, 3)
    mesh = trimesh.Trimesh(vertices=positions, faces=indices, process=True)
    mesh.merge_vertices()
    return bool(mesh.is_watertight)


class TestShellFeature:
    def _open_top_box(self, w: float, length: float, h: float, t: float) -> FeatureProgram:
        return FeatureProgram(
            name="box",
            parameters=[],
            features=[
                SketchFeature(id="s", plane="XY", profile=RectProfile(width=w, height=length)),
                ExtrudeFeature(id="e", of="s", distance=h),
                ShellFeature(id="shell", thickness=t, open_faces=["+Z"]),
            ],
        )

    def test_open_top_shell_matches_analytic(self) -> None:
        compiled, _ = kernel.compile(self._open_top_box(80, 60, 40, 3))
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            enclosure_volume(80, 60, 40, 3), rel=1e-9
        )
        assert compiled.mass_props.bbox_mm == {"x": 80, "y": 60, "z": 40}

    def test_closed_shell_is_hollow_but_watertight(self) -> None:
        program = FeatureProgram(
            name="hollow",
            parameters=[],
            features=[
                SketchFeature(id="s", plane="XY", profile=RectProfile(width=40, height=40)),
                ExtrudeFeature(id="e", of="s", distance=40),
                ShellFeature(id="shell", thickness=2, open_faces=[]),  # fully closed shell
            ],
        )
        compiled, _ = kernel.compile(program)
        # closed hollow box: outer minus inner (40-2*2)^3
        expected = 40**3 - 36**3
        assert compiled.mass_props.volume_mm3 == pytest.approx(expected, rel=1e-9)
        assert _watertight(compiled.mesh)

    def test_wall_too_thick_raises_geometry_error(self) -> None:
        # T=25 on a 40-wide box → walls overlap → shell fails
        with pytest.raises(GeometryError, match="shell"):
            kernel.compile(self._open_top_box(40, 40, 40, 25))

    def test_shell_before_solid_raises(self) -> None:
        program = FeatureProgram(
            name="bad",
            parameters=[],
            features=[ShellFeature(id="shell", thickness=2, open_faces=["+Z"])],
        )
        with pytest.raises(GeometryError, match="no solid"):
            kernel.compile(program)


class TestEnclosureTemplate:
    def test_default_matches_analytic_volume(self) -> None:
        # default R=3 → test with R=0 for exact analytic comparison
        compiled, _ = kernel.compile(build_enclosure({"R": 0}))
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            enclosure_volume(100, 70, 40, 3), rel=1e-6
        )
        assert compiled.mass_props.bbox_mm == {"x": 100, "y": 70, "z": 40}

    @pytest.mark.parametrize(
        ("overrides", "expected_args"),
        [
            ({"W": 150, "R": 0}, (150, 70, 40, 3)),
            ({"H": 60, "T": 4, "R": 0}, (100, 70, 60, 4)),
            ({"L": 120, "R": 0}, (100, 120, 40, 3)),
        ],
    )
    def test_parametric_rebuild_tracks_analytic_volume(
        self, overrides: dict[str, float], expected_args: tuple[float, ...]
    ) -> None:
        compiled, _ = kernel.compile(build_enclosure(overrides))
        assert compiled.mass_props.volume_mm3 == pytest.approx(
            enclosure_volume(*expected_args), rel=1e-6
        )

    def test_fillet_reduces_volume_and_stays_watertight(self) -> None:
        flat, _ = kernel.compile(build_enclosure({"R": 0}))
        rounded, _ = kernel.compile(build_enclosure({"R": 8}))
        assert rounded.mass_props.volume_mm3 < flat.mass_props.volume_mm3
        assert _watertight(rounded.mesh)

    def test_default_is_watertight(self) -> None:
        compiled, _ = kernel.compile(build_enclosure({}))
        assert _watertight(compiled.mesh)

    def test_determinism(self) -> None:
        a, _ = kernel.compile(build_enclosure({}))
        b, _ = kernel.compile(build_enclosure({}))
        assert a.mass_props.volume_mm3 == b.mass_props.volume_mm3
        assert a.mesh.positions_b64 == b.mesh.positions_b64
