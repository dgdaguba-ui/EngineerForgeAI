"""Round standoff / spacer template.

Geometry (CAD frame, Z-up, mm): a cylinder of outer diameter OD extruded H
along +Z, with a concentric through-bore of diameter ID — a tube. Common as
a PCB standoff or general spacer.

Analytic solid volume:
    V = π/4 · (OD² − ID²) · H
which the kernel golden test asserts against the compiled B-rep.
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
    Parameter(id="OD", label="Outer diameter", value=8, min=3, max=60, step=0.5),
    Parameter(id="ID", label="Bore diameter", value=3.4, min=0.5, max=55, step=0.1),
    Parameter(id="H", label="Height", value=15, min=2, max=200, step=1),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(
        expr="ID - OD + 1",
        message=(
            "Bore diameter leaves under 0.5 mm of wall — reduce the bore or "
            "enlarge the outer diameter"
        ),
    ),
    TemplateCheck(
        expr="1.6 - (OD - ID)",
        message="Wall between bore and outer is thin (<0.8 mm) — may print weak",
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    return FeatureProgram(
        name="Standoff",
        parameters=parameters,
        features=[
            SketchFeature(id="body", plane="XY", profile=CircleProfile(diameter="OD")),
            ExtrudeFeature(id="shaft", of="body", distance="H"),
            HoleFeature(id="bore", axis="Z", u=0, v=0, diameter="ID"),
        ],
        provenance={"generator": "template:standoff", "version": "1"},
    )


STANDOFF_TEMPLATE = PartTemplate(
    id="standoff",
    name="Standoff / Spacer",
    description=(
        "Parametric round standoff/spacer: a cylinder with a concentric "
        "through-bore. Common for PCB mounts and general spacers."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
