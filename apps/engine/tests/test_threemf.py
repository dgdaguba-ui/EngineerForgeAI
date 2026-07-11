from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from engineerforge_engine.services.threemf import Part3MF, read_3mf, write_3mf

CUBE_VERTICES = [
    (0.0, 0.0, 0.0),
    (10.0, 0.0, 0.0),
    (10.0, 10.0, 0.0),
    (0.0, 10.0, 0.0),
    (0.0, 0.0, 10.0),
    (10.0, 0.0, 10.0),
    (10.0, 10.0, 10.0),
    (0.0, 10.0, 10.0),
]
CUBE_TRIANGLES = [
    (0, 2, 1), (0, 3, 2),  # bottom
    (4, 5, 6), (4, 6, 7),  # top
    (0, 1, 5), (0, 5, 4),
    (1, 2, 6), (1, 6, 5),
    (2, 3, 7), (2, 7, 6),
    (3, 0, 4), (3, 4, 7),
]


def cube_part(name: str = "cube", color: str | None = "#ff8800") -> Part3MF:
    return Part3MF(
        name=name,
        vertices=list(CUBE_VERTICES),
        triangles=list(CUBE_TRIANGLES),
        color_hex=color,
        material_name="PLA-Orange" if color else None,
    )


def test_write_then_read_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "part.3mf"
    write_3mf(target, [cube_part()])

    parts = read_3mf(target)
    assert len(parts) == 1
    part = parts[0]
    assert part.name == "cube"
    assert len(part.vertices) == 8
    assert len(part.triangles) == 12
    assert part.color_hex == "#ff8800"
    assert part.material_name == "PLA-Orange"
    # geometry integrity
    assert part.vertices[6] == (10.0, 10.0, 10.0)
    assert all(0 <= i < 8 for tri in part.triangles for i in tri)


def test_multi_part_colors(tmp_path: Path) -> None:
    target = tmp_path / "multi.3mf"
    write_3mf(
        target,
        [
            cube_part("body", "#112233"),
            cube_part("plain", None),
            cube_part("accent", "#AABBCC"),
        ],
    )
    parts = read_3mf(target)
    assert [p.name for p in parts] == ["body", "plain", "accent"]
    assert parts[0].color_hex == "#112233"
    assert parts[1].color_hex is None
    assert parts[2].color_hex == "#aabbcc"  # normalized to lowercase


def test_archive_structure_is_spec_compliant(tmp_path: Path) -> None:
    target = tmp_path / "spec.3mf"
    write_3mf(target, [cube_part()])
    with zipfile.ZipFile(target) as archive:
        names = set(archive.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "3D/3dmodel.model" in names
        model = archive.read("3D/3dmodel.model").decode("utf-8")
        assert 'unit="millimeter"' in model
        assert "basematerials" in model


def test_rejects_empty_input(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_3mf(tmp_path / "x.3mf", [])
    with pytest.raises(ValueError):
        write_3mf(tmp_path / "y.3mf", [Part3MF(name="empty", vertices=[], triangles=[])])


def test_alpha_colors_normalized(tmp_path: Path) -> None:
    target = tmp_path / "alpha.3mf"
    write_3mf(target, [cube_part("a", "#12345678")])
    assert read_3mf(target)[0].color_hex == "#123456"
