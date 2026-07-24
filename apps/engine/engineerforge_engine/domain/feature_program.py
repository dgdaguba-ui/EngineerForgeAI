"""Feature Program IR v1 (`efir/1`) — the editable parametric artifact.

A part is an ordered recipe of features whose numeric fields are expressions
over named parameters (ADR-0002). The AI and the UI edit THIS document; the
CAD kernel compiles it to geometry. Determinism: same program → same solid.

v1 feature set (deliberately small, honestly scoped):
  * sketch      — rect | circle | polygon profile on a principal plane
  * extrude     — extrude a sketch along its plane normal
  * hole        — axis-aligned through-hole(s) with linear count/spacing
  * fillet      — fillet all edges parallel to a principal axis

Not yet in v1 (roadmap Phase 2+): boolean between bodies, patterns as
first-class features, chamfers, shells, face-selected operations.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from .expressions import Expr

EFIR_VERSION: Literal["efir/1"] = "efir/1"

Axis = Literal["X", "Y", "Z"]
PlaneName = Literal["XY", "YZ", "XZ"]
FaceRef = Literal["+X", "-X", "+Y", "-Y", "+Z", "-Z"]
BooleanMode = Literal["union", "cut", "intersect"]

_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Parameter(_CamelModel):
    """A named, user-editable value. Feature expressions reference it by id."""

    id: str
    label: str
    value: float
    unit: str = "mm"
    min: float | None = None
    max: float | None = None
    step: float | None = None
    integer: bool = False

    @field_validator("id")
    @classmethod
    def _valid_id(cls, v: str) -> str:
        if not _ID_RE.match(v):
            raise ValueError(f"parameter id {v!r} must match {_ID_RE.pattern}")
        return v

    @model_validator(mode="after")
    def _range_sane(self) -> Parameter:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"parameter {self.id}: min > max")
        return self

    def clamp_check(self, value: float) -> str | None:
        """Return an error message if value violates this parameter's bounds."""
        if self.integer and value != int(value):
            return f"{self.id} must be an integer"
        if self.min is not None and value < self.min:
            return f"{self.id} must be ≥ {self.min}"
        if self.max is not None and value > self.max:
            return f"{self.id} must be ≤ {self.max}"
        return None


class ParamDiffEntry(_CamelModel):
    """One proposed-but-not-yet-applied parameter change.

    Produced when validating an edit without committing it (e.g. an
    AI-proposed change awaiting user review, M2.2) — never mutates the part.
    """

    param_id: str
    label: str
    old_value: float
    new_value: float
    unit: str


# ── sketch profiles ───────────────────────────────────────────────────────────


class RectProfile(_CamelModel):
    kind: Literal["rect"] = "rect"
    width: Expr
    height: Expr


class CircleProfile(_CamelModel):
    kind: Literal["circle"] = "circle"
    diameter: Expr


class PolygonProfile(_CamelModel):
    kind: Literal["polygon"] = "polygon"
    # closed automatically; points are (u, v) in the sketch plane's local axes
    points: list[tuple[Expr, Expr]] = Field(min_length=3)


class GearProfile(_CamelModel):
    """An external spur-gear tooth outline (involute flanks).

    The kernel expands this into a closed involute-gear polygon at compile time
    from the standard proportions (module, teeth, pressure angle), so the tooth
    count is a live parameter — a fixed polygon can't express that. Standard
    full-depth teeth: addendum = module, dedendum = 1.25·module.
    """

    kind: Literal["gear"] = "gear"
    module: Expr
    teeth: Expr
    pressure_angle: Expr = 20  # degrees


Profile = Annotated[
    RectProfile | CircleProfile | PolygonProfile | GearProfile,
    Field(discriminator="kind"),
]


# ── features ──────────────────────────────────────────────────────────────────


class SketchFeature(_CamelModel):
    op: Literal["sketch"] = "sketch"
    id: str
    plane: PlaneName = "XY"
    profile: Profile


class ExtrudeFeature(_CamelModel):
    """Extrude a sketch along its plane normal (XY→+Z, YZ→+X, XZ→−Y).

    ``offset`` shifts the start of the extrusion along the plane normal (0 =
    start at the sketch plane). A non-zero offset lets a body begin where an
    earlier one ended, so stacked/flanged parts (a lid, a shouldered standoff)
    can be built as unioned extrudes without a boolean feature.
    """

    op: Literal["extrude"] = "extrude"
    id: str
    of: str  # sketch feature id
    distance: Expr
    offset: Expr = 0
    #: how this body combines with the solid so far: union (add), cut (subtract),
    #: or intersect (keep the overlap). The first extrude must be a union.
    mode: BooleanMode = "union"


