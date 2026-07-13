import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { newProjectDoc, type ProjectInfo } from "@efc/ipc-contracts";

import { EngineClient } from "../../engine/client";
import type { PartDetail } from "../../engine/types";
import { useEngineStore } from "../../state/engineStore";
import { useProjectStore } from "../../state/projectStore";
import { useViewportStore } from "../../state/viewportStore";
import { makePartDetail } from "../../test/fixtures";
import { useParametricStore } from "./parametricStore";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

interface ClientMock {
  fetchMock: ReturnType<typeof vi.fn>;
  patchBodies: () => Array<{ values: Record<string, number> }>;
}

function installClient(detailFactory: (url: string, init?: RequestInit) => PartDetail): ClientMock {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) =>
    jsonResponse(detailFactory(url, init)),
  );
  useEngineStore.setState({
    client: new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchMock),
  });
  return {
    fetchMock,
    patchBodies: () =>
      fetchMock.mock.calls
        .filter((c) => (c[1] as RequestInit | undefined)?.method === "PATCH")
        .map((c) => JSON.parse((c[1] as RequestInit).body as string)),
  };
}

function openProject(): void {
  const doc = newProjectDoc({ id: "p1", name: "Proj", now: "t" });
  const info: ProjectInfo = { id: "p1", name: "Proj", path: "C:\\w\\Proj.efproj", updatedAt: "t" };
  useProjectStore.setState({ info, doc, dirty: false });
}

beforeEach(() => {
  useParametricStore.getState().clear();
  useViewportStore.getState().clear();
  useProjectStore.setState({ info: null, doc: null, dirty: false });
});

afterEach(() => {
  useParametricStore.getState().clear();
  vi.useRealTimers();
});

describe("parametricStore.createFromTemplate", () => {
  it("creates a part and adds a linked viewport object", async () => {
    installClient(() =>
      makePartDetail({
        partId: "eng-1",
        features: [{ op: "sketch", id: "s" }, { op: "extrude", id: "e", distance: "H" }],
      }),
    );
    await useParametricStore.getState().createFromTemplate("bracket-l");

    const active = useParametricStore.getState().active;
    expect(active?.partId).toBe("eng-1");
    expect(active?.features.map((f) => f.op)).toEqual(["sketch", "extrude"]);
    const objects = useViewportStore.getState().objects;
    expect(objects).toHaveLength(1);
    expect(objects[0]!.parametricPartId).toBe("eng-1");
    expect(active?.objectId).toBe(objects[0]!.id);
  });

  it("records a parametric part in the open project doc", async () => {
    installClient(() => makePartDetail());
    openProject();
    await useParametricStore.getState().createFromTemplate("bracket-l");

    const doc = useProjectStore.getState().doc!;
    expect(doc.parts).toHaveLength(1);
    expect(doc.parts[0]!.kind).toBe("parametric");
    expect(doc.parts[0]!.program).toBeDefined();
    expect(useProjectStore.getState().dirty).toBe(true);
    expect(useParametricStore.getState().active?.projectPartId).toBe(doc.parts[0]!.id);
  });

  it("surfaces engine errors", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: "GEOMETRY_ERROR", message: "fillet failed", details: {}, retryable: false },
        }),
        { status: 422 },
      ),
    );
    useEngineStore.setState({
      client: new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchMock),
    });
    await useParametricStore.getState().createFromTemplate("bracket-l");
    expect(useParametricStore.getState().error).toContain("fillet failed");
    expect(useViewportStore.getState().objects).toHaveLength(0);
  });
});

describe("parametricStore.setParam (live rebuild)", () => {
  it("debounces edits into one PATCH and swaps geometry", async () => {
    vi.useFakeTimers();
    const mock = installClient((url, init) => {
      if (init?.method === "PATCH") {
        const body = JSON.parse(init.body as string) as { values: Record<string, number> };
        return makePartDetail({ partId: "eng-1", values: body.values, volumeCm3: 42 });
      }
      return makePartDetail({ partId: "eng-1" });
    });

    await useParametricStore.getState().createFromTemplate("bracket-l");
    const versionBefore = useViewportStore.getState().contentVersion;

    useParametricStore.getState().setParam("W", 50);
    useParametricStore.getState().setParam("W", 60); // rapid edits collapse
    expect(useParametricStore.getState().active?.parameters.find((p) => p.id === "W")?.value).toBe(60);

    await vi.advanceTimersByTimeAsync(400);
    const patches = mock.patchBodies();
    expect(patches).toHaveLength(1);
    expect(patches[0]!.values).toMatchObject({ W: 60, H: 60 });

    const state = useParametricStore.getState();
    expect(state.active?.massProps.volumeCm3).toBe(42);
    expect(useViewportStore.getState().contentVersion).toBeGreaterThan(versionBefore);
  });

  it("persists the rebuilt program into the project doc", async () => {
    vi.useFakeTimers();
    installClient((url, init) => {
      if (init?.method === "PATCH") {
        const body = JSON.parse(init.body as string) as { values: Record<string, number> };
        return makePartDetail({ values: body.values });
      }
      return makePartDetail();
    });
    openProject();
    await useParametricStore.getState().createFromTemplate("bracket-l");

    useParametricStore.getState().setParam("W", 80);
    await vi.advanceTimersByTimeAsync(400);

    const savedProgram = useProjectStore.getState().doc!.parts[0]!.program as {
      parameters: Array<{ id: string; value: number }>;
    };
    expect(savedProgram.parameters.find((p) => p.id === "W")?.value).toBe(80);
  });

  it("keeps rebuild errors visible without losing state", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "PATCH") {
        return new Response(
          JSON.stringify({
            error: { code: "GEOMETRY_ERROR", message: "radius too large", details: {}, retryable: false },
          }),
          { status: 422 },
        );
      }
      return jsonResponse(makePartDetail());
    });
    useEngineStore.setState({
      client: new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchMock),
    });

    await useParametricStore.getState().createFromTemplate("bracket-l");
    useParametricStore.getState().setParam("W", 55);
    await vi.advanceTimersByTimeAsync(400);

    expect(useParametricStore.getState().error).toContain("radius too large");
    expect(useParametricStore.getState().active?.partId).toBe("engpart1");
  });
});

describe("undo/redo", () => {
  it("restores previous values and triggers a rebuild", async () => {
    vi.useFakeTimers();
    const mock = installClient((url, init) => {
      if (init?.method === "PATCH") {
        const body = JSON.parse(init.body as string) as { values: Record<string, number> };
        return makePartDetail({ values: body.values });
      }
      return makePartDetail();
    });

    await useParametricStore.getState().createFromTemplate("bracket-l");
    useParametricStore.getState().setParam("W", 70);
    await vi.advanceTimersByTimeAsync(400);

    useParametricStore.getState().undo();
    expect(
      useParametricStore.getState().active?.parameters.find((p) => p.id === "W")?.value,
    ).toBe(40);
    await vi.advanceTimersByTimeAsync(400);
    expect(mock.patchBodies().at(-1)!.values.W).toBe(40);

    useParametricStore.getState().redo();
    expect(
      useParametricStore.getState().active?.parameters.find((p) => p.id === "W")?.value,
    ).toBe(70);
    await vi.advanceTimersByTimeAsync(400);
    expect(mock.patchBodies().at(-1)!.values.W).toBe(70);
  });

  it("undo is a no-op with an empty stack", () => {
    useParametricStore.getState().undo();
    expect(useParametricStore.getState().active).toBeNull();
  });
});
