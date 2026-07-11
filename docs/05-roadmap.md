# 05 — Implementation Roadmap, Milestones, Sprints & MVP

## How to read this

- Work is grouped into **Phases → Milestones → 2-week Sprints**.
- **Every milestone has an exit bar**: functional + tested (unit/integration/e2e as noted) + documented. No milestone is "done" until its exit bar is green. This is the discipline that keeps the product from becoming 25 stubs.
- **Estimates are in engineering-weeks (EW)**, not calendar dates — divide by team size for calendar time. A rough solo/calendar guide is given per phase, but treat it as order-of-magnitude. This is a large product; honesty about that is a feature.
- **MVP = Phase 1** (the "walking skeleton"). It is genuinely usable and proves every architectural seam end-to-end.

> **Reality check.** A polished, all-features build rivaling Fusion 360 + OrcaSlicer + Blender is a multi-year, multi-engineer effort. This roadmap front-loads a *real* working slice, then adds capability in vertical, shippable increments — each one demoable and tested.

---

## Phase 0 — Foundations ✅ (in progress)

**Goal:** architecture, scaffold, contracts, CI skeleton. *(This documentation set + repo scaffold.)*

- [x] Architecture, folder structure, DB schema, API design, roadmap docs
- [ ] Monorepo tooling live (pnpm workspaces, Turborepo, shared config packages)
- [ ] Python engine bootstrap (FastAPI, `/health`, DI container, Python 3.12 env)
- [ ] CI: lint + typecheck + unit test on PR (TS + Python); pre-commit hooks
- [ ] `core-domain` IR schema + codegen (Zod ↔ Pydantic) round-trips
- **Exit bar:** `pnpm dev` starts renderer + main + engine; `/health` green; CI passes on a trivial change; IR schema compiles in both languages.
- **Estimate:** ~3 EW.

---

## Phase 1 — MVP: the Walking Skeleton 🎯

**Thesis:** one part family, fully alive end-to-end — proving UI ↔ IPC ↔ Engine ↔ AI ↔ CAD kernel ↔ export ↔ print-estimate. Better one part that *truly works* than twenty that don't.

**MVP user story:**
> "Design an L-bracket, 40×60, 4 mm thick, two 5 mm holes, PETG." → an editable parametric model appears in the viewport in <60 s. I drag *Thickness* to 6 mm and it rebuilds live. I see mass, and a Flashforge print estimate (time, filament, cost). I export STL + 3MF and save the project.

### Milestone 1.1 — Skeleton & viewport (Sprints 1–2)
- Electron shell (hardened: contextIsolation, sandbox), main-process **engine supervisor**, typed IPC.
- Next.js renderer in Electron; **dark theme** design-system primitives; **dockable panel** layout (viewport / chat / params / inspector).
- **3D viewport** (react-three-fiber): load a glTF mesh from the engine, orbit/pan/zoom, grid, lighting, measure-ready camera.
- Engine: `/parts` compile endpoint returns a hardcoded IR → CadQuery → glTF (prove the pipe).
- **Exit bar:** a bracket compiled by the engine renders in the viewport, orbitable. e2e (Playwright) launches app, sees the mesh.

### Milestone 1.2 — Feature Program IR + parametric rebuild (Sprints 3–4)
- Define **IR v1** (`efir/1`) in `core-domain`; codegen to Pydantic/Zod.
- **CadQueryKernel** adapter: compile sketch/extrude/hole/fillet/pattern; safe expression evaluator; feature DAG partial rebuild.
- **Bracket template** (first part generator plugin) with parameter schema + engineering constraints (min wall).
- **Parameter editor** panel: edit values → debounced `PATCH /params` → live rebuild; mass/volume readout.
- **Undo/redo** at IR level (command pattern).
- **Exit bar:** changing any parameter rebuilds correctly <500 ms p95; golden-file test (intent→volume within tol); property test (watertight, volume>0).

