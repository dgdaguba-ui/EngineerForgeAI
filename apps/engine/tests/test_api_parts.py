"""End-to-end API tests for the parametric parts flow — the MVP spine:
template → compile → live param patch → export."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from helpers import bracket_volume


def test_templates_listed(client: TestClient) -> None:
    resp = client.get("/api/v1/templates")
    assert resp.status_code == 200
    templates = resp.json()
    bracket = next(t for t in templates if t["id"] == "bracket-l")
    param_ids = {p["id"] for p in bracket["parameters"]}
    assert {"W", "H", "D", "T", "HD", "R", "HC"} <= param_ids


def test_create_patch_and_mass_flow(client: TestClient) -> None:
    # create with defaults + PETG
    created = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "bracket-l", "values": {"R": 0}, "materialId": "petg"},
    )
    assert created.status_code == 200
    part = created.json()
    part_id = part["partId"]
    assert part["templateId"] == "bracket-l"
    assert part["program"]["schema"] == "efir/1"
    assert part["compiled"]["mesh"]["vertexCount"] > 0

    expected_volume = bracket_volume(40, 60, 40, 4, 5, 2)
    mass_props = part["compiled"]["massProps"]
    assert abs(mass_props["volumeMm3"] - expected_volume) < 0.01
    # solid PETG mass = cm³ × 1.27
    assert abs(mass_props["massG"] - mass_props["volumeCm3"] * 1.27) < 0.05

    # live parametric rebuild: widen the bracket
    patched = client.patch(
        f"/api/v1/parts/{part_id}/params", json={"values": {"W": 60}}
    )
    assert patched.status_code == 200
    new_props = patched.json()["compiled"]["massProps"]
    assert abs(new_props["volumeMm3"] - bracket_volume(60, 60, 40, 4, 5, 2)) < 0.01
    assert new_props["bboxMm"]["x"] == 60

    # GET returns the updated state
    fetched = client.get(f"/api/v1/parts/{part_id}").json()
    assert fetched["program"]["parameters"][0]["value"] == 60


def test_param_validation(client: TestClient) -> None:
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "bracket-l"}
    ).json()
    part_id = created["partId"]

    out_of_range = client.patch(
        f"/api/v1/parts/{part_id}/params", json={"values": {"T": 0.5}}
    )
    assert out_of_range.status_code == 400
    assert "≥" in out_of_range.json()["error"]["message"]

    unknown = client.patch(
        f"/api/v1/parts/{part_id}/params", json={"values": {"NOPE": 1}}
    )
    assert unknown.status_code == 400

    non_integer = client.patch(
        f"/api/v1/parts/{part_id}/params", json={"values": {"HC": 2.5}}
    )
    assert non_integer.status_code == 400


def test_template_checks_surface_warnings(client: TestClient) -> None:
    thin = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "bracket-l", "values": {"T": 1.0, "R": 0}},
    ).json()
    assert any("min wall" in w for w in thin["compiled"]["warnings"])


def test_geometry_error_maps_to_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/parts/from-template",
        json={"templateId": "bracket-l", "values": {"R": 8, "T": 2}},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "GEOMETRY_ERROR"


def test_reorder_features(client: TestClient) -> None:
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "bracket-l", "values": {"R": 0}}
    ).json()
    part_id = created["partId"]
    ids = [f["id"] for f in created["program"]["features"]]
    volume = created["compiled"]["massProps"]["volumeMm3"]

    # swap the two hole rows — geometrically valid, volume unchanged
    v = ids.index("holes_vertical")
    h = ids.index("holes_horizontal")
    reordered = ids.copy()
    reordered[v], reordered[h] = reordered[h], reordered[v]

    resp = client.post(
        f"/api/v1/parts/{part_id}/features/reorder", json={"featureIds": reordered}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [f["id"] for f in body["program"]["features"]] == reordered
    assert abs(body["compiled"]["massProps"]["volumeMm3"] - volume) < 0.01


def test_reorder_rejects_bad_id_set(client: TestClient) -> None:
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "bracket-l"}
    ).json()
    part_id = created["partId"]
    resp = client.post(
        f"/api/v1/parts/{part_id}/features/reorder", json={"featureIds": ["nope"]}
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_REQUEST"


def test_reorder_invalid_geometry_leaves_part_unchanged(client: TestClient) -> None:
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "bracket-l", "values": {"R": 0}}
    ).json()
    part_id = created["partId"]
    ids = [f["id"] for f in created["program"]["features"]]

    # reverse the order → a fillet/hole before the extrude has no solid to act on
    resp = client.post(
        f"/api/v1/parts/{part_id}/features/reorder", json={"featureIds": list(reversed(ids))}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "GEOMETRY_ERROR"

    # the stored part is untouched — original order still compiles/serves
    fetched = client.get(f"/api/v1/parts/{part_id}").json()
    assert [f["id"] for f in fetched["program"]["features"]] == ids


def test_compile_raw_program_round_trip(client: TestClient) -> None:
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "bracket-l", "values": {"R": 0}}
    ).json()
    program = created["program"]

    # a project reopen sends the saved program back verbatim
    recompiled = client.post("/api/v1/parts/compile", json={"program": program})
    assert recompiled.status_code == 200
    body = recompiled.json()
    assert body["templateId"] == "bracket-l"  # provenance restored the template link
    assert (
        body["compiled"]["massProps"]["volumeMm3"]
        == created["compiled"]["massProps"]["volumeMm3"]
    )


def test_exports(client: TestClient, tmp_path: Path) -> None:
    created = client.post(
        "/api/v1/parts/from-template", json={"templateId": "bracket-l", "materialId": "pla"}
    ).json()
    part_id = created["partId"]

    step = client.post(
        f"/api/v1/parts/{part_id}/export",
        json={"format": "step", "dstPath": str(tmp_path / "bracket.step")},
    )
    assert step.status_code == 200
    step_file = Path(step.json()["dstPath"])
    assert "ISO-10303-21" in step_file.read_text(errors="ignore")[:200]

    for fmt in ("stl", "3mf", "obj", "glb"):
        resp = client.post(
            f"/api/v1/parts/{part_id}/export",
            json={"format": fmt, "dstPath": str(tmp_path / f"bracket.{fmt}")},
        )
        assert resp.status_code == 200, fmt
        assert Path(resp.json()["dstPath"]).stat().st_size > 0

    bad = client.post(
        f"/api/v1/parts/{part_id}/export",
        json={"format": "iges", "dstPath": str(tmp_path / "bracket.iges")},
    )
    assert bad.status_code == 400


def test_unknown_part_404_shape(client: TestClient) -> None:
    resp = client.get("/api/v1/parts/doesnotexist")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_REQUEST"


def test_capabilities_reports_cad(client: TestClient) -> None:
    features = client.get("/api/v1/capabilities").json()["features"]
    assert features["cad_kernel"] is True
    assert features["parametric_templates"] is True
    assert features["step_export"] is True
