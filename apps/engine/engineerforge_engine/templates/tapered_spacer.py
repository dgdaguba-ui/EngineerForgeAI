"""Tapered spacer / conical bushing template.

Geometry: a right-circular frustum (base radius R1, top radius R2, height H)
made by revolving a trapezoid profile 360°, with a concentric through-bore of
diameter B. The first template built on the `revolve` feature.

Analytic solid volume (frustum minus bore, R2 > B/2):
    V = π·H·(R1² + R1·R2 + R2²)/3 − π·(B/2)²·H
The revolve axis is the sketch plane's local u-axis, so the part's axis lies
along X; reorient in the viewer if a different up-axis is wanted.
"""

from __future__ import annotations

from ..domain.feature_program import (
    FeatureProgram,
    HoleFeature,
    Parameter,
    PolygonProfile,
    RevolveFeature,
    SketchFeature,
)
from . import PartTemplate, TemplateCheck

PARAMETERS: list[Parameter] = [
    Parameter(id="R1", label="Base radius", value=15, min=3, max=80, step=0.5),
    Parameter(id="R2", label="Top radius", value=10, min=2, max=80, step=0.5),
    Parameter(id="H", label="Height", value=12, min=2, max=150, step=1),
    Parameter(id="B", label="Bore diameter", value=6, min=0.5, max=60, step=0.5),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(
        expr="B - 2*R2 + 1.6",
        message="Bore leaves under 0.8 mm of wall at the narrow end — shrink the bore or widen R2",
    ),
    TemplateCheck(
        expr="R2 - R1 - 0.001",
        message="Top radius ≥ base radius — this widens upward rather than tapering (still valid)",
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    return FeatureProgram(
        name="Tapered Spacer",
        parameters=parameters,
        features=[
            # trapezoid in local (u=axial, v=radial): revolve about u → a frustum
            SketchFeature(
                id="section",
                plane="XY",
                profile=PolygonProfile(
                    points=[("0", "0"), ("0", "R1"), ("H", "R2"), ("H", "0")]
                ),
            ),
            RevolveFeature(id="body", of="section", angle="360", axis="u"),
            HoleFeature(id="bore", axis="X", u=0, v=0, diameter="B"),
        ],
        provenance={"generator": "template:tapered-spacer", "version": "1"},
    )


TAPERED_SPACER_TEMPLATE = PartTemplate(
    id="tapered-spacer",
    name="Tapered Spacer",
    description=(
        "Parametric conical spacer/bushing: a frustum (base radius to top "
        "radius over a height) with a concentric through-bore, made with a "
        "revolve. Use as a tapered standoff, funnel collar, or reducer."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
