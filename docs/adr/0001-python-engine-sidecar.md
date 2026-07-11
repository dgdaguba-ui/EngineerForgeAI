# 0001 — Python engine as a sidecar process (not WASM)

Status: Accepted

## Context
The product needs mature parametric B-rep CAD, mesh processing, and FEA. The strongest libraries for this (OpenCascade via `OCP`, `CadQuery`, `Trimesh`, `Open3D`, `numpy`/`scipy`) are Python-native. The UI, however, is best built with the JS/React/Three.js ecosystem inside Electron. Doing geometry in the browser via WASM (e.g. OpenCascade.js) is possible but significantly less capable, harder to extend, and slower to develop against for parametric B-rep + analysis.

## Decision
Run a dedicated **Python engine as a sidecar process** (FastAPI on localhost), supervised by the Electron main process. Three.js in the renderer is **display-only**; the engine is the authoritative geometry/analysis/AI kernel. Communication is versioned REST + WebSocket with a per-session token.

## Consequences
**Positive:** best-in-class geometry stack; process isolation (a kernel crash can't kill the UI); clean language boundary (TS for UI/data, Python for compute); the same engine serves desktop and hosted modes unchanged.
**Negative:** must ship/supervise a Python runtime (bundled, frozen); an extra IPC/HTTP hop; cross-language type contracts to maintain (mitigated by codegen).
**Neutral:** forces a clean API boundary early, which improves testability.

## Alternatives considered
- **WASM geometry in-browser:** rejected — weaker parametric/FEA capability, harder extensibility.
- **Rust/C++ native kernel:** far higher build cost; premature. The port/adapter design lets us swap the kernel later without a rewrite.
- **Node-native geometry:** ecosystem is immature for B-rep/FEA.