### Milestone 1.3 — AI design + copilot (Sprints 5–6)
- **AIProviderPort** + **ClaudeProvider** (primary) with tool-calling; **OllamaProvider** stub for offline.
- Pipeline stages: **intent parsing** (schema-validated) → **planner** (select bracket template, fill params) → compile.
- **AI chat panel**: prompt → part; "make the holes 6 mm", "add a third hole" → **IR patch diff** → apply → rebuild.
- Sandbox scaffold for any generative fallback (even if MVP only uses the template path).
- **Exit bar:** the MVP user story works with a real prompt; AI edits are shown as diffs before applying; tool-calls (not free-text numbers) drive changes. Integration test mocks the provider deterministically.

### Milestone 1.4 — Export, print estimate, persistence (Sprints 7–8)
- **Export**: STL, 3MF, STEP via engine.
- **Print estimate** (Flashforge-oriented, single material to start): filament mass from volume×infill×density, time heuristic, cost; **orientation suggestion** (v1 heuristic).
- **Materials (read-only seed)**: PLA/PETG/ABS… library backing mass/cost.
- **Persistence**: `.efproj` local save/load (IR + cached mesh + manifest); recent-projects list.
- **Exit bar:** full user story incl. export files that slice cleanly in FlashPrint/OrcaSlicer; project reopens identically. e2e covers prompt→edit→export→save→reopen.

**Phase 1 estimate:** ~16 EW (8 sprints). **MVP exit = a genuinely useful single-part parametric AI CAD + print-prep tool.**

---

## Phase 2 — Parametric depth & data plane (Milestones 2.1–2.3)
- **Part template library:** gear (spur), enclosure/box, adapter, clamp, pipe-fitting, standoff, bracket variants, cable-organizer, hinge, handle. Each: schema + generator + golden tests.
- **Robust editor:** constraints surfaced, param dependencies, validation, presets.
- **Data plane live:** Prisma + Postgres + Supabase Auth; project/version/part persistence; **cloud sync** (local-first reconcile); assets to Supabase Storage.
- **Property inspector** + **timeline** (feature history) panels.
- **Exit bar:** 10+ tested part types; sign-in + sync works; versions immutable & restorable.
- **Estimate:** ~12 EW.

## Phase 3 — Mesh engineering (Milestone 3.1–3.2)
- Import STL/OBJ/PLY/3MF; **repair** (non-manifold, holes, normals); **watertight** check; **wall-thickness** field + min-wall violations; **simplify/refine**; mesh **boolean**; convex hull; mass properties on meshes.
- **Exit bar:** repair turns known-broken meshes watertight (property-tested); wall-thickness heatmap in viewport.
- **Estimate:** ~10 EW.

## Phase 4 — Materials & multi-material (Flashforge) (Milestone 4.1–4.2)
- Full **material library** (curated + custom CRUD); **per-body material & colour assignment** in IR; **compatibility matrix** + warnings; **usage + purge-tower estimates**; **colour preview** in viewport; **multi-material 3MF export**; Flashforge/FlashPrint profile mapping.
- **Exit bar:** a 2–4 material model previews correctly and exports a 3MF FlashPrint opens with correct material/colour mapping; purge estimate within target tolerance.
- **Estimate:** ~10 EW.

## Phase 5 — Engineering analysis (Milestone 5.1–5.3)
- **Calculators** (bolt, bearing, beam, gear, spring, shaft, tolerance stack-up, CoG/mass, FoS) — each tested to textbook values, exposed as AI tools + panels.
- **FEA-lite**: analytical estimators → tetra linear-static solver (scikit-fem/sfepy + gmsh); **stress heatmap**, **weak-point** + **failure** heuristics; **print-orientation** optimiser (strength/support trade-off).
- **AI Copilot** grounded in analysis ("where will it fail?", "how do I strengthen this?").
- **Exit bar:** calculators match references; FEA-lite matches analytical cantilever within tolerance; all outputs labelled advisory with assumptions.
- **Estimate:** ~16 EW.

