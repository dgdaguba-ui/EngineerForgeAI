import { describe, expect, it } from "vitest";

import type { IrFeature } from "../../engine/types";
import { editableFields } from "./featureFields";

describe("editableFields", () => {
  it("exposes distance + offset for an extrude", () => {
    const fields = editableFields({
      op: "extrude",
      id: "body",
      distance: "H",
      offset: 0,
    } as IrFeature);
    expect(fields).toEqual([
      { key: "distance", label: "Distance", kind: "expr", value: "H" },
      { key: "offset", label: "Offset", kind: "expr", value: "0" },
    ]);
  });

  it("exposes hole scalars incl. an axis enum", () => {
    const fields = editableFields({
      op: "hole",
      id: "h",
      diameter: 5,
      u: "0",
      v: "0",
      count: 2,
      spacing: "10",
      axis: "Z",
    } as IrFeature);
    expect(fields.map((f) => f.key)).toEqual([
      "diameter",
      "u",
      "v",
      "count",
      "spacing",
      "axis",
    ]);
    // numeric values render as strings
    expect(fields.find((f) => f.key === "diameter")).toMatchObject({ kind: "expr", value: "5" });
    const axis = fields.find((f) => f.key === "axis")!;
    expect(axis.kind).toBe("enum");
    expect(axis.options).toEqual(["X", "Y", "Z"]);
    expect(axis.value).toBe("Z");
  });

  it("exposes plane for a sketch and thickness for a shell", () => {
    expect(editableFields({ op: "sketch", id: "s", plane: "XY" } as IrFeature)).toEqual([
      { key: "plane", label: "Plane", kind: "enum", value: "XY", options: ["XY", "YZ", "XZ"] },
    ]);
    expect(editableFields({ op: "shell", id: "c", thickness: "T" } as IrFeature)).toEqual([
      { key: "thickness", label: "Thickness", kind: "expr", value: "T" },
    ]);
  });

  it("exposes length + axis for a chamfer", () => {
    const fields = editableFields({
      op: "chamfer",
      id: "edges",
      length: "C",
      axis: "Z",
    } as IrFeature);
    expect(fields.map((f) => f.key)).toEqual(["length", "axis"]);
    expect(fields[0]).toMatchObject({ kind: "expr", value: "C" });
    expect(fields[1]).toMatchObject({ kind: "enum", options: ["X", "Y", "Z"] });
  });

  it("returns nothing for an unknown op", () => {
    expect(editableFields({ op: "loft", id: "x" } as unknown as IrFeature)).toEqual([]);
  });
});
