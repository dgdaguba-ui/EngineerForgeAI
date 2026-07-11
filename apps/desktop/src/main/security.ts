import { randomBytes } from "node:crypto";
import path from "node:path";

/** Mint the per-session bearer token shared with the engine sidecar. */
export function newSessionToken(): string {
  return randomBytes(32).toString("hex");
}

/**
 * Tracks filesystem paths the user explicitly granted — individual files via
 * native dialogs, and whole directories for opened projects. `fs:readFile`
 * only serves approved paths, so a compromised renderer cannot read arbitrary
 * files through IPC.
 */
export class PathAllowlist {
  private approvedFiles = new Set<string>();
  private approvedDirs = new Set<string>();

  private normalize(p: string): string {
    return path.resolve(p);
  }

  approve(p: string): void {
    this.approvedFiles.add(this.normalize(p));
  }

  /** Approve a directory tree (e.g. an opened .efproj bundle). */
  approveDir(dir: string): void {
    this.approvedDirs.add(this.normalize(dir));
  }

  isApproved(p: string): boolean {
    const resolved = this.normalize(p);
    if (this.approvedFiles.has(resolved)) return true;
    for (const dir of this.approvedDirs) {
      const rel = path.relative(dir, resolved);
      if (rel !== "" && !rel.startsWith("..") && !path.isAbsolute(rel)) {
        return true;
      }
    }
    return false;
  }
}
