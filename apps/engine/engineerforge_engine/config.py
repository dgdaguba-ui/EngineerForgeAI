"""Typed, environment-driven settings. No secret is ever hardcoded here."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Engine configuration, sourced from environment variables (and .env in dev).

    Fields with an explicit ``validation_alias`` read that exact env var (no prefix);
    everything else uses the ``EFC_`` prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="EFC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        # Accept both the env-var alias (e.g. ANTHROPIC_API_KEY) and the Python
        # field name (e.g. anthropic_api_key), so construction in tests/code works.
        populate_by_name=True,
    )

    # --- app / server ---
    app_name: str = "EngineerForge Engine"
    version: str = "0.1.0"
    host: str = Field(default="127.0.0.1", validation_alias="EFC_ENGINE_HOST")
    port: int = Field(default=8000, validation_alias="EFC_ENGINE_PORT")
    log_level: str = Field(default="info", validation_alias="EFC_ENGINE_LOG_LEVEL")

    # --- engine auth: if set, requests require Authorization: Bearer <token> ---
    engine_token: SecretStr | None = Field(default=None, validation_alias="EFC_ENGINE_TOKEN")

    # --- AI provider selection ---
    ai_provider: str = Field(default="auto", validation_alias="EFC_AI_PROVIDER")  # auto|stub|claude
    ai_model: str = Field(default="claude-opus-4-8", validation_alias="EFC_AI_MODEL")
    ai_max_tokens: int = Field(default=8192, validation_alias="EFC_AI_MAX_TOKENS")
    ai_thinking: str = Field(default="adaptive", validation_alias="EFC_AI_THINKING")  # adaptive|off

    # --- integrations ---
    blender_path: str | None = Field(default=None, validation_alias="EFC_BLENDER_PATH")

    # --- provider credentials (standard env var names, no EFC_ prefix) ---
    anthropic_api_key: SecretStr | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    ollama_host: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST")

    @property
    def has_anthropic_key(self) -> bool:
        return self.anthropic_api_key is not None and bool(
            self.anthropic_api_key.get_secret_value()
        )


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings singleton."""
    return Settings()
