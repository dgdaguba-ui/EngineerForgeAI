import { BufferAttribute, BufferGeometry } from "three";
import { beforeEach, describe, expect, it } from "vitest";

import { combinedBoundingBox, useViewportStore } from "./viewportStore";

function makeGeometry(size = 10): BufferGeometry {
  const g = new BufferGeometry();
  const positions = new Float32Array([0, 0, 0, size, 0, 0, 0, size, 0]);
  g.setAttribute("position", new BufferAttribute(positions, 3));
  g.computeBoundingBox();
  return g;
}

beforeEach(() => {
  useViewportStore.getState().clear();
  useViewportStore.setState({ contentVersion: 0, selectedId: null });
});

describe("viewportStore", () => {
  it("adds a mesh, selects it, and bumps contentVersion", () => {
    const id = useViewportStore
      .getState()
      .addMesh({ name: "part.stl", sourcePath: "C:/p/part.stl", geometry: makeGeometry() });
    const s = useViewportStore.getState();
    expect(s.objects).toHaveLength(1);
    expect(s.selectedId).toBe(id);
    expect(s.contentVersion).toBe(1);
  });

  it("assigns distinct palette colors", () => {
    const st = useViewportStore.getState();
    st.addMesh({ name: "a", sourcePath: null, geometry: makeGeometry() });
    st.addMesh({ name: "b", sourcePath: null, geometry: makeGeometry() });
    const [a, b] = useViewportStore.getState().objects;
    expect(a!.color).not.toBe(b!.color);
  });

  it("toggles visibility", () => {
    const id = useViewportStore
      .getState()
      .addMesh({ name: "a", sourcePath: null, geometry: makeGeometry() });
    useViewportStore.getState().toggleVisible(id);
    expect(useViewportStore.getState().objects[0]!.visible).toBe(false);
  });

  it("removes objects and clears selection", () => {
    const id = useViewportStore
      .getState()
      .addMesh({ name: "a", sourcePath: null, geometry: makeGeometry() });
    useViewportStore.getState().removeObject(id);
    const s = useViewportStore.getState();
    expect(s.objects).toHaveLength(0);
    expect(s.selectedId).toBeNull();
  });

  it("keeps selection when removing a different object", () => {
    const st = useViewportStore.getState();
    st.addMesh({ name: "a", sourcePath: null, geometry: makeGeometry() });
    const b = st.addMesh({ name: "b", sourcePath: null, geometry: makeGeometry() });
    const a = useViewportStore.getState().objects[0]!.id;
    useViewportStore.getState().select(b);
    useViewportStore.getState().removeObject(a);
    expect(useViewportStore.getState().selectedId).toBe(b);
  });
});

describe("combinedBoundingBox", () => {
  it("returns null for an empty scene", () => {
    expect(combinedBoundingBox([])).toBeNull();
  });

  it("unions visible objects and skips hidden ones", () => {
    const st = useViewportStore.getState();
    st.addMesh({ name: "a", sourcePath: null, geometry: makeGeometry(10) });
    const bigId = st.addMesh({ name: "b", sourcePath: null, geometry: makeGeometry(50) });

    let box = combinedBoundingBox(useViewportStore.getState().objects);
    expect(box!.max.x).toBeCloseTo(50);

    useViewportStore.getState().toggleVisible(bigId);
    box = combinedBoundingBox(useViewportStore.getState().objects);
    expect(box!.max.x).toBeCloseTo(10);
  });
});
