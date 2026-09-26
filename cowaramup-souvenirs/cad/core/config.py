"""Configuration loading. Everything configurable lives in ../../config/*.json."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"


@lru_cache(maxsize=None)
def load(name: str) -> dict:
    with open(CONFIG / f"{name}.json", encoding="utf-8") as fh:
        return json.load(fh)


def reload():
    load.cache_clear()


def dims(product_id: str | None = None, size: str = "STANDARD") -> dict:
    """Merged dimension dict for a product; adds 'scale' for the size preset."""
    d = load("dimensions")
    out = dict(d["global"])
    if product_id and product_id in d:
        out.update(d[product_id])
    out["scale"] = d["sizes"][size]
    out["size"] = size
    return out


def toolheads() -> dict:
    return load("toolheads")


def printer() -> dict:
    return load("toolheads")["printer"]


def palette() -> dict:
    return load("colors")["palette"]


def variants() -> dict:
    return load("variants")["variants"]


def materials() -> dict:
    return load("materials")["materials"]


def costs() -> dict:
    return load("costs")


def tool_assignment(variant: str | None = None) -> dict[str, dict]:
    """Effective {tool: {material, colour, hex}} = loaded toolheads + optional colour variant."""
    th = toolheads()
    pal = palette()
    var = variants().get(variant, {}) if variant else {}
    out = {}
    for t in ("tool_1", "tool_2", "tool_3", "tool_4"):
        colour = var.get(t) or th[t]["colour"]
        out[t] = {
            "material": th[t]["material"],
            "colour": colour,
            "colour_name": pal[colour]["name"],
            "hex": pal[colour]["hex"],
            "role": th[t]["role"],
        }
    return out


def bond_quality(a: str, b: str) -> str:
    table = load("materials")["bonding"]
    return table.get(f"{a}|{b}") or table.get(f"{b}|{a}") or "unknown"
