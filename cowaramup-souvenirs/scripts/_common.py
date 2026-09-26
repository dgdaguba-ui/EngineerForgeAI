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
    "CRW-001": ("cad.products.crw001_keyring", ["STANDARD"],
                ["classic", "aussie", "surf", "wine", "christmas", "jersey", "farmer", "camping", "beach"]),
    "CRW-002": ("cad.products.crw002_magnet", ["STANDARD"], ["classic", "aussie", "christmas"]),
    # v2 editions: STANDARD (3 colours, no base) and DELUXE (4 colours + paddock base)
    "CRW-003": ("cad.products.crw003_mini_cow", ["STANDARD", "DELUXE"], ["classic", "aussie", "jersey", "christmas"]),
    "CRW-004": ("cad.products.crw004_phone_stand", ["STANDARD"], ["classic"]),
    "CRW-005": ("cad.products.crw005_articulated_cow", ["STANDARD"], ["classic", "jersey"]),
}
DEFAULT_VARIANT = "classic"
STAGE = "prototypes"   # stl/<STAGE>, 3mf/<STAGE>

GEN = ROOT / "products" / "generated"


def _source_stamp() -> float:
    files = list((ROOT / "cad").rglob("*.py")) + list((ROOT / "config").glob("*.json"))
    return max(f.stat().st_mtime for f in files if "archive" not in f.parts)


def build(pid: str, size: str = "STANDARD", use_cache: bool = True):
    """Build a product; results are cached (products/generated/cache) until any cad/ or
    config/ file changes - sculpted products take minutes to evaluate."""
    import pickle

    import numpy as np

    from cad.core import geom, sdf
    from cad.core.export import clean_mesh
    cache = GEN / "cache" / f"{pid}-{size}.pkl"
    if use_cache and cache.exists() and cache.stat().st_mtime > _source_stamp():
        with open(cache, "rb") as fh:
            product = pickle.load(fh)
        for p in product.parts:
            p.solid = sdf.to_manifold(*p.solid)
        if product.envelope is not None:
            product.envelope = sdf.to_manifold(*product.envelope)
        return product
    mod = importlib.import_module(REGISTRY[pid][0])
    product = mod.build(size)
    for p in product.parts:
        p.solid = clean_mesh(p.solid)
    if product.envelope is not None:
        product.envelope = clean_mesh(product.envelope)
    # serialise solids as mesh arrays
    solids = [p.solid for p in product.parts]
    env = product.envelope
    for p in product.parts:
        p.solid = geom.mesh_arrays(p.solid)
    if env is not None:
        product.envelope = geom.mesh_arrays(env)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, "wb") as fh:
        pickle.dump(product, fh)
    for p, s_ in zip(product.parts, solids):
        p.solid = s_
    product.envelope = env
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
