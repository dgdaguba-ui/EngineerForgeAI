# Project Status — EngineerForge AI

_Living document. Updated at every milestone._

**Last updated:** 2026-07-12
**Current phase:** 🟢 Phase 1 in progress — M1.2 (parametric CAD core) complete; next M1.3 (AI design pipeline)
**Build health:** 🟢 all gates green

## Test & quality gates (current)

| Suite | Count | Status |
|---|---|---|
| Engine (pytest, incl. real-Blender + CAD golden tests) | 127 | ✅ |
| Renderer (vitest) | 59 | ✅ |
| Desktop (vitest) | 36 | ✅ |
| IPC contracts (vitest) | 12 | ✅ |
| **Total** | **234** | ✅ |
| ruff + mypy --strict (engine) | — | ✅ clean |
| tsc strict (all TS packages) | — | ✅ clean |
| Electron `--smoke` e2e (spawns real engine) | — | ✅ state=running |
| Live API e2e (parametric loop: create→5 rebuilds→STEP/3MF→reopen) | — | ✅ avg 162ms rebuild (<500ms target) |

## Environment (verified)
| Tool | Status | Notes |
|---|---|---|
| Node | 20.18.0 ✅ | `.nvmrc` |
| pnpm | 9.12.0 ✅ | installed via npm (corepack signature bug on this Node build) |
| Python (engine) | 3.12.11 ✅ | uv-managed; **NOT** system Python 3.14 |
| Blender | 5.0 ✅ | auto-detected; integration tests run against it |
| Docker | ❌ deferred | not required offline-first; needed for local Postgres/hosted mode |

## Milestones
| # | Milestone | Commit |
|---|---|---|
| 0.1 | Repo foundation + tracking docs + shared config | `ab4b7fb` |
| 0.2 | Python 3.12 engine (FastAPI, DI, AIProvider: Stub + Claude) | `e818a70` |
| 0.3 | Electron shell, engine supervisor, typed IPC, React renderer | `4b4de6b` |
| 0.4 | Three.js viewport (orbit/grid/lights/selection/STL) | `1154eb4` |
| 0.5 | AI chat panel with offline delivery queue | `402c6e5` |
| 0.6 | Local-first `.efproj` projects + CloudService (Local/Supabase) | `0ee5323` |
| 0.7 | Blender bridge + mesh conversion + native 3MF | `ad4f4da` |
| 0.8 | Flashforge workspace (printers/materials/compat/estimates/3MF export) | `b9556db` |
| 1.2 | **Feature Program IR + CadQuery kernel + live parametric rebuild** | HEAD |

## What M1.2 adds (the product's core)
- Click **"+ New L-Bracket"** → an editable parametric part compiles through CadQuery/OpenCascade and appears in the viewport.
- Drag any parameter (width, thickness, hole count/diameter, fillet…) → validated, debounced **live rebuild** (~160 ms) with exact B-rep mass properties and engineering warnings (min wall, fillet feasibility, hole overlap).
- IR-level **undo/redo**; **STEP/3MF/STL/OBJ/GLB export** of the B-rep; parts persist in `.efproj` as editable Feature Programs and recompile on reopen.
- Compiler correctness is golden-tested against closed-form volumes (1e-6 relative).

## What works today (run `pnpm dev`)
- Desktop app boots; supervisor spawns the Python engine (health-gated, auto-restart).
- Import STLs into a 3D viewport (orbit, selection, inspector with mm dims).
- AI copilot chat — Claude when `ANTHROPIC_API_KEY` is set, deterministic offline stub otherwise; requests queue and retry when offline.
- Projects: create/open/save transparent `.efproj` bundles; reopening restores the scene; recents list.
- Blender: detected automatically; open models in Blender; headless script execution; format conversion (STL/OBJ/PLY/GLB/GLTF/3MF native, FBX via Blender).
- Flashforge: pick a printer (build volume drawn in viewport), assign materials/colors to slots, per-part slot assignment, compatibility warnings, mass/cost/fit + purge estimates, multi-material 3MF export that FlashPrint opens.

## Key decisions in force
- **Offline-first** (ADR-0004): local files are the source of truth; Claude/Supabase optional enhancements.
- **Provider abstractions:** `AIProvider` (stub/claude, ollama/openai planned) and `CloudService` (local/supabase) — business logic never touches vendor SDKs.
- **Feature Program IR** (ADR-0002) is the Phase 1 centerpiece: AI edits an editable parametric recipe, never raw meshes.
- **Engine pinned to Python 3.12** (ADR-0001); **Vite renderer in Electron** (ADR-0005).
- **Honest capability surface:** unimplemented features return 501 `CAPABILITY_NOT_AVAILABLE` (e.g. STEP/IGES until the Phase 1 CAD kernel) — never fake output.

## Open items / user actions available
- Add `ANTHROPIC_API_KEY` to `.env` → live Claude copilot (offline stub otherwise).
- Add `SUPABASE_URL` + `SUPABASE_ANON_KEY` → cloud auth/backup (local-only otherwise).
- Install Docker Desktop → local Postgres for the Phase 2 data plane.
- Configure a git remote for backup/collaboration.
