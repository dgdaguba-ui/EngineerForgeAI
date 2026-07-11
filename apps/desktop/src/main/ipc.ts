/**
 * IPC registration. Every request is validated against the Zod schema from
 * @efc/ipc-contracts before the handler runs — the renderer is never trusted.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";

import { app, dialog, ipcMain, type BrowserWindow } from "electron";
import { channels, type ChannelName } from "@efc/ipc-contracts";

import type { EngineSupervisor } from "./supervisor.js";
import type { PathAllowlist } from "./security.js";

interface IpcDeps {
  supervisor: EngineSupervisor;
  allowlist: PathAllowlist;
  getWindow: () => BrowserWindow | null;
}

function handle<C extends ChannelName>(
  channel: C,
  handler: (req: unknown) => Promise<unknown> | unknown,
): void {
  ipcMain.handle(channel, async (_event, payload: unknown) => {
    const def = channels[channel];
    const req = def.req.parse(payload ?? undefined);
    const res = await handler(req);
    return def.res.parse(res);
  });
}

export function registerIpc(deps: IpcDeps): void {
  const { supervisor, allowlist, getWindow } = deps;

  handle("app:getVersion", () => ({
    app: app.getVersion(),
    electron: process.versions.electron ?? "unknown",
  }));

  handle("engine:getStatus", () => supervisor.getStatus());

  handle("engine:getConnection", () => {
    const status = supervisor.getStatus();
    return {
      baseUrl: status.state === "running" ? status.baseUrl : null,
      token: status.state === "running" ? supervisor.getToken() : null,
    };
  });

  handle("engine:restart", async () => await supervisor.restart());

  handle("dialog:openFile", async (req) => {
    const options = req as { title?: string; filters?: { name: string; extensions: string[] }[] };
    const dialogOptions: Electron.OpenDialogOptions = { properties: ["openFile"] };
    if (options.title !== undefined) dialogOptions.title = options.title;
    if (options.filters !== undefined) dialogOptions.filters = options.filters;
    const win = getWindow();
    const result = win
      ? await dialog.showOpenDialog(win, dialogOptions)
      : await dialog.showOpenDialog(dialogOptions);
    const first = result.filePaths[0];
    if (result.canceled || !first) return null;
    allowlist.approve(first);
    return { path: first, name: path.basename(first) };
  });

  handle("dialog:saveFile", async (req) => {
    const options = req as {
      title?: string;
      defaultName?: string;
      filters?: { name: string; extensions: string[] }[];
    };
    const dialogOptions: Electron.SaveDialogOptions = {};
    if (options.title !== undefined) dialogOptions.title = options.title;
    if (options.defaultName !== undefined) dialogOptions.defaultPath = options.defaultName;
    if (options.filters !== undefined) dialogOptions.filters = options.filters;
    const win = getWindow();
    const result = win
      ? await dialog.showSaveDialog(win, dialogOptions)
      : await dialog.showSaveDialog(dialogOptions);
    if (result.canceled || !result.filePath) return null;
    allowlist.approve(result.filePath);
    return { path: result.filePath, name: path.basename(result.filePath) };
  });

  handle("fs:readFile", async (req) => {
    const { path: filePath } = req as { path: string };
    if (!allowlist.isApproved(filePath)) {
      throw new Error("Path not approved: files must be selected via a dialog first.");
    }
    const data = await readFile(filePath);
    return {
      name: path.basename(filePath),
      byteLength: data.byteLength,
      dataBase64: data.toString("base64"),
    };
  });
}
