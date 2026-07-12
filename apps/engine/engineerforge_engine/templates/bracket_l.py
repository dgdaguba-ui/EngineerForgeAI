"""L-mounting-bracket template — the MVP's first parametric part.

Geometry (CAD frame, Z-up, mm): an L cross-section drawn on the YZ plane and
extruded W along +X. The vertical leg is W×H×T; the horizontal leg W×D×T.
Mounting holes: HC per leg, drilled through each leg's thickness, in a row
along X centered on W/2.

Analytic solid volume (R = 0):
    V = W·T·(H + D − T) − 2·HC·π·(HD/2)²·T
which the kernel golden test asserts against the compiled B-rep.
"""

from __future__ import annotations

from ..domain.feature_program import (
    ExtrudeFeature,
    FeatureProgram,
    FilletFeature,
    HoleFeature,
    Parameter,
    PolygonProfile,
    SketchFeature,
)
from . import PartTemplate, TemplateCheck

PARAMETERS: list[Parameter] = [
    Parameter(id="W", label="Width", value=40, min=10, max=300, step=1),
    Parameter(id="H", label="Height (vertical leg)", value=60, min=10, max=300, step=1),
    Parameter(id="D", label="Depth (horizontal leg)", value=40, min=10, max=300, step=1),
    Parameter(id="T", label="Thickness", value=4, min=1, max=20, step=0.5),
    Parameter(id="HD", label="Hole diameter", value=5, min=1, max=20, step=0.5),
    Parameter(id="R", label="Corner fillet radius", value=0, min=0, max=15, step=0.5),
    Parameter(
        id="HC", label="Holes per leg", value=2, min=1, max=4, step=1, integer=True, unit=""
    ),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(expr="1.2 - T", message="Thickness below 1.2 mm prints poorly (min wall)"),
    TemplateCheck(
        # opposing fillets share each leg's end face → feasible radius < T/2
        expr="R - T / 2",
        message="Fillet radius ≥ T/2 cannot build (opposing fillets share the leg end faces)",
    ),
    TemplateCheck(
        expr="HD * 2 - min(H, D) / 2",
        message="Holes are large relative to the legs — check edge distances",
    ),
    TemplateCheck(
        # spacing = (W − 4·HD)/(HC − 1); holes merge when spacing < 2·HD.
        # The min(HC−1, 1) factor disables the check for a single hole.
        expr="(2 * HD - (W - 4 * HD) / max(HC - 1, 1)) * min(HC - 1, 1)",
        message="Adjacent holes overlap or nearly touch — increase W or reduce HC/HD",
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    return FeatureProgram(
        name="L-Bracket",
        parameters=parameters,
        features=[
            SketchFeature(
                id="profile",
                plane="YZ",
                profile=PolygonProfile(
                    # (u, v) on YZ plane = (global Y, global Z)
                    points=[
                        (0, 0),
                        ("D", 0),
                        ("D", "T"),
                        ("T", "T"),
                        ("T", "H"),
                        (0, "H"),
                    ]
                ),
            ),
            ExtrudeFeature(id="body", of="profile", distance="W"),
            # vertical-leg holes: through thickness (Y), row along X, near the top
            HoleFeature(
                id="holes_vertical",
                axis="Y",
                u="W / 2",
                v="H - 2 * HD",
                diameter="HD",
                count="HC",
                spacing="(W - 4 * HD) / max(HC - 1, 1)",
                spread_axis="X",
            ),
            # horizontal-leg holes: through thickness (Z), row along X, near the front
            HoleFeature(
                id="holes_horizontal",
                axis="Z",
                u="W / 2",
                v="D - 2 * HD",
                diameter="HD",
                count="HC",
                spacing="(W - 4 * HD) / max(HC - 1, 1)",
                spread_axis="X",
            ),
            # fillet along the extrusion axis (inner corner + profile edges)
            FilletFeature(id="corner_fillet", axis="X", radius="R"),
        ],
        provenance={"generator": "template:bracket-l", "version": "1"},
    )


BRACKET_L_TEMPLATE = PartTemplate(
    id="bracket-l",
    name="L-Bracket",
    description=(
        "Parametric L mounting bracket: two perpendicular legs with mounting-hole "
        "rows and an optional corner fillet."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
