/**
 * Viewport scene state: loaded objects, selection, and a version counter the
 * camera uses to re-fit when content changes.
 */
import { Box3 } from "three";
import type { BufferGeometry } from "three";
import { create } from "zustand";

export interface SceneObject {
  id: string;
  name: string;
  sourcePath: string | null;
  /** Linked project part id (when the object belongs to an open project). */
  partId: string | null;
  geometry: BufferGeometry;
  color: string;
  visible: boolean;
}

const PALETTE = ["#8b9dc3", "#7cc4a0", "#c4a97c", "#b48bc4", "#7cb8c4", "#c48b8b"];

let counter = 0;
function newId(): string {
  counter += 1;
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `obj_${counter}`;
}

interface ViewportState {
  objects: SceneObject[];
  selectedId: string | null;
  /** Increments when contents change — consumed by the camera fit effect. */
  contentVersion: number;
  addMesh: (input: {
    name: string;
    sourcePath: string | null;
    geometry: BufferGeometry;
    partId?: string | null;
  }) => string;
  select: (id: string | null) => void;
  toggleVisible: (id: string) => void;
  removeObject: (id: string) => void;
  clear: () => void;
}

export const useViewportStore = create<ViewportState>((set, get) => ({
  objects: [],
  selectedId: null,
  contentVersion: 0,

  addMesh: ({ name, sourcePath, geometry, partId = null }) => {
    const id = newId();
    const color = PALETTE[get().objects.length % PALETTE.length] ?? "#8b9dc3";
    set((s) => ({
      objects: [...s.objects, { id, name, sourcePath, partId, geometry, color, visible: true }],
      selectedId: id,
      contentVersion: s.contentVersion + 1,
    }));
    return id;
  },

  select: (id) => set({ selectedId: id }),

  toggleVisible: (id) =>
    set((s) => ({
      objects: s.objects.map((o) => (o.id === id ? { ...o, visible: !o.visible } : o)),
    })),

  removeObject: (id) =>
    set((s) => {
      const target = s.objects.find((o) => o.id === id);
      target?.geometry.dispose();
      return {
        objects: s.objects.filter((o) => o.id !== id),
        selectedId: s.selectedId === id ? null : s.selectedId,
        contentVersion: s.contentVersion + 1,
      };
    }),

  clear: () =>
    set((s) => {
      for (const o of s.objects) o.geometry.dispose();
      return { objects: [], selectedId: null, contentVersion: s.contentVersion + 1 };
    }),
}));

/** Combined world-space bounding box of all visible objects (null when empty). */
export function combinedBoundingBox(objects: SceneObject[]): Box3 | null {
  const box = new Box3();
  let any = false;
  for (const o of objects) {
    if (!o.visible) continue;
    if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
    if (o.geometry.boundingBox) {
      box.union(o.geometry.boundingBox);
      any = true;
    }
  }
  return any ? box : null;
}
