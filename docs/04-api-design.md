# 04 — API & IPC Design

Three contract boundaries, each **typed and versioned**:

1. **Renderer ⇄ Main** — Electron IPC (`packages/ipc-contracts`, Zod-validated).
2. **Main/Renderer ⇄ Engine** — HTTP REST + WebSocket (FastAPI, OpenAPI-generated TS client).
3. **App ⇄ Data plane** — Next.js route handlers / server actions over Prisma + Supabase.

General rules: **semantic versioning of the API surface** (`/api/v1`), all payloads validated at the boundary, errors follow a single envelope, long operations stream progress over WebSocket, everything idempotent where feasible.

---

## 1. Engine REST API (`/api/v1`) — Intelligence plane

Base: `http://127.0.0.1:{port}` (desktop) or the hosted engine URL. Auth: `Authorization: Bearer {sessionToken}`.

### Error envelope (all endpoints)
```jsonc
{ "error": { "code": "GEOMETRY_COMPILE_FAILED", "message": "…", "details": {…}, "retryable": false } }
```

### 1.1 Health & meta
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Liveness/readiness (kernel loaded, versions). |
| GET | `/api/v1/capabilities` | Registered plugins/templates/calculators/exporters. |

### 1.2 AI CAD & assistant
| Method | Path | Body / notes |
|---|---|---|
| POST | `/api/v1/ai/design` | `{ prompt, context?, provider? }` → starts a design job; streams over WS. Returns `{ jobId }`. |
| POST | `/api/v1/ai/edit` | `{ partId, instruction, provider? }` → proposes an **IR patch** (diff), does not auto-apply. |
| POST | `/api/v1/ai/chat` | `{ messages, tools?, provider? }` → copilot; tool-calls resolve to engine capabilities. Streams. |
| POST | `/api/v1/ai/intent` | `{ prompt }` → parsed `DesignIntent` only (debug/inspection). |

### 1.3 Parts & parametric rebuild
| Method | Path | Body / notes |
|---|---|---|
| POST | `/api/v1/parts` | `{ featureProgram }` → compile → `{ partId, mesh, paramTable, dfm, massProps }`. |
| GET | `/api/v1/parts/{id}` | Current IR + last compiled result. |
| PATCH | `/api/v1/parts/{id}/params` | `{ params: {H: 62, T: 5} }` → partial rebuild → new mesh + massProps (streams progress). |
| POST | `/api/v1/parts/{id}/patch` | Apply an IR patch (add/modify/remove features) → rebuild. |
| GET | `/api/v1/parts/{id}/mesh` | Tessellation as glTF/3MF (query: `lod`, `format`). |

### 1.4 Mesh engineering
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/mesh/import` | Upload STL/OBJ/PLY/3MF → mesh handle + stats. |
| POST | `/api/v1/mesh/repair` | `{ meshId, ops:[non_manifold, holes, normals] }` → repaired mesh + report. |
| POST | `/api/v1/mesh/analyze` | Watertight, wall-thickness field, min-wall violations, CoG/mass/volume. |
| POST | `/api/v1/mesh/simplify` | `{ meshId, targetTris | ratio }`. |
| POST | `/api/v1/mesh/boolean` | `{ a, b, op: union|diff|intersect }`. |

### 1.5 Analysis & calculators
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/calc/{name}` | e.g. `bolt`, `beam`, `gear`, `spring`, `shaft`, `bearing`, `tolerance` — `{ inputs }` → `{ result, assumptions, method, advisory:true }`. |
| POST | `/api/v1/fea/linear-static` | `{ partId, loads, supports, materialId }` → `{ maxStress, displacement, heatmapAsset, weakPoints, advisory:true }` (streams meshing/solve progress). |
| POST | `/api/v1/analysis/print-orientation` | Recommended orientation(s) with rationale. |

### 1.6 Materials & multi-material
| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/materials` | Merged system + user library. |
| POST | `/api/v1/materials/compatibility` | `{ materials:[…] }` → pairwise warnings (adhesion, temp, soluble support). |
| POST | `/api/v1/parts/{id}/materials` | Assign materials/colours to bodies; returns usage + purge estimate. |

### 1.7 Print optimisation & slicing
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/print/estimate` | `{ partId, profile }` → time, per-material mass, purge, cost. |
| POST | `/api/v1/print/optimize` | → recommended profile (orientation, layers, walls, infill, supports…) with rationale. |
| POST | `/api/v1/slice/export` | `{ partId, slicer, profileId }` → slicer project/profile + geometry asset. |

