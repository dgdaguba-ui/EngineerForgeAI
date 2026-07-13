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

// ── parametric part fixtures ─────────────────────────────────────────────────

import type { IrFeature, IrParameter, PartDetail, RawMeshPayload } from "../engine/types";

export function bufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

/** One CAD-frame triangle as an engine RawMesh payload. */
export function makeRawMeshPayload(
  vertices: Vec3[] = [
    [0, 0, 0],
    [10, 0, 0],
    [0, 5, 20],
  ],
): RawMeshPayload {
  const positions = new Float32Array(vertices.flat());
  const indices = new Uint32Array(vertices.map((_, i) => i));
  return {
    positionsB64: bufferToBase64(positions.buffer),
    indicesB64: bufferToBase64(indices.buffer),
    vertexCount: vertices.length,
    triangleCount: Math.floor(vertices.length / 3),
  };
}

export function makeIrParameter(overrides: Partial<IrParameter> & { id: string }): IrParameter {
  return {
    label: overrides.id,
    value: 10,
    unit: "mm",
    min: 1,
    max: 300,
    step: 1,
    integer: false,
    ...overrides,
  };
}

export function makePartDetail(
  overrides: Partial<{
    partId: string;
    values: Record<string, number>;
    warnings: string[];
    volumeCm3: number;
    features: IrFeature[];
  }> = {},
): PartDetail {
  const values = overrides.values ?? { W: 40, H: 60 };
  const parameters = Object.entries(values).map(([id, value]) =>
    makeIrParameter({ id, value }),
  );
  return {
    partId: overrides.partId ?? "engpart1",
    name: "L-Bracket",
    templateId: "bracket-l",
    program: {
      schema: "efir/1",
      name: "L-Bracket",
      parameters,
      features: overrides.features ?? [],
    },
    compiled: {
      mesh: makeRawMeshPayload(),
      massProps: {
        volumeMm3: (overrides.volumeCm3 ?? 30) * 1000,
        volumeCm3: overrides.volumeCm3 ?? 30,
        massG: null,
        materialId: null,
        cogMm: [0, 0, 0],
        bboxMm: { x: values.W ?? 40, y: 40, z: values.H ?? 60 },
      },
      warnings: overrides.warnings ?? [],
    },
    materialId: null,
  };
}
