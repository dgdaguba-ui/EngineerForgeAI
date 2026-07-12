"""M1.4 — parametric print estimates, orientation hint, mixed 3MF export."""

from __future__ import annotations

from pathlib import Path

import trimesh
from engineerforge_engine.application.print_service import orientation_hint
from engineerforge_engine.services.threemf import read_3mf
from fastapi.testclient import TestClient


class TestOrientationHint:
    def test_flat_already(self) -> None:
        hint = orientation_hint({"x": 40, "y": 60, "z": 4})
        assert "Orientation OK" in hint

    def test_suggests_laying_flat(self) -> None:
        hint = orientation_hint({"x": 4, "y": 60, "z": 40})
        assert "Lay flat" in hint and "X" in hint


class TestParametricEstimate:
    def test_estimate_by_part_id_uses_exact_brep_metrics(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/parts/from-template",
            json={"templateId": "bracket-l", "values": {"R": 0}},
        ).json()
        part_id = created["partId"]
        exact_volume_cm3 = created["compiled"]["massProps"]["volumeCm3"]

        resp = client.post(
            "/api/v1/print/estimate",
            json={
                "partId": part_id,
                "materialId": "petg",
                "infill": 0.2,
                "printerId": "flashforge-ad5x",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # kernel rounds cm³ to 4 decimals, estimate to 3 — same underlying value
        assert abs(data["volumeCm3"] - exact_volume_cm3) < 0.001
        assert data["watertight"] is True
        assert data["fitsPrinter"] is True
        assert data["orientationHint"]
        # bracket 40×40×60: smallest extent is X/Y → suggests laying flat
        assert "Lay flat" in data["orientationHint"] or "Orientation OK" in data["orientationHint"]

    def test_one_of_mesh_or_part_enforced(self, client: TestClient, tmp_path: Path) -> None:
        mesh = tmp_path / "c.stl"
        trimesh.creation.box(extents=(5, 5, 5)).export(str(mesh))
        both = client.post(
            "/api/v1/print/estimate",
            json={"meshPath": str(mesh), "partId": "x", "materialId": "pla"},
        )
        assert both.status_code == 400
        neither = client.post("/api/v1/print/estimate", json={"materialId": "pla"})
        assert neither.status_code == 400

    def test_mesh_path_still_works_with_hint(self, client: TestClient, tmp_path: Path) -> None:
        mesh = tmp_path / "plate.stl"
        trimesh.creation.box(extents=(60, 40, 3)).export(str(mesh))
        data = client.post(
            "/api/v1/print/estimate",
            json={"meshPath": str(mesh), "materialId": "pla"},
        ).json()
        assert "Orientation OK" in data["orientationHint"]


class TestMixed3mfExport:
    def test_parametric_and_mesh_parts_in_one_job(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        created = client.post(
            "/api/v1/parts/from-template", json={"templateId": "bracket-l"}
        ).json()
        mesh_file = tmp_path / "grip.stl"
        trimesh.creation.box(extents=(10, 10, 10)).export(str(mesh_file))
        dst = tmp_path / "job.3mf"

        resp = client.post(
            "/api/v1/export/3mf",
            json={
                "dstPath": str(dst),
                "parts": [
                    {
                        "partId": created["partId"],
                        "name": "bracket",
                        "colorHex": "#22d3ee",
                        "materialName": "PETG",
                    },
                    {
                        "meshPath": str(mesh_file),
                        "name": "grip",
                        "colorHex": "#b48bc4",
                        "materialName": "TPU 95A",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        parts = read_3mf(dst)
        assert [p.name for p in parts] == ["bracket", "grip"]
        assert len(parts[0].triangles) == created["compiled"]["mesh"]["triangleCount"]

    def test_part_entry_one_of_enforced(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post(
            "/api/v1/export/3mf",
            json={
                "dstPath": str(tmp_path / "x.3mf"),
                "parts": [{"name": "bad"}],
            },
        )
        assert resp.status_code == 400
