# Changelog

All notable changes to EngineerForge AI are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Phase 0 architecture package: overview, architecture, folder structure, database schema, API design, roadmap, MVP plan, testing strategy, deployment, CI/CD, security checklist, performance strategy (`docs/`).
- Architecture Decision Records 0001–0004 (`docs/adr/`).
- Monorepo scaffold: pnpm workspaces + Turborepo; root config (`package.json`, `pnpm-workspace.yaml`, `turbo.json`, `.gitignore`, `.env.example`, `.nvmrc`, `.python-version`).
- Canonical Prisma data-plane schema (`prisma/schema.prisma`).
- Project tracking docs: `PROJECT_STATUS.md`, `CHANGELOG.md`, `TODO.md`, root `ARCHITECTURE.md`.

### Notes
- Toolchain verified on the dev machine: Node 20.18, pnpm 9.12, Python 3.12.11 (uv), Blender 5.0.
- Docker/Postgres deferred (offline-first does not require them).
