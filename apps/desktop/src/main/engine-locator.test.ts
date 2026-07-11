import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  buildEngineArgs,
  nextBackoffMs,
  resolveEngineDir,
  resolvePythonPath,
} from "./engine-locator.js";

describe("resolveEngineDir", () => {
  it("uses sibling apps/engine in dev", () => {
    const dir = resolveEngineDir({
      appPath: path.join("C:", "repo", "apps", "desktop"),
      isPackaged: false,
      resourcesPath: path.join("C:", "unused"),
    });
    expect(dir).toBe(path.resolve(path.join("C:", "repo", "apps", "engine")));
  });

  it("uses resources/engine when packaged", () => {
    const dir = resolveEngineDir({
      appPath: path.join("C:", "install", "app.asar"),
      isPackaged: true,
      resourcesPath: path.join("C:", "install", "resources"),
    });
    expect(dir).toBe(path.join("C:", "install", "resources", "engine"));
  });
});

describe("resolvePythonPath", () => {
  const engineDir = path.join("C:", "repo", "apps", "engine");
  const winVenv = path.join(engineDir, ".venv", "Scripts", "python.exe");
  const posixVenv = path.join(engineDir, ".venv", "bin", "python");

  it("prefers a valid EFC_ENGINE_PYTHON override", () => {
    const override = path.join("C:", "py312", "python.exe");
    const result = resolvePythonPath({
      engineDir,
      envOverride: override,
      platform: "win32",
      fs: { exists: (p) => p === override },
    });
    expect(result).toBe(override);
  });

  it("ignores an override that does not exist and falls back to the venv", () => {
    const result = resolvePythonPath({
      engineDir,
      envOverride: path.join("C:", "missing", "python.exe"),
      platform: "win32",
      fs: { exists: (p) => p === winVenv },
    });
    expect(result).toBe(winVenv);
  });

  it("uses bin/python on posix", () => {
    const result = resolvePythonPath({
      engineDir,
      envOverride: null,
      platform: "linux",
      fs: { exists: (p) => p === posixVenv },
    });
    expect(result).toBe(posixVenv);
  });

  it("returns null when nothing exists (never system python)", () => {
    const result = resolvePythonPath({
      engineDir,
      envOverride: null,
      platform: "win32",
      fs: { exists: () => false },
    });
    expect(result).toBeNull();
  });
});

describe("buildEngineArgs", () => {
  it("builds a uvicorn invocation bound to loopback", () => {
    const args = buildEngineArgs(8123);
    expect(args).toContain("uvicorn");
    expect(args).toContain("engineerforge_engine.api.main:app");
    expect(args).toContain("127.0.0.1");
    expect(args).toContain("8123");
  });
});

describe("nextBackoffMs", () => {
  it("doubles and caps at 15s", () => {
    expect(nextBackoffMs(0)).toBe(1000);
    expect(nextBackoffMs(1)).toBe(2000);
    expect(nextBackoffMs(3)).toBe(8000);
    expect(nextBackoffMs(10)).toBe(15_000);
  });
});
