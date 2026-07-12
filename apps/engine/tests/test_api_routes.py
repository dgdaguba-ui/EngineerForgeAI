from __future__ import annotations

from engineerforge_engine.api.main import create_app
from engineerforge_engine.config import Settings
from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["provider"]["provider"] == "stub"
    assert data["provider"]["available"] is True


def test_capabilities(client: TestClient) -> None:
    data = client.get("/api/v1/capabilities").json()
    assert data["ai"]["active_provider"] == "stub"
    assert data["features"]["ai_chat"] is True
    assert data["features"]["cad_kernel"] is True
    assert data["features"]["fea"] is False  # honest roadmap flag


def test_chat_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "Design a gear"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "stub"
    assert "Design a gear" in data["content"]


def test_chat_empty_messages_returns_400(client: TestClient) -> None:
    resp = client.post("/api/v1/ai/chat", json={"messages": []})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_REQUEST"


def test_bearer_token_enforced_when_configured() -> None:
    app = create_app(
        Settings(_env_file=None, ai_provider="stub", engine_token="secret")  # type: ignore[call-arg]
    )
    with TestClient(app) as c:
        payload = {"messages": [{"role": "user", "content": "hi"}]}
        assert c.post("/api/v1/ai/chat", json=payload).status_code == 401
        ok = c.post(
            "/api/v1/ai/chat",
            json=payload,
            headers={"Authorization": "Bearer secret"},
        )
        assert ok.status_code == 200
