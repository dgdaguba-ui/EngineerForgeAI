/**
 * STL parsing utilities. Pure functions — unit-tested without WebGL.
 *
 * Conventions: model units are millimetres. STL files are conventionally
 * Z-up; the viewport (three.js) is Y-up, so geometry is rotated at import
 * time (so world-space bounding boxes equal geometry bounding boxes).
 */
import { BufferGeometry } from "three";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";

export function base64ToArrayBuffer(b64: string): ArrayBuffer {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

export interface ParseStlOptions {
  /** Rotate Z-up (CAD/STL convention) to Y-up (three.js). Default true. */
  zUpToYUp?: boolean;
}

export function parseStlToGeometry(
  buffer: ArrayBuffer,
  options: ParseStlOptions = {},
): BufferGeometry {
  const { zUpToYUp = true } = options;
  const loader = new STLLoader();
  const geometry = loader.parse(buffer);
  if (!geometry.attributes.normal) {
    geometry.computeVertexNormals();
  }
  if (zUpToYUp) {
    geometry.rotateX(-Math.PI / 2);
  }
  geometry.computeBoundingBox();
  return geometry;
}

export interface MeshStats {
  triangles: number;
  /** Bounding-box dimensions in mm (world axes after import rotation). */
  size: { x: number; y: number; z: number };
}

export function meshStats(geometry: BufferGeometry): MeshStats {
  const position = geometry.getAttribute("position");
  const triangles = geometry.index
    ? geometry.index.count / 3
    : position
      ? position.count / 3
      : 0;
  if (!geometry.boundingBox) geometry.computeBoundingBox();
  const bb = geometry.boundingBox;
  const size = bb
    ? { x: bb.max.x - bb.min.x, y: bb.max.y - bb.min.y, z: bb.max.z - bb.min.z }
    : { x: 0, y: 0, z: 0 };
  return { triangles, size };
}
