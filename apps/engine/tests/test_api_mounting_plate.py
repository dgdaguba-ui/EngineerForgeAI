"""API-level coverage for the mounting-plate template — proves the second
template flows through the same create/patch/export pipeline as the first."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from test_mounting_plate import plate_volume


def test_listed_alongside_bracket(client: TestClient) -> None:
    templates = client.get("/api/v1/templates").json()
    ids = {t["id"] for t in templates}
    assert {"bracket-l", "mounting-plate"} <= ids
    plate = next(t for t in templates if t["id"] == "mounting-plate")
    param_ids = {p["id"] for p in plate["parameters"]}
    assert {"W", "L", "T", "M", "HD", "CD", "R"} <= param_ids


def test_create_patch_and_export(client: TestClient, tmp_path: Path) -> None:
    created = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "mounting-plate", "values": {"R": 0}, "materialId": "pla"},
    )
    assert created.status_code == 200
    part = created.json()
    part_id = part["partId"]
    assert part["templateId"] == "mounting-plate"

    expected = plate_volume(80, 60, 5, 5, 8)
    assert abs(part["compiled"]["massProps"]["volumeMm3"] - expected) < 0.01

    patched = client.patch(f"/api/v1/parts/{part_id}/params", json={"values": {"W": 100}})
    assert patched.status_code == 200
    new_expected = plate_volume(100, 60, 5, 5, 8)
    assert abs(patched.json()["compiled"]["massProps"]["volumeMm3"] - new_expected) < 0.01

    step = client.post(
        f"/api/v1/parts/{part_id}/export",
        json={"format": "step", "dstPath": str(tmp_path / "plate.step")},
    )
    assert step.status_code == 200
    assert "ISO-10303-21" in Path(step.json()["dstPath"]).read_text(errors="ignore")[:200]


def test_oversized_fillet_maps_to_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "mounting-plate", "values": {"W": 40, "L": 40, "R": 25}},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "GEOMETRY_ERROR"


def test_print_estimate_by_part_id(client: TestClient) -> None:
    created = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "mounting-plate", "values": {"R": 0}},
    ).json()
    resp = client.post(
        "/api/v1/print/estimate",
        json={"partId": created["partId"], "materialId": "petg", "printerId": "flashforge-ad5x"},
    )
    assert resp.status_code == 200
    assert resp.json()["fitsPrinter"] is True
