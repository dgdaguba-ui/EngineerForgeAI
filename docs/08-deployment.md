# 08 — Local Development Setup, Deployment & Docker

Covers: local dev bootstrap, the **Python 3.12 constraint**, desktop packaging, and optional hosted (team) mode.

---

## 1. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Node.js | 20 LTS | `.nvmrc` pins it |
| pnpm | 9+ | `corepack enable` |
| Python | **3.12.x** | **Not 3.14** — see §2 |
| uv | latest | fast Python env/dep manager |
| Git | 2.4+ | |
| Docker | latest | hosted mode + CI parity + Blender jobs |
| Blender | 4.x | optional until Phase 6 |

### ⚠️ 2. The Python version constraint (important)
This machine has **Python 3.14**, but the CAD/mesh stack (`cadquery`, `OCP`/OpenCascade, `open3d`) does **not** ship wheels for 3.14 yet. Building them from source is impractical. **The engine therefore targets Python 3.12**, installed and managed *independently of system Python*:

```bash
# from apps/engine
uv python install 3.12          # uv fetches a standalone 3.12 (doesn't touch system Python)
uv venv --python 3.12 .venv
uv sync                         # installs pinned deps into .venv
```
The desktop supervisor launches the engine using this pinned interpreter path (configurable via `EFC_ENGINE_PYTHON`). Do not rely on `python` on PATH.

---

## 3. Local development

```bash
git clone <repo> && cd engineerforge-ai
corepack enable && pnpm install          # JS workspaces
pnpm --filter engine setup               # runs uv python install 3.12 + uv sync
cp .env.example .env                      # fill Supabase + AI keys (see below)
pnpm db:up                                # local Postgres via Docker
pnpm prisma migrate dev && pnpm db:seed   # schema + material library
pnpm dev                                  # renderer + main + engine concurrently
```

- `pnpm dev` uses Turborepo to run: Next.js renderer, Electron main (which supervises the engine), and `uvicorn` for the engine with reload.
- `pnpm codegen` regenerates cross-language types (IR schema → Pydantic/Zod) and the engine OpenAPI → TS client.
- Secrets live in `.env` (dev) and the **OS keychain** at runtime (never in project files or the renderer bundle).

### `.env.example` (keys, not values)
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/efc
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=     # server-side only, never shipped to renderer
ANTHROPIC_API_KEY=             # stored in keychain at runtime
OPENAI_API_KEY=
OLLAMA_HOST=http://localhost:11434
EFC_ENGINE_PYTHON=             # optional override for the 3.12 interpreter
```

---

## 4. Desktop packaging (the primary product)

- **electron-builder** produces signed installers: Windows (NSIS/`.exe` + MSIX), macOS (`.dmg`, notarised), Linux (`AppImage`, `.deb`).
- The **Python engine is bundled** as a standalone artifact (PyInstaller/`uv`-frozen env) so users need no Python install. The supervisor prefers the bundled interpreter; `EFC_ENGINE_PYTHON` overrides for dev.
- **Auto-update** via electron-updater against a release feed (GitHub Releases or S3).
- Native deps (OCP) are large — installer size is a tracked budget; per-OS build matrix in CI.

### Packaging layout (installed app)
```
EngineerForge AI/
├─ EngineerForge.exe            # Electron
├─ resources/renderer/          # built Next.js
└─ resources/engine/            # frozen Python 3.12 + engine + OCP/trimesh/open3d
```

---

## 5. Hosted / team mode (optional, Phase 2+)

Same code, different composition root + transport. For small manufacturers wanting shared projects:

```
┌── Web client (Next.js) ──┐   ┌── Data plane (Next.js API) ──┐   ┌── Engine (FastAPI) ──┐
│  browser UART/viewport   │──▶│  Prisma + Supabase (RLS)     │──▶│  containerised, HPA  │
└──────────────────────────┘   └──────────────────────────────┘   │  Blender workers     │
                                                                    └──────────────────────┘
```

- **Engine container** (`infra/docker/engine.Dockerfile`): Python 3.12-slim + OCP/trimesh/open3d + FastAPI + a headless Blender for jobs. Scales horizontally; stateless (state in DB/Storage).
- **Data plane**: Supabase (managed Postgres + Auth + Storage) or self-hosted Postgres; Next.js deployed to a container/Vercel-style host.
- **`docker-compose.yml`** for local hosted-mode parity: `postgres`, `engine`, `web`, `ollama` (optional).
- Autoscaling on the engine (CPU-bound geometry/FEA); job queue (Redis/RQ) for long Blender/FEA tasks.

### Example (illustrative) `infra/docker/engine.Dockerfile`
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglu1-mesa libxrender1 libxi6 libxkbcommon0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY apps/engine/pyproject.toml apps/engine/uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY apps/engine/ .
EXPOSE 8000
CMD ["uv","run","uvicorn","engineerforge_engine.api.main:app","--host","0.0.0.0","--port","8000"]
```

---

## 6. Environments & config
- **dev** (local, hot reload) · **ci** (ephemeral) · **staging** (hosted, pre-release) · **prod**.
- Config via env + a typed config module per app; secrets from keychain/secret manager, never committed.
- Database migrations run in a gated release step (never auto-migrate prod on boot).

## 7. Release process (summary; CI in [`09-cicd.md`](09-cicd.md))
1. Tag `vX.Y.Z` → CI builds installers (matrix), engine container, runs full test suite.
2. Sign + notarise; publish to release feed; auto-update picks it up.
3. Run DB migration job against prod; smoke test; announce.
4. Rollback = re-point update feed to previous release + reverse migration if needed.
