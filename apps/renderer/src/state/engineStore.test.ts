import { beforeEach, describe, expect, it, vi } from "vitest";

import type { EfcBridge, EngineStatus } from "@efc/ipc-contracts";

import { useEngineStore } from "./engineStore";

const runningStatus: EngineStatus = {
  state: "running",
  pid: 42,
  port: 9001,
  baseUrl: "http://127.0.0.1:9001",
  message: "engine ready",
  restarts: 0,
};

function makeBridge(): EfcBridge & { emit: (status: EngineStatus) => void } {
  let statusListener: ((payload: EngineStatus) => void) | null = null;
  return {
    invoke: vi.fn(async (channel: string) => {
      if (channel === "engine:getStatus") return runningStatus;
      if (channel === "engine:getConnection") {
        return { baseUrl: runningStatus.baseUrl, token: "tok" };
      }
      if (channel === "engine:restart") return runningStatus;
      throw new Error(`unexpected channel ${channel}`);
    }) as EfcBridge["invoke"],
    on: ((_event: string, listener: (payload: EngineStatus) => void) => {
      statusListener = listener;
      return () => {
        statusListener = null;
      };
    }) as EfcBridge["on"],
    emit: (status: EngineStatus) => statusListener?.(status),
  };
}

beforeEach(() => {
  // reset the zustand store between tests
  useEngineStore.setState({
    bridgeAvailable: false,
    status: null,
    connection: { baseUrl: null, token: null },
    initialized: false,
  });
  delete (window as { efc?: EfcBridge }).efc;
});

describe("engineStore", () => {
  it("degrades gracefully without the bridge (browser mode)", async () => {
    await useEngineStore.getState().init();
    const s = useEngineStore.getState();
    expect(s.bridgeAvailable).toBe(false);
    expect(s.status).toBeNull();
  });

  it("initializes from the bridge and builds a connected client", async () => {
    const bridge = makeBridge();
    (window as { efc?: EfcBridge }).efc = bridge;

    await useEngineStore.getState().init();
    const s = useEngineStore.getState();
    expect(s.bridgeAvailable).toBe(true);
    expect(s.status?.state).toBe("running");
    expect(s.connection.baseUrl).toBe("http://127.0.0.1:9001");
    expect(s.client.connected).toBe(true);
  });

  it("updates status from push events", async () => {
    const bridge = makeBridge();
    (window as { efc?: EfcBridge }).efc = bridge;
    await useEngineStore.getState().init();

    bridge.emit({ ...runningStatus, state: "restarting", message: "crashed" });
    expect(useEngineStore.getState().status?.state).toBe("restarting");
  });

  it("does not re-init twice", async () => {
    const bridge = makeBridge();
    (window as { efc?: EfcBridge }).efc = bridge;
    await useEngineStore.getState().init();
    await useEngineStore.getState().init();
    // one getStatus + one getConnection from the first init only
    expect((bridge.invoke as ReturnType<typeof vi.fn>).mock.calls.length).toBe(2);
  });
});
