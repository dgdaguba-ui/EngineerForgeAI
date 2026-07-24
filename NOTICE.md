# Attributions

## Freeform (text-to-CAD) generation

The freeform generation feature — letting the AI author a CAD script that is
executed in a sandbox to produce a mesh part — is **inspired by**
[earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) (MIT
License) and the [build123d](https://github.com/gumyr/build123d) project.

No source code from those projects is included here. EngineerForge AI
implements the capability on its existing **CadQuery / OpenCASCADE** kernel
(the same OpenCASCADE geometry engine that build123d wraps), so the freeform
path shares the engine's kernel, tessellation format, and export pipeline
rather than adding a second CAD stack. See:

- `apps/engine/engineerforge_engine/domain/script_guard.py` — static safety guard
- `apps/engine/engineerforge_engine/adapters/cad/freeform_runner_main.py` — sandboxed subprocess runner
- `apps/engine/engineerforge_engine/adapters/cad/cadquery_freeform.py` — process-isolation adapter

### Security note

Executing model-authored code is inherently risky. The freeform path uses
defence-in-depth — a static AST guard (import allow-list, no dunder access, no
dangerous builtins), a restricted `__builtins__`, an audit hook blocking process
spawning and networking, and a separate process with a hard timeout — but this
is **not** a hardened security boundary. Python cannot be fully sandboxed
in-process. True isolation (container/VM) is future work and is gated on the
same Docker dependency as the M2.3 data plane.

## Core dependencies

- [CadQuery](https://github.com/CadQuery/cadquery) (Apache-2.0) and
  OpenCASCADE — the parametric and freeform geometry kernel.
- [trimesh](https://github.com/mikedh/trimesh) (MIT) — mesh export.
