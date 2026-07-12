import { describe, expect, it } from "vitest";

import {
  EFPROJ_SCHEMA_VERSION,
  newProjectDoc,
  ProjectDocSchema,
} from "./project.js";

describe("ProjectDocSchema", () => {
  it("accepts a freshly created doc", () => {
    const doc = newProjectDoc({ id: "p1", name: "Bracket", now: "2026-07-11T00:00:00Z" });
    const parsed = ProjectDocSchema.parse(doc);
    expect(parsed.schema).toBe(EFPROJ_SCHEMA_VERSION);
    expect(parsed.parts).toEqual([]);
    expect(parsed.units).toBe("mm");
  });

  it("rejects unknown schema versions", () => {
    const doc = { ...newProjectDoc({ id: "p", name: "x", now: "t" }), schema: "efproj/999" };
    expect(() => ProjectDocSchema.parse(doc)).toThrow();
  });

  it("validates part color format", () => {
    const doc = newProjectDoc({ id: "p", name: "x", now: "t" });
    const bad = {
      ...doc,
      parts: [{ id: "a", name: "a.stl", asset: "assets/a.stl", colorHex: "red" }],
    };
    expect(() => ProjectDocSchema.parse(bad)).toThrow();
    const good = {
      ...doc,
      parts: [{ id: "a", name: "a.stl", asset: "assets/a.stl", colorHex: "#aabb01" }],
    };
    expect(ProjectDocSchema.parse(good).parts[0]!.colorHex).toBe("#aabb01");
  });

  it("supports mesh and parametric part kinds", () => {
    const doc = newProjectDoc({ id: "p", name: "x", now: "t" });
    // legacy mesh entries default kind
    const mesh = ProjectDocSchema.parse({
      ...doc,
      parts: [{ id: "m", name: "m.stl", asset: "assets/m.stl" }],
    });
    expect(mesh.parts[0]!.kind).toBe("mesh");

    const parametric = ProjectDocSchema.parse({
      ...doc,
      parts: [
        { id: "b", name: "L-Bracket", kind: "parametric", program: { schema: "efir/1" } },
      ],
    });
    expect(parametric.parts[0]!.kind).toBe("parametric");

    // kind/payload mismatches rejected
    expect(() =>
      ProjectDocSchema.parse({
        ...doc,
        parts: [{ id: "m", name: "m.stl" }], // mesh without asset
      }),
    ).toThrow();
    expect(() =>
      ProjectDocSchema.parse({
        ...doc,
        parts: [{ id: "b", name: "B", kind: "parametric" }], // no program
      }),
    ).toThrow();
  });

  it("defaults optional collections", () => {
    const doc = newProjectDoc({ id: "p", name: "x", now: "t" });
    const parsed = ProjectDocSchema.parse({
      schema: doc.schema,
      id: doc.id,
      name: doc.name,
      createdAt: doc.createdAt,
      updatedAt: doc.updatedAt,
    });
    expect(parsed.parts).toEqual([]);
    expect(parsed.materialSlots).toEqual([]);
    expect(parsed.printerProfileId).toBeNull();
    expect(parsed.partSlotAssignments).toEqual({});
  });
});
