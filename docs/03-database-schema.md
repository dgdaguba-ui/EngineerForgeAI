# 03 — Database Schema (Data Plane)

The relational schema is the **queryable, collaborative, syncable** layer: accounts, projects, versions, materials, analyses, print history, BOM, assets. Heavy binaries (STL/STEP/renders) live in **Supabase Storage**; the DB stores their metadata + storage keys. The **Feature Program IR** is stored as JSONB on `PartVersion` (small, diffable) with large tessellations cached as assets.

- **Engine:** PostgreSQL (Supabase-hosted or self-hosted).
- **ORM:** Prisma (`prisma/schema.prisma` is canonical; this doc explains it).
- **Auth:** Supabase Auth (`auth.users`); our `User` row mirrors it 1:1 via `authId`.
- **Multi-tenancy:** every user-owned row carries `ownerId` (and optional `orgId`) to enforce **Supabase Row-Level Security** — a user reads only their rows / their org's rows.
- **Local mirror:** the desktop app keeps a **SQLite** cache with the same logical shape for offline use; a sync engine reconciles on reconnect (last-writer-wins per version, with version rows being immutable/append-only to avoid conflicts).

## Entity-relationship overview

```
User ─┬─< Membership >─ Organization
      │
      ├─< Project ──< ProjectVersion
      │      │
      │      ├─< Part ──< PartVersion ──< MaterialAssignment >── Material
      │      │                 │
      │      │                 └─< Analysis        (FEA / calculator cache)
      │      │
      │      ├─< Assembly ──< AssemblyNode (self-ref tree) ──< Mate
      │      ├─< Drawing
      │      ├─< PrintJob ──> PrintProfile
      │      ├─< Bom ──< BomItem
      │      └─< Asset            (Storage metadata: stl/step/glb/render/thumbnail)
      │
      ├─< Material (custom, owner/org-scoped)
      └─< AuditLog
Fastener   (global + org library)
```

## Design notes

- **Immutable versions.** `ProjectVersion` / `PartVersion` are append-only snapshots (semantic-ish version label + parent link) → clean history, easy diff, conflict-free sync. The mutable `Project`/`Part` rows point at a `headVersionId`.
- **IR storage.** `PartVersion.featureProgram` = JSONB (the IR). Small and query-friendly (e.g., index parts by material via a generated column later). Compiled meshes are `Asset`s referenced by the version.
- **Analyses cached & invalidated.** An `Analysis` row is keyed by `(partVersionId, kind, inputsHash)`; if the IR/version changes, prior analyses remain but are marked stale by mismatched `partVersionId`.
- **Materials are library rows**, not enums, so users add custom materials; curated ones are `isSystem = true, ownerId = null`.
- **Cost & print history** live on `PrintJob` with both **estimated** and **actual** fields → feeds estimate-accuracy metrics.
- **Assets** never store bytes in Postgres — only `storageBucket`, `storageKey`, `contentType`, `sizeBytes`, `checksum`.
- **Enums** for constrained vocab (asset kind, analysis kind, print status, manufacturing process, mate type).
- **Soft delete** via `deletedAt` on user-facing aggregates; hard delete is a privileged, audited operation (never done automatically).

## Canonical schema

The authoritative definition is [`prisma/schema.prisma`](../prisma/schema.prisma). Summary of models:

| Model | Purpose | Key fields |
|---|---|---|
| `User` | App profile mirroring Supabase auth | `authId`, `email`, `preferences` |
| `Organization`, `Membership` | Teams for small manufacturers | `role` (OWNER/ADMIN/MEMBER) |
| `Project` | Top-level design container | `headVersionId`, `ownerId`, `orgId` |
| `ProjectVersion` | Immutable project snapshot | `label`, `parentId`, `createdById` |
| `Part` | A component within a project | `projectId`, `headVersionId` |
| `PartVersion` | Immutable IR snapshot | `featureProgram` (JSONB), `paramTableCache`, `massG`, `volumeMm3` |
| `Material` | Curated + custom materials | `density`, `youngsModulus`, `yieldStrength`, `shrinkage`, `printTempC`, `costPerKg`, `isSystem` |
| `MaterialAssignment` | Body/feature → material (multi-material) | `partVersionId`, `bodyRef`, `materialId`, `colorHex` |
| `Assembly`, `AssemblyNode`, `Mate` | Assembly tree + constraints | self-referential `parentId`, `mateType` |
| `Analysis` | Cached FEA/calculator result | `kind`, `inputsHash`, `result` (JSONB), `advisory` |
| `PrintProfile` | Slicer profile | `slicer`, `settings` (JSONB) |
| `PrintJob` | Print history + estimates/actuals | `estMaterialG`, `actMaterialG`, `estMinutes`, `estCost`, `status` |
| `Bom`, `BomItem` | Bill of materials | `quantity`, `unitCost`, `reference` |
| `Drawing` | Engineering drawing metadata | `sheetSize`, `revision`, `pdfAssetId` |
| `Fastener` | Fastener library | `standard`, `size`, `grade` |
| `Asset` | Storage object metadata | `kind`, `storageKey`, `checksum`, `sizeBytes` |
| `AuditLog` | Security/compliance trail | `actorId`, `action`, `target`, `meta` |

## Indexing & performance (initial)

- `Project(ownerId, updatedAt)`, `Part(projectId)`, `PartVersion(partId, createdAt)` for list views.
- `Analysis(partVersionId, kind, inputsHash)` unique — cache key.
- `Asset(ownerId, kind)`, `PrintJob(projectId, createdAt)`.
- `Material(ownerId)` + partial index `WHERE isSystem` for the curated set.
- JSONB GIN index on `PartVersion.featureProgram` deferred until query patterns emerge.

## Migrations & seeding

- `prisma migrate` for schema evolution; migrations reviewed in PRs, run in CI against an ephemeral Postgres.
- `prisma/seed.ts` seeds the **system material library** (PLA/PETG/ABS/ASA/Nylon/CF/TPU/PC/PVA/support) and a demo project. Material seed source is `packages/materials/data`.
