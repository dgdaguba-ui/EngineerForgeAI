import { describe, expect, it } from "vitest";

import { makeRawMeshPayload } from "../../test/fixtures";
import { rawMeshToGeometry } from "./rawMesh";

describe("rawMeshToGeometry", () => {
  it("decodes positions/indices and applies CAD Z-up → viewport Y-up", () => {
    const geometry = rawMeshToGeometry(
      makeRawMeshPayload([
        [0, 0, 0],
        [10, 0, 0],
        [0, 5, 20], // CAD (x=0, y=5, z=20)
      ]),
    );
    const pos = geometry.getAttribute("position");
    expect(pos.count).toBe(3);
    // rotateX(-90°): (x, y, z) → (x, z, −y)
    expect(pos.getX(2)).toBeCloseTo(0);
    expect(pos.getY(2)).toBeCloseTo(20);
    expect(pos.getZ(2)).toBeCloseTo(-5);
    expect(geometry.getIndex()!.count).toBe(3);
    expect(geometry.getAttribute("normal")).toBeDefined();
    expect(geometry.boundingBox).not.toBeNull();
  });

  it("rejects corrupt payloads", () => {
    const payload = makeRawMeshPayload();
    expect(() =>
      rawMeshToGeometry({ ...payload, vertexCount: payload.vertexCount + 1 }),
    ).toThrow(/corrupt/);
  });
});
