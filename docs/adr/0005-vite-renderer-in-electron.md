# 0005 — Vite (not Next.js) for the Electron renderer

Status: Accepted

## Context
The preferred stack lists Next.js for the frontend. Next.js is built around a server (SSR/route handlers) or a static export. Inside Electron, embedding a Node server per desktop install adds a process, port, and attack surface for zero benefit — the renderer is a local, single-page, long-lived workspace UI (viewport, panels, chat), not a routed website. The desktop renderer must also load from `file://` in packaged builds, which Next.js supports only via constrained static export.

## Decision
The **desktop renderer is a Vite + React + TypeScript SPA** (`apps/renderer`): instant HMR in dev, a plain static bundle loaded by Electron in production, first-class Tailwind/vitest integration. **Next.js remains the choice for the future hosted/web mode** (Phase 2+ data-plane BFF and team web app), where its server model earns its keep. All UI is plain React components — portable to the Next.js app unchanged.

## Consequences
**Positive:** simpler/leaner desktop runtime (no embedded server), trivial `file://` packaging, faster dev loop, smaller bundle.
**Negative:** deviates from the stated stack for the desktop shell (documented here); if the hosted web app ships, two build tools coexist (mitigated by shared `packages/ui` components).
**Neutral:** the data-plane API moves to the Electron main process (local) and later a Next.js service (hosted) — matching ADR-0004's local-first design.

## Alternatives considered
- **Next.js static export in Electron:** rejected — loses the only Next.js advantages (server features) while keeping its constraints.
- **Next.js dev server embedded in the app:** rejected — extra process/port/attack surface per install; slower start.
