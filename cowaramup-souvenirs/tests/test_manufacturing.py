"""Tool-change simulation, toolhead requirement handling, 3MF export."""
import zipfile

import numpy as np
import trimesh

from cad.core import analysis, config, export
from cad.core.tools import effective_tools


def test_toolchange_simulation_basic():
    M = np.array([[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 0, 0], [1, 0, 0, 0]], bool)
    r = analysis.simulate_toolchanges(M)
    # L0: T1; L1: T1->T2; L2: stay T2 -> T1; L3: T1 -> 2 changes... greedy keeps current tool first
    assert r["tool_changes"] == 2
    assert r["layers_with_changes"] == 2


def test_single_tool_never_changes():
    assert analysis.simulate_toolchanges(np.ones((50, 1), bool).repeat(4, 1) & [1, 0, 0, 0])["tool_changes"] == 0


def test_batch_amortises_purge(products):
    p = products["CRW-001"]
    a = analysis.analyse(p, deep=False)
    b = analysis.batch_plan(p, a)
    per_unit = [r["purge_per_unit_g"] for r in b["rows"]]
    assert per_unit == sorted(per_unit, reverse=True)


def test_strict_material_requirement_is_reported(products):
    """Mini cow needs a rigid tool 4; with TPU loaded the resolver must flag SETUP and cost it as PLA."""
    th = config.toolheads()
    tools, issues = effective_tools(products["CRW-003"])
    if config.materials()[th["tool_4"]["material"]]["flexible"]:
        assert any(i["level"] == "SETUP" for i in issues)
        assert tools["tool_4"]["material"] == "PLA"


def test_variant_keeps_functional_tpu_colour(products):
    tools, _ = effective_tools(products["CRW-004"], "christmas")
    assert tools["tool_4"]["material"] == "TPU"
    assert tools["tool_4"]["colour"] == config.toolheads()["tool_4"]["colour"]


def test_3mf_round_trip(products, tmp_path):
    p = products["CRW-004"]
    tools, _ = effective_tools(p, "classic")
    f = tmp_path / "t.3mf"
    export.write_3mf(p, f, tools, np.zeros(3), "classic")
    z = zipfile.ZipFile(f)
    assert {"3D/3dmodel.model", "[Content_Types].xml", "_rels/.rels", "Metadata/crw_toolmap.json"} <= set(z.namelist())
    scene = trimesh.load(f)
    assert len(scene.geometry) == len(p.parts)
