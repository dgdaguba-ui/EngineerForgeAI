# Architecture Decision Records

Each ADR captures one significant decision: context, the decision, and its consequences. Status is one of `Proposed | Accepted | Superseded`. New decisions add a new numbered file; we don't rewrite history — we supersede.

| # | Title | Status |
|---|---|---|
| [0001](0001-python-engine-sidecar.md) | Python engine as a sidecar process (not WASM) | Accepted |
| [0002](0002-feature-program-ir.md) | Feature Program IR as the core editable artifact | Accepted |
| [0003](0003-ai-provider-abstraction.md) | AI provider abstraction with tool-calling | Accepted |
| [0004](0004-local-first-with-cloud-sync.md) | Local-first data with optional cloud sync | Accepted |

**Template:** copy this structure for new ADRs.
```
# NNNN — Title
Status: Proposed | Accepted | Superseded by NNNN
## Context
## Decision
## Consequences (positive / negative / neutral)
## Alternatives considered
```
