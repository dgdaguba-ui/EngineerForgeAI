"""Shared analytic helpers for CAD tests (pytest inserts tests/ on sys.path)."""

from __future__ import annotations

import math


def bracket_volume(w: float, h: float, d: float, t: float, hd: float, hc: int) -> float:
    """Analytic L-bracket solid volume with fillet radius 0."""
    return w * t * (h + d - t) - 2 * hc * math.pi * (hd / 2) ** 2 * t
