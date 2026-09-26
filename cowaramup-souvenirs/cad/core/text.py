"""Text -> shapely polygons, using the bold DejaVu Sans that ships with matplotlib.

Chosen because it is always available with matplotlib (no system font
dependency) and its bold stroke is ~15 % of cap height, which lets the
minimum-feature validator reason about legibility.
"""
from __future__ import annotations

from functools import lru_cache

from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

FONT = FontProperties(family="DejaVu Sans", weight="bold")


@lru_cache(maxsize=64)
def _raw(text: str):
    # Size 100 then scale: better curve resolution from the font outline.
    path = TextPath((0, 0), text, size=100, prop=FONT)
    shape = Polygon()
    for ring in path.to_polygons(closed_only=True):
        if len(ring) < 3:
            continue
        p = Polygon(ring).buffer(0)
        shape = shape.symmetric_difference(p)  # even-odd fill (letter counters)
    return shape


def text_shape(text: str, cap_height: float, cx: float = 0.0, cy: float = 0.0,
               max_width: float | None = None, letter_spacing: float = 0.0, min_counter: float = 0.0):
    """Centred text polygon with a given CAP height (mm).

    If max_width is given the text is shrunk (never stretched) to fit.
    letter_spacing (mm) adds tracking between glyphs.
    min_counter (mm^2): letter counters (holes in A, R, P...) smaller than this are
    filled - in a knock-out they would otherwise become unprintable colour islands.
    """
    if letter_spacing:
        glyphs = []
        x = 0.0
        for ch in text:
            g = _raw(ch)
            if not g.is_empty:
                glyphs.append(affinity.translate(g, x, 0))
            adv = TextPath((0, 0), ch, size=100, prop=FONT).get_extents().width if ch != " " else 35
            x += adv + letter_spacing * 100 / cap_height * 0.73
        shape = unary_union(glyphs)
    else:
        shape = _raw(text)
    cap = _raw("H").bounds[3]  # cap height at size 100
    s = cap_height / cap
    shape = affinity.scale(shape, s, s, origin=(0, 0))
    minx, miny, maxx, maxy = shape.bounds
    if max_width and (maxx - minx) > max_width:
        k = max_width / (maxx - minx)
        shape = affinity.scale(shape, k, k, origin=(0, 0))
        minx, miny, maxx, maxy = shape.bounds
    if min_counter > 0:
        polys = [Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area >= min_counter])
                 for p in (shape.geoms if hasattr(shape, "geoms") else [shape])]
        shape = unary_union(polys)
        minx, miny, maxx, maxy = shape.bounds
    # Centre on the cap-height box so descender-free text sits visually centred.
    capbox_h = (maxy - min(miny, 0))
    return affinity.translate(shape, cx - (minx + maxx) / 2, cy - (min(miny, 0) + capbox_h / 2))
