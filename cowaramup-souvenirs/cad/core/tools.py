"""Resolve what each toolhead will ACTUALLY print for a product.

Inputs: config/toolheads.json (what is loaded), an optional colour variant, and
the product's per-tool requirements. Output: effective material + colour per
tool, plus setup issues (e.g. 'this product needs rigid PLA in tool_4 but TPU
is loaded').
"""
from __future__ import annotations

from . import config
from .model import TOOLS, Product


def effective_tools(product: Product, variant: str | None = None):
    loaded = config.tool_assignment(None)
    coloured = config.tool_assignment(variant) if variant else loaded
    mats = config.materials()
    pal = config.palette()
    out, issues = {}, []
    for t in TOOLS:
        info = dict(coloured[t])
        info["material"] = loaded[t]["material"]
        req = product.requirements.get(t, {})
        want_flex = req.get("flexible")
        is_flex = mats[info["material"]]["flexible"]
        if want_flex is not None and is_flex != want_flex:
            need = "flexible" if want_flex else "rigid"
            pref = req.get("preferred_material", "TPU" if want_flex else "PLA")
            if req.get("strict"):
                issues.append({"level": "SETUP", "tool": t,
                               "msg": f"{product.id} needs a {need} material in {t} ({req.get('why', '')}); "
                                      f"{info['material']} is loaded. Load {pref} before printing."})
                info["material"] = pref
            else:
                issues.append({"level": "WARN", "tool": t,
                               "msg": f"{product.id} prefers {need} ({pref}) in {t}; {info['material']} "
                                      f"loaded - printable, but: {req.get('why', '')}"})
        # A functional flexible tool keeps the physically loaded colour (variants recolour decoration only)
        if want_flex and mats[info["material"]]["flexible"] and variant:
            info.update({k: loaded[t][k] for k in ("colour", "colour_name", "hex")})
        if not pal[info["colour"]]["materials"].get(info["material"], True):
            issues.append({"level": "WARN", "tool": t,
                           "msg": f"colour {info['colour_name']} is not commonly available in {info['material']}"})
        out[t] = info
    return out, issues
