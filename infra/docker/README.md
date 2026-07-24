# Local data plane (Postgres)

The EngineerForge AI app is **offline-first** and runs fully without this. A
local PostgreSQL is only needed for the optional hosted / data-plane mode (the
Prisma schema in [`prisma/`](../../prisma)) — usage tracking and future
multi-device / collaboration features.

## Prerequisites

- **Docker Desktop** running (WSL 2 backend on Windows).
- The repo's `.env` with `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/efc`
  (the credentials the compose file provisions).

## Commands (from the repo root)

```bash
pnpm db:up          # start Postgres 16 in the background
pnpm db:migrate     # apply prisma/migrations (= prisma migrate deploy)
pnpm db:studio      # open Prisma Studio (browser DB viewer)
pnpm db:down        # stop Postgres (data is kept in the named volume)
```

To wipe the database (drop the data volume):

```bash
docker compose -f infra/docker/docker-compose.dev.yml down -v
```

## Verify

```bash
docker exec efc-postgres psql -U postgres -d efc -c "\dt"
```

The initial migration (`prisma/migrations/0001_init`) creates 22 tables
(`User`, `Organization`, `Project`, `Part`, `Material`, `Analysis`, …) plus
Prisma's `_prisma_migrations` bookkeeping table.
