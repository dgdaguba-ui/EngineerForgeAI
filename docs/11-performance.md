# 11 — Performance Optimisation Strategy

Performance is a product feature: parametric rebuilds must feel instant, the viewport must stay at 60 fps, and heavy jobs must never freeze the UI. Budgets are asserted in CI (benchmarks) where feasible.

## Performance budgets (targets)

| Operation | Target |
|---|---|
| Parametric rebuild (typical part), p95 | < 500 ms |
| Prompt → first rendered part | < 60 s (mostly LLM latency) |
| Viewport interaction | 60 fps; ≤ 16 ms frame for ≤ 1 M-tri scenes |
| Mesh import (10 M tris) | < 5 s to first display (progressive) |
| App cold start to interactive | < 4 s |
| Engine memory (idle) | < 400 MB; bounded growth under load |

## Rebuild & geometry (engine)
- **Partial DAG re-execution** — only features downstream of a changed node recompute (the IR makes this precise).
- **Content-hash cache** — identical IR compiles hit a cache (in-memory + on-disk) keyed by canonicalised IR hash.
- **Worker pool** — geometry ops run in worker processes; the API stays responsive; crashes are isolated + retried.
- **LOD tessellation** — return a coarse mesh immediately, refine asynchronously; viewport swaps in higher LOD.
- **Streaming** — long jobs (FEA, Blender, big rebuilds) stream progress over WebSocket; nothing blocks.
- **Lazy heavy imports** — OCP/Open3D imported on first use so engine boot is fast.

## Viewport & renderer (Three.js / r3f)
- Instanced meshes for patterns/assemblies; merge static geometry; frustum + occlusion culling.
- BVH (`three-mesh-bvh`) for fast picking/section/measure on large meshes.
- glTF with Draco/meshopt compression for mesh transfer; transferable ArrayBuffers over IPC.
- Cap devicePixelRatio; adaptive quality (drop shadows/AA under load); `requestIdleCallback` for non-critical work.
- Offload mesh post-processing to Web Workers; keep the main thread for input + render.
- Virtualise large trees/lists (assembly tree, material list, timeline).

## Data plane
- Cursor pagination; select only needed columns; avoid N+1 (Prisma `include` audited).
- Cache the material library and capabilities; `ETag`/`If-None-Match` on reads.
- Immutable version rows → aggressive caching, no invalidation churn.
- Indexes per [`03-database-schema.md`](03-database-schema.md); add JSONB GIN only when query patterns demand.

## AI cost & latency
- **Prompt/response caching** (esp. Claude prompt caching) for repeated context (system prompt, tool schemas, part context).
- Stream tokens to the chat immediately; optimistic UI for tool results where safe.
- **Template path avoids LLM codegen** entirely for known parts → faster + cheaper + deterministic.
- Small/local models (Ollama) for cheap intent classification when offline/private; escalate to cloud for hard designs.
- Batch/deduplicate tool calls; cap context window with a rolling summary of the design session.

## Memory & stability
- Bounded caches (LRU) for meshes/analyses; evict by size.
- Dispose Three.js geometries/materials/textures on unmount (leak-tested).
- Engine supervisor restarts on OOM/crash and replays last IR; watchdog on the WS connection.

## Measuring & guarding
- `pytest-benchmark` budgets on rebuild/compile; regressions fail CI.
- Renderer perf traced (React Profiler, `stats.js` in dev); frame-time regressions caught in perf e2e (nightly).
- Real-user (opt-in) telemetry: rebuild latency histogram, fps, memory — to prioritise real bottlenecks over guesses.
- **Optimise from measurement, not intuition** — every perf change cites a before/after number.
