"""Counterbored mounting boss template.

Geometry (CAD frame, Z-up, mm): a cylindrical boss (outer diameter OD, height
H) with a concentric through-bore of diameter B and, recessed into the top
face, a counterbore of diameter CB and depth CD (for a screw head to sit
flush). The counterbore is a boolean-cut extrude positioned with a plane offset.

Analytic solid volume (B < CB < OD, CD < H):
    V = π/4 · (OD²·H − B²·H − (CB² − B²)·CD)
"""

from __future__ import annotations

from ..domain.feature_program import (
    CircleProfile,
    ExtrudeFeature,
    FeatureProgram,
    HoleFeature,
    Parameter,
    SketchFeature,
)
from . import PartTemplate, TemplateCheck

PARAMETERS: list[Parameter] = [
    Parameter(id="OD", label="Outer diameter", value=16, min=6, max=80, step=0.5),
    Parameter(id="H", label="Height", value=14, min=4, max=120, step=1),
    Parameter(id="B", label="Bore diameter", value=3.4, min=0.5, max=40, step=0.1),
    Parameter(id="CB", label="Counterbore diameter", value=6.5, min=1, max=70, step=0.1),
    Parameter(id="CD", label="Counterbore depth", value=3.5, min=0.5, max=100, step=0.5),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(
        expr="CB - OD + 1.6",
        message="Counterbore leaves under 0.8 mm of outer wall — widen OD or shrink CB",
    ),
    TemplateCheck(
        expr="B - CB + 0.5",
        message="Bore is not smaller than the counterbore — the head recess has no shoulder",
    ),
    TemplateCheck(
        expr="CD - H + 1",
        message="Counterbore is nearly as deep as the boss — little material left beneath",
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    return FeatureProgram(
        name="Counterbored Boss",
        parameters=parameters,
        features=[
            SketchFeature(id="body_s", plane="XY", profile=CircleProfile(diameter="OD")),
            ExtrudeFeature(id="body", of="body_s", distance="H"),
            HoleFeature(id="bore", axis="Z", u=0, v=0, diameter="B"),
            SketchFeature(id="cbore_s", plane="XY", profile=CircleProfile(diameter="CB")),
            # recess the counterbore into the top face: a cut extrude spanning
            # z = [H − CD, H]
            ExtrudeFeature(
                id="counterbore", of="cbore_s", distance="CD", offset="H - CD", mode="cut"
            ),
        ],
        provenance={"generator": "template:counterbored-boss", "version": "1"},
    )


COUNTERBORED_BOSS_TEMPLATE = PartTemplate(
    id="counterbored-boss",
    name="Counterbored Boss",
    description=(
        "Parametric cylindrical mounting boss with a through-bore and a top "
        "counterbore for a flush screw head. Uses a boolean-cut recess; common "
        "for fastening panels and enclosure lids."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
