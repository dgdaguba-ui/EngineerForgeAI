import { describe, expect, it } from "vitest";

import type { IrFeature } from "../../engine/types";
import { featureDetail, toFeatureView } from "./featureSummary";

describe("featureDetail", () => {
  it("summarizes a sketch with its plane and profile kind", () => {
    const f: IrFeature = { op: "sketch", id: "profile", plane: "YZ", profile: { kind: "polygon" } };
    expect(featureDetail(f)).toBe("YZ · polygon");
  });

  it("summarizes an extrude distance", () => {
    expect(featureDetail({ op: "extrude", id: "body", distance: "W" })).toBe("distance W");
  });

  it("summarizes a hole row vs a single hole", () => {
    expect(
      featureDetail({ op: "hole", id: "h", diameter: "HD", count: "HC", axis: "Y" }),
    ).toBe("⌀HD ×HC along Y");
    expect(featureDetail({ op: "hole", id: "h", diameter: "CD", count: 1, axis: "Z" })).toBe(
      "⌀CD through Z",
    );
  });

  it("summarizes a fillet", () => {
    expect(featureDetail({ op: "fillet", id: "f", radius: "R", axis: "Z" })).toBe("r R ∥Z");
  });

  it("summarizes a shell with open faces (both alias forms)", () => {
    expect(
      featureDetail({ op: "shell", id: "s", thickness: "T", openFaces: ["+Z"] }),
    ).toBe("wall T open +Z");
    expect(
      featureDetail({ op: "shell", id: "s", thickness: "T", open_faces: ["+Z", "-X"] }),
    ).toBe("wall T open +Z,-X");
    expect(featureDetail({ op: "shell", id: "s", thickness: 2 })).toBe("wall 2");
  });

  it("falls back to the op name for unknown features", () => {
    expect(featureDetail({ op: "loft", id: "x" })).toBe("loft");
  });
});

describe("toFeatureView", () => {
  it("attaches a glyph and passes through op/id", () => {
    const view = toFeatureView({ op: "shell", id: "cavity", thickness: "T" });
    expect(view).toMatchObject({ op: "shell", id: "cavity", glyph: "▣" });
    expect(view.detail).toContain("wall");
  });

  it("uses a bullet glyph for unknown ops", () => {
    expect(toFeatureView({ op: "mystery", id: "z" }).glyph).toBe("•");
  });
});
