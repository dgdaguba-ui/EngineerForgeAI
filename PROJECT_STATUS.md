# Project Status — EngineerForge AI

_Living document. Updated at every milestone._

**Last updated:** 2026-07-11
**Current phase:** Phase 0 — Bootstrap & Foundations
**Build health:** 🟢 toolchain verified; engine milestone in progress

## Environment (verified 2026-07-11)
| Tool | Status | Notes |
|---|---|---|
| Node | 20.18.0 ✅ | `.nvmrc` |
| pnpm | 9.12.0 ✅ | installed via npm (corepack signature bug on this Node build) |
| Python (engine) | 3.12.11 ✅ | uv-managed; **NOT** system Python 3.14 |
| uv | 0.11.15 ✅ | manages the engine interpreter + deps |
| Blender | 5.0 ✅ | `C:\Program Files\Blender Foundation\Blender 5.0` |
| Docker | ❌ deferred | not installed; **not required** for offline-first. Needed only for local Postgres/hosted mode. Compose files written & ready. |
| Network (npm/PyPI) | ✅ | reachable |

## Phase 0 milestones
| # | Milestone | Status |
|---|---|---|
| 0.1 | Repo foundation + tracking docs + shared config | ✅ `ab4b7fb` |
| 0.2 | Python 3.12 engine (FastAPI, DI, AIProvider abstraction, tests) | ✅ 20 tests, ruff+mypy clean |
| 0.3 | Electron + React + TS shell (supervisor, IPC, health) | ✅ 31 TS tests + smoke e2e |
| 0.4 | 3D viewport (Three.js: orbit, lights, grid, selection, STL) | ✅ 46 TS tests |
| 0.5 | AI chat panel (→ AIProvider, offline queue) | ✅ 36 renderer tests |
| 0.6 | Project manager (CloudService: Local source-of-truth + Supabase) | ✅ 86 TS tests total |
| 0.7 | Blender integration (detect/launch/exec, STL/STEP/OBJ/3MF/GLB IO) | 🟡 in progress |
| 0.8 | Flashforge workspace (profiles, materials, build volume, FlashPrint export) | ⬜ |

## Key decisions in force
- **Offline-first.** Local `.efproj` files are the source of truth; Claude + Supabase are wired but never required. See [ADR-0004](docs/adr/0004-local-first-with-cloud-sync.md).
- **Provider abstractions.** `AIProvider` (Stub/Claude/OpenAI/Ollama) and `CloudService` (Local/Supabase) — business logic never calls a vendor directly.
- **Feature Program IR** is the core editable artifact. See [ADR-0002](docs/adr/0002-feature-program-ir.md).
- **Engine on Python 3.12**, independent of system Python. See [ADR-0001](docs/adr/0001-python-engine-sidecar.md).

## Open items / risks
- Docker/Postgres deferred → cloud sync + Prisma migrations pending Docker install (user action).
- Native CAD deps (CadQuery/OCP, Open3D) land in Phase 1/3; verify 3.12 wheels on Windows at that point.
- Git repo is local-only (no remote configured yet).
