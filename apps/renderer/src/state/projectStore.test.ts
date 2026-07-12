import { beforeEach, describe, expect, it, vi } from "vitest";

import type { EfcBridge, ProjectDoc, ProjectInfo } from "@efc/ipc-contracts";
import { newProjectDoc } from "@efc/ipc-contracts";

import { EngineClient } from "../engine/client";
import { makePartDetail, stlBase64 } from "../test/fixtures";
import { useEngineStore } from "./engineStore";
import { useProjectStore } from "./projectStore";
import { useViewportStore } from "./viewportStore";

const NOW = "2026-07-11T12:00:00.000Z";

function bundle(name: string, parts: ProjectDoc["parts"] = []): { info: ProjectInfo; doc: ProjectDoc } {
  const doc = { ...newProjectDoc({ id: `id-${name}`, name, now: NOW }), parts };
  return {
    info: { id: doc.id, name, path: `C:\\work\\${name}.efproj`, updatedAt: NOW },
    doc,
  };
}

interface FakeBridgeOptions {
  createResult?: ReturnType<typeof bundle> | null;
  openResult?: ReturnType<typeof bundle> | null;
  pickedFile?: { path: string; name: string } | null;
}

function makeBridge(opts: FakeBridgeOptions = {}) {
  const b64 = stlBase64();
  const calls: Array<{ channel: string; payload: unknown }> = [];
  const bridge: EfcBridge = {
    invoke: (async (channel: string, payload: unknown) => {
      calls.push({ channel, payload });
      switch (channel) {
        case "project:create":
          return opts.createResult ?? null;
        case "project:open":
          return opts.openResult ?? null;
        case "project:openPath":
          return opts.openResult;
        case "project:recent":
          return [];
        case "project:save": {
          const req = payload as { path: string; doc: ProjectDoc };
          return {
            id: req.doc.id,
            name: req.doc.name,
            path: req.path,
            updatedAt: "2026-07-11T13:00:00.000Z",
          };
        }
        case "project:importAsset": {
          const req = payload as { sourcePath: string };
          const base = req.sourcePath.split(/[\\/]/).pop() ?? "part.stl";
          return { relPath: `assets/${base}`, name: base };
        }
        case "dialog:openFile":
          return opts.pickedFile ?? null;
        case "fs:readFile":
          return { name: "x.stl", byteLength: 0, dataBase64: b64 };
        default:
          throw new Error(`unexpected channel ${channel}`);
      }
    }) as EfcBridge["invoke"],
    on: vi.fn() as unknown as EfcBridge["on"],
  };
  return { bridge, calls };
}

beforeEach(() => {
  useViewportStore.getState().clear();
  useProjectStore.setState({
    info: null,
    doc: null,
    dirty: false,
    recent: [],
    busy: false,
    error: null,
  });
  // disconnected engine client unless a test installs one
  useEngineStore.setState({ client: new EngineClient({ baseUrl: null, token: null }) });
  delete (window as { efc?: EfcBridge }).efc;
});

