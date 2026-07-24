# TODO

Active worklist. Checked items are done + committed. See `docs/05-roadmap.md` for the full multi-phase plan and `PROJECT_STATUS.md` for current health.

## Phase 0 — Bootstrap & Foundations

### M0.1 — Repo foundation + tracking docs ✅
- [x] Monorepo root config (pnpm/turbo/tsconfig base)
- [x] Tracking docs: PROJECT_STATUS, CHANGELOG, TODO, root ARCHITECTURE
- [x] Shared config package (`packages/config`: tsconfig, eslint)
- [x] `.editorconfig`
- [x] Commit

### M0.2 — Python 3.12 engine bootstrap ✅
- [x] `pyproject.toml` (uv), FastAPI + uvicorn, ruff + mypy + pytest
- [x] Clean-architecture skeleton: `domain / application / ports / adapters / api / di`
- [x] Config module (env-driven, typed) — no hardcoded secrets
- [x] `AIProvider` port + `StubProvider` + `ClaudeProvider` (+ registry/selection by config)
- [x] `GET /health`, `GET /api/v1/capabilities`, `POST /api/v1/ai/chat` (bearer-token auth when configured)
- [x] Unit tests (providers, config, DI, routes) green — 20 passed; ruff + mypy strict clean
- [x] Live smoke test (boot uvicorn, hit all endpoints offline); commit

### M0.3 — Electron + React + TS shell ✅
- [x] Desktop main (hardened: contextIsolation, sandbox, no nodeIntegration, nav lockdown) + preload allowlist + typed IPC (`packages/ipc-contracts`, Zod-validated both ways)
- [x] Engine supervisor (spawn/monitor/restart pinned 3.12 interpreter, ephemeral port, bearer token, exponential backoff)
- [x] React + TS renderer (Vite + Tailwind dark shell) with engine status store + REST client
- [x] Dialog-gated file access (PathAllowlist) — renderer can only read user-picked paths
- [x] 31 TS tests green (contracts 7, desktop 12, renderer 12); `--smoke` e2e spawns real engine → running; commit

### M0.4 — 3D viewport ✅
- [x] Three.js (r3f) scene: orbit controls (damped), 4-light rig, 220mm grid + axes, camera auto-fit on content change
- [x] STL loader (binary + ASCII, Z-up→Y-up) + click selection with highlight; scene tree panel (select/hide/remove); inspector (dims mm, triangle count)
- [x] Dialog-gated import flow; 17 new tests (46 renderer/desktop/contracts total); visual + WebGL verification; commit

### M0.5 — AI chat panel ✅
- [x] Chat UI → engine `/ai/chat` via `AIProvider` (multi-turn history, system prompt, provider/model badges, collapsible reasoning)
- [x] Offline request queue: retryable failures queue with exponential backoff (3s→30s), auto-flush on engine reconnect, manual "Retry queued", correct reply ordering for queued backlogs
- [x] 7 store tests (36 renderer total); request shape verified against the live engine; commit

### M0.6 — Project manager ✅
- [x] `CloudService` port + `LocalOnlyCloud` (always works) + `SupabaseCloud` (auth + project backup; enabled by env, lazy client, network-failure-safe)
- [x] `.efproj` bundle format (versioned schema, atomic writes, asset import with sanitized dedup names); recents (dedupe, prune-deleted, corrupt-safe)
- [x] Project panel UI (new/open/recent/save/close, dirty indicator); opening a project reloads its parts into the viewport; STL import copies into project assets and records a part
- [x] Directory-scoped path allowlist for opened projects (traversal + prefix-sibling tested)
- [x] 24 new tests (contracts 11 / desktop 36 / renderer 39 total); smoke e2e re-verified; commit

### M0.7 — Blender integration ✅
- [x] Detect local Blender (env override → PATH → versioned Program Files scan; version probe cached) — finds Blender 5.0 on this machine
- [x] Launch Blender (detached GUI, optional file); execute headless Python scripts with `EFC_RESULT` JSON round-trip, timeouts, output capture
- [x] Conversion service: STL/OBJ/PLY/GLB/GLTF/3MF natively (trimesh + own spec-compliant 3MF reader/writer — works without Blender); FBX via Blender with version-fallback operators; FBX⇄3MF via STL hop; STEP/IGES → honest 501 CAPABILITY_NOT_AVAILABLE (Phase 1 CAD kernel)
- [x] API: /blender/status,/launch,/run-script + /convert; capabilities reports formats + blender detection
- [x] Renderer: Inspector "Open in Blender" + "Export As…" (3MF/STL/OBJ/PLY/GLB/FBX)
- [x] 20 engine tests incl. 3 real-Blender integration tests (script exec + real STL→FBX); engine 56 / renderer 40; commit

