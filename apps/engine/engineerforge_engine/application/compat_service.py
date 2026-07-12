"""Material compatibility analysis for multi-material printing.

Two independent signal sources, combined by worst severity:
  1. adhesion-chemistry pairing rules between material families,
  2. process windows — shared nozzle-temperature overlap (critical on
     filament-switching single-nozzle systems like the AD5X) and bed-
     temperature mismatch.

Levels: ok < caution < incompatible.
"""

from __future__ import annotations

from itertools import combinations

from ..domain.errors import InvalidRequestError
from ..domain.materials import (
    CompatibilityLevel,
    CompatibilityPair,
    CompatibilityReport,
    Material,
)
from ..services.catalog import material_by_id

_SEVERITY: dict[CompatibilityLevel, int] = {"ok": 0, "caution": 1, "incompatible": 2}

# Adhesion pairing between chemistry families. Same family defaults to ok.
_PAIR_RULES: dict[frozenset[str], tuple[CompatibilityLevel, str]] = {
    frozenset({"pla", "petg"}): (
        "caution",
        "PLA-PETG interlayer bond is weak; avoid load paths across the interface",
    ),
    frozenset({"pla", "tpu"}): ("caution", "TPU bonds moderately to PLA; test peel strength"),
    frozenset({"petg", "tpu"}): ("ok", "TPU adheres well to PETG"),
    frozenset({"pla", "styrenic"}): (
        "incompatible",
        "PLA and ABS/ASA/HIPS neither bond nor share process temperatures",
    ),
    frozenset({"petg", "styrenic"}): ("caution", "PETG–styrenic adhesion is unreliable"),
    frozenset({"pla", "pva"}): ("ok", "PVA is the standard soluble support for PLA"),
    frozenset({"petg", "pva"}): ("ok", "PVA works as soluble support for PETG"),
    frozenset({"tpu", "pva"}): ("ok", "PVA works as soluble support for TPU"),
    frozenset({"styrenic", "pva"}): (
        "incompatible",
        "PVA degrades at styrenic process temperatures",
    ),
    frozenset({"polyamide", "pva"}): (
        "incompatible",
        "PVA degrades at nylon process temperatures",
    ),
    frozenset({"pc", "pva"}): ("incompatible", "PVA degrades at PC process temperatures"),
    frozenset({"pla", "polyamide"}): ("incompatible", "no adhesion and no shared process window"),
    frozenset({"petg", "polyamide"}): ("caution", "limited adhesion; nylon prefers hotter process"),
    frozenset({"tpu", "polyamide"}): (
        "caution",
        "possible but adhesion varies; dry both materials",
    ),
    frozenset({"styrenic", "polyamide"}): ("caution", "marginal adhesion"),
    frozenset({"pla", "pc"}): ("incompatible", "no shared process window"),
    frozenset({"petg", "pc"}): ("caution", "marginal adhesion; large temperature gap"),
    frozenset({"tpu", "pc"}): ("caution", "adhesion varies"),
    frozenset({"styrenic", "pc"}): ("caution", "possible in enclosed printers; watch warping"),
    frozenset({"polyamide", "pc"}): ("caution", "both hygroscopic and hot; adhesion varies"),
    frozenset({"tpu", "styrenic"}): ("caution", "TPU–ABS adhesion is weak"),
}


def _adhesion_rule(a: Material, b: Material) -> tuple[CompatibilityLevel, str]:
    if a.adhesion_group == b.adhesion_group:
        # soluble support within its own family (HIPS for ABS/ASA) is a feature
        if a.soluble_support or b.soluble_support:
            return ("ok", "soluble support pairing within the same chemistry family")
        return ("ok", "same chemistry family")
    rule = _PAIR_RULES.get(frozenset({a.adhesion_group, b.adhesion_group}))
    if rule is not None:
        return rule
    return ("caution", "untested material pairing — validate adhesion on a test coupon")


def _support_override(a: Material, b: Material) -> str | None:
    for support, part in ((a, b), (b, a)):
        if support.soluble_support and part.adhesion_group in support.support_for:
            return f"{support.name} is a soluble support for {part.name}"
    return None


def analyze_pair(a: Material, b: Material) -> CompatibilityPair:
    level, reason = _adhesion_rule(a, b)
    reasons = [reason]

    support_note = _support_override(a, b)
    if support_note and level == "ok":
        reasons = [support_note]

    overlap = min(a.print_temp_max_c, b.print_temp_max_c) - max(
        a.print_temp_min_c, b.print_temp_min_c
    )
    bed_delta = abs(a.bed_temp_c - b.bed_temp_c)

    if overlap < 0:
        level = "incompatible"
        reasons.append(
            "no shared nozzle-temperature window "
            f"({a.name}: {a.print_temp_min_c}-{a.print_temp_max_c}°C, "
            f"{b.name}: {b.print_temp_min_c}-{b.print_temp_max_c}°C) — "
            "cannot co-print through one nozzle"
        )
    elif overlap < 10 and _SEVERITY[level] < _SEVERITY["caution"]:
        level = "caution"
        reasons.append(f"narrow shared nozzle-temperature window ({overlap}°C)")

    if bed_delta > 25:
        if _SEVERITY[level] < _SEVERITY["caution"]:
            level = "caution"
        reasons.append(f"bed temperature mismatch ({bed_delta}°C) risks warping/adhesion issues")

    return CompatibilityPair(
        a=a.id,
        b=b.id,
        level=level,
        reasons=reasons,
        nozzle_temp_overlap_c=overlap,
        bed_temp_delta_c=bed_delta,
    )


def analyze(material_ids: list[str]) -> CompatibilityReport:
    unique_ids = list(dict.fromkeys(material_ids))
    if len(unique_ids) < 2:
        raise InvalidRequestError("compatibility analysis needs at least two distinct materials")
    materials: list[Material] = []
    for material_id in unique_ids:
        material = material_by_id(material_id)
        if material is None:
            raise InvalidRequestError(f"unknown material id: {material_id}")
        materials.append(material)

    pairs = [analyze_pair(a, b) for a, b in combinations(materials, 2)]
    worst: CompatibilityLevel = "ok"
    for pair in pairs:
        if _SEVERITY[pair.level] > _SEVERITY[worst]:
            worst = pair.level
    return CompatibilityReport(pairs=pairs, worst=worst)
