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

### M0.7 — Blender integration
- [ ] Detect local Blender (5.0) + configurable path
- [ ] Launch Blender; execute Blender Python scripts (headless)
- [ ] Import/export STL, OBJ, GLB (trimesh) + STEP, 3MF (Blender/OCP)
- [ ] Commit

### M0.8 — Flashforge workspace
- [ ] Printer profiles (build volume, nozzles, materials)
- [ ] Material library (seed) + multi-material setup
- [ ] Build-volume visualization in viewport
- [ ] FlashPrint-compatible export
- [ ] Commit

## Deferred / needs user action
- [ ] Install Docker Desktop → enable local Postgres + `docker-compose.dev.yml`
- [ ] Provide `ANTHROPIC_API_KEY` (else AI runs on `StubProvider`)
- [ ] Provide Supabase URL + keys (else cloud sync is inert; local still works)
- [ ] Configure a git remote for backup/collaboration