class RevolveFeature(_CamelModel):
    """Revolve a sketch profile around an in-plane axis to make a solid of revolution.

    ``axis`` is the sketch plane's local axis to spin around — ``"u"`` (the first
    in-plane axis) or ``"v"`` (the second); for an XY sketch, u→X and v→Y. The
    profile must lie entirely on one side of that axis (it may touch it) or the
    revolve self-intersects. ``angle`` in degrees, 0 < angle ≤ 360. Enables
    pulleys, rings, knobs, and other turned parts.
    """

    op: Literal["revolve"] = "revolve"
    id: str
    of: str  # sketch feature id
    angle: Expr = 360
    axis: Literal["u", "v"] = "u"


class HoleFeature(_CamelModel):
    """Axis-aligned through-hole(s).

    Position (u, v) maps per drill axis: X→(y,z), Y→(x,z), Z→(x,y).
    `count` > 1 produces a linear row spread along `spread_axis`
    (perpendicular to the drill axis), centered on (u, v).
    """

    op: Literal["hole"] = "hole"
    id: str
    axis: Axis = "Z"
    u: Expr
    v: Expr
    diameter: Expr
    count: Expr = 1
    spacing: Expr = 0
    spread_axis: Axis | None = None

    @model_validator(mode="after")
    def _spread_perpendicular(self) -> HoleFeature:
        if self.spread_axis is not None and self.spread_axis == self.axis:
            raise ValueError(f"hole {self.id}: spread_axis must differ from drill axis")
        return self


class FilletFeature(_CamelModel):
    """Fillet every edge parallel to `axis`. radius ≤ 0 skips (no-op)."""

    op: Literal["fillet"] = "fillet"
    id: str
    axis: Axis
    radius: Expr


class ChamferFeature(_CamelModel):
    """Chamfer every edge parallel to `axis` by `length`. length ≤ 0 skips (no-op)."""

    op: Literal["chamfer"] = "chamfer"
    id: str
    axis: Axis
    length: Expr


class ShellFeature(_CamelModel):
    """Hollow the current solid, leaving walls of `thickness`.

    Faces named in `open_faces` are removed (e.g. ``["+Z"]`` opens the top,
    producing an open-topped box). An empty list produces a fully closed
    hollow shell. Signed convention: the wall grows inward.
    """

    op: Literal["shell"] = "shell"
    id: str
    thickness: Expr
    open_faces: list[FaceRef] = Field(default_factory=list)


Feature = Annotated[
    SketchFeature
    | ExtrudeFeature
    | RevolveFeature
    | HoleFeature
    | FilletFeature
    | ChamferFeature
    | ShellFeature,
    Field(discriminator="op"),
]


class FeatureProgram(_CamelModel):
    schema_version: Literal["efir/1"] = Field(default=EFIR_VERSION, alias="schema")
    name: str
    units: Literal["mm"] = "mm"
    parameters: list[Parameter] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _structure_valid(self) -> FeatureProgram:
        param_ids = [p.id for p in self.parameters]
        if len(param_ids) != len(set(param_ids)):
            raise ValueError("duplicate parameter ids")
        feature_ids = [f.id for f in self.features]
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError("duplicate feature ids")
        sketch_ids = {f.id for f in self.features if isinstance(f, SketchFeature)}
        for f in self.features:
            if isinstance(f, ExtrudeFeature | RevolveFeature) and f.of not in sketch_ids:
                raise ValueError(f"{f.op} {f.id} references unknown sketch {f.of!r}")
        return self

    def parameter_values(self) -> dict[str, float]:
        return {p.id: p.value for p in self.parameters}

    def parameter_by_id(self, param_id: str) -> Parameter | None:
        return next((p for p in self.parameters if p.id == param_id), None)


# ── compile results ───────────────────────────────────────────────────────────


class RawMesh(_CamelModel):
    """Tessellated triangles for transport: little-endian base64 buffers.

    positions: float32 xyz triplets (CAD frame, Z-up, mm);
    indices: uint32 triangle indices. Normals are computed client-side.
    """

    positions_b64: str
    indices_b64: str
    vertex_count: int
    triangle_count: int


class MassProps(_CamelModel):
    volume_mm3: float
    volume_cm3: float
    mass_g: float | None = None  # solid mass when a material is set
    material_id: str | None = None
    cog_mm: tuple[float, float, float]
    bbox_mm: dict[str, float]  # {"x": …, "y": …, "z": …} extents


class CompiledPart(_CamelModel):
    mesh: RawMesh
    mass_props: MassProps
    warnings: list[str] = Field(default_factory=list)
