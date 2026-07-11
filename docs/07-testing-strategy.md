# 07 — Testing Strategy

Testing is an **exit-bar requirement of every milestone**, not a phase. The goal: prevent the "25 shallow features" failure mode by making each vertical slice provably correct before the next.

## Test pyramid

```
         ▲  E2E (Playwright over Electron)        few, high-value user journeys
        ▲▲  Contract tests (OpenAPI ↔ client; IPC schemas)
       ▲▲▲  Integration (use case + real adapters; engine API; DB w/ ephemeral PG)
      ▲▲▲▲  Component (React Testing Library) + property/golden (geometry)
     ▲▲▲▲▲  Unit (domain, calculators, IR eval, planner) — many, fast
```

## By area

### TypeScript (renderer / desktop / packages)
- **Unit:** Vitest — domain types, IR client, stores, planner glue, IPC validators.
- **Component:** React Testing Library — panels (param editor, chat, inspector); interaction + a11y assertions.
- **Contract:** generated engine client tested against the OpenAPI schema; IPC channels validated against `ipc-contracts` Zod schemas (drift fails CI).
- **E2E:** Playwright drives the built Electron app for the MVP journeys (prompt→part→edit→export→save→reopen). Runs headless in CI, screenshots on failure.

### Python (engine)
- **Unit:** pytest — IR expression evaluator, feature DAG ordering, calculators (asserted against **textbook reference values**), planner intent→template mapping.
- **Property-based:** Hypothesis — geometry invariants that must always hold:
  - compiled parts are **watertight** and **manifold**;
  - `volume > 0`, `mass = volume × density`;
  - repair(makes-broken) ⇒ watertight;
  - parametric rebuild is **deterministic** (same IR ⇒ same mesh hash within float tol).
- **Golden-file:** canonical intents → stored volume/bbox/mesh-hash; regressions flagged. Golden assets versioned; regeneration is an explicit, reviewed step.
- **Integration:** FastAPI `TestClient` — endpoints incl. rebuild, export, estimate; **mocked deterministic AI provider** so AI-driven paths are reproducible.
- **Sandbox tests:** assert generated-code sandbox blocks network, filesystem escape, disallowed imports, and enforces timeouts.
- **Benchmarks:** pytest-benchmark on rebuild/compile; perf budgets asserted (see [`11-performance.md`](11-performance.md)).

### Data plane
- Prisma against an **ephemeral Postgres** (Testcontainers/CI service); migration up/down tested each PR.
- RLS policy tests: a user cannot read another user's rows/objects.
- Sync/reconcile tests: offline edits merge correctly; immutable versions never conflict.

### AI-specific testing
- **Determinism harness:** provider mock returns fixed tool-call sequences → pipeline assertions are stable.
- **Guardrail tests:** the model can change geometry/numbers **only** via tool-calls; free-text "numbers" never mutate state.
- **Eval suite (offline, non-blocking):** a set of prompts scored for intent-parse accuracy and template selection; tracked over time, not gated per-PR (flaky by nature). Run nightly.
- **Injection tests:** malicious content in imported files/model output is treated as data, never executed as instructions.

## Coverage & quality gates
- Domain + calculators + IR core: **≥90%** line/branch.
- Application/use-cases: **≥80%**.
- Adapters/UI: pragmatic; critical paths covered, no hard % gate.
- CI blocks merge on: lint, typecheck (TS strict + mypy), unit + integration + contract, and the MVP e2e once it exists.
- Flaky tests are quarantined with an owner + issue, never left to rot in the suite.

## Test data & fixtures
- Canonical IR fixtures + known-broken meshes + reference calculator cases live in `apps/engine/tests/fixtures` and `tests/fixtures`.
- Sample exported STL/3MF used to gate "sliceable" checks are checked in and re-validated.

## Manual verification gates (can't be fully automated)
- Exported geometry **opens & slices** in FlashPrint / OrcaSlicer (checklist per release).
- Multi-material colour/material mapping visually correct (Phase 4).
- Blender round-trip fidelity (Phase 6).
These are release-checklist items with checked-in sample outputs to reduce manual burden over time.
