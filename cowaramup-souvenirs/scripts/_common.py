"""Shared helpers for the pipeline scripts (path setup, product registry, caching)."""
from __future__ import annotations

import importlib
import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore", category=RuntimeWarning, module="trimesh")

# id -> (module, sizes to generate, colour variants to export as 3MF)
REGISTRY = {
    "CRW-001": ("cad.products.crw001_keyring", ["STANDARD", "SMALL", "LARGE"],
                ["classic", "aussie", "surf", "wine", "christmas", "jersey", "farmer", "camping", "beach"]),
    "CRW-002": ("cad.products.crw002_magnet", ["STANDARD", "SMALL", "LARGE"], ["classic", "aussie"]),
    # LARGE mini: parts validate but the merged single-colour mesh has a tangency at 1.25x - not exported yet
    "CRW-003": ("cad.products.crw003_mini_cow", ["STANDARD"], ["classic", "aussie", "jersey"]),
    "CRW-004": ("cad.products.crw004_phone_stand", ["STANDARD"], ["classic"]),
    "CRW-005": ("cad.products.crw005_articulated_cow", ["STANDARD"], ["classic", "jersey"]),
}
DEFAULT_VARIANT = "classic"
STAGE = "prototypes"   # stl/<STAGE>, 3mf/<STAGE>

GEN = ROOT / "products" / "generated"


def build(pid: str, size: str = "STANDARD"):
    from cad.core.export import clean_mesh
    mod = importlib.import_module(REGISTRY[pid][0])
    product = mod.build(size)
    for p in product.parts:
        p.solid = clean_mesh(p.solid)
    return product


def analysis_path(stem: str) -> Path:
    return GEN / f"{stem}.analysis.json"


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=_default)
        fh.write("\n")


def _default(o):
    import numpy as np
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def rel(path: Path) -> str:
    return str(Path(path).resolve().relative_to(ROOT))


def selected(args_products):
    return args_products or list(REGISTRY)
