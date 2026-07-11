# 01 — Software Architecture

This is the authoritative system design for EngineerForge AI. It defines the process model, the layering, the core abstractions (especially the **Feature Program IR** and the **AI CAD pipeline**), the module/plugin system, security, and the key trade-offs. ADRs in [`adr/`](adr/) record individual decisions.

---

## 1. Architectural goals & forces

| Force | Consequence for the design |
|---|---|
| Heavy native geometry/AI compute lives in the **Python ecosystem** (OpenCascade, CadQuery, Trimesh, Open3D, numpy/scipy). | A dedicated Python **engine** process; JS/Three.js is display-only. |
| Modern reactive **UI** with a real 3D viewport. | Next.js + React + react-three-fiber in an Electron renderer. |
| **Desktop-first, offline-capable**, but syncable for teams. | Local-first data model + optional Supabase/Postgres sync. |
| AI must produce **editable, reproducible** models. | The **Feature Program IR** as the central artifact; AI edits IR, not meshes. |
| LLM-generated code is **untrusted**. | Sandboxed subprocess execution with AST allowlist + resource limits. |
| **Clean architecture / SOLID / DI / testability**. | Domain-centric layering with ports & adapters in every tier. |
| **Plugin extensibility** (part generators, calculators, exporters). | A typed plugin/registry system with capability contracts. |

Non-negotiable qualities: **determinism** of geometry, **inspectability** of AI actions, **isolation** of untrusted code, **typed contracts** across every process boundary.

---

## 2. Process & deployment model

EngineerForge AI runs as **three cooperating processes** on the desktop, plus an optional hosted mode.

```
                          Electron app (single installed product)
   ┌───────────────────────────────────────────────────────────────────────────────┐
   │  (1) MAIN PROCESS  — Node/TS                                                     │
   │      • BrowserWindow lifecycle, native menus, file dialogs, auto-update         │
   │      • Process Supervisor: spawns/monitors/restarts the Python engine           │
   │      • Secure IPC broker (contextBridge; no nodeIntegration in renderer)        │
   │      • Data plane host: Prisma client, Supabase SDK, local SQLite cache         │
   │      • Composition root / DI container for TS services                          │
   └───────────────┬──────────────────────────────────────────┬─────────────────────┘
        IPC (typed, │ contextBridge)                localhost  │ REST + WebSocket
                    ▼                                 (token)   ▼
   ┌────────────────────────────────┐        ┌──────────────────────────────────────┐
   │ (2) RENDERER — Next.js/React    │        │ (3) ENGINE — Python / FastAPI         │
   │   • Dockable panels, viewport   │◀──────▶│   • CAD kernel (CadQuery/OCP)         │
   │   • AI chat, parameter editor   │  WS/   │   • Mesh services (Trimesh/Open3D)    │
   │   • r3f Three.js scene          │  REST  │   • FEA-lite, calculators             │
   │   • Zustand/Redux state         │        │   • AI orchestration (tools)          │
   │   • Sandboxed (no Node)         │        │   • Slicer profiles, Blender bridge   │
   └────────────────────────────────┘        │   • Sandboxed code-exec subprocess    │
                                              └──────────────────────────────────────┘
```

**Why three processes?**
- **Isolation & crash safety** — a geometry op that segfaults OpenCascade must not take down the UI. The supervisor restarts the engine and replays the last IR.
- **Right tool per plane** — TS for UI/orchestration/data; Python for geometry/AI.
- **Security** — renderer is sandboxed; the engine binds to `127.0.0.1` only, with a per-session bearer token minted by the main process.

**Optional hosted mode** (small-manufacturer/team): the same Python engine runs as a container behind the data-plane API; the Electron app becomes a thin client, or the UI is served as a web app. The port/adapter design means **no code fork** — only the composition root and transport change. See [`docs/08-deployment.md`](docs/08-deployment.md).

### Transport contracts
- **Renderer ⇄ Main:** typed IPC channels defined in `packages/ipc-contracts` (Zod-validated request/response, no ambient `ipcRenderer`).
- **Renderer/Main ⇄ Engine:** versioned **REST** for request/response (`/api/v1/...`) + **WebSocket** for streaming (AI tokens, long geometry jobs, rebuild progress). OpenAPI schema generated from FastAPI → typed client generated for TS. Contract tests keep them in sync.

---

## 3. Layered (clean) architecture

