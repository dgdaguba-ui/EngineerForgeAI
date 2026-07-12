/**
 * Decode the engine's RawMesh transport (little-endian base64 buffers) into a
 * three.js BufferGeometry. The engine emits CAD-frame Z-up coordinates; the
 * viewport is Y-up, so geometry is rotated at decode time (same convention as
 * STL import). Vertex duplication from the kernel tessellation is preserved —
 * it gives correct flat shading on mechanical parts.
 */
import { BufferAttribute, BufferGeometry } from "three";

import { base64ToArrayBuffer } from "../viewport/stl";
import type { RawMeshPayload } from "../../engine/types";

export function rawMeshToGeometry(mesh: RawMeshPayload): BufferGeometry {
  const positions = new Float32Array(base64ToArrayBuffer(mesh.positionsB64));
  const indices = new Uint32Array(base64ToArrayBuffer(mesh.indicesB64));
  if (positions.length !== mesh.vertexCount * 3) {
    throw new Error(
      `mesh payload corrupt: ${positions.length / 3} vertices, expected ${mesh.vertexCount}`,
    );
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new BufferAttribute(positions, 3));
  geometry.setIndex(new BufferAttribute(indices, 1));
  geometry.rotateX(-Math.PI / 2); // CAD Z-up → viewport Y-up
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  return geometry;
}
