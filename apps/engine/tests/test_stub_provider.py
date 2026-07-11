from __future__ import annotations

from engineerforge_engine.adapters.ai.stub import StubProvider
from engineerforge_engine.domain.ai import ChatMessage, ChatRequest, Role


async def test_chat_is_deterministic_and_echoes_user() -> None:
    provider = StubProvider()
    req = ChatRequest(messages=[ChatMessage(role=Role.user, content="Design a bracket")])
    r1 = await provider.chat(req)
    r2 = await provider.chat(req)
    assert r1.content == r2.content
    assert r1.provider == "stub"
    assert r1.stop_reason == "end_turn"
    assert "Design a bracket" in r1.content


async def test_health_always_available() -> None:
    health = await StubProvider().health()
    assert health.available is True
    assert health.provider == "stub"
