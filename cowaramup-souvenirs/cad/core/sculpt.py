"""Turn SDF fields into printable, colour-separated parts.

    env field --support_free--> mesh --+
    layer fields ------------> meshes -+--> Painter3D (exact booleans) --> Parts

The support-free closure is applied to the envelope only; everything it adds
(45-degree fillets under chins, ears, bells) belongs to whatever colour region
contains it, or else to tool 1.
"""
from __future__ import annotations

import numpy as np

from . import sdf
from .model import Painter3D, Part


def sculpt_parts(grid: sdf.Grid, env: np.ndarray, layers, closure: bool = True,
                 decimate_env: int = 180_000, decimate_layer: int = 60_000,
                 base_tool: str = "tool_1", base_feature: str = "body", group: str = "main",
                 post_cut=None, return_field: bool = False):
    """post_cut: fields removed AFTER the closure (engravings, bed-face debosses, magnet
    pockets) - otherwise the 45-degree fill would close them."""
    envc = sdf.support_free(env, grid.h) if closure else env
    for c in (post_cut or []):
        envc = np.maximum(envc, -c)
    env_m = sdf.mesh(envc, grid, decimate_to=decimate_env)
    painter = Painter3D()
    painter.paint(base_tool, env_m, base_feature)
    for tool, field, name in layers:
        if (field < 0).sum() < 8:
            continue
        painter.paint(tool, sdf.mesh(field, grid, decimate_to=decimate_layer), name)
    regions = painter.resolve(env_m)
    for r in regions.values():
        # collapse sub-micron edges left by the booleans: vertex-welding readers (slicers,
        # STL) would otherwise see non-manifold edges. <= 1 um geometric change.
        r["solid"] = r["solid"].simplify(1e-3)
    env_m = env_m.simplify(1e-3)
    parts = [Part(f"{group}_{t}" if group != "main" else t, t, regions[t]["solid"],
                  ", ".join(regions[t]["features"]), group) for t in sorted(regions)]
    if return_field:
        return parts, env_m, envc
    return parts, env_m
