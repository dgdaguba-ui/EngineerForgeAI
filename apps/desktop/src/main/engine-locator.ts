/**
 * Pure helpers for locating the Python engine and its interpreter.
 * Filesystem access is injected so every branch is unit-testable.
 */
import path from "node:path";

export interface LocatorFs {
  exists(p: string): boolean;
}

/** Where the engine source lives: repo layout in dev, resources/ in packaged builds. */
export function resolveEngineDir(opts: {
  appPath: string;
  isPackaged: boolean;
  resourcesPath: string;
}): string {
  if (opts.isPackaged) {
    return path.join(opts.resourcesPath, "engine");
  }
  // dev: apps/desktop → apps/engine
  return path.resolve(opts.appPath, "..", "engine");
}

/**
 * Resolve the Python 3.12 interpreter for the engine.
 * Order: explicit EFC_ENGINE_PYTHON override → the engine's uv-managed .venv.
 * Never falls back to system `python` (which may be 3.14 — see ADR-0001).
 */
export function resolvePythonPath(opts: {
  engineDir: string;
  envOverride: string | null | undefined;
  platform: NodeJS.Platform;
  fs: LocatorFs;
}): string | null {
  if (opts.envOverride && opts.fs.exists(opts.envOverride)) {
    return opts.envOverride;
  }
  const venvPython =
    opts.platform === "win32"
      ? path.join(opts.engineDir, ".venv", "Scripts", "python.exe")
      : path.join(opts.engineDir, ".venv", "bin", "python");
  return opts.fs.exists(venvPython) ? venvPython : null;
}

/** uvicorn invocation for the engine process. */
export function buildEngineArgs(port: number): string[] {
  return [
    "-m",
    "uvicorn",
    "engineerforge_engine.api.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    String(port),
    "--log-level",
    "info",
  ];
}

/** Exponential restart backoff, capped at 15s. */
export function nextBackoffMs(restarts: number): number {
  return Math.min(1000 * 2 ** restarts, 15_000);
}
