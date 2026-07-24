"""V-belt pulley template.

Geometry: a rim of outer diameter OD and face width W with a V-groove of depth
GD and mouth width GW cut into the outer surface, and a concentric bore of
diameter B — all formed by revolving one cross-section polygon 360°.

The cross-section (local u = axial, v = radial) runs from the bore radius out to
the rim, with a V-notch at the outer edge; the bore is the inner edge of the
section, so no separate hole feature is needed. Volume has no tidy closed form
(the groove is a revolved notch); the golden test checks it with Pappus's
theorem (V = 2π · r̄ · A) computed from the same section polygon.
"""

from __future__ import annotations

from ..domain.feature_program import (
    FeatureProgram,
    Parameter,
    PolygonProfile,
    RevolveFeature,
    SketchFeature,
)
from . import PartTemplate, TemplateCheck

PARAMETERS: list[Parameter] = [
    Parameter(id="OD", label="Outer diameter", value=40, min=10, max=200, step=1),
    Parameter(id="W", label="Face width", value=12, min=4, max=80, step=0.5),
    Parameter(id="GD", label="Groove depth", value=6, min=1, max=40, step=0.5),
    Parameter(id="GW", label="Groove mouth width", value=8, min=1, max=60, step=0.5),
    Parameter(id="B", label="Bore diameter", value=8, min=1, max=120, step=0.5),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(
        expr="GW - W + 1",
        message="Groove mouth is nearly as wide as the face — widen W or narrow GW",
    ),
    TemplateCheck(
        expr="GD - (OD/2 - B/2) + 1",
        message="Groove root reaches the bore — reduce GD, shrink B, or enlarge OD",
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    # cross-section in local (u = axial, v = radial), CCW, from the bore out
    section = [
        ("0", "B/2"),
        ("W", "B/2"),
        ("W", "OD/2"),
        ("W/2 + GW/2", "OD/2"),  # right lip of the groove mouth
        ("W/2", "OD/2 - GD"),  # groove root (V point)
        ("W/2 - GW/2", "OD/2"),  # left lip of the groove mouth
        ("0", "OD/2"),
    ]
    return FeatureProgram(
        name="V-Belt Pulley",
        parameters=parameters,
        features=[
            SketchFeature(id="section", plane="XY", profile=PolygonProfile(points=section)),
            RevolveFeature(id="body", of="section", angle="360", axis="u"),
        ],
        provenance={"generator": "template:v-pulley", "version": "1"},
    )


V_PULLEY_TEMPLATE = PartTemplate(
    id="v-pulley",
    name="V-Belt Pulley",
    description=(
        "Parametric V-belt pulley: a rim with a V-groove and a concentric bore, "
        "made by revolving one cross-section. Set outer diameter, face width, "
        "groove depth/width, and bore."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
