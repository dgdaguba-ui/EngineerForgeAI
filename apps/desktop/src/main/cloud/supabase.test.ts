import { afterEach, describe, expect, it, vi } from "vitest";

import type { ProjectDoc, ProjectInfo } from "@efc/ipc-contracts";

const getSessionMock = vi.fn();
const uploadMock = vi.fn();
const fromMock = vi.fn(() => ({ upload: uploadMock }));

vi.mock("@supabase/supabase-js", () => ({
  createClient: () => ({
    auth: {
      getSession: getSessionMock,
      signInWithPassword: vi.fn(),
      signOut: vi.fn(),
    },
    storage: { from: fromMock },
  }),
}));

// imported after the mock is declared
import { DEFAULT_BUCKET, SupabaseCloud } from "./supabase.js";

function doc(): ProjectDoc {
  return {
    schema: "efproj/1",
    id: "p1",
    name: "P",
    units: "mm",
    createdAt: "t",
    updatedAt: "t",
    parts: [],
    printerProfileId: null,
    materialSlots: [],
    partSlotAssignments: {},
  };
}
const info: ProjectInfo = { id: "p1", name: "P", path: "C:/x", updatedAt: "t" };

afterEach(() => {
  vi.clearAllMocks();
});

describe("SupabaseCloud.pushProject bucket", () => {
  it("uploads to the configured bucket at <userId>/<projectId>/project.json", async () => {
    getSessionMock.mockResolvedValue({ data: { session: { user: { id: "u1" } } } });
    uploadMock.mockResolvedValue({ error: null });

    const res = await new SupabaseCloud("https://x.supabase.co", "anon", "mybucket").pushProject(
      info,
      doc(),
    );

    expect(res.ok).toBe(true);
    expect(fromMock).toHaveBeenCalledWith("mybucket");
    expect(uploadMock.mock.calls[0]![0]).toBe("u1/p1/project.json");
  });

  it("defaults the bucket to efproject", async () => {
    getSessionMock.mockResolvedValue({ data: { session: { user: { id: "u1" } } } });
    uploadMock.mockResolvedValue({ error: null });

    await new SupabaseCloud("https://x.supabase.co", "anon").pushProject(info, doc());

    expect(fromMock).toHaveBeenCalledWith("efproject");
    expect(DEFAULT_BUCKET).toBe("efproject");
  });

  it("reports a clean failure when not signed in (no upload attempted)", async () => {
    getSessionMock.mockResolvedValue({ data: { session: null } });

    const res = await new SupabaseCloud("https://x.supabase.co", "anon").pushProject(info, doc());

    expect(res.ok).toBe(false);
    expect(res.detail).toContain("Not signed in");
    expect(uploadMock).not.toHaveBeenCalled();
  });
});
