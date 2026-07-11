import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import type { ProjectInfo } from "@efc/ipc-contracts";

import { RecentProjects } from "./recents.js";

let tmp: string;
let recents: RecentProjects;

function makeProjectDir(name: string): string {
  const dir = path.join(tmp, `${name}.efproj`);
  mkdirSync(dir, { recursive: true });
  writeFileSync(path.join(dir, "project.json"), "{}", "utf8");
  return dir;
}

function info(name: string, dir: string): ProjectInfo {
  return { id: name, name, path: dir, updatedAt: "2026-07-11T00:00:00Z" };
}

beforeEach(() => {
  tmp = mkdtempSync(path.join(os.tmpdir(), "efc-recents-"));
  recents = new RecentProjects(path.join(tmp, "store", "recent.json"));
});

afterEach(() => {
  rmSync(tmp, { recursive: true, force: true });
});

describe("RecentProjects", () => {
  it("returns empty when nothing stored", async () => {
    expect(await recents.list()).toEqual([]);
  });

  it("adds most-recent-first and dedupes by path", async () => {
    const a = makeProjectDir("A");
    const b = makeProjectDir("B");
    await recents.add(info("A", a));
    await recents.add(info("B", b));
    await recents.add(info("A", a)); // re-open A

    const list = await recents.list();
    expect(list.map((e) => e.name)).toEqual(["A", "B"]);
  });

  it("filters out projects deleted from disk", async () => {
    const a = makeProjectDir("A");
    const b = makeProjectDir("B");
    await recents.add(info("A", a));
    await recents.add(info("B", b));
    rmSync(a, { recursive: true, force: true });

    const list = await recents.list();
    expect(list.map((e) => e.name)).toEqual(["B"]);
  });

  it("survives a corrupt storage file", async () => {
    const storageFile = path.join(tmp, "store", "recent.json");
    mkdirSync(path.dirname(storageFile), { recursive: true });
    writeFileSync(storageFile, "definitely not json", "utf8");
    expect(await recents.list()).toEqual([]);
    const a = makeProjectDir("A");
    await recents.add(info("A", a));
    expect((await recents.list()).map((e) => e.name)).toEqual(["A"]);
  });
});
