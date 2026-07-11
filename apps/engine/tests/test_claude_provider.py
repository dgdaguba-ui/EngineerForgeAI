from __future__ import annotations

from engineerforge_engine.adapters.ai.claude import ClaudeProvider, split_system_and_messages
from engineerforge_engine.domain.ai import ChatMessage, ChatRequest, Role


def test_split_merges_system_and_filters_non_conversational() -> None:
    req = ChatRequest(
        system="S1",
        messages=[
            ChatMessage(role=Role.system, content="S2"),
            ChatMessage(role=Role.user, content="U"),
            ChatMessage(role=Role.assistant, content="A"),
            ChatMessage(role=Role.tool, content="T"),  # dropped until tool-calling lands
        ],
    )
    system, messages = split_system_and_messages(req)
    assert system == "S1\n\nS2"
    assert messages == [
        {"role": "user", "content": "U"},
        {"role": "assistant", "content": "A"},
    ]


def test_split_returns_none_system_when_absent() -> None:
    req = ChatRequest(messages=[ChatMessage(role=Role.user, content="hi")])
    system, messages = split_system_and_messages(req)
    assert system is None
    assert messages == [{"role": "user", "content": "hi"}]


async def test_health_unavailable_without_key() -> None:
    health = await ClaudeProvider(api_key=None).health()
    assert health.available is False
    assert health.provider == "claude"


def test_thinking_param_modes() -> None:
    assert ClaudeProvider(api_key=None, thinking="off")._thinking_param() == {"type": "disabled"}
    adaptive = ClaudeProvider(api_key=None, thinking="adaptive")._thinking_param()
    assert adaptive == {"type": "adaptive", "display": "summarized"}