### M0.8 — Flashforge workspace ✅
- [x] Printer profiles: 6 Flashforge machines (AD5X 4-material filament-switching, Adventurer 5M/Pro, Creator Pro 2 + 4S IDEX, Guider 3) with build volume, temps, purge-per-change
- [x] Material library: 10 curated materials (PLA→PC, PVA/HIPS soluble supports) with density, strength, modulus, temps, shrinkage, cost — schema-validated at load
- [x] Compatibility engine: adhesion-family rules + nozzle-window/bed-delta checks (ok/caution/incompatible with reasons); caught 2 real data errors during testing
- [x] Usage estimate (volume→mass/cost with stated assumptions, watertight check, rotation-aware fit) + purge-tower estimate (tool-change model)
- [x] Multi-material 3MF export (per-part color/material) — FlashPrint-compatible container, verified by reader round-trip
- [x] Renderer: Flashforge panel (printer select, 4-slot material/color setup, compatibility warnings, per-part slot assignment, estimates, Export 3MF); build volume + bed grid in viewport; all state mirrored into `.efproj`
- [x] 31 engine tests + 7 store tests; live e2e of the full flow; commit

**PHASE 0 COMPLETE**

## Phase 1 — MVP walking skeleton

### M1.1 — Skeleton & viewport ✅ (delivered during Phase 0: shell, supervisor, IPC, viewport)

### M1.2 — Feature Program IR + CadQuery kernel + parametric rebuild ✅
- [x] CadQuery 2.8 installed on Python 3.12 (risk gate passed; resolved numpy/numba constraint conflict)
- [x] Safe expression evaluator (AST whitelist: arithmetic, params, min/max/abs/round; injection-tested)
- [x] Feature Program IR v1 (`efir/1`): parameters + sketch(rect/circle/polygon)/extrude/hole(rows)/fillet, validation, camelCase wire form
- [x] CadQueryKernel: lazy OCP import, exact B-rep volume/CoG/bbox, RawMesh transport, typed GeometryError with actionable hints
- [x] L-Bracket template with engineering checks (min wall, fillet<T/2, hole overlap); golden tests vs closed-form volumes (rel 1e-6)
- [x] PartsService + API: /templates, /parts/from-template, /parts/compile, GET, PATCH /params (validated live rebuild), /export (STEP/STL/3MF/OBJ/GLB)
- [x] Renderer: ParametricPanel (sliders/inputs, mass/warnings, undo/redo), debounced live rebuild with geometry swap, template creation, Inspector STEP export, `.efproj` persistence (parametric parts recompile on open)
- [x] Verified: 40 new engine tests (127 total) + 12 new renderer tests (59 total); live e2e — rebuilds avg 162ms/max 250ms (<500ms target), STEP ISO-10303 verified, reopen identical; commit

### M1.3 — AI design pipeline ✅
- [x] AiToolbox: engine capabilities as tools (list_part_templates, create_part_from_template, update_part_parameters) — all numbers from the kernel, never generated text (ADR-0003)
- [x] Claude provider: manual tool-calling loop (assistant echo + tool_result turns, error results, usage summed, 6-iteration cap) — tested against a scripted fake client
- [x] StubProvider: deterministic offline design flow ("Design a bracket 50x70, 4 mm thick, with 2 holes, in petg" → real compiled part) — the MVP story works with zero credentials
- [x] ChatResponse.actions → renderer: created parts auto-load into viewport + project doc; updated parts refresh geometry; action chips in chat
- [x] 10 engine + 1 renderer tests (137/60); live HTTP chat-design verified; commit
- [x] Later (Phase 2): IR patch proposals as reviewable diffs before apply → **done in M2.2**; streaming tool progress over WS → still pending

