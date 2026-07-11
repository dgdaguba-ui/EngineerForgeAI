# Changelog

All notable changes to EngineerForge AI are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **Project manager (M0.6):** local-first `.efproj` bundle format (versioned Zod schema, atomic saves, asset imports with sanitized de-duplicated names), recents list (deduped, prunes deleted, corrupt-safe), Project panel (new/open/recent/save/close with dirty indicator). Opening a project restores its parts into the 3D viewport; imports inside a project copy into `assets/` and record parts. `CloudService` abstraction with `LocalOnlyCloud` and `SupabaseCloud` (env-gated, lazy client, degrades cleanly offline — local files remain the source of truth). Directory-scoped file-access approvals for opened projects. Dev `.env` loader in the Electron main process.
- **AI chat panel (M0.5):** copilot chat wired to the engine's `AIProvider` endpoint with multi-turn history and an engineering system prompt; offline-first delivery queue (retryable failures queue with 3s→30s backoff, auto-flush when the engine reconnects, manual retry); replies inserted in correct conversational order for queued backlogs; provider/model badges and collapsible reasoning display.
- **3D viewport (M0.4):** react-three-fiber scene with damped orbit controls, printer-scale grid + axes, multi-light rig, camera auto-fit; STL import (binary + ASCII, Z-up→Y-up normalization) through the dialog-gated IPC path; click-to-select with emissive highlight; Scene panel (select/hide/remove, palette colors) and Inspector panel (mm dimensions, triangle count). three.js split into its own build chunk.
- **Desktop shell (M0.3):** hardened Electron main (contextIsolation, sandbox, single-instance, navigation lockdown), self-contained preload with channel allowlist, `@efc/ipc-contracts` (Zod-validated typed IPC + push events), EngineSupervisor (pinned Python 3.12, ephemeral port, per-session bearer token, health gate, exponential-backoff restarts, `--smoke` e2e mode), dialog-gated file access. Vite + React + Tailwind dark renderer with engine status store, typed engine REST client, and live engine health/capabilities card. ADR-0005 (Vite renderer). 31 TS tests.
- **Engine (M0.2):** Python 3.12 FastAPI engine with clean architecture (`domain/application/ports/adapters/di/api`), typed env-driven config, `AIProvider` port with offline `StubProvider` + `ClaudeProvider` (Claude Opus 4.8, adaptive thinking), provider auto-selection with offline fallback, single error envelope, optional bearer-token auth, `/health`, `/api/v1/capabilities`, `/api/v1/ai/chat`. 20 unit/integration tests; ruff + strict mypy clean.
- Phase 0 architecture package: overview, architecture, folder structure, database schema, API design, roadmap, MVP plan, testing strategy, deployment, CI/CD, security checklist, performance strategy (`docs/`).
- Architecture Decision Records 0001–0004 (`docs/adr/`).
- Monorepo scaffold: pnpm workspaces + Turborepo; root config (`package.json`, `pnpm-workspace.yaml`, `turbo.json`, `.gitignore`, `.env.example`, `.nvmrc`, `.python-version`).
- Canonical Prisma data-plane schema (`prisma/schema.prisma`).
- Project tracking docs: `PROJECT_STATUS.md`, `CHANGELOG.md`, `TODO.md`, root `ARCHITECTURE.md`.

### Notes
- Toolchain verified on the dev machine: Node 20.18, pnpm 9.12, Python 3.12.11 (uv), Blender 5.0.
- Docker/Postgres deferred (offline-first does not require them).
