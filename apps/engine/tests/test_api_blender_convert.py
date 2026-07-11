from __future__ import annotations

from pathlib import Path

import trimesh
from fastapi.testclient import TestClient


def test_blender_status_shape(client: TestClient) -> None:
    resp = client.get("/api/v1/blender/status")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"detected", "info", "detail"}
    assert isinstance(data["detected"], bool)


def test_capabilities_reports_formats_and_blender(client: TestClient) -> None:
    data = client.get("/api/v1/capabilities").json()
    assert data["features"]["mesh_convert"] is True
    assert "3mf" in data["formats"]["native"]
    assert "fbx" in data["formats"]["with_blender"]
    assert "step" in data["formats"]["cad_pending_phase1"]
    assert isinstance(data["features"]["blender_bridge"], bool)


def test_convert_endpoint_native(client: TestClient, tmp_path: Path) -> None:
    src = tmp_path / "part.stl"
    trimesh.creation.box(extents=(5.0, 5.0, 5.0)).export(str(src))
    dst = tmp_path / "part.3mf"

    resp = client.post(
        "/api/v1/convert",
        json={"srcPath": str(src), "dstPath": str(dst)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["engine"] == "native"
    assert data["srcFormat"] == "stl"
    assert data["dstFormat"] == "3mf"
    assert Path(data["dstPath"]).exists()


def test_convert_endpoint_step_returns_501(client: TestClient, tmp_path: Path) -> None:
    src = tmp_path / "part.stl"
    trimesh.creation.box(extents=(5.0, 5.0, 5.0)).export(str(src))
    resp = client.post(
        "/api/v1/convert",
        json={"srcPath": str(src), "dstPath": str(tmp_path / "part.step")},
    )
    assert resp.status_code == 501
    assert resp.json()["error"]["code"] == "CAPABILITY_NOT_AVAILABLE"


def test_run_script_validates_empty_code(client: TestClient) -> None:
    resp = client.post("/api/v1/blender/run-script", json={"code": "   "})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_REQUEST"


def test_launch_missing_file_rejected(client: TestClient) -> None:
    resp = client.post("/api/v1/blender/launch", json={"file": "C:/definitely/missing.blend"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "FILE_OPERATION_ERROR"