### M1.4 — MVP polish ✅ — **PHASE 1 MVP COMPLETE**
- [x] Print estimate accepts `partId` (exact B-rep volume/bbox, watertight by construction) — Flashforge panel estimates parametric parts
- [x] Orientation hint (lay-flat bbox heuristic, labelled as such) on all estimates
- [x] Bulk 3MF export mixes mesh files and live parametric parts (`partId` entries)
- [x] CI workflow committed (`.github/workflows/ci.yml`: TS suites + engine ruff/mypy/pytest on 3.12) — activates with a GitHub remote
- [x] MVP acceptance checklist run and recorded in docs/06-mvp-plan.md (deviations documented: diff-approval → Phase 2, time estimate → Phase 4 slicer profiles, FlashPrint manual gate)

## Phase 2 — next up (docs/05-roadmap.md)

### M2.1 — Template library expansion (in progress)
- [x] **Mounting/adapter plate** template: rectangular plate, symmetric 4-corner hole pattern (two linear-row holes), center bore, optional rounded corners — built from the existing IR. 16 golden/API tests.
- [x] **IR `shell` feature** (hollow a solid to a wall thickness, remove named faces) + kernel executor with a volume-decrease guard (caught CadQuery silently returning the un-hollowed solid for over-thick walls) + **Enclosure/project-box** template (open-top hollow box, floor, rounded corners). 15 golden/API tests incl. closed-form cavity volume.
- [x] Proved the template registry is a true plugin seam: `AiToolbox.list_part_templates` and the Claude/stub design flows discover new templates with zero AI-layer code change.
- [x] **Standoff / spacer** template (round tube: cylinder + concentric through-bore) — 6 golden tests vs π/4·(OD²−ID²)·H. Four templates now.
- [x] **Gear (spur)** — added a `GearProfile` IR profile kind; the kernel expands it into a closed involute tooth outline at compile time (`gear_outline`: base/pitch/addendum/root circles, involute flanks sized to the standard tooth thickness, radial drop + root arc between teeth), so the tooth count Z is a live parameter. New **Spur Gear** template (module/teeth/face-width/bore/pressure-angle) with an undercut warning (<17 teeth). Fifth template. 13 golden/API tests (bounded volume, exact key radii, tooth count, degenerate-param guards).
- [x] **Flanged Standoff** (offset-extrude stacking) and **Counterbored Boss** (offset + boolean-cut recess) templates — 6th and 7th templates.
- [ ] Pipe fitting, clamp — evaluate case by case against the IR feature set

### M2.6 — IR feature expansion
- [x] **`chamfer`** feature (edge chamfer parallel to an axis) — mirrors fillet.
- [x] **Plane-offset extrude** (`ExtrudeFeature.offset`) — stacked/flanged multi-body parts without a boolean feature.
- [x] **Boolean extrude modes** (`ExtrudeFeature.mode` = union/cut/intersect) — arbitrary pockets/slots/trims against the running solid.
- [x] **`revolve`** feature (solids of revolution around an in-plane axis, partial/full angle) — unlocks turned parts; **Tapered Spacer** template (8th) built on it.

### M2.5 — Freeform (text-to-CAD) generation
- [x] **Sandboxed freeform CAD** (integrating the approach of earthtojake/text-to-cad): the AI writes a CadQuery script, executed through a static AST guard (`script_guard`: import allow-list, no dunder access, no dangerous builtins, requires a `result` assignment) + a **separate-process sandbox** (restricted builtins, audit hook blocking process/network, hard timeout). Produces a **non-parametric mesh part** that loads in the viewport alongside IR parts (not editable in the Parameters panel). Volume/bbox still measured from the real B-rep (ADR-0003 preserved). New `POST /api/v1/freeform` (+ get/export STEP/STL), AI tool `generate_cad_script`, renderer `registerFreeformPart`. Implemented on the existing CadQuery kernel (build123d resolves but swaps the OCP variant + destabilises the proven setup). 33 new tests (guard + real-subprocess service/API/tool + renderer). Attribution in `NOTICE.md`. **Security caveat: best-effort, not a hardened boundary — true isolation needs a container (gated on Docker).**

