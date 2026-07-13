"""Enclosure / project-box template — the first part enabled by the shell IR
feature (M2.1 IR extension).

Geometry (CAD frame, Z-up, mm): a rectangle W (X) × L (Y) centered on the
origin is extruded H along +Z, then hollowed to a wall thickness T with the
top (+Z) face removed — an open-topped box with a solid floor. Vertical outer
corners are optionally filleted (radius R).

Analytic solid volume (R = 0):
    V = W·L·H − (W−2T)(L−2T)(H−T)
(outer box minus the internal cavity: floor of thickness T, open top so the
cavity height is H−T). The kernel golden test asserts this against the
compiled B-rep.
"""

from __future__ import annotations

from ..domain.feature_program import (
    ExtrudeFeature,
    FeatureProgram,
    FilletFeature,
    Parameter,
    RectProfile,
    ShellFeature,
    SketchFeature,
)
from . import PartTemplate, TemplateCheck

PARAMETERS: list[Parameter] = [
    Parameter(id="W", label="Width", value=100, min=20, max=400, step=1),
    Parameter(id="L", label="Length", value=70, min=20, max=400, step=1),
    Parameter(id="H", label="Height", value=40, min=10, max=300, step=1),
    Parameter(id="T", label="Wall thickness", value=3, min=1, max=20, step=0.5),
    Parameter(id="R", label="Corner fillet radius", value=3, min=0, max=40, step=0.5),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(expr="1.2 - T", message="Wall below 1.2 mm prints poorly (min wall)"),
    TemplateCheck(
        expr="2 * T - W + 1",
        message="Walls nearly meet across the width — reduce wall thickness or widen the box",
    ),
    TemplateCheck(
        expr="2 * T - L + 1",
        message="Walls nearly meet across the length — reduce wall thickness or lengthen the box",
    ),
    TemplateCheck(
        expr="T - H + 1",
        message="Wall thickness leaves no usable internal height — increase the height",
    ),
    TemplateCheck(
        expr="R - min(W, L) / 2",
        message="Fillet radius ≥ min(W, L)/2 cannot build — reduce R or enlarge the footprint",
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    return FeatureProgram(
        name="Enclosure",
        parameters=parameters,
        features=[
            SketchFeature(id="footprint", plane="XY", profile=RectProfile(width="W", height="L")),
            ExtrudeFeature(id="body", of="footprint", distance="H"),
            # hollow out, leaving a solid floor and an open top
            ShellFeature(id="cavity", thickness="T", open_faces=["+Z"]),
            # round the four outer vertical corners
            FilletFeature(id="corner_fillet", axis="Z", radius="R"),
        ],
        provenance={"generator": "template:enclosure-box", "version": "1"},
    )


ENCLOSURE_BOX_TEMPLATE = PartTemplate(
    id="enclosure-box",
    name="Enclosure Box",
    description=(
        "Parametric open-top enclosure / project box: hollow walls of a set "
        "thickness, a solid floor, and optional rounded corners."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
