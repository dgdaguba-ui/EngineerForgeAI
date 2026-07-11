# 0003 — AI provider abstraction with tool-calling

Status: Accepted

## Context
The product must support cloud models (Claude, OpenAI) for quality and a local model (Ollama) for offline/private use. The AI must **drive engineering actions safely** — it must not fabricate dimensions, material data, or analysis numbers.

## Decision
Define a single `AIProviderPort` with **tool/function-calling** semantics, implemented by `ClaudeProvider`, `OpenAIProvider`, and `OllamaProvider`. The tools exposed to the model are the engine's own capabilities (`create_part_from_template`, `edit_feature_program`, `run_calculator`, `estimate_print`, `query_material`, `run_fea`, `repair_mesh`). The model **orchestrates tools**; all numbers originate from deterministic solvers/library data, never from free text. Provider is selectable per request; responses stream over WebSocket; prompt/response caching reduces cost.

## Consequences
**Positive:** provider-independent core; offline capability; safety by construction (numbers come from tools); testable via a deterministic mock provider; cost control via caching and the template path.
**Negative:** must normalise three different tool-calling APIs behind one interface; capability schemas must be kept in sync across providers.
**Neutral:** encourages exposing engine features as well-typed tools — which also benefits the plugin system.

## Alternatives considered
- **Single hardcoded provider:** rejected — no offline/private option, vendor lock-in.
- **Free-text prompting without tools:** rejected — invites fabricated numbers and unverifiable actions.
- **LangChain-style mega-framework:** rejected for the core — heavier than needed; we keep a thin, typed port. (Reference the bundled `claude-api` guidance for Claude tool-runner patterns.)
