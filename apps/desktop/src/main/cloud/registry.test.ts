import { describe, expect, it } from "vitest";

import { buildCloudService } from "./registry.js";

describe("buildCloudService", () => {
  it("falls back to local-only without configuration", async () => {
    const svc = buildCloudService({});
    expect(svc.name).toBe("local");
    const status = await svc.status();
    expect(status.enabled).toBe(false);
    expect(status.signedIn).toBe(false);
  });

  it("treats blank values as unconfigured", async () => {
    const svc = buildCloudService({ SUPABASE_URL: "  ", SUPABASE_ANON_KEY: "" });
    expect(svc.name).toBe("local");
  });

  it("selects supabase when both url and key are present", () => {
    const svc = buildCloudService({
      SUPABASE_URL: "https://example.supabase.co",
      SUPABASE_ANON_KEY: "anon-key",
    });
    expect(svc.name).toBe("supabase");
  });

  it("local-only push reports cleanly instead of failing", async () => {
    const svc = buildCloudService({});
    const result = await svc.pushProject(
      { id: "p", name: "P", path: "C:/x", updatedAt: "t" },
      // minimal valid doc
      {
        schema: "efproj/1",
        id: "p",
        name: "P",
        units: "mm",
        createdAt: "t",
        updatedAt: "t",
        parts: [],
        printerProfileId: null,
        materialSlots: [],
        partSlotAssignments: {},
      },
    );
    expect(result.ok).toBe(false);
    expect(result.detail).toContain("local");
  });
});
