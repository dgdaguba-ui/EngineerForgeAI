/**
 * Engine connection state. Subscribes to supervisor push events via the
 * preload bridge and exposes a ready-to-use EngineClient.
 */
import { create } from "zustand";

import type { EngineStatus } from "@efc/ipc-contracts";

import { EngineClient, type EngineConnectionInfo } from "../engine/client";
import { getBridge } from "../ipc/efc";

interface EngineStoreState {
  bridgeAvailable: boolean;
  status: EngineStatus | null;
  connection: EngineConnectionInfo;
  client: EngineClient;
  initialized: boolean;
  init: () => Promise<void>;
  refreshConnection: () => Promise<void>;
  restart: () => Promise<void>;
}

const disconnected: EngineConnectionInfo = { baseUrl: null, token: null };

export const useEngineStore = create<EngineStoreState>((set, get) => ({
  bridgeAvailable: false,
  status: null,
  connection: disconnected,
  client: new EngineClient(disconnected),
  initialized: false,

  init: async () => {
    if (get().initialized) return;
    const bridge = getBridge();
    if (!bridge) {
      set({ bridgeAvailable: false, initialized: true });
      return;
    }
    set({ bridgeAvailable: true, initialized: true });

    bridge.on("engine:statusChanged", (status) => {
      set({ status });
      void get().refreshConnection();
    });

    const status = await bridge.invoke("engine:getStatus", undefined);
    set({ status });
    await get().refreshConnection();
  },

  refreshConnection: async () => {
    const bridge = getBridge();
    if (!bridge) return;
    const conn = await bridge.invoke("engine:getConnection", undefined);
    const connection: EngineConnectionInfo = { baseUrl: conn.baseUrl, token: conn.token };
    const prev = get().connection;
    if (prev.baseUrl !== connection.baseUrl || prev.token !== connection.token) {
      set({ connection, client: new EngineClient(connection) });
    }
  },

  restart: async () => {
    const bridge = getBridge();
    if (!bridge) return;
    const status = await bridge.invoke("engine:restart", undefined);
    set({ status });
    await get().refreshConnection();
  },
}));
