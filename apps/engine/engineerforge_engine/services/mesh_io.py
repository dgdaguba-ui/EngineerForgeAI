"""Shared mesh loading (trimesh + native 3MF)."""

from __future__ import annotations

from pathlib import Path

import trimesh

from ..domain.errors import EngineError, FileOperationError
from .threemf import read_3mf


class MeshLoadError(EngineError):
    code = "MESH_LOAD_ERROR"
    http_status = 400


def load_mesh(path: str | Path) -> trimesh.Trimesh:
    """Load any supported mesh file as a single (possibly concatenated) Trimesh."""
    src = Path(path)
    if not src.exists():
        raise FileOperationError(f"Mesh file does not exist: {src}")
    if src.suffix.lower() == ".3mf":
        parts = read_3mf(src)
        if not parts:
            raise MeshLoadError(f"No mesh objects found in {src}")
        meshes = [
            trimesh.Trimesh(vertices=p.vertices, faces=p.triangles, process=False)
            for p in parts
        ]
        return meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)
    loaded = trimesh.load(str(src), force="mesh")
    if not isinstance(loaded, trimesh.Trimesh) or loaded.is_empty:
        raise MeshLoadError(f"Could not load a mesh from {src}")
    return loaded
