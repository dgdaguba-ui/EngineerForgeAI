import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  LocalProjectStore,
  normalizeProjectDir,
  ProjectStoreError,
  projectNameFromDir,
} from "./local-store.js";

let tmp: string;
let store: LocalProjectStore;

beforeEach(() => {
  tmp = mkdtempSync(path.join(os.tmpdir(), "efc-projtest-"));
  store = new LocalProjectStore(() => "2026-07-11T10:00:00.000Z");
});

afterEach(() => {
  rmSync(tmp, { recursive: true, force: true });
});

describe("normalizeProjectDir / projectNameFromDir", () => {
  it("appends .efproj when missing and derives the name", () => {
    expect(normalizeProjectDir(path.join("C:", "x", "Bracket"))).toBe(
      path.join("C:", "x", "Bracket.efproj"),
    );
    expect(projectNameFromDir(path.join("C:", "x", "Bracket.efproj"))).toBe("Bracket");
  });
});

describe("LocalProjectStore", () => {
  it("creates a project and reopens it identically", async () => {
    const created = await store.createProject(path.join(tmp, "Gearbox"));
    expect(created.info.name).toBe("Gearbox");
    expect(created.info.path.endsWith(".efproj")).toBe(true);

    const opened = await store.openProject(created.info.path);
    expect(opened.doc).toEqual(created.doc);
    expect(opened.info).toEqual(created.info);
  });

  it("refuses to create over an existing project", async () => {
    const created = await store.createProject(path.join(tmp, "Twice"));
    await expect(store.createProject(created.info.path)).rejects.toMatchObject({
      code: "ALREADY_EXISTS",
    });
  });

  it("rejects non-project directories", async () => {
    await expect(store.openProject(tmp)).rejects.toMatchObject({ code: "NOT_A_PROJECT" });
  });

  it("rejects corrupt JSON", async () => {
    const created = await store.createProject(path.join(tmp, "Corrupt"));
    writeFileSync(path.join(created.info.path, "project.json"), "{not json", "utf8");
    await expect(store.openProject(created.info.path)).rejects.toMatchObject({
      code: "INVALID_PROJECT",
    });
  });

  it("rejects schema-invalid documents", async () => {
    const created = await store.createProject(path.join(tmp, "BadSchema"));
    await writeFile(
      path.join(created.info.path, "project.json"),
      JSON.stringify({ schema: "efproj/1", id: "", name: "x" }),
      "utf8",
    );
    await expect(store.openProject(created.info.path)).rejects.toBeInstanceOf(ProjectStoreError);
  });

  it("saveProject stamps updatedAt and persists changes", async () => {
    const created = await store.createProject(path.join(tmp, "Save"));
    const laterStore = new LocalProjectStore(() => "2026-07-12T00:00:00.000Z");
    const info = await laterStore.saveProject(created.info.path, {
      ...created.doc,
      printerProfileId: "flashforge-ad5x",
    });
    expect(info.updatedAt).toBe("2026-07-12T00:00:00.000Z");
    const reopened = await store.openProject(created.info.path);
    expect(reopened.doc.printerProfileId).toBe("flashforge-ad5x");
    expect(reopened.doc.updatedAt).toBe("2026-07-12T00:00:00.000Z");
  });

  it("imports assets with sanitized, de-duplicated names", async () => {
    const created = await store.createProject(path.join(tmp, "Assets"));
    const src = path.join(tmp, "my part (v2).stl");
    writeFileSync(src, "solid x\nendsolid x\n", "utf8");

    const first = await store.importAsset(created.info.path, src);
    const second = await store.importAsset(created.info.path, src);
    expect(first.relPath).toBe("assets/my_part_v2_.stl");
    expect(second.relPath).toBe("assets/my_part_v2_-1.stl");

    const copied = await readFile(path.join(created.info.path, first.relPath), "utf8");
    expect(copied).toContain("solid x");
  });

  it("rejects importing a missing source file", async () => {
    const created = await store.createProject(path.join(tmp, "Missing"));
    await expect(
      store.importAsset(created.info.path, path.join(tmp, "nope.stl")),
    ).rejects.toMatchObject({ code: "ASSET_MISSING" });
  });
});
