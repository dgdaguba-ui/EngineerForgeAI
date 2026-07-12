"""Bundled catalog loading — materials and printer profiles.

Data ships as JSON inside the package and is schema-validated on first load
(fail fast on corrupt data). Custom user materials arrive with the data plane
in Phase 2; these are the curated system entries.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from ..domain.materials import Material, PrinterProfile


def _read_data_file(filename: str) -> object:
    source = resources.files("engineerforge_engine.data").joinpath(filename)
    with source.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_materials() -> tuple[Material, ...]:
    raw = _read_data_file("materials.json")
    if not isinstance(raw, list):
        raise ValueError("materials.json must contain a list")
    materials = tuple(Material.model_validate(entry) for entry in raw)
    ids = [m.id for m in materials]
    if len(ids) != len(set(ids)):
        raise ValueError("materials.json contains duplicate ids")
    return materials


@lru_cache(maxsize=1)
def load_printers() -> tuple[PrinterProfile, ...]:
    raw = _read_data_file("printers.json")
    if not isinstance(raw, list):
        raise ValueError("printers.json must contain a list")
    printers = tuple(PrinterProfile.model_validate(entry) for entry in raw)
    ids = [p.id for p in printers]
    if len(ids) != len(set(ids)):
        raise ValueError("printers.json contains duplicate ids")
    return printers


def material_by_id(material_id: str) -> Material | None:
    return next((m for m in load_materials() if m.id == material_id), None)


def printer_by_id(printer_id: str) -> PrinterProfile | None:
    return next((p for p in load_printers() if p.id == printer_id), None)
