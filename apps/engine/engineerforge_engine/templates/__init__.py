"""Parametric part templates — the deterministic core of AI CAD.

A template maps a validated parameter set to a Feature Program (pure
function, golden-tested). The AI's job for known part types is only to pick
a template and fill parameters — which is easy to validate (ADR-0002/0003).
Templates register here; this registry is the plugin seam for Phase 2's
part-generator plugins.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ..domain.feature_program import FeatureProgram, Parameter


@dataclass(frozen=True)
class TemplateCheck:
    """Post-validation advisory: `expr` > 0 triggers `message` as a warning."""

    expr: str
    message: str


@dataclass(frozen=True)
class PartTemplate:
    id: str
    name: str
    description: str
    parameters: list[Parameter]
    build: Callable[[dict[str, float]], FeatureProgram]
    checks: list[TemplateCheck] = field(default_factory=list)


class TemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, PartTemplate] = {}

    def register(self, template: PartTemplate) -> None:
        if template.id in self._templates:
            raise ValueError(f"duplicate template id {template.id!r}")
        self._templates[template.id] = template

    def get(self, template_id: str) -> PartTemplate | None:
        return self._templates.get(template_id)

    def all(self) -> list[PartTemplate]:
        return list(self._templates.values())


def default_registry() -> TemplateRegistry:
    from .bracket_l import BRACKET_L_TEMPLATE
    from .enclosure_box import ENCLOSURE_BOX_TEMPLATE
    from .gear import GEAR_TEMPLATE
    from .mounting_plate import MOUNTING_PLATE_TEMPLATE
    from .standoff import STANDOFF_TEMPLATE

    registry = TemplateRegistry()
    registry.register(BRACKET_L_TEMPLATE)
    registry.register(MOUNTING_PLATE_TEMPLATE)
    registry.register(ENCLOSURE_BOX_TEMPLATE)
    registry.register(STANDOFF_TEMPLATE)
    registry.register(GEAR_TEMPLATE)
    return registry
