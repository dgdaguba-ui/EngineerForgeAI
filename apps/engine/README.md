# EngineerForge Engine (Python / FastAPI)

The **Geometry & Intelligence plane** — a localhost sidecar the Electron app supervises. It hosts AI orchestration now, and (per the roadmap) the CAD kernel, mesh services, FEA, slicer, and Blender bridge in later phases.

## Architecture

Clean architecture with dependency injection:

```
engineerforge_engine/
├─ domain/       pure entities + value objects (no framework deps)
├─ ports/        abstract interfaces (AIProvider, …)
├─ adapters/     concrete implementations (ai/stub, ai/claude, …)
├─ application/  use cases (ChatService, …)
├─ di/           composition root (Container wires adapters → ports)
├─ api/          FastAPI routers (v1) + error envelope + auth
└─ config.py     typed, env-driven settings (no hardcoded secrets)
```

Dependencies point inward. The application depends only on **ports**; concrete adapters are chosen at the composition root and are trivially swapped with fakes in tests.

## Offline-first & provider abstraction

- `AIProvider` port → `StubProvider` (offline/dev, deterministic), `ClaudeProvider` (Anthropic). OpenAI/Ollama are future adapters behind the same port.
- Selected by `EFC_AI_PROVIDER` (`auto` | `stub` | `claude`). `auto` uses Claude when `ANTHROPIC_API_KEY` is set, otherwise falls back to `StubProvider` — **the engine always works without any key or network.**
- The app never imports the Anthropic SDK directly; everything goes through `AIProvider`.

## Setup (Python 3.12 via uv)

```bash
cd apps/engine
uv venv --python 3.12 .venv
uv sync
```

## Run

```bash
uv run uvicorn engineerforge_engine.api.main:app --host 127.0.0.1 --port 8000
# health:
curl http://127.0.0.1:8000/health
```

## Test / lint / typecheck

```bash
uv run pytest
uv run ruff check .
uv run mypy engineerforge_engine
```

## Configuration (env)

| Var | Default | Meaning |
|---|---|---|
| `EFC_AI_PROVIDER` | `auto` | `auto` \| `stub` \| `claude` |
| `EFC_AI_MODEL` | `claude-opus-4-8` | Claude model id |
| `EFC_AI_MAX_TOKENS` | `8192` | response cap |
| `EFC_AI_THINKING` | `adaptive` | `adaptive` \| `off` |
| `EFC_ENGINE_TOKEN` | _(unset)_ | if set, requests need `Authorization: Bearer <token>` |
| `ANTHROPIC_API_KEY` | _(unset)_ | enables `ClaudeProvider`; absent ⇒ `StubProvider` |

Secrets come from the environment/keychain — never hardcoded, never logged.