Every tier follows the same dependency rule: **dependencies point inward**; the domain knows nothing about frameworks, transports, or vendors.

```
        ┌─────────────────────────────────────────────────────────┐
        │ Presentation:  React components · FastAPI routers · CLI  │
        ├─────────────────────────────────────────────────────────┤
        │ Application (use cases): GeneratePartFromPrompt,         │
        │   RebuildModel, RepairMesh, EstimatePrint, RunFEA, ...   │
        ├─────────────────────────────────────────────────────────┤
        │ Ports (interfaces): CadKernelPort, MeshServicePort,      │
        │   AIProviderPort, SlicerPort, BlenderPort, StoragePort   │
        ├─────────────────────────────────────────────────────────┤
        │ Domain (pure): Part, Feature, Parameter, Sketch,         │
        │   Assembly, Constraint, Material, MeshModel, PrintProfile│
        └─────────────────────────────────────────────────────────┘
        Infrastructure (adapters) implements Ports from the outside:
        CadQueryKernel · TrimeshMeshService · ClaudeProvider ·
        OllamaProvider · OrcaSlicerAdapter · BlenderSubprocessBridge ·
        SupabaseStorage · PrismaProjectRepository
```

- **Domain** (`packages/core-domain` in TS; `engineerforge_engine/domain` in Python): entities, value objects, and the **Feature Program IR** types. Pure, no I/O. The IR types are the *shared contract* and are defined once and mirrored (schema-generated) across TS/Python.
- **Application**: use-case services orchestrate domain + ports. One class per use case; constructor-injected dependencies.
- **Ports**: abstract interfaces. The application depends only on these.
- **Infrastructure**: concrete adapters chosen at the composition root.
- **Presentation**: thin; translates transport ⇄ use-case calls.

**Dependency injection.** Python: a container (`dependency-injector`, or a hand-rolled provider registry) wires adapters → ports at startup, overridable in tests with fakes. TS: `tsyringe`/InversifyJS or explicit factory composition in the Electron main process. **No service locates its own dependencies**; everything is injected → everything is unit-testable with fakes.

---

## 4. The Feature Program IR

The Feature Program is the heart of the system: a serialisable, ordered, parametric description of a part.

### 4.1 Why an IR (not code, not mesh)
| Option | Problem |
|---|---|
| Store a **mesh** (STL) | Not editable; loses design intent, dimensions, features. |
| Store **LLM-written CadQuery code** | Non-deterministic, unsafe to re-run, hard to diff/edit, brittle. |
| Store a **Feature Program IR** ✅ | Editable, diffable, deterministic, safe, AI-manipulable, kernel-agnostic. |

The IR decouples *intent* from *execution*: the AI and UI manipulate the IR; the kernel compiles the IR to geometry. Swapping CadQuery for another kernel later is an adapter change, not a rewrite.

### 4.2 Shape (illustrative)
```jsonc
{
  "schema": "efir/1",
  "part": {
    "id": "part_bracket_01",
    "name": "L-Mounting Bracket",
    "units": "mm",
    "parameters": [
      { "id": "W",  "label": "Width",         "value": 40, "min": 10, "max": 200, "unit": "mm" },
      { "id": "H",  "label": "Height",        "value": 60, "min": 10, "max": 200, "unit": "mm" },
      { "id": "T",  "label": "Thickness",     "value": 4,  "min": 1,  "max": 20,  "unit": "mm" },
      { "id": "D",  "label": "Hole Diameter", "value": 5,  "min": 1,  "max": 30,  "unit": "mm" },
      { "id": "R",  "label": "Fillet Radius", "value": 3,  "min": 0,  "max": 15,  "unit": "mm" },
      { "id": "M",  "label": "Material",      "value": "PETG", "kind": "enum" }
    ],
    "features": [
      { "op": "sketch",  "id": "s1", "plane": "XY",
        "profile": { "kind": "rect", "w": "W", "h": "T" } },
      { "op": "extrude", "id": "e1", "of": "s1", "distance": "H" },
      { "op": "hole",    "id": "h1", "on": "e1", "at": { "x": "W/2", "z": "H-10" },
        "diameter": "D", "through": true },
      { "op": "fillet",  "id": "f1", "edges": "convex_vertical", "radius": "R" },
      { "op": "pattern", "id": "p1", "of": "h1", "kind": "linear", "count": 2, "spacing": "H-20" }
    ],
    "constraints": [ { "kind": "min_wall", "value": 1.2, "reason": "printability@0.4mm nozzle" } ],
    "provenance": { "generatedBy": "planner:template:bracket.l", "aiModel": "claude", "editable": true }
  }
}
```

