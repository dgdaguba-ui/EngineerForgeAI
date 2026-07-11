"""Anthropic Claude provider.

Follows current Claude API guidance for Opus 4.8:
  * default model ``claude-opus-4-8``;
  * adaptive thinking (``{"type": "adaptive"}``) — no ``budget_tokens``;
  * **no** ``temperature``/``top_p``/``top_k`` (they return 400 on 4.8);
  * ``system`` passed as a top-level parameter, not inside ``messages``.

The Anthropic SDK is imported lazily so the engine boots even if the package
or a key is missing — in that case the provider simply reports itself
unavailable and the registry falls back to the StubProvider.
"""

from __future__ import annotations

from ...domain.ai import ChatRequest, ChatResponse, ProviderHealth, Role, Usage
from ...domain.errors import AIProviderError, InvalidRequestError, ProviderUnavailableError
from ...ports.ai_provider import AIProvider

try:  # optional dependency / import-time resilience
    import anthropic

    _ANTHROPIC_IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover - defensive
    anthropic = None  # type: ignore[assignment]
    _ANTHROPIC_IMPORT_ERROR = str(exc)


def split_system_and_messages(
    request: ChatRequest,
) -> tuple[str | None, list[dict[str, str]]]:
    """Split a ChatRequest into (system_prompt, anthropic_messages).

    Pure and unit-tested: system-role messages are merged into the system
    prompt; only user/assistant turns go into the messages array (tool turns
    are ignored until tool-calling lands).
    """
    system_parts: list[str] = []
    if request.system:
        system_parts.append(request.system)
    messages: list[dict[str, str]] = []
    for m in request.messages:
        if m.role == Role.system:
            system_parts.append(m.content)
        elif m.role in (Role.user, Role.assistant):
            messages.append({"role": m.role.value, "content": m.content})
    system = "\n\n".join(p for p in system_parts if p.strip()) or None
    return system, messages


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "claude-opus-4-8",
        max_tokens: int = 8192,
        thinking: str = "adaptive",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._thinking = thinking
        self._client: object | None = None

    def _get_client(self) -> object:
        if anthropic is None:
            raise ProviderUnavailableError(
                f"anthropic SDK unavailable: {_ANTHROPIC_IMPORT_ERROR}"
            )
        if not self._api_key:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is not set")
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    def _thinking_param(self) -> dict[str, str] | None:
        if self._thinking == "off":
            return {"type": "disabled"}
        # adaptive (recommended for an engineering assistant); summarized so the
        # UI can optionally surface reasoning instead of a silent pause.
        return {"type": "adaptive", "display": "summarized"}

    async def chat(self, request: ChatRequest) -> ChatResponse:
        client = self._get_client()
        system, messages = split_system_and_messages(request)
        if not messages:
            raise InvalidRequestError("request contains no user/assistant messages")

        model = request.model or self._model
        kwargs: dict[str, object] = {
            "model": model,
            "max_tokens": request.max_tokens or self._max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        thinking = self._thinking_param()
        if thinking is not None:
            kwargs["thinking"] = thinking

        try:
            resp = await client.messages.create(**kwargs)  # type: ignore[attr-defined]
        except Exception as exc:  # map SDK errors → engine errors
            raise self._map_error(exc) from exc

        text_parts: list[str] = []
        thinking_parts: list[str] = []
        for block in getattr(resp, "content", []) or []:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(getattr(block, "text", ""))
            elif btype == "thinking":
                t = getattr(block, "thinking", "") or ""
                if t:
                    thinking_parts.append(t)

        content = "".join(text_parts)
        stop_reason = getattr(resp, "stop_reason", None)
        if stop_reason == "refusal" and not content:
            content = "[Claude declined to respond to this request.]"

        usage_obj = getattr(resp, "usage", None)
        usage = Usage(
            input_tokens=getattr(usage_obj, "input_tokens", 0) or 0,
            output_tokens=getattr(usage_obj, "output_tokens", 0) or 0,
        )
        return ChatResponse(
            content=content,
            provider=self.name,
            model=getattr(resp, "model", model),
            stop_reason=stop_reason,
            thinking="\n".join(thinking_parts) or None,
            usage=usage,
        )

    def _map_error(self, exc: Exception) -> AIProviderError:
        retryable = False
        if anthropic is not None:
            retryable = isinstance(
                exc,
                (
                    anthropic.RateLimitError,
                    anthropic.APIConnectionError,
                    anthropic.InternalServerError,
                ),
            )
        return AIProviderError(
            f"Claude request failed: {exc}", retryable=retryable, details={"model": self._model}
        )

    async def health(self) -> ProviderHealth:
        if anthropic is None:
            return ProviderHealth(
                provider=self.name,
                available=False,
                detail=f"anthropic SDK not importable: {_ANTHROPIC_IMPORT_ERROR}",
            )
        if not self._api_key:
            return ProviderHealth(
                provider=self.name,
                available=False,
                detail="ANTHROPIC_API_KEY not set",
            )
        return ProviderHealth(
            provider=self.name,
            available=True,
            detail=f"ready (model={self._model}, thinking={self._thinking})",
        )
