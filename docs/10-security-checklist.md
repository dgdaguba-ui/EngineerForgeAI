# 10 — Security Checklist

EngineerForge AI executes AI-generated code, loads untrusted geometry files, talks to cloud services, and ships to desktops. Security is designed in, not bolted on. This is the actionable checklist; the model is described in [`01-architecture.md#security-architecture`](01-architecture.md#8-security-architecture).

## Electron hardening
- [ ] `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true` on every window.
- [ ] No `@electron/remote`; renderer touches the OS **only** via the whitelisted `preload` (`window.efc`).
- [ ] Strict **CSP**; disable `eval`; `webSecurity: true`; block `window.open`/new-window except allow-listed.
- [ ] Validate **all** IPC input with Zod on the main side; never trust the renderer.
- [ ] Verify navigation targets; deny arbitrary `file://`/remote loads.
- [ ] Auto-update over HTTPS with signature verification; pin the update feed.

## Untrusted code execution (LLM-generated CadQuery / third-party plugins)
- [ ] Runs in a **separate subprocess**, never in the API worker.
- [ ] **No network** (blocked at process level), **filesystem restricted** to a scratch dir.
- [ ] **CPU / memory / wall-time limits**; timeouts kill and report cleanly.
- [ ] **AST allowlist**: only whitelisted imports/calls; deny `os`, `sys`, `subprocess`, `socket`, `open` outside scratch, `__import__`, dunder escapes, `eval`/`exec`.
- [ ] Output validated (geometry only) before it re-enters the trusted process.
- [ ] Sandbox escape attempts are unit-tested (network, fs, import, timeout).

## AI safety & prompt injection
- [ ] System prompts forbid fabricating engineering values; numbers must come from **tool calls** (calculators/materials/solvers).
- [ ] Content from imported files/model output is treated as **data, not instructions** (injection-resistant).
- [ ] AI edits are **proposed as diffs**, applied only on explicit user action — no silent state mutation.
- [ ] Provider API keys never sent to the renderer; requests proxied through main/data-plane.
- [ ] Rate-limit + budget caps on AI calls; log tool invocations for audit.

## Engine transport
- [ ] FastAPI binds `127.0.0.1` on an ephemeral port (desktop); never `0.0.0.0` in desktop mode.
- [ ] Every request requires a **per-session bearer token** minted by main at spawn.
- [ ] Request size limits, timeouts, and input validation (Pydantic) on all endpoints.
- [ ] Hosted mode adds authn/z, TLS, WAF, and per-tenant isolation.

## Data, secrets & privacy
- [ ] Secrets in OS keychain (`keytar`) / secret manager — never in project files, logs, or the renderer bundle.
- [ ] `SERVICE_ROLE` keys used **server-side only**; renderer uses anon key + user session.
- [ ] **Supabase RLS** on every table/bucket: users access only their own (or their org's) rows/objects.
- [ ] Signed, expiring URLs for Storage; no public buckets for user assets.
- [ ] No personal data in URLs/query strings; TLS everywhere for cloud.
- [ ] Telemetry is opt-in, anonymised, and never includes model geometry or prompts without consent.
- [ ] Clear data-deletion path; hard deletes are privileged + audit-logged.

## Supply chain & build
- [ ] Lockfiles committed (`pnpm-lock.yaml`, `uv.lock`); `--frozen` installs in CI.
- [ ] Dependency audit + CodeQL + secret scanning in CI; criticals block merge.
- [ ] License compliance check (esp. OCP/CadQuery/Open3D licenses reviewed before distribution).
- [ ] Code signing for all installers; notarisation on macOS.
- [ ] SBOM generated per release.
- [ ] Signing/notary secrets scoped to the release workflow; unavailable to fork PRs.

## File import safety
- [ ] Parse untrusted STL/OBJ/STEP/… defensively; cap size/complexity; time-box parsing.
- [ ] Reject/΅sanitise pathological meshes (billions of tris, NaN coords) before processing.
- [ ] Imported files never auto-execute anything; no macro-bearing formats executed.

## Release gate
Security scan green · sandbox tests pass · RLS tests pass · secrets audit clean · signing verified · SBOM attached. All required before a tagged release ships.
