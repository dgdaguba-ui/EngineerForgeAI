"""AiToolbox — engine capabilities exposed to AI providers as tools.

This is the safety architecture of ADR-0003 in code: the model orchestrates
tools; every dimension, volume, and mass comes from the deterministic kernel
and catalog, never from generated text. Tool schemas use the Anthropic
tool-definition shape (name/description/input_schema), which the Claude
provider passes through directly and other providers can translate.
"""

from __future__ import annotations

from typing import Any

from ..domain.ai import ChatAction
from ..domain.errors import EngineError
from .freeform_service import FreeformDetail, FreeformService
from .parts_service import PartDetail, PartsService


def _part_summary(detail: PartDetail) -> str:
    props = detail.compiled.mass_props
    bbox = props.bbox_mm
    mass = f", {props.mass_g} g" if props.mass_g is not None else ""
    warn = (
        f" Warnings: {'; '.join(detail.compiled.warnings)}"
        if detail.compiled.warnings
        else ""
    )
    return (
        f"{detail.name} (part {detail.part_id}): "
        f"{bbox['x']}×{bbox['y']}×{bbox['z']} mm, "
        f"{props.volume_cm3} cm³{mass}.{warn}"
    )


def _freeform_summary(detail: FreeformDetail) -> str:
    props = detail.mass_props
    bbox = props.bbox_mm
    return (
        f"{detail.name} (freeform part {detail.part_id}): "
        f"{bbox['x']}×{bbox['y']}×{bbox['z']} mm, {props.volume_cm3} cm³. "
        "Loaded as a non-parametric mesh (not editable in the Parameters panel)."
    )


class ToolExecution:
    """Result of one tool invocation, carrying both the model-facing text and
    the UI-facing action record."""

    def __init__(self, action: ChatAction, model_output: str) -> None:
        self.action = action
        self.model_output = model_output


class AiToolbox:
    def __init__(self, parts: PartsService, freeform: FreeformService | None = None) -> None:
        self._parts = parts
        self._freeform = freeform

    def definitions(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = [
            {
                "name": "list_part_templates",
                "description": (
                    "List the available parametric part templates with their "
                    "editable parameters, defaults, and allowed ranges."
                ),
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "create_part_from_template",
                "description": (
                    "Create an editable parametric part from a template. Use "
                    "list_part_templates first to see parameter ids and ranges. "
                    "Returns exact volume/bounding box computed by the CAD kernel."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "templateId": {"type": "string"},
                        "values": {
                            "type": "object",
                            "description": "parameter id → numeric value overrides",
                            "additionalProperties": {"type": "number"},
                        },
                        "materialId": {
                            "type": "string",
                            "description": "optional material id (e.g. pla, petg)",
                        },
                    },
                    "required": ["templateId"],
                },
            },
            {
                "name": "update_part_parameters",
                "description": (
                    "Propose changing parameters on an existing parametric part. "
                    "Values are validated against each parameter's range but the "
                    "part is NOT rebuilt — the change is returned as a diff for "
                    "the user to review and apply or discard in the UI."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "partId": {"type": "string"},
                        "values": {
                            "type": "object",
                            "additionalProperties": {"type": "number"},
                        },
                    },
                    "required": ["partId", "values"],
                },
            },
        ]
        if self._freeform is not None:
            tools.append(
                {
                    "name": "generate_cad_script",
                    "description": (
                        "Generate a one-off part by writing a CadQuery Python script "
                        "for shapes the parametric templates cannot express (organic, "
                        "swept, lofted, or complex boolean geometry). Assign the final "
                        "shape to a variable named `result` (a cadquery Workplane or "
                        "Shape). Only `cadquery` (as `cq`), `math`, and `numpy` are "
                        "available; no file, network, or system access. The result is "
                        "a NON-parametric mesh part — it is NOT editable in the "
                        "Parameters panel, so prefer create_part_from_template when a "
                        "template fits. Volume/bbox are measured from the real solid."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "CadQuery script assigning `result`",
                            },
                            "name": {"type": "string", "description": "optional part name"},
                        },
                        "required": ["code"],
                    },
                }
            )
        return tools

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolExecution:
        try:
            if name == "list_part_templates":
                templates = self._parts.list_templates()
                lines = []
                for t in templates:
                    params = ", ".join(
                        f"{p.id}={p.value}{p.unit}"
                        + (f" [{p.min}..{p.max}]" if p.min is not None else "")
                        for p in t.parameters
                    )
                    lines.append(f"{t.id}: {t.name} — {t.description} Parameters: {params}")
                text = "\n".join(lines) or "no templates registered"
                return ToolExecution(
                    ChatAction(tool=name, ok=True, summary=f"{len(templates)} template(s)"),
                    text,
                )

            if name == "create_part_from_template":
                detail = self._parts.create_from_template(
                    str(arguments.get("templateId", "")),
                    _number_map(arguments.get("values")),
                    _opt_str(arguments.get("materialId")),
                )
                summary = f"Created {_part_summary(detail)}"
                return ToolExecution(
                    ChatAction(tool=name, ok=True, summary=summary, part_id=detail.part_id),
                    summary,
                )

            if name == "update_part_parameters":
                part_id = str(arguments.get("partId", ""))
                diff = self._parts.preview_params(part_id, _number_map(arguments.get("values")))
                if diff:
                    changes = ", ".join(
                        f"{d.label} {d.old_value}→{d.new_value} {d.unit}" for d in diff
                    )
                    summary = f"Proposed change to part {part_id}: {changes}"
                else:
                    summary = f"No change proposed for part {part_id} (values already current)"
                model_output = summary + " (pending user approval in the UI)"
                return ToolExecution(
                    ChatAction(
                        tool=name,
                        ok=True,
                        summary=summary,
                        part_id=part_id,
                        diff=diff,
                        pending=bool(diff),
                    ),
                    model_output,
                )

            if name == "generate_cad_script" and self._freeform is not None:
                ff_detail = self._freeform.generate(
                    str(arguments.get("code", "")),
                    _opt_str(arguments.get("name")),
                )
                summary = f"Generated {_freeform_summary(ff_detail)}"
                return ToolExecution(
                    ChatAction(tool=name, ok=True, summary=summary, part_id=ff_detail.part_id),
                    summary,
                )

            failure = f"unknown tool: {name}"
        except EngineError as exc:
            failure = f"{name} failed: {exc.message}"
        except (TypeError, ValueError) as exc:
            failure = f"{name} failed: invalid arguments ({exc})"

        return ToolExecution(ChatAction(tool=name, ok=False, summary=failure), failure)


def _number_map(raw: object) -> dict[str, float]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("values must be an object of numbers")
    return {str(k): float(v) for k, v in raw.items()}


def _opt_str(raw: object) -> str | None:
    return None if raw in (None, "") else str(raw)
