# 09 — CI/CD & GitHub Actions

Principles: **fast PR feedback**, **cross-language** (TS + Python), **cross-OS** for desktop builds, **no manual release steps**, **security scanning built in**.

## Pipelines

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | PR, push to `main` | lint, typecheck, unit + integration + contract tests (TS & Python), codegen-drift check |
| `e2e.yml` | PR (labelled) + nightly | Playwright over built Electron app (Linux; Win/macOS nightly) |
| `security.yml` | PR + weekly | dependency audit, secret scan, CodeQL, license check |
| `build.yml` | tag `v*` | build signed installers (Win/macOS/Linux matrix) + engine Docker image |
| `release.yml` | tag `v*` after build | publish release, push update feed, run prod DB migration job |
| `nightly-eval.yml` | schedule | AI eval suite (non-blocking), perf benchmark trend |

## Key design points

- **Turborepo remote cache** → only changed packages rebuild/test; PRs stay fast.
- **Path-filtered jobs** — engine (Python) and app (TS) jobs run independently; a docs-only PR skips heavy jobs.
- **Codegen drift gate** — `pnpm codegen && git diff --exit-code` fails if generated types (IR Pydantic/Zod, OpenAPI client) are stale.
- **Ephemeral Postgres** service container for Prisma/RLS integration tests; migrations applied then torn down.
- **Python 3.12 pinned** in CI (matches runtime); OCP/open3d wheels cached.
- **Matrix desktop builds** with code signing secrets scoped to the release workflow only (never exposed to PRs from forks).

## Illustrative `ci.yml`

```yaml
name: ci
on:
  pull_request:
  push: { branches: [main] }
concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }

jobs:
  js:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version-file: .nvmrc, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm codegen && git diff --exit-code    # drift gate
      - run: pnpm turbo lint typecheck test

  engine:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: postgres, POSTGRES_DB: efc_test }
        ports: [ '5432:5432' ]
        options: >-
          --health-cmd="pg_isready" --health-interval=10s
          --health-timeout=5s --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv python install 3.12
      - working-directory: apps/engine
        run: uv sync --frozen
      - working-directory: apps/engine
        run: uv run ruff check . && uv run mypy . && uv run pytest -q
```

## Illustrative `build.yml` (desktop matrix)

```yaml
name: build
on: { push: { tags: ['v*'] } }
jobs:
  desktop:
    strategy:
      matrix: { os: [ubuntu-latest, windows-latest, macos-latest] }
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version-file: .nvmrc, cache: pnpm }
      - uses: astral-sh/setup-uv@v3
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter engine freeze         # bundle Python 3.12 engine
      - run: pnpm --filter desktop build          # electron-builder → installer
        env:
          CSC_LINK: ${{ secrets.CSC_LINK }}        # code signing (scoped to this workflow)
          APPLE_ID: ${{ secrets.APPLE_ID }}
      - uses: actions/upload-artifact@v4
        with: { name: installer-${{ matrix.os }}, path: dist/ }
```

## Branching & versioning
- Trunk-based: short-lived branches → PR → `main`. `main` is always releasable.
- **Conventional Commits** → automated changelog + semver bump.
- Release by tagging `vX.Y.Z`; pre-releases use `-rc.N`.
- Migrations reviewed in PR; applied only in the gated `release.yml` job.

## Quality gates (block merge)
lint · typecheck (TS strict + mypy) · unit/integration/contract · codegen drift · security scan (no criticals) · (once it exists) MVP e2e.