describe("projectStore", () => {
  it("createProject sets the bundle and clears the scene", async () => {
    const b = bundle("Fresh");
    const { bridge } = makeBridge({ createResult: b });
    (window as { efc?: EfcBridge }).efc = bridge;
    useViewportStore.getState().addMesh({
      name: "leftover",
      sourcePath: null,
      geometry: new (await import("three")).BufferGeometry(),
    });

    await useProjectStore.getState().createProject();
    expect(useProjectStore.getState().info?.name).toBe("Fresh");
    expect(useProjectStore.getState().dirty).toBe(false);
    expect(useViewportStore.getState().objects).toHaveLength(0);
  });

  it("openRecent loads parts into the viewport with part links", async () => {
    const b = bundle("WithParts", [
      {
        id: "part-1",
        name: "bracket.stl",
        kind: "mesh" as const,
        asset: "assets/bracket.stl",
        colorHex: null,
      },
    ]);
    const { bridge, calls } = makeBridge({ openResult: b });
    (window as { efc?: EfcBridge }).efc = bridge;

    await useProjectStore.getState().openRecent(b.info.path);
    const objects = useViewportStore.getState().objects;
    expect(objects).toHaveLength(1);
    expect(objects[0]!.partId).toBe("part-1");
    expect(objects[0]!.name).toBe("bracket.stl");
    // asset was read from inside the project directory
    const read = calls.find((c) => c.channel === "fs:readFile");
    expect((read!.payload as { path: string }).path).toBe(
      `${b.info.path}/assets/bracket.stl`,
    );
  });

  it("importStl inside a project copies the asset and records a part", async () => {
    const b = bundle("Proj");
    const { bridge, calls } = makeBridge({
      openResult: b,
      pickedFile: { path: "C:\\downloads\\clip.stl", name: "clip.stl" },
    });
    (window as { efc?: EfcBridge }).efc = bridge;

    await useProjectStore.getState().openRecent(b.info.path);
    await useProjectStore.getState().importStl();

    const state = useProjectStore.getState();
    expect(state.doc!.parts).toHaveLength(1);
    expect(state.doc!.parts[0]!.asset).toBe("assets/clip.stl");
    expect(state.dirty).toBe(true);
    expect(useViewportStore.getState().objects).toHaveLength(1);
    expect(useViewportStore.getState().objects[0]!.partId).toBe(state.doc!.parts[0]!.id);

    const importCall = calls.find((c) => c.channel === "project:importAsset");
    expect((importCall!.payload as { projectPath: string }).projectPath).toBe(b.info.path);
  });

  it("importStl without a project stays scene-only", async () => {
    const { bridge, calls } = makeBridge({
      pickedFile: { path: "C:\\downloads\\loose.stl", name: "loose.stl" },
    });
    (window as { efc?: EfcBridge }).efc = bridge;

    await useProjectStore.getState().importStl();
    expect(useViewportStore.getState().objects).toHaveLength(1);
    expect(useProjectStore.getState().doc).toBeNull();
    expect(calls.some((c) => c.channel === "project:importAsset")).toBe(false);
  });

  it("save persists and clears dirty", async () => {
    const b = bundle("Save");
    const { bridge, calls } = makeBridge({ openResult: b });
    (window as { efc?: EfcBridge }).efc = bridge;

    await useProjectStore.getState().openRecent(b.info.path);
    useProjectStore.getState().updateDoc((doc) => ({ ...doc, printerProfileId: "ff-ad5x" }));
    expect(useProjectStore.getState().dirty).toBe(true);

    await useProjectStore.getState().save();
    const state = useProjectStore.getState();
    expect(state.dirty).toBe(false);
    expect(state.info!.updatedAt).toBe("2026-07-11T13:00:00.000Z");
    const saveCall = calls.find((c) => c.channel === "project:save");
    expect((saveCall!.payload as { doc: ProjectDoc }).doc.printerProfileId).toBe("ff-ad5x");
  });

  it("closeProject clears state and scene", async () => {
    const b = bundle("Close", [
      { id: "p", name: "a.stl", kind: "mesh" as const, asset: "assets/a.stl", colorHex: null },
    ]);
    const { bridge } = makeBridge({ openResult: b });
    (window as { efc?: EfcBridge }).efc = bridge;
    await useProjectStore.getState().openRecent(b.info.path);
    expect(useViewportStore.getState().objects).toHaveLength(1);

    useProjectStore.getState().closeProject();
    expect(useProjectStore.getState().info).toBeNull();
    expect(useViewportStore.getState().objects).toHaveLength(0);
  });

  it("loads parametric parts by recompiling their program via the engine", async () => {
    const b = bundle("Para", [
      {
        id: "part-p",
        name: "L-Bracket",
        kind: "parametric",
        program: { schema: "efir/1", name: "L-Bracket", parameters: [] },
        colorHex: null,
      },
    ]);
    const { bridge } = makeBridge({ openResult: b });
    (window as { efc?: EfcBridge }).efc = bridge;
    const engineFetch = vi.fn(async (_url: string, _init?: RequestInit) =>
      new Response(JSON.stringify(makePartDetail({ partId: "eng-9" })), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    useEngineStore.setState({
      client: new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, engineFetch),
    });

    await useProjectStore.getState().openRecent(b.info.path);
    const objects = useViewportStore.getState().objects;
    expect(objects).toHaveLength(1);
    expect(objects[0]!.parametricPartId).toBe("eng-9");
    expect(objects[0]!.partId).toBe("part-p");
    expect(objects[0]!.sourcePath).toBeNull();
    expect(engineFetch.mock.calls[0]![0]).toContain("/api/v1/parts/compile");
    expect(useProjectStore.getState().error).toBeNull();
  });

  it("reports parametric parts cleanly when the engine is offline", async () => {
    const b = bundle("ParaOffline", [
      {
        id: "part-p",
        name: "L-Bracket",
        kind: "parametric",
        program: { schema: "efir/1" },
        colorHex: null,
      },
    ]);
    const { bridge } = makeBridge({ openResult: b });
    (window as { efc?: EfcBridge }).efc = bridge;
    // engine client left disconnected by beforeEach

    await useProjectStore.getState().openRecent(b.info.path);
    expect(useViewportStore.getState().objects).toHaveLength(0);
    expect(useProjectStore.getState().error).toContain("needs the engine");
    // the project still opens — doc is intact
    expect(useProjectStore.getState().doc?.parts).toHaveLength(1);
  });

  it("surfaces errors without leaving busy stuck", async () => {
    const bridge: EfcBridge = {
      invoke: (async () => {
        throw new Error("boom");
      }) as EfcBridge["invoke"],
      on: vi.fn() as unknown as EfcBridge["on"],
    };
    (window as { efc?: EfcBridge }).efc = bridge;

    await useProjectStore.getState().openRecent("C:\\x");
    expect(useProjectStore.getState().error).toContain("boom");
    expect(useProjectStore.getState().busy).toBe(false);
  });
});