Key points:
- **Parameters are symbolic**; feature fields reference them by expression (`"H-10"`), evaluated by a small, safe expression evaluator (no `eval`).
- Features are an **ordered DAG** by `id`/`of`/`on` references → deterministic rebuild + partial re-execution (only downstream of a changed node).
- **Constraints** (min wall, tolerance, printability) are checked during compile; violations surface as DFM warnings.
- **Provenance** records how each part/feature was produced (template vs AI-generated), enabling trust/undo/diff.

### 4.3 Compilation
`FeatureProgram → CadKernelPort.compile() → { brep, mesh(tessellation), paramTable, dfmReport }`. The CadQuery adapter walks the feature DAG, resolves expressions, and builds geometry. Output mesh (glTF/3MF) streams to the renderer for display; the B-rep (STEP) is retained for export and analysis.

### 4.4 Editing model
- **Parameter change** → re-evaluate expressions → re-run affected features → new mesh. Undo/redo is IR-level (command pattern).
- **AI edits** ("add ribs", "reduce weight 30%") → the AI proposes an **IR patch** (add/modify/remove features, adjust params) → user sees a **diff** → apply → rebuild. Weight reduction may combine IR edits (shell, infill hint, rib pattern) with mesh-level optimisation, always reported with before/after mass.

---

## 5. The AI CAD pipeline

The pipeline turns natural language into an editable model with **layered fallback** — deterministic where possible, generative where necessary, sandboxed always.

```
 "Design a mounting bracket 40×60, 4mm, two 5mm holes, PETG"
        │
        ▼  (1) INTENT PARSING  — AIProviderPort (Claude/OpenAI/Ollama)
   DesignIntent { type:"bracket.l", dims:{...}, features:[hole×2], material:"PETG", use:"wall mount" }
        │       (validated against Pydantic/Zod schema; ambiguity → clarifying question)
        ▼  (2) PLANNER
   ┌─ known type? → TEMPLATE: parametric generator fills a vetted Feature Program  (deterministic ✅)
   └─ novel shape? → CODEGEN: LLM writes CadQuery → SANDBOX exec → lift to IR where possible
        │
        ▼  (3) KERNEL COMPILE  — CadKernelPort
   { brep, mesh, paramTable, dfmReport }
        │
        ▼  (4) RESULT → UI
   Editable parameters + live viewport + DFM/printability notes
        │
        ▼  (5) ITERATE  — "add ribs" / "make printable" / "reduce weight"
   AI proposes IR patch → diff → apply → rebuild (loop)
```

### 5.1 Part templates (the reliable core)
A registry of **parametric part generators** (bracket, gear, enclosure, adapter, clamp, pipe-fitting, hinge, cable-organizer, …). Each template:
- declares its **parameter schema** (with sane ranges/defaults + engineering constraints),
- emits a **Feature Program** from parameters (pure function),
- is **unit- and golden-file-tested** (intent → deterministic volume/mesh hash).

Templates are the trustworthy backbone; the LLM's job for known parts is *only* to select the template and fill parameters — which is easy to validate. This is what makes "Design a gearbox housing" reliable rather than a dice roll.

### 5.2 Generative fallback (sandboxed)
For shapes with no template, the LLM writes CadQuery executed in a **hardened sandbox** (see §8). Successful geometry is captured; where the operations map to known feature ops, they're **lifted into the IR** so the result stays editable. Non-liftable geometry is stored as a parametrised code-feature with its inputs exposed as parameters (still re-runnable, still sandboxed).

### 5.3 AI provider abstraction
`AIProviderPort` unifies Claude, OpenAI, and Ollama behind one interface with **tool/function-calling**. Tools exposed to the model are the engine's own capabilities: `create_part_from_template`, `edit_feature_program`, `run_calculator`, `estimate_print`, `repair_mesh`, `run_fea`, `query_material`. The model **orchestrates tools**; it does not invent numbers. Provider selection is per-request (cloud for quality, Ollama for offline/private). Streaming via WebSocket. Prompt/response caching for cost.

