"""Mesh format conversion.

Strategy selection (offline-first):
  * STL/OBJ/PLY/GLB/GLTF ⇄ each other → native (trimesh), no Blender needed;
  * 3MF ⇄ mesh formats → native (our 3MF reader/writer + trimesh);
  * FBX in either direction → Blender (the only supported FBX toolchain);
    FBX ⇄ 3MF routes through a temporary STL hop;
  * STEP/IGES/DXF/SVG → CapabilityNotAvailableError until the CAD kernel
    lands (Phase 1) — an honest error, not a fake conversion.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import trimesh
from pydantic import BaseModel, Field

from ..domain.errors import (
    CapabilityNotAvailableError,
    EngineError,
    FileOperationError,
    InvalidRequestError,
)
from ..ports.blender import BlenderPort
from ..services.threemf import Part3MF, read_3mf, write_3mf

NATIVE_FORMATS = frozenset({"stl", "obj", "ply", "glb", "gltf", "3mf"})
BLENDER_FORMATS = frozenset({"fbx"})
CAD_FORMATS = frozenset({"step", "stp", "iges", "igs", "dxf", "svg"})
SUPPORTED_FORMATS = NATIVE_FORMATS | BLENDER_FORMATS


class ConversionFailedError(EngineError):
    code = "CONVERSION_FAILED"
    http_status = 502


class ConvertResult(BaseModel):
    src_format: str = Field(alias="srcFormat")
    dst_format: str = Field(alias="dstFormat")
    dst_path: str = Field(alias="dstPath")
    engine: str  # "native" | "blender" | "blender+native"
    triangles: int | None = None

    model_config = {"populate_by_name": True}


def format_of(path: str) -> str:
    suffix = Path(path).suffix.lower().lstrip(".")
    if not suffix:
        raise InvalidRequestError(f"cannot infer format from path without extension: {path}")
    return suffix


class ConvertService:
    def __init__(self, blender: BlenderPort) -> None:
        self._blender = blender

    def convert(self, src: str, dst: str, timeout_sec: float = 180) -> ConvertResult:
        src_path, dst_path = Path(src), Path(dst)
        if not src_path.exists():
            raise FileOperationError(f"Source file does not exist: {src}")
        src_fmt, dst_fmt = format_of(src), format_of(dst)

        for fmt in (src_fmt, dst_fmt):
            if fmt in CAD_FORMATS:
                raise CapabilityNotAvailableError(
                    f"{fmt.upper()} conversion requires the CAD kernel "
                    "(roadmap Phase 1); mesh formats available now: "
                    + ", ".join(sorted(SUPPORTED_FORMATS))
                )
            if fmt not in SUPPORTED_FORMATS:
                raise InvalidRequestError(
                    f"Unsupported format '{fmt}'. Supported: "
                    + ", ".join(sorted(SUPPORTED_FORMATS))
                )

        dst_path.parent.mkdir(parents=True, exist_ok=True)

        if src_fmt in NATIVE_FORMATS and dst_fmt in NATIVE_FORMATS:
            triangles = self._convert_native(src_path, dst_path, src_fmt, dst_fmt)
            return ConvertResult(
                src_format=src_fmt,
                dst_format=dst_fmt,
                dst_path=str(dst_path),
                engine="native",
                triangles=triangles,
            )

        # FBX on at least one side → Blender required.
        if self._blender.detect() is None:
            raise CapabilityNotAvailableError(
                "FBX conversion requires a local Blender installation "
                "(none detected; set EFC_BLENDER_PATH if installed)."
            )

        if src_fmt == "3mf" or dst_fmt == "3mf":
            # Blender has no native 3MF I/O — hop through a temporary STL.
            with tempfile.TemporaryDirectory(prefix="efc-convert-") as tmp:
                hop = Path(tmp) / "hop.stl"
                if src_fmt == "3mf":
                    self._convert_native(src_path, hop, "3mf", "stl")
                    self._convert_blender(str(hop), str(dst_path), timeout_sec)
                else:  # fbx → 3mf
                    self._convert_blender(str(src_path), str(hop), timeout_sec)
                    self._convert_native(hop, dst_path, "stl", "3mf")
            return ConvertResult(
                src_format=src_fmt,
                dst_format=dst_fmt,
                dst_path=str(dst_path),
                engine="blender+native",
            )

        self._convert_blender(str(src_path), str(dst_path), timeout_sec)
        return ConvertResult(
            src_format=src_fmt,
            dst_format=dst_fmt,
            dst_path=str(dst_path),
            engine="blender",
        )

    # ── strategies ──────────────────────────────────────────────────────────

    def _load_native(self, src: Path, src_fmt: str) -> trimesh.Trimesh:
        if src_fmt == "3mf":
            parts = read_3mf(src)
            if not parts:
                raise ConversionFailedError(f"No mesh objects found in {src}")
            meshes = [
                trimesh.Trimesh(vertices=p.vertices, faces=p.triangles, process=False)
                for p in parts
            ]
            return meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)
        loaded = trimesh.load(str(src), force="mesh")
        if not isinstance(loaded, trimesh.Trimesh) or loaded.is_empty:
            raise ConversionFailedError(f"Could not load a mesh from {src}")
        return loaded

    def _convert_native(self, src: Path, dst: Path, src_fmt: str, dst_fmt: str) -> int:
        mesh = self._load_native(src, src_fmt)
        if dst_fmt == "3mf":
            write_3mf(
                dst,
                [
                    Part3MF(
                        name=src.stem,
                        vertices=[tuple(v) for v in mesh.vertices.tolist()],
                        triangles=[tuple(f) for f in mesh.faces.tolist()],
                    )
                ],
            )
        else:
            mesh.export(str(dst))
        if not dst.exists():
            raise ConversionFailedError(f"Export produced no file at {dst}")
        return int(len(mesh.faces))

    def _convert_blender(self, src: str, dst: str, timeout_sec: float) -> None:
        result = self._blender.convert(src, dst, timeout_sec=timeout_sec)
        if not result.ok or not Path(dst).exists():
            detail = (result.stderr or result.stdout)[-2000:]
            raise ConversionFailedError(f"Blender conversion failed: {detail}")