### M2.2 — AI & UX depth
- [x] **Reviewable IR diffs for AI edits before apply**: `update_part_parameters` now *proposes* a validated `ParamDiffEntry[]` (old→new per parameter) instead of mutating the part. The engine never recompiles on a proposal; the chat UI shows an Apply/Discard diff card, and only Apply triggers the real PATCH + geometry swap + project-doc persist. 15 new tests (engine preview/tool-loop + renderer store/component). No-op values are dropped from the diff.
- [x] **Streaming chat responses**: `POST /api/v1/ai/chat/stream` streams `ChatStreamEvent`s as newline-delimited JSON over chunked HTTP (chosen over a raw WebSocket — reuses the bearer-token header, CORS, error envelope, and the mockable `fetch` transport; no bidirectional need for request-scoped chat). `AIProvider.stream` has a default single-chunk wrapper; Stub streams word-by-word, Claude streams real token deltas through the manual tool loop (emitting `action` events as tools run). Renderer `chatStream` async-generator parses NDJSON; the chat store accumulates deltas into a live assistant bubble and finalizes on `done`, preserving the offline queue on pre-first-chunk failures. 12 new tests (engine provider/endpoint + renderer client/store).
- [ ] Rebuild progress streaming — **deferred, honestly**: a rebuild is one ~160 ms `kernel.compile()` call with no real intermediate progress; a progress bar would be fabricated (violates the no-placeholder rule). Revisit only if/when rebuilds get slow enough to instrument real kernel stages.

### M2.3 — Data plane (offline-safe parts done; Postgres/Supabase round-trip needs user actions)
- [x] **Prisma initial migration** generated offline from the canonical schema (`prisma/migrations/0001_init/migration.sql`, 483 lines — all tables/enums/indexes/FKs) + `migration_lock.toml`. Ready to `prisma migrate deploy` the moment a Postgres URL exists. (Applying it still needs Docker/a DB — user action.)
- [x] **CloudSyncQueue** — offline-first background project backup over the existing `CloudService`: dedupe by project id (latest doc wins), exponential-backoff retry on failure, no-op when local-only, disposed on quit. Wired to new IPC `cloud:queueProject` / `cloud:syncStatus`. 5 desktop tests (no-op local, push+clear, dedupe-while-queued, backoff-then-succeed, dispose). Mirrors the chat delivery-queue policy.
- [ ] Real Supabase round-trip verification (needs `SUPABASE_URL` + keys — user action) and a renderer sync-status indicator.
- [ ] Prisma client generation + runtime data-plane wiring for hosted mode (needs Docker Postgres — user action).

### M2.4 — UI depth
- [x] **Feature Timeline panel**: read-only ordered view of the selected parametric part's IR feature list (op glyph + id + per-op summary; sketch/extrude/hole/fillet/shell). Makes the model recipe visible. 11 renderer tests (featureSummary pure logic + component render + store population). Header badge fixed to "Phase 2".
- [x] **Feature reordering**: the Feature Timeline is now interactive — per-feature move up/down (▲▼) reorders the IR and recompiles through a new `POST /parts/{id}/features/reorder` endpoint. The reordered program is compiled first; orders the kernel rejects (e.g. a fillet/hole before its extrude) leave the part unchanged and surface the geometry error. 7 new tests (engine service/API + renderer client/store/component).
- [x] **Per-feature field editing**: expanding a feature row reveals an inline editor for its scalar fields — expression/number fields as text (commit on Enter/blur), enum fields as selects — via a new `PATCH /parts/{id}/features/{featureId}` endpoint (`PartsService.patch_feature`). `op`/`id` are immutable; unknown fields and invalid values/geometry are rejected and leave the part unchanged. Complex fields (sketch profiles, polygon points, shell open-faces, hole spread axis, extrude sketch ref) are intentionally omitted from the inline editor rather than faked. 13 new tests (engine service/API + renderer helper/store/component). **M2.4 complete.**

## Deferred / needs user action
- [ ] Install Docker Desktop → enable local Postgres + `docker-compose.dev.yml`
- [ ] Provide `ANTHROPIC_API_KEY` (else AI runs on `StubProvider`)
- [ ] Provide Supabase URL + keys (else cloud sync is inert; local still works)
- [x] Configure a git remote for backup/collaboration → `origin` = github.com/dgdaguba-ui/EngineerForgeAI (CI now active)
