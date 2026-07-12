from __future__ import annotations

from pathlib import Path

import trimesh
from engineerforge_engine.services.threemf import read_3mf
from fastapi.testclient import TestClient


def test_materials_endpoint(client: TestClient) -> None:
    resp = client.get("/api/v1/materials")
    assert resp.status_code == 200
    data = resp.json()
    ids = {m["id"] for m in data}
    assert "pla" in ids and "pva" in ids
    pla = next(m for m in data if m["id"] == "pla")
    assert pla["densityGCm3"] == 1.24  # camelCase over the wire


def test_printers_endpoint(client: TestClient) -> None:
    data = client.get("/api/v1/printers").json()
    ad5x = next(p for p in data if p["id"] == "flashforge-ad5x")
    assert ad5x["materialSlots"] == 4
    assert ad5x["buildVolume"] == {"x": 220, "y": 220, "z": 220}


def test_compatibility_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/materials/compatibility", json={"materialIds": ["pla", "abs"]}
    )
    assert resp.status_code == 200
    assert resp.json()["worst"] == "incompatible"


def test_estimate_endpoint(client: TestClient, tmp_path: Path) -> None:
    mesh = tmp_path / "cube.stl"
    trimesh.creation.box(extents=(20.0, 20.0, 20.0)).export(str(mesh))
    resp = client.post(
        "/api/v1/print/estimate",
        json={
            "meshPath": str(mesh),
            "materialId": "petg",
            "infill": 0.25,
            "printerId": "flashforge-ad5x",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["volumeCm3"] > 7.9
    assert data["fitsPrinter"] is True
    assert data["massG"] > 0
    assert isinstance(data["assumptions"], list)


def test_purge_estimate_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/print/purge-estimate",
        json={
            "printerId": "flashforge-ad5x",
            "materialIds": ["pla", "pva"],
            "heightMm": 40,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["toolChanges"] == 100


def test_export_3mf_multimaterial(client: TestClient, tmp_path: Path) -> None:
    body_path = tmp_path / "body.stl"
    grip_path = tmp_path / "grip.stl"
    trimesh.creation.box(extents=(30.0, 30.0, 10.0)).export(str(body_path))
    trimesh.creation.box(extents=(10.0, 10.0, 10.0)).export(str(grip_path))
    dst = tmp_path / "job.3mf"

    resp = client.post(
        "/api/v1/export/3mf",
        json={
            "dstPath": str(dst),
            "parts": [
                {
                    "meshPath": str(body_path),
                    "name": "body",
                    "colorHex": "#22d3ee",
                    "materialName": "PETG",
                },
                {
                    "meshPath": str(grip_path),
                    "name": "grip",
                    "colorHex": "#b48bc4",
                    "materialName": "TPU 95A",
                },
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["parts"] == 2
    assert data["sizeBytes"] > 0

    # verify the archive is a valid multi-material 3MF
    parts = read_3mf(dst)
    assert [p.name for p in parts] == ["body", "grip"]
    assert parts[0].color_hex == "#22d3ee"
    assert parts[0].material_name == "PETG"
    assert parts[1].material_name == "TPU 95A"


def test_capabilities_flashforge_features(client: TestClient) -> None:
    features = client.get("/api/v1/capabilities").json()["features"]
    assert features["material_catalog"] is True
    assert features["printer_profiles"] is True
    assert features["print_estimate"] is True
    assert features["multi_material_3mf_export"] is True
