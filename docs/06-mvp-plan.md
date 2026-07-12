# 06 — MVP Plan (Engineering Detail)

The MVP is **Phase 1** of the roadmap: one part family, fully alive end-to-end. This document is the concrete build order — what to write, in what sequence, and how we know each step works.

## MVP scope (locked)

**In:** Electron shell · dark dockable UI · r3f viewport · Feature Program IR v1 · CadQuery bracket template · live parametric rebuild · AI design + edit (Claude, tool-calling) · STL/3MF/STEP export · single-material Flashforge print estimate + orientation hint · `.efproj` local save/load.

**Out (deferred to later phases):** cloud sync, multi-material, FEA, calculators beyond mass, mesh import/repair, Blender, assemblies, drawings, additional part types.

**Definition of done:** the MVP user story (see roadmap) runs reliably, is covered by unit + integration + one e2e path, and is documented in the README quickstart.

## Build order

### Step 0 — Tooling (Phase 0 remainder)
- `pnpm-workspace.yaml`, `turbo.json`, root scripts, shared `packages/config` (eslint/tsconfig/tailwind/prettier).
- Engine: `pyproject.toml` (uv), FastAPI app, `/health`, settings, DI container. **Pin Python 3.12.**
- `packages/core-domain`: IR types + schema; codegen script → Pydantic + Zod.
- **Verify:** `pnpm dev` runs all three; `/health` returns kernel + versions; `pnpm codegen` regenerates without drift.

### Step 1 — Engine: compile a hardcoded IR (Milestone 1.1)
- `domain/feature_program.py` (Pydantic IR) · `ports/cad_kernel.py` · `adapters/cadquery_kernel.py`.
- Implement `sketch(rect)`, `extrude` first; return tessellated **glTF** + mass properties.
- `POST /api/v1/parts` accepts an IR, returns `{ mesh, massProps, dfm }`.
- **Verify:** curl a bracket IR → valid glTF; pytest golden test on volume.

### Step 2 — Desktop shell + viewport (Milestone 1.1)
- `apps/desktop`: hardened `main` (contextIsolation, sandbox, no nodeIntegration), preload `window.efc`, **engine supervisor** (spawn/monitor/restart, health-gate), typed IPC.
- `apps/renderer`: Next.js in Electron; `packages/ui` dark theme + dockable layout; r3f viewport that fetches `/parts/{id}/mesh` and renders it; orbit controls, grid, lights.
- **Verify:** Playwright launches the app and asserts the bracket mesh is visible and orbitable.

### Step 3 — IR v1 + parametric rebuild + template (Milestone 1.2)
- Finalise IR v1 ops: `sketch, extrude, hole, fillet, pattern`; safe expression evaluator; feature **DAG** with partial re-execution.
- `templates/bracket_l.py`: parameter schema (W,H,T,D,R,material) + generator → IR; min-wall constraint.
- Renderer **parameter editor**: controls bound to params → debounced `PATCH /parts/{id}/params` → swap mesh; live **mass/volume** readout. IR-level **undo/redo**.
- **Verify:** golden (intent→volume±tol), property (watertight, volume>0, manifold), perf (<500 ms p95 rebuild), e2e (drag param → mesh changes).

### Step 4 — AI design + edit (Milestone 1.3)
- `ports/ai_provider.py` + `adapters/ai/claude.py` (tool-calling) + `ollama.py` stub.
- Tools: `create_part_from_template`, `edit_feature_program`, `estimate_print`, `query_material`.
- Pipeline: `POST /ai/design` (intent→planner→compile, streamed over WS) and `POST /ai/edit` (returns **IR patch**; UI shows diff → apply).
- **AI chat panel** wired to WS streaming.
- Sandbox scaffold (`sandbox/`) present for future generative fallback.
- **Verify:** integration test with a **mocked deterministic provider** drives prompt→part and edit→patch; the model changes geometry only via tool-calls; manual test with real Claude.

### Step 5 — Export + print estimate + persistence (Milestone 1.4)
- Export adapters: STL, 3MF, STEP.
- `print/estimate`: mass = volume × infill-adjusted density; time heuristic; cost from material `costPerKg`; **orientation hint** (bbox/overhang heuristic). Seed materials from `packages/materials`.
- `.efproj` bundle read/write (manifest + IR + cached mesh + thumbnail); recent-projects.
- **Verify:** exported STL/3MF slice cleanly in FlashPrint & OrcaSlicer (manual gate + checked-in sample files); reopen `.efproj` reproduces identical IR/mesh; e2e covers prompt→edit→export→save→reopen.

## MVP acceptance checklist (status 2026-07-12)
- [x] Prompt → editable parametric bracket in viewport (<60 s). *Offline stub: instant; verified live over HTTP with analytic-correct volume.*
- [x] Every parameter edits live (<500 ms p95 rebuild). *Measured avg 162 ms / max 250 ms over 5 rebuilds.*
- [x] Numbers come from tools, never generated text (ADR-0003). *Partial deviation: AI edits apply directly with action chips + undo, instead of a diff-approval step — reviewable IR diffs moved to Phase 2 (see TODO).*
- [x] STL + 3MF + STEP export. *STEP verified ISO-10303-21; 3MF verified by spec-compliant reader round-trip; FlashPrint open remains a manual release-gate item.*
- [x] Single-material print estimate (mass/cost/fit) + orientation hint. *Works for mesh files and parametric parts (exact B-rep metrics); time estimate deferred to slicer-profile integration (Phase 4).*
- [x] `.efproj` save/load round-trips identically (mesh + parametric parts recompile on open).
- [x] Unit + integration + e2e paths green (245+ tests, all suites); CI workflow committed (`.github/workflows/ci.yml`, activates with a GitHub remote); README quickstart accurate.

**MVP: functionally complete.** Remaining deviations are recorded above and in `TODO.md`, not hidden.

## Risks & mitigations (MVP)
| Risk | Mitigation |
|---|---|
| CadQuery/OCP wheels vs Python 3.14 on this machine | Engine uses a **managed Python 3.12** env (uv), independent of system Python. Documented in setup. |
| OpenCascade op crashes | Engine supervisor restarts + replays last IR; compile in a worker with timeout. |
| LLM emits invalid intent/params | Schema validation + range clamping + clarifying-question path; template path avoids codegen. |
| Rebuild latency | Partial DAG re-execution; mesh LOD; cache by IR content hash. |
| Print-estimate accuracy | Calibrate against known prints; label as estimate; refine in Phase 4. |
