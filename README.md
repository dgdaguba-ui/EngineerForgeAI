# EngineerForge AI

**An AI-native desktop workspace for mechanical design, parametric CAD, mesh engineering, and multi-material 3D print preparation.**

EngineerForge AI combines a conversational engineering assistant, a parametric CAD kernel, a Blender bridge, engineering calculators, mesh repair, lightweight FEA, and slicer/print optimisation into one desktop application — tuned for Flashforge multi-material printers but slicer- and printer-agnostic.

> Think *Fusion 360 + Blender + OrcaSlicer + ChatGPT*, local-first, with an AI that produces **editable parametric models**, not throwaway meshes.

---

## Status

🟢 **Phase 0 complete — working desktop foundation.** The app boots an Electron shell that supervises the Python engine, renders STLs in a Three.js viewport, chats with an AI copilot (Claude or offline stub, with an offline request queue), manages local-first `.efproj` projects, drives a detected Blender install (launch/scripts/conversion incl. native 3MF), and provides a Flashforge multi-material workspace (printer profiles, material library + compatibility warnings, usage/purge estimates, FlashPrint-compatible multi-material 3MF export). 181 tests across four suites; see [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

**Run it:** `pnpm install && pnpm --filter engine setup` once, then `pnpm dev` (see [`docs/08-deployment.md`](docs/08-deployment.md)).

Next: **Phase 1 — the MVP walking skeleton** (Feature Program IR, CadQuery kernel, AI-driven parametric parts) per [`docs/05-roadmap.md`](docs/05-roadmap.md).

## STEM_KIT — modular 3D-printable STEM kits

[`STEM_KIT/`](STEM_KIT/README.md) is a self-contained, parametric OpenSCAD library of
educational STEM kits (solar car, hand-crank dynamo, wind turbine, pulley and
linkage labs) built on one mechanical standard, with generated STLs, automated
geometry/assembly verification, and lesson + experiment sheets.

## Start here

| I want to… | Read |
|---|---|
| Understand the vision, users, and scope | [`docs/00-overview.md`](docs/00-overview.md) |
| Understand how the system is built | [`docs/01-architecture.md`](docs/01-architecture.md) |
| See the folder layout and why | [`docs/02-folder-structure.md`](docs/02-folder-structure.md) |
| See the data model | [`docs/03-database-schema.md`](docs/03-database-schema.md) |
| See the API & IPC contracts | [`docs/04-api-design.md`](docs/04-api-design.md) |
| See milestones, sprints, and the MVP | [`docs/05-roadmap.md`](docs/05-roadmap.md) |
| Set up a dev machine | [`docs/08-deployment.md`](docs/08-deployment.md) |
| Understand testing | [`docs/07-testing-strategy.md`](docs/07-testing-strategy.md) |
| Review key decisions | [`docs/adr/`](docs/adr/) |

## The one idea that makes this work

Everything hinges on the **Feature Program IR** — an intermediate representation that describes a part as an *ordered, parametric recipe* (sketch → extrude → hole → fillet → pattern…) rather than as a mesh or as free-text code. See [`docs/01-architecture.md#the-feature-program-ir`](docs/01-architecture.md#the-feature-program-ir).

- The **AI** emits and edits the IR, not raw geometry — so models stay **editable and reproducible**.
- The **CAD kernel** executes the IR to produce B-rep + mesh + a parameter table.
- Changing a parameter **re-runs the IR** → live parametric rebuild.
- "Reduce weight 30%", "add ribs", "make it printable" become **IR/mesh transforms**, not prompts-and-pray.

## High-level architecture

```
┌──────────────────────────── Electron Desktop Shell (TypeScript) ────────────────────────────┐
│                                                                                              │
│   Renderer  (Next.js + React + Three.js)              Main process (Node)                    │
│   • Dockable UI, 3D viewport, AI chat        ⇄ IPC ⇄  • Window & OS integration               │
│   • Parameter editor, assembly tree                   • Process supervisor / secure broker   │
│                         │                             • Prisma + Supabase (data plane)        │
│                         │ localhost REST/WS (token-authed)                                    │
└─────────────────────────┼────────────────────────────────────────────────────────────────────┘
                          ▼
        ┌──────────── Python Engine Sidecar (FastAPI) — "Geometry & Intelligence" ───────────┐
        │  CAD kernel (CadQuery/OpenCascade) · Mesh (Trimesh/Open3D) · FEA-lite ·             │
        │  AI orchestration (Claude/OpenAI/Ollama) · Slicer profiles · Blender bridge         │
        └─────────────────────────────────────────────────────────────────────────────────────┘
```

Two backends, clear responsibilities:
- **TypeScript / Next.js — Application & Data plane:** auth, projects, versions, persistence, BFF, orchestration.
- **Python / FastAPI — Geometry & Intelligence plane:** CAD, mesh, FEA, AI tools, slicing, Blender.

## Tech stack

Frontend: **Next.js · React · TypeScript · TailwindCSS · Three.js (react-three-fiber)**
Desktop: **Electron · electron-builder**
Backend (data): **Node · Prisma · PostgreSQL · Supabase (Auth + Storage)**
Backend (compute): **Python 3.12 · FastAPI · Uvicorn**
Geometry: **CadQuery / OpenCascade (OCP) · Trimesh · Open3D · manifold3d**
Blender: **Blender Python API (headless + live socket bridge)**
AI: **Claude API · OpenAI API · local Ollama**
Tooling: **pnpm workspaces · Turborepo · Vitest · Playwright · pytest · Ruff · ESLint · GitHub Actions · Docker**

## ⚠️ Important environment note

This machine runs **Python 3.14**, but the CAD/mesh stack (`cadquery`, `OCP`, `open3d`) does **not** yet publish wheels for 3.14. The engine **targets Python 3.12** via a dedicated, managed interpreter (independent of system Python). See [`docs/08-deployment.md`](docs/08-deployment.md).

## Repository layout

```
apps/        desktop (Electron), renderer (Next.js UI), engine (Python FastAPI kernel)
packages/    core-domain, ipc-contracts, ui, materials, config  (shared, typed)
prisma/      schema + migrations (data plane)
infra/       docker, deployment, CI helpers
docs/        architecture, roadmap, ADRs, guides
tests/       cross-cutting e2e (Playwright)
```

See [`docs/02-folder-structure.md`](docs/02-folder-structure.md) for the full rationale.

## License

TBD (recommend a source-available or dual license given the CAD/AI IP — decide before first public release).
