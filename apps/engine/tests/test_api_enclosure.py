"""API-level coverage for the enclosure template + shell feature."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from test_enclosure import enclosure_volume


def test_enclosure_listed(client: TestClient) -> None:
    templates = client.get("/api/v1/templates").json()
    ids = {t["id"] for t in templates}
    assert {"bracket-l", "mounting-plate", "enclosure-box"} <= ids


def test_create_patch_export_enclosure(client: TestClient, tmp_path: Path) -> None:
    created = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "enclosure-box", "values": {"R": 0}, "materialId": "petg"},
    )
    assert created.status_code == 200
    part = created.json()
    part_id = part["partId"]
    assert part["templateId"] == "enclosure-box"
    assert abs(part["compiled"]["massProps"]["volumeMm3"] - enclosure_volume(100, 70, 40, 3)) < 0.1

    patched = client.patch(f"/api/v1/parts/{part_id}/params", json={"values": {"H": 60}})
    assert patched.status_code == 200
    assert abs(
        patched.json()["compiled"]["massProps"]["volumeMm3"] - enclosure_volume(100, 70, 60, 3)
    ) < 0.1

    step = client.post(
        f"/api/v1/parts/{part_id}/export",
        json={"format": "step", "dstPath": str(tmp_path / "box.step")},
    )
    assert step.status_code == 200
    assert "ISO-10303-21" in Path(step.json()["dstPath"]).read_text(errors="ignore")[:200]


def test_thin_wall_warns(client: TestClient) -> None:
    part = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "enclosure-box", "values": {"T": 1.0, "R": 0}},
    ).json()
    assert any("min wall" in w for w in part["compiled"]["warnings"])


def test_overthick_wall_maps_to_422(client: TestClient) -> None:
    # W=L=20 (min), T=20 (max) → 2T ≥ footprint → shell cannot hollow
    resp = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "enclosure-box", "values": {"W": 20, "L": 20, "T": 20, "R": 0}},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "GEOMETRY_ERROR"
