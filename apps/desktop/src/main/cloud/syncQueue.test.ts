import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { CloudResult, CloudStatus, ProjectDoc, ProjectInfo } from "@efc/ipc-contracts";

import type { CloudService } from "./service.js";
import { CloudSyncQueue } from "./syncQueue.js";

function makeDoc(id: string, name = id): ProjectDoc {
  return {
    schema: "efproj/1",
    id,
    name,
    units: "mm",
    createdAt: "t",
    updatedAt: "t",
    parts: [],
    printerProfileId: null,
    materialSlots: [],
    partSlotAssignments: {},
  };
}

function makeInfo(id: string): ProjectInfo {
  return { id, name: id, path: `C:/proj/${id}.efproj`, updatedAt: "t" };
}

class FakeCloud implements CloudService {
  readonly name: string;
  pushed: ProjectDoc[] = [];
  private queue: CloudResult[] = [];
  private fallback: CloudResult = { ok: true, detail: "ok" };

  constructor(name = "supabase") {
    this.name = name;
  }

  /** Script the next N results; later pushes use the last configured fallback. */
  script(...results: CloudResult[]): void {
    this.queue = results.slice(0, -1);
    this.fallback = results[results.length - 1] ?? this.fallback;
  }

  async status(): Promise<CloudStatus> {
    return { provider: this.name, enabled: true, signedIn: true, email: null, detail: "" };
  }
  async signIn(): Promise<CloudStatus> {
    return this.status();
  }
  async signOut(): Promise<CloudStatus> {
    return this.status();
  }
  async pushProject(_info: ProjectInfo, doc: ProjectDoc): Promise<CloudResult> {
    this.pushed.push(doc);
    return this.queue.shift() ?? this.fallback;
  }
}

beforeEach(() => {
  vi.useFakeTimers();
});
afterEach(() => {
  vi.useRealTimers();
});

describe("CloudSyncQueue", () => {
  it("no-ops for a local-only provider", async () => {
    const cloud = new FakeCloud("local");
    const q = new CloudSyncQueue(cloud);
    const status = q.enqueue(makeInfo("p1"), makeDoc("p1"));
    await vi.advanceTimersByTimeAsync(0);
    expect(status.active).toBe(false);
    expect(status.pending).toBe(0);
    expect(cloud.pushed).toHaveLength(0);
  });

  it("pushes an enqueued project and clears it", async () => {
    const cloud = new FakeCloud();
    const q = new CloudSyncQueue(cloud);
    q.enqueue(makeInfo("p1"), makeDoc("p1"));
    await vi.advanceTimersByTimeAsync(0);
    expect(cloud.pushed).toHaveLength(1);
    const s = q.status();
    expect(s.pending).toBe(0);
    expect(s.lastSyncedAt).not.toBeNull();
    expect(s.lastError).toBeNull();
  });

  it("dedupes by project id — only the latest document is kept", async () => {
    const cloud = new FakeCloud();
    cloud.script({ ok: false, detail: "offline" }); // first flush fails → stays queued
    const q = new CloudSyncQueue(cloud, { initialRetryMs: 10 });

    q.enqueue(makeInfo("p1"), makeDoc("p1", "v1"));
    await vi.advanceTimersByTimeAsync(0);
    q.enqueue(makeInfo("p1"), makeDoc("p1", "v2")); // supersedes while queued
    expect(q.status().pending).toBe(1);

    cloud.script({ ok: true, detail: "ok" }); // network back
    await vi.advanceTimersByTimeAsync(20); // retry timer fires
    expect(q.status().pending).toBe(0);
    // the last pushed document for p1 is the latest version
    expect(cloud.pushed.at(-1)!.name).toBe("v2");
  });

  it("retries with backoff after a failure, then succeeds", async () => {
    const cloud = new FakeCloud();
    cloud.script({ ok: false, detail: "unreachable" }, { ok: true, detail: "ok" });
    const q = new CloudSyncQueue(cloud, { initialRetryMs: 10 });

    q.enqueue(makeInfo("p1"), makeDoc("p1"));
    await vi.advanceTimersByTimeAsync(0);
    // first attempt failed → still pending, error recorded
    expect(q.status().pending).toBe(1);
    expect(q.status().lastError).toContain("unreachable");

    await vi.advanceTimersByTimeAsync(10); // backoff retry fires and succeeds
    expect(q.status().pending).toBe(0);
    expect(q.status().lastError).toBeNull();
    expect(cloud.pushed.length).toBeGreaterThanOrEqual(2);
  });

  it("dispose cancels pending retries", async () => {
    const cloud = new FakeCloud();
    cloud.script({ ok: false, detail: "offline" }, { ok: false, detail: "offline" });
    const q = new CloudSyncQueue(cloud, { initialRetryMs: 10 });
    q.enqueue(makeInfo("p1"), makeDoc("p1"));
    await vi.advanceTimersByTimeAsync(0);
    const pushesBefore = cloud.pushed.length;

    q.dispose();
    await vi.advanceTimersByTimeAsync(100); // no further flushes should occur
    expect(cloud.pushed.length).toBe(pushesBefore);
    expect(q.status().pending).toBe(0); // queue cleared on dispose
  });
});
