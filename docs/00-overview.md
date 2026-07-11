# 00 — Product Overview, Vision & Scope

## 1. Vision

EngineerForge AI is a **local-first, AI-native engineering workspace** that takes a part from *intent* → *parametric model* → *analysis* → *manufacturing-ready output* without leaving one application. It is built around a single conviction:

> An AI that designs mechanical parts must produce **editable engineering models**, not static meshes. If the output cannot be dimensioned, re-parameterised, analysed, and manufactured, it is a picture, not a design.

## 2. Target users & primary jobs-to-be-done

| User | Primary job | What they need from us |
|---|---|---|
| Mechanical engineer | Design functional parts fast, verify they won't fail | Parametric CAD, FEA-lite, calculators, tolerances, drawings |
| Chemical/process engineer | Fixtures, enclosures, fluid/pipe fittings | Parametric fittings, material chemistry compatibility, sealing |
| Product designer | Iterate form + function, present | Blender bridge, rendering, exploded views, DFM feedback |
| Hobby maker | "Make me a bracket that fits X" and print it | Conversational design, print prep, one-click slice |
| Prototype developer | Rapid iteration, multi-material | Fast rebuilds, multi-material assignment, print estimates |
| Small manufacturer | Repeatable parts, BOM, cost | Versioning, BOM, cost history, manufacturing advisor |

## 3. Scope

### In scope (the product we are building)
- Conversational **AI CAD** that emits editable parametric models (Feature Program IR).
- **Parametric editing** with a live parameter table and constraint-aware rebuild.
- **Mesh engineering**: repair, watertight/manifold checks, wall-thickness, simplify/refine.
- **Engineering calculators**: bolts, bearings, beams, gears, springs, shafts, tolerance stack-up, CoG/mass, factor of safety.
- **FEA-lite**: linear static stress estimation, weak-point + failure heuristics, print-orientation advice.
- **Materials**: curated + custom library with density, strength, shrinkage, temps, modulus, cost.
- **Multi-material / Flashforge**: material & colour assignment, compatibility warnings, usage + purge estimates, colour preview.
- **Print optimisation**: orientation, layer height, walls, infill, supports, brim/raft, speed, cooling.
- **Blender bridge**: headless ops + live round-trip (booleans, remesh, decimate, UV, geometry nodes, texture bake).
- **Assemblies**: multi-part, constraints, exploded views, interference detection, fastener library, BOM.
- **Reverse engineering** (later): scan → primitive/feature recognition → CAD.
- **Drawings**: dimensioned views, sections, isometrics, title block, revisions, PDF.
- **Manufacturing advisor**: 3D print vs CNC vs laser vs injection vs cast vs waterjet.
- **Slicer export**: FlashPrint/OrcaSlicer/Prusa/Cura/Bambu + auto profiles.
- **Project dashboard**: projects, versions, assets, print/cost history.
- **AI Copilot**: continuous, context-aware suggestions grounded in the actual model + analysis.

### Explicitly out of scope (v1)
- Full nonlinear / dynamic / thermal / CFD FEA (we do *estimation*, clearly labelled; not a substitute for certified analysis).
- Cloud real-time multiplayer co-editing (architecture allows it later; not built in v1).
- A from-scratch geometry kernel (we stand on OpenCascade/CadQuery — building a kernel is a decade-long project).
- Generative topology optimisation solver (we approximate/advise; may integrate an external solver later).
- Certified/regulated engineering sign-off. **All analysis output is advisory** (see §6).

## 4. Product principles

1. **Editable or it doesn't ship.** Every AI-generated part is a parametric Feature Program.
2. **Local-first, cloud-optional.** Works fully offline; syncs when signed in.
3. **Deterministic where it matters.** Same intent + params → same geometry (golden-file tested).
4. **The AI is a co-engineer, not an oracle.** It proposes IR/mesh edits you can inspect, diff, undo.
5. **Honest analysis.** Estimates are labelled as estimates, with assumptions surfaced.
6. **Manufacturing-aware from the first click.** DFM and printability are first-class, not an afterthought.
7. **Open, inspectable files.** Project format is transparent; no lock-in.

## 5. Success metrics (product-level)

- **Time-to-first-printable-part** from a natural-language prompt < 60 s (MVP target).
- **Parametric rebuild** latency < 500 ms for typical parts (p95).
- **Round-trip fidelity**: export → re-import STEP preserves parametric intent for supported feature set.
- **Print-estimate accuracy**: predicted vs actual filament mass within ±10% on calibrated profiles.
- **AI edit acceptance rate**: % of AI-proposed IR edits the user keeps without manual correction.

## 6. Safety, liability & honesty posture

EngineerForge AI performs **engineering estimation**, not certified analysis. This must be reflected in-product and in every calculator/FEA result:

- Results display **assumptions, method, and confidence**, and a persistent "advisory — verify before manufacturing load-bearing/safety-critical parts" note.
- The **AI never fabricates** material data or analysis numbers; values come from the material library and deterministic solvers, and the AI explains provenance.
- LLM-generated geometry code executes **sandboxed** (see architecture §Security).
- No personalized safety certification, medical, or regulated-load guarantees.

## 7. Glossary

| Term | Meaning |
|---|---|
| **Feature Program (IR)** | Ordered parametric recipe describing a part; the core editable artifact. |
| **Design Intent** | Structured JSON capturing what the user asked for (type, dims, features, use). |
| **Kernel** | The Python geometry engine (CadQuery/OpenCascade + mesh + FEA). |
| **Data plane** | TypeScript/Next.js side: auth, projects, persistence, orchestration. |
| **Intelligence plane** | Python/FastAPI side: geometry, mesh, FEA, AI tools, slicing, Blender. |
| **`.efproj`** | EngineerForge project bundle (transparent, on-disk). |
| **DFM** | Design for Manufacturing feedback. |
| **Purge tower** | Multi-material waste structure; we estimate its volume/cost. |
