import { describe, expect, it } from "vitest";

import { base64ToArrayBuffer, meshStats, parseStlToGeometry } from "./stl";

type Vec3 = [number, number, number];
type Triangle = [Vec3, Vec3, Vec3];

/** Build a minimal binary STL (80-byte header + count + 50 bytes/triangle). */
export function makeBinaryStl(triangles: Triangle[]): ArrayBuffer {
  const buffer = new ArrayBuffer(84 + triangles.length * 50);
  const view = new DataView(buffer);
  view.setUint32(80, triangles.length, true);
  let offset = 84;
  for (const tri of triangles) {
    // normal (unused by the parser's bbox logic)
    view.setFloat32(offset, 0, true);
    view.setFloat32(offset + 4, 0, true);
    view.setFloat32(offset + 8, 1, true);
    offset += 12;
    for (const v of tri) {
      view.setFloat32(offset, v[0], true);
      view.setFloat32(offset + 4, v[1], true);
      view.setFloat32(offset + 8, v[2], true);
      offset += 12;
    }
    view.setUint16(offset, 0, true);
    offset += 2;
  }
  return buffer;
}

const TRIANGLE: Triangle = [
  [0, 0, 0],
  [10, 0, 0],
  [0, 20, 0],
];

describe("parseStlToGeometry (binary)", () => {
  it("parses vertices and applies the Z-up → Y-up rotation", () => {
    const geometry = parseStlToGeometry(makeBinaryStl([TRIANGLE]));
    const pos = geometry.getAttribute("position");
    expect(pos.count).toBe(3);
    const stats = meshStats(geometry);
    expect(stats.triangles).toBe(1);
    // STL (x=10, y=20) → world (x=10, z=20) after rotation; height y ≈ 0
    expect(stats.size.x).toBeCloseTo(10);
    expect(stats.size.y).toBeCloseTo(0);
    expect(stats.size.z).toBeCloseTo(20);
  });

  it("keeps native axes when zUpToYUp is false", () => {
    const geometry = parseStlToGeometry(makeBinaryStl([TRIANGLE]), { zUpToYUp: false });
    const stats = meshStats(geometry);
    expect(stats.size.x).toBeCloseTo(10);
    expect(stats.size.y).toBeCloseTo(20);
    expect(stats.size.z).toBeCloseTo(0);
  });
});

describe("parseStlToGeometry (ascii)", () => {
  it("parses ASCII STL content", () => {
    const ascii = [
      "solid test",
      "facet normal 0 0 1",
      "outer loop",
      "vertex 0 0 0",
      "vertex 10 0 0",
      "vertex 0 20 0",
      "endloop",
      "endfacet",
      "endsolid test",
    ].join("\n");
    const buffer = new TextEncoder().encode(ascii).buffer as ArrayBuffer;
    const geometry = parseStlToGeometry(buffer);
    expect(meshStats(geometry).triangles).toBe(1);
  });
});

describe("base64ToArrayBuffer", () => {
  it("round-trips bytes", () => {
    const original = new Uint8Array([0, 1, 2, 250, 255]);
    const b64 = btoa(String.fromCharCode(...original));
    const decoded = new Uint8Array(base64ToArrayBuffer(b64));
    expect([...decoded]).toEqual([...original]);
  });
});
