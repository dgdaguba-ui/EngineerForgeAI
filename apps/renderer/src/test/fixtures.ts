/** Shared test fixtures: minimal binary STL builders. */

export type Vec3 = [number, number, number];
export type Triangle = [Vec3, Vec3, Vec3];

/** Build a minimal binary STL (80-byte header + count + 50 bytes/triangle). */
export function makeBinaryStl(triangles: Triangle[]): ArrayBuffer {
  const buffer = new ArrayBuffer(84 + triangles.length * 50);
  const view = new DataView(buffer);
  view.setUint32(80, triangles.length, true);
  let offset = 84;
  for (const tri of triangles) {
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

export const UNIT_TRIANGLE: Triangle = [
  [0, 0, 0],
  [10, 0, 0],
  [0, 20, 0],
];

export function stlBase64(triangles: Triangle[] = [UNIT_TRIANGLE]): string {
  const bytes = new Uint8Array(makeBinaryStl(triangles));
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}
