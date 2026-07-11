from __future__ import annotations

import pytest
from engineerforge_engine.adapters.ai.stub import StubProvider
from engineerforge_engine.application.chat_service import ChatService
from engineerforge_engine.domain.ai import ChatMessage, ChatRequest, Role
from engineerforge_engine.domain.errors import InvalidRequestError


async def test_empty_messages_raise_invalid_request() -> None:
    service = ChatService(StubProvider())
    with pytest.raises(InvalidRequestError):
        await service.chat(ChatRequest(messages=[]))


async def test_delegates_to_provider() -> None:
    service = ChatService(StubProvider())
    resp = await service.chat(
        ChatRequest(messages=[ChatMessage(role=Role.user, content="hi")])
    )
    assert resp.provider == "stub"
    assert service.provider_name == "stub"
