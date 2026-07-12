import { BufferAttribute, BufferGeometry } from "three";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { newProjectDoc, type ProjectInfo } from "@efc/ipc-contracts";

import { EngineClient } from "../../engine/client";
import { useEngineStore } from "../../state/engineStore";
import { useProjectStore } from "../../state/projectStore";
import { useViewportStore } from "../../state/viewportStore";
import { useFlashforgeStore } from "./flashforgeStore";

const PRINTERS = [
  {
    id: "flashforge-ad5x",
    name: "Flashforge AD5X",
    brand: "Flashforge",
    buildVolume: { x: 220, y: 220, z: 220 },
    extruders: 1,
    materialSlots: 4,
    nozzleDiameterMm: 0.4,
    maxNozzleTempC: 300,
    maxBedTempC: 110,
    enclosed: false,
    multiMaterialSystem: "filament-switching",
    purgePerChangeMm3: 300,
    slicer: "FlashPrint",
  },
  {
    id: "flashforge-adventurer-5m",
    name: "Adventurer 5M",
    brand: "Flashforge",
    buildVolume: { x: 220, y: 220, z: 220 },
    extruders: 1,
    materialSlots: 1,
    nozzleDiameterMm: 0.4,
    maxNozzleTempC: 280,
    maxBedTempC: 110,
    enclosed: false,
    multiMaterialSystem: "none",
    purgePerChangeMm3: 0,
    slicer: "FlashPrint",
  },
];

const MATERIALS = [
  { id: "pla", name: "PLA", colorHex: "#e8e8e8" },
  { id: "pva", name: "PVA", colorHex: "#f0e6c8" },
];

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function installClient(): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(async (url: string) => {
    if (url.endsWith("/api/v1/printers")) return jsonResponse(PRINTERS);
    if (url.endsWith("/api/v1/materials")) return jsonResponse(MATERIALS);
    if (url.endsWith("/api/v1/materials/compatibility")) {
      return jsonResponse({ pairs: [{ a: "pla", b: "pva", level: "ok", reasons: ["support"], nozzleTempOverlapC: 30, bedTempDeltaC: 0 }], worst: "ok" });
    }
    throw new Error(`unexpected url ${url}`);
  });
  useEngineStore.setState({
    client: new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchMock),
  });
  return fetchMock;
}

function makeGeometry(): BufferGeometry {
  const g = new BufferGeometry();
  g.setAttribute("position", new BufferAttribute(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]), 3));
  g.computeBoundingBox();
  return g;
}

function openProject(): ProjectInfo {
  const doc = newProjectDoc({ id: "p1", name: "Proj", now: "t" });
  const info: ProjectInfo = { id: "p1", name: "Proj", path: "C:\\w\\Proj.efproj", updatedAt: "t" };
  useProjectStore.setState({ info, doc, dirty: false });
  return info;
}

beforeEach(() => {
  useFlashforgeStore.setState({
    printers: [],
    materials: [],
    loaded: false,
    loadError: null,
    printerId: null,
    slots: [],
    assignments: {},
    compat: null,
  });
  useViewportStore.getState().clear();
  useViewportStore.getState().setBuildVolume(null);
  useProjectStore.setState({ info: null, doc: null, dirty: false });
});

