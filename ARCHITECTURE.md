# Architecture (Living Summary)

> This is the **living, implementation-tracking** architecture summary. The full design lives in [`docs/01-architecture.md`](docs/01-architecture.md) and the ADRs in [`docs/adr/`](docs/adr/). This file reflects what is **actually built** and how the pieces fit as the code grows.

## The system in one picture

```
Electron Desktop (TypeScript)
├─ main process   → window, OS, engine supervisor, IPC broker, CloudService (Local/Supabase)
├─ preload        → narrow contextBridge surface (window.efc)
└─ renderer (React+TS+Three.js) → dockable UI, 3D viewport, AI chat, project manager
                      │ localhost REST/WS (token)
                      ▼
Python Engine (FastAPI, 3.12)  → Geometry & Intelligence plane
├─ domain / application / ports / adapters   (clean architecture + DI)
├─ AIProvider abstraction  → Stub | Claude | (OpenAI | Ollama future)
├─ (Phase 1+) CAD kernel, mesh, FEA, slicer, Blender bridge
```

## Two planes, clear ownership
- **Application & Data plane (TypeScript):** UI, orchestration, `CloudService` (LocalStorageProvider = source of truth; SupabaseProvider = optional sync/auth), persistence.
- **Geometry & Intelligence plane (Python):** `AIProvider` orchestration, and (later) CAD/mesh/FEA/slicer/Blender.

## Core principles (enforced in code)
1. **Offline-first.** Every local feature works with no internet. Cloud enhances, never gates. ([ADR-0004](docs/adr/0004-local-first-with-cloud-sync.md))
2. **Provider abstraction.** Business logic depends on `AIProvider` / `CloudService` **ports**, never on Anthropic/Supabase SDKs directly. Providers are selected by config and swappable. ([ADR-0003](docs/adr/0003-ai-provider-abstraction.md))
3. **Feature Program IR** is the editable artifact; AI edits IR, not meshes/code. ([ADR-0002](docs/adr/0002-feature-program-ir.md))
4. **Clean architecture + SOLID.** Dependencies point inward; adapters wired at a composition root via DI. Fully unit-testable with fakes.
5. **Modular/plugin-ready.** Capabilities (part generators, calculators, exporters, AI tools) register against typed contracts.
6. **Security.** No hardcoded secrets; env/keychain; untrusted code sandboxed; hardened Electron. ([`docs/10-security-checklist.md`](docs/10-security-checklist.md))

## Provider abstraction (as implemented)

```
AIProvider (port)                     CloudService (port)
├─ StubProvider     (offline/dev, default when no key)   ├─ LocalStorageProvider  (source of truth)
├─ ClaudeProvider   (Anthropic)                          └─ SupabaseProvider      (auth + optional sync)
├─ OpenAIProvider   (future)
└─ OllamaProvider   (future, local)
```
Selection: `EFC_AI_PROVIDER` / `EFC_CLOUD_PROVIDER` config → DI container resolves the concrete adapter. Absent credentials ⇒ graceful fallback to `StubProvider` / `LocalStorageProvider`; the app never breaks.

## Current implementation state (Phase 0 complete)
- ✅ **Engine** (`apps/engine`, Python 3.12/FastAPI): clean architecture + DI; `AIProvider` (Stub offline / Claude via adaptive-thinking Opus 4.8); Blender adapter (detect/launch/headless scripts); conversion service (STL/OBJ/PLY/GLB/GLTF/3MF native via trimesh + own 3MF reader/writer, FBX via Blender, STEP → honest 501 until Phase 1); material/printer catalogs; compatibility engine; usage/purge estimates; multi-material 3MF export. 87 tests, mypy strict.
- ✅ **Desktop** (`apps/desktop`, Electron): hardened shell, engine supervisor (pinned 3.12, token, backoff restarts, `--smoke` e2e), Zod-validated IPC, dialog-gated file access, local-first `.efproj` store + recents, `CloudService` (LocalOnly/Supabase). 36 tests.
- ✅ **Renderer** (`apps/renderer`, Vite/React): dark workspace shell; r3f viewport (orbit/grid/lights/selection/STL, printer build volume); AI chat with offline delivery queue; project panel; Flashforge panel (slots, compatibility, estimates, 3MF export); Inspector with Blender/export actions. 47 tests.
- ✅ **Contracts** (`packages/ipc-contracts`): channel map + `.efproj` schema shared by main/preload/renderer. 11 tests.
- ✅ **Parametric core (M1.2):** Feature Program IR v1 + safe expression evaluator (`domain/`), CadQueryKernel behind `CadKernelPort` (exact B-rep props, RawMesh transport), template registry (L-Bracket first) with engineering checks, PartsService session store, parts/templates API; renderer ParametricPanel (live debounced rebuild, undo/redo), STEP export, `.efproj` parametric persistence. Golden-tested vs closed-form volumes; live rebuild ~160 ms.
- ⬜ **Phase 1 remaining:** M1.3 AI design pipeline (tool-calling → templates → IR patches as diffs), M1.4 MVP polish (see `TODO.md`).

_When a milestone lands, update this file's "current state" and the relevant section._
