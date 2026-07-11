# 02 — Folder Structure

A **pnpm-workspace + Turborepo monorepo**. Rationale: the TS UI/data plane and shared domain types must evolve atomically; the Python engine lives in the same repo for coordinated releases and contract tests, but is an independent build unit.

```
engineerforge-ai/
├─ apps/
│  ├─ desktop/                     # Electron shell (TypeScript)
│  │  ├─ src/
│  │  │  ├─ main/                  # main process: window, menus, auto-update
│  │  │  │  ├─ supervisor/         # spawns/monitors the Python engine
│  │  │  │  ├─ ipc/                # typed IPC handlers (validate w/ ipc-contracts)
│  │  │  │  ├─ data/               # Prisma client + Supabase SDK (data plane)
│  │  │  │  └─ di/                 # composition root (wire adapters → ports)
│  │  │  └─ preload/               # contextBridge surface (the ONLY renderer API)
│  │  ├─ electron-builder.yml
│  │  └─ package.json
│  │
│  ├─ renderer/                    # Next.js + React + Three.js UI
│  │  ├─ src/
│  │  │  ├─ app/                   # Next.js app router (also hosts BFF API routes)
│  │  │  ├─ features/              # feature-sliced UI: viewport, chat, params,
│  │  │  │                         #   assembly-tree, materials, drawings, print
│  │  │  ├─ viewport/              # react-three-fiber scene, gizmos, section views
│  │  │  ├─ state/                 # Zustand stores (session/project/viewport/chat)
│  │  │  ├─ ipc/                   # typed client to main process
│  │  │  └─ engine-client/         # generated OpenAPI client for the Python engine
│  │  └─ package.json
│  │
│  └─ engine/                      # Python FastAPI kernel (Intelligence plane)
│     ├─ engineerforge_engine/
│     │  ├─ domain/                # pure entities + Feature Program IR (Pydantic)
│     │  ├─ application/           # use cases (GeneratePart, Rebuild, RepairMesh…)
│     │  ├─ ports/                 # abstract interfaces (CadKernel, Mesh, AI, Slicer…)
│     │  ├─ adapters/              # cadquery/ trimesh/ open3d/ ai/ slicer/ blender/
│     │  ├─ api/                   # FastAPI routers + schemas (v1)
│     │  ├─ sandbox/               # hardened subprocess exec for generated code
│     │  ├─ templates/             # parametric part generators (bracket, gear…)
│     │  ├─ calculators/           # bolt, beam, gear, spring, tolerance…
│     │  ├─ fea/                   # FEA-lite solvers
│     │  ├─ di/                    # dependency-injector container
│     │  └─ config.py
│     ├─ tests/                    # pytest: unit, integration, golden, property
│     ├─ pyproject.toml            # uv/poetry; targets Python 3.12
│     └─ README.md
│
├─ packages/
│  ├─ core-domain/                 # shared TS domain types + IR schema (source of truth)
│  │  └─ src/                      #   → generates Python Pydantic + TS Zod from one schema
│  ├─ ipc-contracts/               # typed IPC channels + Zod request/response schemas
│  ├─ ui/                          # design system: dark theme, dockable panels, primitives
│  ├─ materials/                   # material library data (JSON) + schema + loader
│  └─ config/                      # shared eslint, tsconfig, tailwind, prettier
│
├─ prisma/
│  ├─ schema.prisma                # data-plane schema (see 03-database-schema.md)
│  ├─ migrations/
│  └─ seed.ts                      # seed materials, demo project
│
├─ infra/
│  ├─ docker/                      # engine image, hosted-mode compose
│  ├─ ci/                          # reusable CI scripts
│  └─ deploy/                      # hosted deployment manifests
│
├─ docs/                           # this documentation set + ADRs + diagrams
├─ tests/
│  └─ e2e/                         # Playwright end-to-end across the Electron app
├─ scripts/                        # dev bootstrap, codegen (OpenAPI→TS, schema→Pydantic)
│
├─ .github/workflows/              # CI/CD (lint, test, build installers, docker, release)
├─ pnpm-workspace.yaml
├─ turbo.json
├─ package.json                    # root scripts (dev, build, test, lint)
├─ .nvmrc                          # Node 20 LTS
├─ .python-version                 # 3.12 (engine)
├─ .gitignore
└─ README.md
```

## Conventions

- **Feature-sliced UI** (`renderer/src/features/*`): each panel is a self-contained slice (components, hooks, local state, tests) — not layered by type. Keeps the 20+ panels independently ownable.
- **Ports live with the layer that owns the abstraction**; adapters are grouped by vendor under `adapters/`.
- **One source of truth for cross-language types**: the IR + DTOs are defined once (`packages/core-domain`) and code-generated into Zod (TS) and Pydantic (Python) so the contract can't drift. `scripts/codegen` runs in CI.
- **Tests co-locate** with code (`*.test.ts`, `test_*.py`); only cross-app e2e lives in top-level `tests/`.
- **No app imports another app**; they communicate only through `packages/*` contracts and the network/IPC boundaries.

## Build graph (Turborepo)

`core-domain` → `ipc-contracts`/`materials`/`ui` → `renderer`/`desktop`. The Python `engine` builds independently (uv/poetry) but its OpenAPI schema feeds `renderer/engine-client` codegen. `turbo run build` respects this graph and caches per-package.