describe("flashforgeStore", () => {
  it("loads printers and materials from the engine", async () => {
    installClient();
    await useFlashforgeStore.getState().load();
    const s = useFlashforgeStore.getState();
    expect(s.loaded).toBe(true);
    expect(s.printers).toHaveLength(2);
    expect(s.materials.map((m) => m.id)).toEqual(["pla", "pva"]);
  });

  it("selectPrinter sizes slots and sets the viewport build volume", async () => {
    installClient();
    await useFlashforgeStore.getState().load();

    useFlashforgeStore.getState().selectPrinter("flashforge-ad5x");
    expect(useFlashforgeStore.getState().slots).toHaveLength(4);
    expect(useViewportStore.getState().buildVolume).toEqual({ x: 220, y: 220, z: 220 });

    useFlashforgeStore.getState().selectPrinter("flashforge-adventurer-5m");
    expect(useFlashforgeStore.getState().slots).toHaveLength(1);

    useFlashforgeStore.getState().selectPrinter(null);
    expect(useViewportStore.getState().buildVolume).toBeNull();
  });

  it("persists printer and slots into an open project doc", async () => {
    installClient();
    await useFlashforgeStore.getState().load();
    openProject();

    useFlashforgeStore.getState().selectPrinter("flashforge-ad5x");
    useFlashforgeStore.getState().setSlotMaterial(0, "pla");

    const doc = useProjectStore.getState().doc!;
    expect(doc.printerProfileId).toBe("flashforge-ad5x");
    expect(doc.materialSlots[0]).toMatchObject({ materialId: "pla", colorHex: "#e8e8e8" });
    expect(useProjectStore.getState().dirty).toBe(true);
  });

  it("slot material adopts the material color unless customized", async () => {
    installClient();
    await useFlashforgeStore.getState().load();
    useFlashforgeStore.getState().selectPrinter("flashforge-ad5x");

    useFlashforgeStore.getState().setSlotColor(1, "#123456");
    useFlashforgeStore.getState().setSlotMaterial(1, "pva");
    expect(useFlashforgeStore.getState().slots[1]).toMatchObject({
      materialId: "pva",
      colorHex: "#123456", // custom color preserved
    });
  });

  it("assignObject records assignments and mirrors part-linked ones to the doc", async () => {
    installClient();
    await useFlashforgeStore.getState().load();
    openProject();
    useFlashforgeStore.getState().selectPrinter("flashforge-ad5x");

    const linkedId = useViewportStore.getState().addMesh({
      name: "bracket",
      sourcePath: "C:/x/bracket.stl",
      geometry: makeGeometry(),
      partId: "part-9",
    });
    const looseId = useViewportStore.getState().addMesh({
      name: "loose",
      sourcePath: null,
      geometry: makeGeometry(),
    });

    useFlashforgeStore.getState().assignObject(linkedId, 2);
    useFlashforgeStore.getState().assignObject(looseId, 0);

    expect(useFlashforgeStore.getState().assignments[linkedId]).toBe(2);
    expect(useProjectStore.getState().doc!.partSlotAssignments).toEqual({ "part-9": 2 });

    useFlashforgeStore.getState().assignObject(linkedId, null);
    expect(useProjectStore.getState().doc!.partSlotAssignments).toEqual({});
  });

  it("syncFromProject restores printer, slots, and assignments by partId", async () => {
    installClient();
    await useFlashforgeStore.getState().load();

    const doc = {
      ...newProjectDoc({ id: "p2", name: "P2", now: "t" }),
      printerProfileId: "flashforge-ad5x",
      materialSlots: [
        { index: 0, materialId: "pla", colorHex: "#ffffff" },
        { index: 1, materialId: "pva", colorHex: null },
      ],
      partSlotAssignments: { "part-1": 1 },
    };
    useProjectStore.setState({
      info: { id: "p2", name: "P2", path: "C:\\w\\P2.efproj", updatedAt: "t" },
      doc,
      dirty: false,
    });
    const objectId = useViewportStore.getState().addMesh({
      name: "a",
      sourcePath: "C:/w/P2.efproj/assets/a.stl",
      geometry: makeGeometry(),
      partId: "part-1",
    });

    useFlashforgeStore.getState().syncFromProject();
    const s = useFlashforgeStore.getState();
    expect(s.printerId).toBe("flashforge-ad5x");
    expect(s.slots).toHaveLength(4); // resized to the printer's slot count
    expect(s.slots[0]).toMatchObject({ materialId: "pla" });
    expect(s.assignments[objectId]).toBe(1);
    expect(useViewportStore.getState().buildVolume).not.toBeNull();
  });

  it("refreshCompat requires two distinct materials", async () => {
    const fetchMock = installClient();
    await useFlashforgeStore.getState().load();
    useFlashforgeStore.getState().selectPrinter("flashforge-ad5x");

    useFlashforgeStore.getState().setSlotMaterial(0, "pla");
    await useFlashforgeStore.getState().refreshCompat();
    expect(useFlashforgeStore.getState().compat).toBeNull();

    useFlashforgeStore.getState().setSlotMaterial(1, "pva");
    await useFlashforgeStore.getState().refreshCompat();
    expect(useFlashforgeStore.getState().compat?.worst).toBe("ok");
    const compatCalls = fetchMock.mock.calls.filter((c) =>
      (c[0] as string).endsWith("/materials/compatibility"),
    );
    expect(compatCalls).toHaveLength(1);
  });
});