> This maps cleanly onto Claude tool-use / OpenAI function-calling / Ollama tool support. See the bundled `claude-api` skill for Claude-specific tool-runner patterns when implementing `ClaudeProvider`.

---

## 6. Subsystem designs

### 6.1 Geometry & mesh
- **CAD kernel** (`CadKernelPort` → `CadQueryKernel`): compiles IR, boolean ops, fillets/chamfers, exports STEP/IGES.
- **Mesh services** (`MeshServicePort` → `Trimesh`/`Open3D`/`manifold3d`): repair (non-manifold, hole-fill, normals), watertight check, wall-thickness field, decimate/subdivide, boolean, convex hull, CoG/mass/volume.
- **Reverse engineering** (later): Open3D RANSAC primitive fitting (plane/cylinder/sphere) → feature recognition → IR reconstruction.

### 6.2 Engineering calculators
Pure, deterministic solvers in the domain layer, each with typed inputs/outputs, cited formulas, and unit tests against textbook values: bolt strength/preload, bearing life, beam deflection, column buckling, gear geometry/AGMA-lite, spring rate, shaft sizing, tolerance stack-up (worst-case + RSS), CoG/mass, factor of safety. Exposed to AI as tools and to the UI as panels. **Every result carries its assumptions and method.**

### 6.3 FEA-lite
Linear-static estimation for indicative stress/displacement + weak-point heatmap. Implementation path: start with analytical/heuristic estimators for common load cases (cantilever, simply-supported, pressure), graduate to a tetrahedral linear-elastic solver (e.g. `sfepy`/`scikit-fem` + `gmsh` meshing) behind `FeaPort`. **Always labelled advisory** with mesh quality + assumptions. Never presented as certified.

### 6.4 Materials
Curated library (PLA, PETG, ABS, ASA, Nylon, CF, TPU, PC, PVA, support) + custom materials. Fields: density, shrinkage, tensile/yield strength, Young's modulus, print temps, bed temp, cost/kg, compatibility flags. Backs mass/cost estimates, FEA material params, and multi-material compatibility checks. Seed data in `packages/materials`, synced to Postgres.

### 6.5 Multi-material & Flashforge
- Per-feature/per-body **material & colour assignment** in the IR.
- **Compatibility matrix** (adhesion, temp overlap, soluble-support pairing e.g. PVA↔PLA) → warnings.
- **Usage estimates** per material + **purge-tower volume** estimate for tool changes.
- **Colour preview** in the viewport (per-body materials).
- Export to **3MF** with material/colour metadata; Flashforge/FlashPrint-oriented profiles.

### 6.6 Print optimisation & slicer integration
- Advisor computes orientation (min supports / max strength across print axis), layer height, walls, infill %/pattern, support strategy, brim/raft, speed, cooling — as a **recommended profile** with rationale.
- `SlicerPort` adapters generate/export profiles + geometry to FlashPrint, OrcaSlicer, PrusaSlicer, Cura, Bambu Studio (profile file formats per slicer; 3MF as the rich interchange).

### 6.7 Blender bridge
`BlenderPort` with two adapters:
- **Headless** (`blender --background --python job.py`): booleans, remesh, decimate, UV unwrap, geometry-nodes graphs, texture bake, mesh cleanup — for automated pipeline steps.
- **Live** (socket/add-on round-trip): open a `.blend`, push/pull models for interactive work. *(An MCP Blender add-on is available in this environment and is the reference integration for the live bridge during development.)*
Jobs are queued, sandboxed to a working dir, and versioned so results re-import as new part versions.

### 6.8 Assemblies, drawings, BOM
- **Assembly** = tree of part instances + mates/constraints; interference detection via mesh/BRep intersection; exploded views; fastener library.
- **Drawings**: project B-rep to orthographic + iso views, auto-dimension, sections, title block, revision table → PDF.
- **BOM** generated from the assembly tree + materials + fasteners; cost roll-up; exportable.

---

## 7. Module & plugin architecture

Extensibility is a first-class requirement. A **capability registry** lets features be added without touching the core.

```
PluginManifest {
  id, name, version, engineRange,
  capabilities: [
    { kind: "part-generator", type: "gear.spur", schema, generate(params)->FeatureProgram },
    { kind: "calculator",     id: "bolt.iso898", inputs, outputs, solve(i)->o },
    { kind: "exporter",       format: "3mf.flashforge", export(model)->file },
    { kind: "ai-tool",        name: "reduce_weight", handler },
    { kind: "material-pack",  materials: [...] }
  ]
}
```

