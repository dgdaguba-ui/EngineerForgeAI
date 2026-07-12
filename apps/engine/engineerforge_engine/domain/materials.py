"""Materials and printer-profile domain models (camelCase API aliases)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Material(_CamelModel):
    id: str
    name: str
    category: Literal["rigid", "engineering", "flexible", "support"]
    # adhesion/chemistry family used by compatibility rules
    adhesion_group: str
    density_g_cm3: float = Field(gt=0)
    tensile_strength_mpa: float | None = None
    youngs_modulus_mpa: float | None = None
    print_temp_min_c: int
    print_temp_max_c: int
    bed_temp_c: int
    shrinkage_pct: float = 0.0
    cost_per_kg: float = Field(gt=0)
    color_hex: str = "#b0b0b0"
    soluble_support: bool = False
    # adhesion groups this material can support (for soluble/breakaway supports)
    support_for: list[str] = Field(default_factory=list)
    notes: str = ""


class BuildVolume(_CamelModel):
    x: int = Field(gt=0)
    y: int = Field(gt=0)
    z: int = Field(gt=0)


class PrinterProfile(_CamelModel):
    id: str
    name: str
    brand: str
    build_volume: BuildVolume
    extruders: int = Field(ge=1)
    material_slots: int = Field(ge=1)
    nozzle_diameter_mm: float = 0.4
    max_nozzle_temp_c: int
    max_bed_temp_c: int
    enclosed: bool = False
    multi_material_system: Literal["none", "idex", "filament-switching"]
    # first-order purge waste per material change (0 for single-material)
    purge_per_change_mm3: float = 0.0
    slicer: str = "FlashPrint"


CompatibilityLevel = Literal["ok", "caution", "incompatible"]


class CompatibilityPair(_CamelModel):
    a: str  # material id
    b: str
    level: CompatibilityLevel
    reasons: list[str]
    nozzle_temp_overlap_c: int
    bed_temp_delta_c: int


class CompatibilityReport(_CamelModel):
    pairs: list[CompatibilityPair]
    worst: CompatibilityLevel
