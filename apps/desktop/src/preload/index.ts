/**
 * Preload — the ONLY bridge between the sandboxed renderer and the main
 * process. Exposes a narrow, channel-allowlisted `window.efc` API.
 *
 * Bundled self-contained by esbuild (sandboxed preloads cannot require
 * external modules at runtime).
 */
import { contextBridge, ipcRenderer, type IpcRendererEvent } from "electron";
import { channelNames, eventNames } from "@efc/ipc-contracts";

const allowedChannels = new Set<string>(channelNames);
const allowedEvents = new Set<string>(eventNames);

contextBridge.exposeInMainWorld("efc", {
  invoke: (channel: string, payload: unknown): Promise<unknown> => {
    if (!allowedChannels.has(channel)) {
      return Promise.reject(new Error(`IPC channel not allowed: ${channel}`));
    }
    return ipcRenderer.invoke(channel, payload);
  },
  on: (event: string, listener: (payload: unknown) => void): (() => void) => {
    if (!allowedEvents.has(event)) {
      throw new Error(`IPC event not allowed: ${event}`);
    }
    const wrapped = (_e: IpcRendererEvent, payload: unknown): void => listener(payload);
    ipcRenderer.on(event, wrapped);
    return () => ipcRenderer.removeListener(event, wrapped);
  },
});