## Phase 6 — Blender bridge (Milestone 6.1)
- **Headless** ops (boolean, remesh, decimate, UV, geometry nodes, texture bake, cleanup); **live** round-trip session; jobs versioned back into parts.
- **Exit bar:** send→modify→receive round-trip produces a new tested part version; headless ops in CI (Blender in container).
- **Estimate:** ~8 EW.

## Phase 7 — Assemblies, BOM, drawings (Milestone 7.1–7.3)
- **Assembly** tree + mates/constraints; **interference detection**; **exploded views**; **fastener library**; **BOM** generation + cost; **motion test** (basic).
- **Drawing generator**: ortho + iso views, auto-dimensions, sections, title block, revisions, **PDF export**.
- **Exit bar:** a 3-part assembly with mates, interference report, BOM with costs, and a dimensioned PDF drawing.
- **Estimate:** ~16 EW.

## Phase 8 — Manufacturing breadth & reverse engineering (Milestone 8.1–8.2)
- **Manufacturing advisor** (3DP/CNC/laser/injection/cast/waterjet) with reasoned recommendation.
- **Slicer breadth**: OrcaSlicer/Prusa/Cura/Bambu profile export + optimisation.
- **Reverse engineering**: scan mesh → primitive/feature recognition → IR reconstruction (RANSAC + heuristics).
- **Estimate:** ~14 EW.

## Phase 9 — Hardening, performance, release (Milestone 9.1–9.2)
- Performance pass (see [`docs/11-performance.md`](docs/11-performance.md)); security review ([`docs/10-security-checklist.md`](docs/10-security-checklist.md)); accessibility; crash/telemetry; **auto-update**; signed installers (Win/macOS/Linux); onboarding; docs/site.
- **Exit bar:** signed installers, green security checklist, perf targets met, e2e suite across OSes.
- **Estimate:** ~10 EW.

---

## Timeline summary

| Phase | Focus | Est. (EW) |
|---|---|---:|
| 0 | Foundations | 3 |
| 1 | **MVP walking skeleton** | 16 |
| 2 | Parametric depth + data plane | 12 |
| 3 | Mesh engineering | 10 |
| 4 | Materials + multi-material | 10 |
| 5 | Analysis (calc + FEA) | 16 |
| 6 | Blender bridge | 8 |
| 7 | Assemblies + BOM + drawings | 16 |
| 8 | Mfg advisor + reverse eng | 14 |
| 9 | Hardening + release | 10 |
| | **Total** | **~115 EW** |

Order-of-magnitude calendar: **solo ≈ 2+ years**; **team of 4 ≈ 7–9 months** to a broad v1; the **MVP (Phase 1) is reachable in ~4 months solo / ~6 weeks for a focused pair.** We can and should ship value continuously from Phase 1 onward.

## Sequencing principles

1. **Vertical slices, not horizontal layers** — every milestone touches UI→engine→persistence so integration risk surfaces early.
2. **Templates before generative** — deterministic part generators are the trustworthy core; LLM codegen is the sandboxed fallback.
3. **Estimation honesty** — analysis features ship *advisory-labelled* from day one.
4. **Test debt is not allowed to accumulate** — the exit bar includes tests every milestone.
5. **Cut scope, not quality** — if a phase runs long, drop part types/formats, never testing or the sandbox.

## Immediate next actions (Phase 0 → 1)
1. Stand up monorepo tooling + engine bootstrap + CI (Phase 0 remaining).
2. Build Milestone 1.1 skeleton (Electron + viewport + engine `/parts`).
3. Land IR v1 + CadQuery bracket template + parametric rebuild (1.2).
See [`docs/06-mvp-plan.md`](06-mvp-plan.md) for the MVP build order in engineering detail.
