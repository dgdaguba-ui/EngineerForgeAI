"""Mounting/adapter plate template — a rectangular plate with a symmetric
corner-hole pattern and an optional center bore.

Geometry (CAD frame, Z-up, mm): a rectangle W (X) × L (Y) centered on the
origin, extruded T along +Z. CadQuery's `Workplane.rect()` centers the
profile on the workplane origin, so the plate spans x∈[-W/2, W/2],
y∈[-L/2, L/2] — every hole position below is expressed in that frame.

Four corner holes (diameter HD) sit inset by margin M from each edge;
two HoleFeature rows (top pair, bottom pair) each spread a 2-hole count
along X, reusing the same linear-row mechanism as the L-bracket. A single
center bore (diameter CD) sits at the origin. Corners are optionally
filleted (radius R) — the plate's vertical edges are parallel to Z, so
FilletFeature(axis="Z") rounds exactly the four corners.

Analytic solid volume (R = 0, holes non-overlapping):
    V = W·L·T − 4·π·(HD/2)²·T − π·(CD/2)²·T
which the kernel golden test asserts against the compiled B-rep.
"""

from __future__ import annotations

from ..domain.feature_program import (
    ExtrudeFeature,
    FeatureProgram,
    FilletFeature,
    HoleFeature,
    Parameter,
    RectProfile,
    SketchFeature,
)
from . import PartTemplate, TemplateCheck

PARAMETERS: list[Parameter] = [
    Parameter(id="W", label="Width", value=80, min=20, max=400, step=1),
    Parameter(id="L", label="Length", value=60, min=20, max=400, step=1),
    Parameter(id="T", label="Thickness", value=5, min=1, max=25, step=0.5),
    Parameter(id="M", label="Corner hole margin", value=8, min=3, max=50, step=1),
    Parameter(id="HD", label="Corner hole diameter", value=5, min=1, max=25, step=0.5),
    Parameter(id="CD", label="Center bore diameter", value=8, min=1, max=100, step=0.5),
    Parameter(id="R", label="Corner fillet radius", value=0, min=0, max=40, step=0.5),
]

CHECKS: list[TemplateCheck] = [
    TemplateCheck(expr="1.2 - T", message="Thickness below 1.2 mm prints poorly (min wall)"),
    TemplateCheck(
        # box-corner fillets self-intersect once R exceeds half the shorter side
        expr="R - min(W, L) / 2",
        message="Fillet radius ≥ min(W, L)/2 cannot build — reduce R or enlarge the plate",
    ),
    TemplateCheck(
        expr="HD / 2 - M",
        message="Corner hole diameter exceeds the edge margin — the hole would breach the edge",
    ),
    TemplateCheck(
        # conservative separation check along the shorter half-span: corner-hole
        # center to plate-center distance ≥ sum of the two hole radii
        expr="HD / 2 + CD / 2 - (min(W, L) / 2 - M)",
        message=(
            "Corner holes and the center bore are too close — increase margin "
            "or reduce diameters"
        ),
    ),
]


def build(values: dict[str, float]) -> FeatureProgram:
    """Pure parameters→program mapping. `values` may override defaults."""
    parameters = [
        p.model_copy(update={"value": float(values.get(p.id, p.value))}) for p in PARAMETERS
    ]
    return FeatureProgram(
        name="Mounting Plate",
        parameters=parameters,
        features=[
            SketchFeature(id="profile", plane="XY", profile=RectProfile(width="W", height="L")),
            ExtrudeFeature(id="body", of="profile", distance="T"),
            # top corner pair: y = L/2 - M, x = ±(W/2 - M)
            HoleFeature(
                id="corner_holes_top",
                axis="Z",
                u=0,
                v="L / 2 - M",
                diameter="HD",
                count=2,
                spacing="W - 2 * M",
                spread_axis="X",
            ),
            # bottom corner pair: y = -(L/2 - M)
            HoleFeature(
                id="corner_holes_bottom",
                axis="Z",
                u=0,
                v="-(L / 2 - M)",
                diameter="HD",
                count=2,
                spacing="W - 2 * M",
                spread_axis="X",
            ),
            HoleFeature(id="center_bore", axis="Z", u=0, v=0, diameter="CD"),
            # fillet the four vertical corner edges
            FilletFeature(id="corner_fillet", axis="Z", radius="R"),
        ],
        provenance={"generator": "template:mounting-plate", "version": "1"},
    )


MOUNTING_PLATE_TEMPLATE = PartTemplate(
    id="mounting-plate",
    name="Mounting Plate",
    description=(
        "Parametric rectangular adapter/mounting plate: four symmetric corner "
        "holes, a center bore, and optional rounded corners."
    ),
    parameters=PARAMETERS,
    build=build,
    checks=CHECKS,
)
