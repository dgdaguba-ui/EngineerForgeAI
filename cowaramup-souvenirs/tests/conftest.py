import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pytest  # noqa: E402

import _common as C  # noqa: E402


@pytest.fixture(scope="session")
def products():
    """Every prototype at STANDARD size, built once per test session."""
    return {pid: C.build(pid) for pid in C.REGISTRY}
