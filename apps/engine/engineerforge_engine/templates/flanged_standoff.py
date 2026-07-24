"""Flanged (shouldered) standoff template.

Geometry (CAD frame, Z-up, mm): a wide round flange of diameter FD and height
FH, with a narrower round shaft of diameter SD and height SH stacked on top via
a plane-offset extrude, and a concentric through-bore of diameter B. The first
template to exercise offset extrudes (stacked bodies).

Analytic solid volume (bore passes through both bodies, B < SD < FD):
    V = π/4 · (FD²·FH + SD²·SH − B²·(FH + SH))
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
    Parameter(id="FD", label="Flange diameter", value=20, min=6, max=80, step=0.5),
    Parameter(id="FH", label="Flange height", value=4, min=1, max=40, step=0.5),
    Parameter(id="SD", label="Shaft diameter", value=10, min=3, max=70, step=0.5),
    Parameter(id="SH", label="Shaft height", value=16, min=2, max=200, step=1),
    Parameter(id="B", label="Bore diameter", value=4.2, min=0.5, max=65, step=0.1),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(
        expr="SD - FD + 1",
        message="Shaft is nearly as wide as the flange — little shoulder to seat against",
    ),
    TemplateCheck(
        expr="B - SD + 1.6",
        message="Bore leaves under 0.8 mm of shaft wall — reduce the bore or widen the shaft",
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    return FeatureProgram(
        name="Flanged Standoff",
        parameters=parameters,
        features=[
            SketchFeature(id="flange_s", plane="XY", profile=CircleProfile(diameter="FD")),
            ExtrudeFeature(id="flange", of="flange_s", distance="FH"),
            SketchFeature(id="shaft_s", plane="XY", profile=CircleProfile(diameter="SD")),
            # stacked on top of the flange via a plane-offset extrude
            ExtrudeFeature(id="shaft", of="shaft_s", distance="SH", offset="FH"),
            HoleFeature(id="bore", axis="Z", u=0, v=0, diameter="B"),
        ],
        provenance={"generator": "template:flanged-standoff", "version": "1"},
    )


FLANGED_STANDOFF_TEMPLATE = PartTemplate(
    id="flanged-standoff",
    name="Flanged Standoff",
    description=(
        "Parametric flanged/shouldered standoff: a wide round flange with a "
        "narrower shaft stacked on top and a concentric through-bore. The "
        "shoulder seats against a panel; common for PCB and panel mounts."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
