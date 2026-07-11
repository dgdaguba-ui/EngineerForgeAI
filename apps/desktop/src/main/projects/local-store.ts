/**
 * LocalProjectStore — the source-of-truth persistence for `.efproj` bundles
 * (ADR-0004: local-first). A project is a plain directory:
 *
 *   MyPart.efproj/
 *     project.json   ← validated ProjectDoc
 *     assets/        ← imported meshes
 *
 * Writes are atomic (tmp file + rename) so a crash never corrupts a project.
 */
import { randomUUID } from "node:crypto";
import { existsSync } from "node:fs";
import { copyFile, mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

import {
  newProjectDoc,
  PROJECT_DIR_EXTENSION,
  PROJECT_FILE_NAME,
  ProjectDocSchema,
  type ProjectDoc,
  type ProjectInfo,
} from "@efc/ipc-contracts";

export class ProjectStoreError extends Error {
  constructor(
    message: string,
    readonly code:
      | "NOT_A_PROJECT"
      | "INVALID_PROJECT"
      | "ALREADY_EXISTS"
      | "ASSET_MISSING"
      | "IO_ERROR",
  ) {
    super(message);
    this.name = "ProjectStoreError";
  }
}

function infoFrom(doc: ProjectDoc, dirPath: string): ProjectInfo {
  return { id: doc.id, name: doc.name, path: dirPath, updatedAt: doc.updatedAt };
}

/** Ensure the bundle directory name carries the .efproj extension. */
export function normalizeProjectDir(requestedPath: string): string {
  return requestedPath.endsWith(PROJECT_DIR_EXTENSION)
    ? requestedPath
    : `${requestedPath}${PROJECT_DIR_EXTENSION}`;
}

export function projectNameFromDir(dirPath: string): string {
  return path.basename(dirPath).replace(/\.efproj$/i, "");
}

export class LocalProjectStore {
  constructor(private readonly now: () => string = () => new Date().toISOString()) {}

  async createProject(requestedDirPath: string): Promise<{ info: ProjectInfo; doc: ProjectDoc }> {
    const dirPath = normalizeProjectDir(requestedDirPath);
    if (existsSync(path.join(dirPath, PROJECT_FILE_NAME))) {
      throw new ProjectStoreError(`Project already exists at ${dirPath}`, "ALREADY_EXISTS");
    }
    const doc = newProjectDoc({
      id: randomUUID(),
      name: projectNameFromDir(dirPath),
      now: this.now(),
    });
    await mkdir(path.join(dirPath, "assets"), { recursive: true });
    await this.writeDoc(dirPath, doc);
    return { info: infoFrom(doc, dirPath), doc };
  }

  async openProject(dirPath: string): Promise<{ info: ProjectInfo; doc: ProjectDoc }> {
    const file = path.join(dirPath, PROJECT_FILE_NAME);
    if (!existsSync(file)) {
      throw new ProjectStoreError(
        `${dirPath} is not an EngineerForge project (missing ${PROJECT_FILE_NAME})`,
        "NOT_A_PROJECT",
      );
    }
    let raw: string;
    try {
      raw = await readFile(file, "utf8");
    } catch (e) {
      throw new ProjectStoreError(`Cannot read ${file}: ${String(e)}`, "IO_ERROR");
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      throw new ProjectStoreError(`${file} is not valid JSON`, "INVALID_PROJECT");
    }
    const result = ProjectDocSchema.safeParse(parsed);
    if (!result.success) {
      throw new ProjectStoreError(
        `${file} failed schema validation: ${result.error.issues[0]?.message ?? "unknown"}`,
        "INVALID_PROJECT",
      );
    }
    return { info: infoFrom(result.data, dirPath), doc: result.data };
  }

  async saveProject(dirPath: string, doc: ProjectDoc): Promise<ProjectInfo> {
    const stamped: ProjectDoc = ProjectDocSchema.parse({ ...doc, updatedAt: this.now() });
    await this.writeDoc(dirPath, stamped);
    return infoFrom(stamped, dirPath);
  }

  /**
   * Copy an external file into the project's assets/, returning its
   * project-relative path. Names are sanitized and de-duplicated.
   */
  async importAsset(
    projectDir: string,
    sourcePath: string,
  ): Promise<{ relPath: string; name: string }> {
    if (!existsSync(sourcePath)) {
      throw new ProjectStoreError(`Source file missing: ${sourcePath}`, "ASSET_MISSING");
    }
    const assetsDir = path.join(projectDir, "assets");
    await mkdir(assetsDir, { recursive: true });

    const base = path.basename(sourcePath);
    const ext = path.extname(base);
    const stem = base
      .slice(0, base.length - ext.length)
      .replace(/[^A-Za-z0-9._-]+/g, "_")
      .slice(0, 80);
    let candidate = `${stem}${ext}`;
    let n = 1;
    while (existsSync(path.join(assetsDir, candidate))) {
      candidate = `${stem}-${n}${ext}`;
      n += 1;
    }
    await copyFile(sourcePath, path.join(assetsDir, candidate));
    return { relPath: path.posix.join("assets", candidate), name: candidate };
  }

  private async writeDoc(dirPath: string, doc: ProjectDoc): Promise<void> {
    await mkdir(dirPath, { recursive: true });
    const target = path.join(dirPath, PROJECT_FILE_NAME);
    const tmp = `${target}.tmp-${process.pid}-${Date.now()}`;
    await writeFile(tmp, JSON.stringify(doc, null, 2), "utf8");
    await rename(tmp, target);
  }
}
