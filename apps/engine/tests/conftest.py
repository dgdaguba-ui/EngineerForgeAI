from __future__ import annotations

from collections.abc import Iterator

import pytest
from engineerforge_engine.api.main import create_app
from engineerforge_engine.config import Settings
from fastapi.testclient import TestClient


@pytest.fixture
def stub_settings() -> Settings:
    # Force the offline provider and no auth token, regardless of ambient env.
    return Settings(_env_file=None, ai_provider="stub", engine_token=None)  # type: ignore[call-arg]


@pytest.fixture
def client(stub_settings: Settings) -> Iterator[TestClient]:
    app = create_app(stub_settings)
    with TestClient(app) as c:  # context manager runs the lifespan (builds Container)
        yield c
