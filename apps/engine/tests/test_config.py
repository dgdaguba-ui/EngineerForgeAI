from __future__ import annotations

from engineerforge_engine.config import Settings


def test_model_default_is_opus_4_8() -> None:
    s = Settings(_env_file=None, ai_model="claude-opus-4-8")  # type: ignore[call-arg]
    assert s.ai_model == "claude-opus-4-8"


def test_has_anthropic_key_false_when_unset() -> None:
    s = Settings(_env_file=None, anthropic_api_key=None)  # type: ignore[call-arg]
    assert s.has_anthropic_key is False


def test_has_anthropic_key_true_when_set() -> None:
    s = Settings(_env_file=None, anthropic_api_key="sk-test")  # type: ignore[call-arg]
    assert s.has_anthropic_key is True
