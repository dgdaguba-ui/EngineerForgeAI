import { randomBytes } from "node:crypto";
import path from "node:path";

/** Mint the per-session bearer token shared with the engine sidecar. */
export function newSessionToken(): string {
  return randomBytes(32).toString("hex");
}

/**
 * Tracks filesystem paths the user explicitly granted via native dialogs.
 * `fs:readFile` only serves approved paths, so a compromised renderer cannot
 * read arbitrary files through IPC.
 */
export class PathAllowlist {
  private approved = new Set<string>();

  private normalize(p: string): string {
    return path.resolve(p);
  }

  approve(p: string): void {
    this.approved.add(this.normalize(p));
  }

  isApproved(p: string): boolean {
    return this.approved.has(this.normalize(p));
  }
}