- Plugins register **capabilities** against typed contracts; the app discovers and composes them at the composition root.
- Core "built-in" features are themselves plugins (dogfooding the contract) → forces clean seams.
- Untrusted third-party plugins run with the same sandbox posture as generated code.
- This satisfies SOLID (open/closed) and keeps the 25+ feature areas independently developable and testable.

---

## 8. Security architecture

See [`docs/10-security-checklist.md`](docs/10-security-checklist.md) for the actionable list. Core model:

- **Electron hardening**: `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`, strict CSP, no remote module, validated preload API surface only.
- **Engine binding**: FastAPI binds `127.0.0.1` on an ephemeral port; every request requires a **per-session bearer token** minted by the main process and passed to the sidecar at spawn (never exposed to the renderer except via the IPC broker).
- **Untrusted code execution** (LLM-generated CadQuery, third-party plugins): separate subprocess with **no network**, **restricted filesystem** (a scratch dir only), **CPU/memory/time limits**, and an **AST allowlist** (imports and calls whitelisted; no `os`, `subprocess`, `open` outside scratch, no dunder escapes). Timeouts kill and report cleanly.
- **AI safety**: system prompts forbid fabricating engineering values; numeric outputs must come from tool calls (calculators/materials/solvers). Instruction-injection from imported files/model content is treated as data, never as commands.
- **Secrets**: API keys in the OS keychain (via `keytar`)/Supabase secrets — never in the renderer, never in project files.
- **Data**: local project files are user-owned and inspectable; cloud sync uses Supabase RLS so users only access their own rows/objects.

---

## 9. State management & data flow (runtime)

- **Renderer state**: Zustand (or Redux Toolkit) stores — `sessionStore`, `projectStore`, `viewportStore`, `chatStore`. The **IR is the source of truth** for geometry; the viewport is a projection of the compiled mesh.
- **A typical "change a parameter" flow**:
  1. User edits `Thickness` in the parameter panel → `projectStore.updateParam`.
  2. Debounced call → IPC → engine `POST /api/v1/parts/{id}/rebuild` with the IR patch.
  3. Engine re-runs affected features → returns new mesh (glTF) + DFM report over WS (progress streamed).
  4. Renderer swaps the mesh in the r3f scene; parameter panel shows updated mass/cost.
- **Persistence**: on save, the IR + cached meshes + metadata write to the `.efproj` bundle (local) and, if signed in, sync to Postgres/Storage (data plane).

---

## 10. Technology decisions & trade-offs (summary; details in ADRs)

| Decision | Choice | Rationale | Trade-off |
|---|---|---|---|
| Geometry runtime | **Python engine, not WASM** | Mature B-rep/mesh/FEA stack | Extra process to ship/supervise |
| Editable model | **Feature Program IR** | Determinism + AI-editable + kernel-agnostic | Must maintain a template/feature library |
| CAD kernel | **CadQuery/OpenCascade (OCP)** | Powerful parametric B-rep, Python-native | Heavy deps; Python 3.12 pin |
| UI 3D | **react-three-fiber / Three.js** | Ergonomic React 3D, big ecosystem | Display-only; not the geometry source |
| Desktop | **Electron** | Cross-platform, mature, matches stack | Bundle size, memory |
| Data plane | **Prisma + Postgres + Supabase** | Typed ORM, managed auth/storage | Two-backend complexity |
| AI | **Provider abstraction (Claude/OpenAI/Ollama)** | Quality + offline/private option | Must normalise tool-calling APIs |
| Monorepo | **pnpm + Turborepo** | Shared types, atomic changes | Tooling setup |

See individual records: [`adr/0001`](adr/0001-python-engine-sidecar.md), [`adr/0002`](adr/0002-feature-program-ir.md), [`adr/0003`](adr/0003-ai-provider-abstraction.md), [`adr/0004`](adr/0004-local-first-with-cloud-sync.md).

---

## 11. What this architecture deliberately makes easy

- Adding a **new part type** → write one tested template plugin.
- Adding a **new calculator/exporter/AI-tool** → register a capability; no core change.
- Swapping the **CAD kernel** or an **AI provider** → new adapter behind the existing port.
- Running **hosted/multi-user** → change the composition root + transport, not the domain.
- **Testing** → every use case runs against fake ports; geometry is golden-file/property tested.
