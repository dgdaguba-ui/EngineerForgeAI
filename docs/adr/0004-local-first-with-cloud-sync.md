# 0004 — Local-first data with optional cloud sync

Status: Accepted

## Context
Users are desktop engineers/makers who must work **offline** and own their files, but small manufacturers also want **shared projects, versions, and history** across a team. The stack lists Supabase (Auth + Storage + Postgres) and Prisma.

## Decision
**Local-first with optional cloud sync.** The desktop app is fully functional offline: projects are transparent `.efproj` bundles on disk (manifest + IR + cached meshes + assets), with a local **SQLite** cache for metadata/queue. When the user signs in (Supabase Auth), projects/versions/materials sync to **Postgres** (via Prisma) and binary assets to **Supabase Storage**, guarded by **RLS**. Version rows are **immutable/append-only**, so sync reconciliation is conflict-free (last-writer-wins only on mutable head pointers).

## Consequences
**Positive:** works offline; users own inspectable files (no lock-in); team collaboration + history when signed in; RLS gives per-user/org isolation; immutable versions make sync simple and safe.
**Negative:** two persistence paths (local bundle + cloud DB) to keep coherent; a sync engine to build and test; asset dedup/checksum handling.
**Neutral:** the same schema backs desktop SQLite and cloud Postgres (logical parity), reducing divergence.

## Alternatives considered
- **Cloud-only:** rejected — breaks offline use and file ownership.
- **Local-only:** rejected — no team collaboration/history for small manufacturers.
- **CRDT real-time co-editing:** deferred — valuable later, but heavy; immutable versioning covers v1 collaboration needs.
