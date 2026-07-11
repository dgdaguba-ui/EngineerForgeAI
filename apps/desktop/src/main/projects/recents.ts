/**
 * Recent-projects list, persisted as JSON in the app's userData directory.
 * Entries pointing at deleted projects are filtered out on read.
 */
import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { PROJECT_FILE_NAME, type ProjectInfo } from "@efc/ipc-contracts";

const MAX_RECENTS = 12;

export class RecentProjects {
  constructor(private readonly storageFile: string) {}

  private async readAll(): Promise<ProjectInfo[]> {
    try {
      if (!existsSync(this.storageFile)) return [];
      const raw = await readFile(this.storageFile, "utf8");
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) return [];
      return parsed.filter(
        (e): e is ProjectInfo =>
          typeof e === "object" &&
          e !== null &&
          typeof (e as ProjectInfo).path === "string" &&
          typeof (e as ProjectInfo).name === "string",
      );
    } catch {
      return []; // a corrupt recents file must never break the app
    }
  }

  private async writeAll(entries: ProjectInfo[]): Promise<void> {
    await mkdir(path.dirname(this.storageFile), { recursive: true });
    await writeFile(this.storageFile, JSON.stringify(entries, null, 2), "utf8");
  }

  async add(info: ProjectInfo): Promise<void> {
    const existing = await this.readAll();
    const deduped = existing.filter((e) => path.resolve(e.path) !== path.resolve(info.path));
    await this.writeAll([info, ...deduped].slice(0, MAX_RECENTS));
  }

  /** Most-recent-first list of projects that still exist on disk. */
  async list(): Promise<ProjectInfo[]> {
    const all = await this.readAll();
    return all.filter((e) => existsSync(path.join(e.path, PROJECT_FILE_NAME)));
  }
}
