# TODO

Active worklist. Checked items are done + committed. See `docs/05-roadmap.md` for the full multi-phase plan and `PROJECT_STATUS.md` for current health.

## Phase 0 — Bootstrap & Foundations

### M0.1 — Repo foundation + tracking docs ✅
- [x] Monorepo root config (pnpm/turbo/tsconfig base)
- [x] Tracking docs: PROJECT_STATUS, CHANGELOG, TODO, root ARCHITECTURE
- [x] Shared config package (`packages/config`: tsconfig, eslint)
- [x] `.editorconfig`
- [x] Commit

### M0.2 — Python 3.12 engine bootstrap
- [ ] `pyproject.toml` (uv), FastAPI + uvicorn, ruff + mypy + pytest
- [ ] Clean-architecture skeleton: `domain / application / ports / adapters / api / di`
- [ ] Config module (env-driven, typed) — no hardcoded secrets
- [ ] `AIProvider` port + `StubProvider` + `ClaudeProvider` (+ registry/selection by config)
- [ ] `GET /health`, `GET /api/v1/capabilities`, `POST /api/v1/ai/chat`
- [ ] Unit tests (providers, config, DI, routes) green
- [ ] `uv sync` + `pytest` verified; commit

### M0.3 — Electron + React + TS shell
- [ ] Desktop main (hardened) + preload + typed IPC (`packages/ipc-contracts`)
- [ ] Engine supervisor (spawn/monitor/restart pinned 3.12 interpreter)
- [ ] React + TS renderer (Vite) boots, shows engine health
- [ ] Compile + launch verified; commit

### M0.4 — 3D viewport
- [ ] Three.js scene: orbit controls, lighting, grid
- [ ] STL loader + object selection (raycast)
- [ ] Commit

### M0.5 — AI chat panel
- [ ] Chat UI → engine `/ai/chat` via `AIProvider`
- [ ] Offline request queue + retry-on-reconnect
- [ ] Commit

### M0.6 — Project manager
- [ ] `CloudService` port + `LocalStorageProvider` (source of truth) + `SupabaseProvider`
- [ ] `.efproj` create/open/save; recent projects list UI
- [ ] Commit

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
