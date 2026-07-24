/**
 * CloudSyncQueue — offline-first background backup of project documents.
 *
 * The local `.efproj` file is always the source of truth (ADR-0004); this
 * queue pushes a copy to the configured cloud provider, retrying with
 * exponential backoff when the network or provider is unavailable. It mirrors
 * the renderer's chat delivery-queue policy:
 *   - dedupe by project id — only the latest document for a project is kept;
 *   - a failed push stays queued and is retried on a backoff timer;
 *   - when the provider is local-only, enqueuing is a no-op (nothing to sync).
 *
 * It never throws into the caller: a dead cloud must never disturb local work.
 */
import type { ProjectDoc, ProjectInfo, SyncStatus } from "@efc/ipc-contracts";

import type { CloudService } from "./service.js";

const INITIAL_RETRY_MS = 4_000;
const MAX_RETRY_MS = 60_000;

interface PendingEntry {
  info: ProjectInfo;
  doc: ProjectDoc;
}

export interface SyncQueueOptions {
  initialRetryMs?: number;
  maxRetryMs?: number;
}

export class CloudSyncQueue {
  private readonly queue = new Map<string, PendingEntry>();
  private timer: ReturnType<typeof setTimeout> | null = null;
  private retryMs: number;
  private inFlight = false;
  private lastSyncedAt: number | null = null;
  private lastError: string | null = null;

  constructor(
    private readonly cloud: CloudService,
    private readonly opts: SyncQueueOptions = {},
  ) {
    this.retryMs = this.initialRetryMs;
  }

  private get initialRetryMs(): number {
    return this.opts.initialRetryMs ?? INITIAL_RETRY_MS;
  }

  private get maxRetryMs(): number {
    return this.opts.maxRetryMs ?? MAX_RETRY_MS;
  }

  /** True when a real cloud provider is configured (not local-only). */
  get active(): boolean {
    return this.cloud.name !== "local";
  }

  status(): SyncStatus {
    return {
      active: this.active,
      pending: this.queue.size,
      inFlight: this.inFlight,
      lastSyncedAt: this.lastSyncedAt,
      lastError: this.lastError,
    };
  }

  /** Queue a project for backup. No-op when the provider is local-only. */
  enqueue(info: ProjectInfo, doc: ProjectDoc): SyncStatus {
    if (this.active) {
      this.queue.set(doc.id, { info, doc }); // latest document for a project wins
      void this.flush();
    }
    return this.status();
  }

  /** Attempt to push everything queued. Safe to call repeatedly. */
  async flush(): Promise<void> {
    if (this.inFlight || this.queue.size === 0) return;
    this.inFlight = true;
    this.clearTimer();
    try {
      for (const [id, entry] of [...this.queue]) {
        let result;
        try {
          result = await this.cloud.pushProject(entry.info, entry.doc);
        } catch (e) {
          result = { ok: false, detail: e instanceof Error ? e.message : String(e) };
        }
        if (result.ok) {
          // only clear if this exact document wasn't superseded mid-flight
          const current = this.queue.get(id);
          if (current && current.doc === entry.doc) this.queue.delete(id);
          this.lastSyncedAt = Date.now();
          this.lastError = null;
        } else {
          this.lastError = result.detail;
        }
      }
    } finally {
      this.inFlight = false;
    }
    if (this.queue.size > 0) {
      this.scheduleRetry();
    } else {
      this.retryMs = this.initialRetryMs; // healthy again — reset backoff
    }
  }

  private scheduleRetry(): void {
    if (this.timer) return;
    this.timer = setTimeout(() => {
      this.timer = null;
      void this.flush();
    }, this.retryMs);
    // don't keep the process alive purely for a pending backup retry
    (this.timer as { unref?: () => void }).unref?.();
    this.retryMs = Math.min(this.retryMs * 2, this.maxRetryMs);
  }

  private clearTimer(): void {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  /** Cancel pending retries (app shutdown). */
  dispose(): void {
    this.clearTimer();
    this.queue.clear();
  }
}
