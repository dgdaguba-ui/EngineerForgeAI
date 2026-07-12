from __future__ import annotations

from pathlib import Path

import pytest
import trimesh
from engineerforge_engine.application.convert_service import (
    ConvertService,
    format_of,
)
from engineerforge_engine.domain.blender import BlenderInfo, LaunchResult, ScriptResult
from engineerforge_engine.domain.errors import (
    CapabilityNotAvailableError,
    FileOperationError,
    InvalidRequestError,
)
from engineerforge_engine.ports.blender import BlenderPort


class FakeBlender(BlenderPort):
    """Test double: optionally 'installed'; convert writes a marker file."""

    def __init__(self, installed: bool = True) -> None:
        self.installed = installed
        self.convert_calls: list[tuple[str, str]] = []

    def detect(self) -> BlenderInfo | None:
        return BlenderInfo(executable="fake-blender", version="9.9") if self.installed else None

    def launch(self, file: str | None = None) -> LaunchResult:
        return LaunchResult(pid=1, executable="fake-blender", file=file)

    def run_script(self, code, args=None, timeout_sec=120):  # type: ignore[no-untyped-def]
        raise NotImplementedError

    def convert(self, src: str, dst: str, timeout_sec: float = 180) -> ScriptResult:
        self.convert_calls.append((src, dst))
        # emulate Blender by shuttling geometry through trimesh (or a stub file
        # for formats trimesh cannot write, i.e. FBX)
        if dst.lower().endswith((".stl", ".obj", ".ply", ".glb")):
            trimesh.load(src, force="mesh").export(dst)
        else:
            Path(dst).write_bytes(b"FBX-STUB-CONTENT")
        return ScriptResult(
            ok=True, returncode=0, stdout="EFC_RESULT {}", stderr="", duration_ms=5, result={}
        )


@pytest.fixture
def cube_stl(tmp_path: Path) -> Path:
    mesh = trimesh.creation.box(extents=(10.0, 20.0, 5.0))
    target = tmp_path / "cube.stl"
    mesh.export(str(target))
    return target


def volume_of(path: Path) -> float:
    return float(trimesh.load(str(path), force="mesh").volume)


def test_format_of() -> None:
    assert format_of("C:/x/part.STL") == "stl"
    with pytest.raises(InvalidRequestError):
        format_of("C:/x/noext")


class TestNativeConversions:
    def test_stl_to_obj(self, cube_stl: Path, tmp_path: Path) -> None:
        dst = tmp_path / "out" / "cube.obj"
        result = ConvertService(FakeBlender()).convert(str(cube_stl), str(dst))
        assert result.engine == "native"
        assert result.triangles == 12
        assert dst.exists()
        assert volume_of(dst) == pytest.approx(1000.0, rel=1e-4)

    def test_stl_to_3mf_round_trip_preserves_volume(
        self, cube_stl: Path, tmp_path: Path
    ) -> None:
        service = ConvertService(FakeBlender())
        threemf = tmp_path / "cube.3mf"
        back = tmp_path / "back.stl"
        service.convert(str(cube_stl), str(threemf))
        service.convert(str(threemf), str(back))
        assert volume_of(back) == pytest.approx(volume_of(cube_stl), rel=1e-4)

    def test_glb_to_stl(self, cube_stl: Path, tmp_path: Path) -> None:
        glb = tmp_path / "cube.glb"
        trimesh.load(str(cube_stl), force="mesh").export(str(glb))
        dst = tmp_path / "from_glb.stl"
        result = ConvertService(FakeBlender()).convert(str(glb), str(dst))
        assert result.engine == "native"
        assert volume_of(dst) == pytest.approx(1000.0, rel=1e-3)

    def test_native_path_never_touches_blender(self, cube_stl: Path, tmp_path: Path) -> None:
        blender = FakeBlender(installed=False)  # not even installed
        dst = tmp_path / "cube.ply"
        ConvertService(blender).convert(str(cube_stl), str(dst))
        assert dst.exists()
        assert blender.convert_calls == []


class TestErrorPaths:
    def test_missing_source(self, tmp_path: Path) -> None:
        with pytest.raises(FileOperationError):
            ConvertService(FakeBlender()).convert(
                str(tmp_path / "ghost.stl"), str(tmp_path / "o.obj")
            )

    def test_step_is_capability_error(self, cube_stl: Path, tmp_path: Path) -> None:
        with pytest.raises(CapabilityNotAvailableError, match="feature recognition"):
            ConvertService(FakeBlender()).convert(str(cube_stl), str(tmp_path / "part.step"))

    def test_unknown_format(self, cube_stl: Path, tmp_path: Path) -> None:
        with pytest.raises(InvalidRequestError, match="Unsupported format"):
            ConvertService(FakeBlender()).convert(str(cube_stl), str(tmp_path / "part.xyz"))

    def test_fbx_without_blender(self, cube_stl: Path, tmp_path: Path) -> None:
        with pytest.raises(CapabilityNotAvailableError, match="Blender"):
            ConvertService(FakeBlender(installed=False)).convert(
                str(cube_stl), str(tmp_path / "part.fbx")
            )


class TestBlenderRouting:
    def test_stl_to_fbx_routes_to_blender(self, cube_stl: Path, tmp_path: Path) -> None:
        blender = FakeBlender()
        dst = tmp_path / "cube.fbx"
        result = ConvertService(blender).convert(str(cube_stl), str(dst))
        assert result.engine == "blender"
        assert blender.convert_calls == [(str(cube_stl), str(dst))]
        assert dst.exists()

    def test_3mf_to_fbx_hops_through_stl(self, cube_stl: Path, tmp_path: Path) -> None:
        service = ConvertService(FakeBlender())
        threemf = tmp_path / "cube.3mf"
        service.convert(str(cube_stl), str(threemf))

        blender = FakeBlender()
        service2 = ConvertService(blender)
        dst = tmp_path / "cube.fbx"
        result = service2.convert(str(threemf), str(dst))
        assert result.engine == "blender+native"
        assert len(blender.convert_calls) == 1
        hop_src = blender.convert_calls[0][0]
        assert hop_src.lower().endswith(".stl")  # the temporary hop
        assert dst.exists()

    def test_fbx_to_3mf_hops_through_stl(self, cube_stl: Path, tmp_path: Path) -> None:
        # fabricate an "fbx" that our FakeBlender can read via trimesh: use a
        # real stl renamed — FakeBlender.convert loads with force=mesh, which
        # sniffs content, so this exercises the routing faithfully.
        fbx = tmp_path / "input.fbx"
        fbx.write_bytes(cube_stl.read_bytes())

        blender = FakeBlender()
        # FakeBlender.convert for src=.fbx loads via trimesh: trimesh can't
        # parse "fbx", so patch its convert to copy geometry from the real stl
        original_convert = blender.convert

        def convert_patch(src: str, dst: str, timeout_sec: float = 180) -> ScriptResult:
            return original_convert(str(cube_stl), dst, timeout_sec)

        blender.convert = convert_patch  # type: ignore[method-assign]

        dst = tmp_path / "out.3mf"
        result = ConvertService(blender).convert(str(fbx), str(dst))
        assert result.engine == "blender+native"
        assert dst.exists()
        # verify the produced 3MF is loadable and volumetrically sane
        back = tmp_path / "verify.stl"
        ConvertService(FakeBlender()).convert(str(dst), str(back))
        assert volume_of(back) == pytest.approx(1000.0, rel=1e-3)
