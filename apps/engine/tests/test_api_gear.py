"""API-level coverage for the spur-gear template + GearProfile."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_gear_listed_with_params(client: TestClient) -> None:
    templates = client.get("/api/v1/templates").json()
    gear = next(t for t in templates if t["id"] == "gear")
    param_ids = {p["id"] for p in gear["parameters"]}
    assert {"M", "Z", "T", "B", "PA"} <= param_ids


def test_create_patch_export_gear(client: TestClient, tmp_path: Path) -> None:
    created = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "gear", "values": {"Z": 24}, "materialId": "pla"},
    )
    assert created.status_code == 200
    part = created.json()
    part_id = part["partId"]
    assert part["templateId"] == "gear"
    # bbox spans the addendum circle: 2·(M·Z/2 + M) = M·(Z+2) = 2·26 = 52
    assert abs(part["compiled"]["massProps"]["bboxMm"]["x"] - 52) < 0.1

    # Z is a live parameter — more teeth rebuilds a bigger gear
    patched = client.patch(f"/api/v1/parts/{part_id}/params", json={"values": {"Z": 30}})
    assert patched.status_code == 200
    assert abs(patched.json()["compiled"]["massProps"]["bboxMm"]["x"] - 64) < 0.1

    step = client.post(
        f"/api/v1/parts/{part_id}/export",
        json={"format": "step", "dstPath": str(tmp_path / "gear.step")},
    )
    assert step.status_code == 200
    assert "ISO-10303-21" in Path(step.json()["dstPath"]).read_text(errors="ignore")[:200]


def test_low_tooth_count_warns_undercut(client: TestClient) -> None:
    part = client.post(
        "/api/v1/parts/from-template", json={"templateId": "gear", "values": {"Z": 10}}
    ).json()
    assert any("undercut" in w.lower() for w in part["compiled"]["warnings"])


def test_reorder_and_edit_gear_feature(client: TestClient) -> None:
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "gear"}
    ).json()
    part_id = created["partId"]
    # the gear profile lives on the sketch; the face width is on the extrude
    resp = client.patch(
        f"/api/v1/parts/{part_id}/features/blank", json={"fields": {"distance": 10}}
    )
    assert resp.status_code == 200
    assert resp.json()["compiled"]["massProps"]["bboxMm"]["z"] == 10
