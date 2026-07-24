"""Freeform (text-to-CAD) tests: sandboxed execution, service, API, AI tool.

These exercise the real subprocess runner, so they are slower than pure tests
but verify the actual sandbox boundary end to end.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from engineerforge_engine.adapters.cad.cadquery_freeform import (
    CadQueryFreeformRunner,
    FreeformExecutionError,
)
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.application.ai_tools import AiToolbox
from engineerforge_engine.application.freeform_service import FreeformService
from engineerforge_engine.application.parts_service import PartsService
from engineerforge_engine.domain.script_guard import ScriptSecurityError
from engineerforge_engine.templates import default_registry
from fastapi.testclient import TestClient

BOX_WITH_HOLE = (
    "import cadquery as cq\n"
    "result = cq.Workplane('XY').box(30, 20, 10).faces('>Z').workplane().hole(6)\n"
)


@pytest.fixture(scope="module")
def service() -> FreeformService:
    return FreeformService(CadQueryFreeformRunner())


class TestFreeformService:
    def test_generates_real_geometry(self, service: FreeformService) -> None:
        detail = service.generate(BOX_WITH_HOLE, name="Block")
        assert detail.kind == "freeform"
        assert detail.name == "Block"
        expected = 30 * 20 * 10 - math.pi * 3**2 * 10
        assert detail.mass_props.volume_mm3 == pytest.approx(expected, rel=1e-3)
        assert detail.mass_props.bbox_mm == {"x": 30.0, "y": 20.0, "z": 10.0}
        assert detail.mesh.triangle_count > 0
        # retrievable by id
        assert service.get(detail.part_id).part_id == detail.part_id

    def test_rejects_unsafe_script_before_running(self, service: FreeformService) -> None:
        with pytest.raises(ScriptSecurityError):
            service.generate("import os\nresult = os.getcwd()")

    def test_non_solid_result_is_an_execution_error(self, service: FreeformService) -> None:
        with pytest.raises(FreeformExecutionError):
            service.generate("import cadquery as cq\nresult = cq.Workplane('XY')")

    def test_timeout_is_enforced(self, service: FreeformService) -> None:
        # assigns result (unreachable) so the guard passes; the loop hangs
        with pytest.raises(FreeformExecutionError, match="time limit"):
            service.generate("while True:\n    pass\nresult = 1", timeout_s=2)

    def test_export_step_and_stl(self, service: FreeformService, tmp_path: Path) -> None:
        detail = service.generate(BOX_WITH_HOLE)
        step = service.export(detail.part_id, "step", str(tmp_path / "ff.step"))
        assert Path(step.dst_path).exists() and step.size_bytes > 0
        assert "ISO-10303-21" in Path(step.dst_path).read_text(errors="ignore")[:200]
        stl = service.export(detail.part_id, "stl", str(tmp_path / "ff.stl"))
        assert Path(stl.dst_path).stat().st_size > 0


class TestFreeformTool:
    def test_tool_is_offered_and_generates(self) -> None:
        toolbox = AiToolbox(
            PartsService(CadQueryKernel(), default_registry()),
            FreeformService(CadQueryFreeformRunner()),
        )
        names = {d["name"] for d in toolbox.definitions()}
        assert "generate_cad_script" in names

        ok = toolbox.execute("generate_cad_script", {"code": BOX_WITH_HOLE, "name": "Widget"})
        assert ok.action.ok and ok.action.part_id
        assert "Widget" in ok.action.summary

    def test_tool_absent_without_freeform_service(self) -> None:
        toolbox = AiToolbox(PartsService(CadQueryKernel(), default_registry()))
        names = {d["name"] for d in toolbox.definitions()}
        assert "generate_cad_script" not in names

    def test_unsafe_script_reports_failure_not_raises(self) -> None:
        toolbox = AiToolbox(
            PartsService(CadQueryKernel(), default_registry()),
            FreeformService(CadQueryFreeformRunner()),
        )
        result = toolbox.execute("generate_cad_script", {"code": "import os\nresult = 1"})
        assert result.action.ok is False
        assert "rejected" in result.model_output


class TestFreeformApi:
    def test_generate_get_and_export(self, client: TestClient, tmp_path: Path) -> None:
        created = client.post("/api/v1/freeform", json={"code": BOX_WITH_HOLE, "name": "API Box"})
        assert created.status_code == 200
        body = created.json()
        part_id = body["partId"]
        assert body["kind"] == "freeform"
        assert body["massProps"]["bboxMm"]["x"] == 30.0

        fetched = client.get(f"/api/v1/freeform/{part_id}")
        assert fetched.status_code == 200

        exported = client.post(
            f"/api/v1/freeform/{part_id}/export",
            json={"format": "step", "dstPath": str(tmp_path / "api.step")},
        )
        assert exported.status_code == 200

    def test_unsafe_script_maps_to_400(self, client: TestClient) -> None:
        resp = client.post("/api/v1/freeform", json={"code": "import os\nresult = os.getcwd()"})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SCRIPT_REJECTED"

    def test_non_solid_maps_to_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/freeform", json={"code": "import cadquery as cq\nresult = cq.Workplane('XY')"}
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "FREEFORM_ERROR"