### 1.8 Blender bridge
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/blender/job` | `{ op: boolean|remesh|decimate|uv|geonodes|bake|cleanup, params }` → queued headless job; streams progress; returns new mesh/asset. |
| POST | `/api/v1/blender/open` | Open interactive session (live bridge) for a part. |

### 1.9 Export / import (CAD formats)
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/export` | `{ partId, format: step|iges|stl|3mf|obj|glb|dxf|svg }` → asset. |
| POST | `/api/v1/import` | STEP/IGES/DXF/SVG → IR (where liftable) or mesh handle. |

### WebSocket — `/api/v1/ws?token=…`
Multiplexed by `jobId`. Message frames:
```jsonc
{ "type": "progress", "jobId": "…", "phase": "meshing", "pct": 42 }
{ "type": "token",    "jobId": "…", "text": "…" }          // AI streaming
{ "type": "patch",    "jobId": "…", "irPatch": {…} }        // proposed edit
{ "type": "result",   "jobId": "…", "payload": {…} }
{ "type": "error",    "jobId": "…", "error": {…} }
```

---

## 2. Renderer ⇄ Main IPC (`packages/ipc-contracts`)

Exposed via `contextBridge` as `window.efc` — a **narrow, validated** surface. No raw `ipcRenderer`.

```ts
// packages/ipc-contracts/src/channels.ts (illustrative)
export const channels = {
  'app:openProject':   { req: OpenProjectReq,   res: ProjectDTO },
  'app:saveProject':   { req: SaveProjectReq,   res: SaveResult },
  'project:listRecent':{ req: z.void(),         res: z.array(ProjectSummary) },
  'engine:status':     { req: z.void(),         res: EngineStatus },
  'fs:pickFile':       { req: FilePickerReq,    res: FilePickerRes },
  'auth:session':      { req: z.void(),         res: SessionDTO.nullable() },
  'settings:get':      { req: SettingsKey,      res: SettingsValue },
} as const;
```
- Every handler validates `req` with Zod on the main side; responses are typed.
- The preload only forwards whitelisted channels: `invoke(channel, payload)` → `Promise<res>`.
- Engine calls that need OS/session context (tokens, file paths) go **through main**; pure geometry calls may go renderer→engine directly using the session token provided by main.

---

## 3. Data-plane API (Next.js route handlers / server actions)

Owns persistence and cloud sync via **Prisma + Supabase**. RLS enforced in Postgres; server code runs with the user's session.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/data/projects` | Create project (+ initial version). |
| GET | `/api/data/projects` | List (RLS-scoped). |
| GET | `/api/data/projects/{id}` | Project + head version + parts. |
| POST | `/api/data/projects/{id}/versions` | Append immutable snapshot. |
| POST | `/api/data/parts/{id}/versions` | Append PartVersion (IR + massProps). |
| GET/POST | `/api/data/materials` | List/create materials. |
| POST | `/api/data/print-jobs` | Record print history (est + actuals). |
| POST | `/api/data/assets/sign` | Signed upload/download URL for Supabase Storage. |
| GET | `/api/data/boms/{id}` | BOM with items + cost roll-up. |

Conventions: cursor pagination (`?cursor=&limit=`), `ETag`/`If-None-Match` on read, optimistic concurrency via version rows (append-only → no update conflicts), audit-logged mutations.

---

## 4. Cross-cutting

- **Type source of truth:** DTOs + IR generated once from `packages/core-domain` schemas → Zod (TS) + Pydantic (Python) + OpenAPI. Codegen runs in CI; drift fails the build.
- **Idempotency:** mutating engine jobs accept an `Idempotency-Key`; identical IR compiles are cache-hit by content hash.
- **Observability:** every request carries a `traceId` (renderer→main→engine) for correlated logs.
- **Versioning:** breaking API changes bump `/v2`; the client pins a supported range and negotiates via `/capabilities`.
