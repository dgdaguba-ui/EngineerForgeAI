from __future__ import annotations

from engineerforge_engine.adapters.ai.registry import build_ai_provider
from engineerforge_engine.config import Settings


def test_stub_is_forced() -> None:
    p = build_ai_provider(Settings(_env_file=None, ai_provider="stub"))  # type: ignore[call-arg]
    assert p.name == "stub"


def test_auto_falls_back_to_stub_without_key() -> None:
    p = build_ai_provider(
        Settings(_env_file=None, ai_provider="auto", anthropic_api_key=None)  # type: ignore[call-arg]
    )
    assert p.name == "stub"


def test_auto_selects_claude_with_key() -> None:
    p = build_ai_provider(
        Settings(_env_file=None, ai_provider="auto", anthropic_api_key="sk-test")  # type: ignore[call-arg]
    )
    assert p.name == "claude"


def test_claude_choice_without_key_falls_back_to_stub() -> None:
    p = build_ai_provider(
        Settings(_env_file=None, ai_provider="claude", anthropic_api_key=None)  # type: ignore[call-arg]
    )
    assert p.name == "stub"
