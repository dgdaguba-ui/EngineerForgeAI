/**
 * IPC registration. Every request is validated against the Zod schema from
 * @efc/ipc-contracts before the handler runs — the renderer is never trusted.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";

import { app, dialog, ipcMain, type BrowserWindow } from "electron";
import { channels, type ChannelName, type ProjectDoc } from "@efc/ipc-contracts";

import type { CloudService } from "./cloud/service.js";
import type { CloudSyncQueue } from "./cloud/syncQueue.js";
import type { LocalProjectStore } from "./projects/local-store.js";
import type { RecentProjects } from "./projects/recents.js";
import type { PathAllowlist } from "./security.js";
import type { EngineSupervisor } from "./supervisor.js";

interface IpcDeps {
  supervisor: EngineSupervisor;
  allowlist: PathAllowlist;
  projects: LocalProjectStore;
  recents: RecentProjects;
  cloud: CloudService;
  syncQueue: CloudSyncQueue;
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
  const { supervisor, allowlist, projects, recents, cloud, syncQueue, getWindow } = deps;

  // ── app / engine ────────────────────────────────────────────────────────────

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

  // ── dialogs & files ─────────────────────────────────────────────────────────

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

  // ── projects (local-first) ──────────────────────────────────────────────────

  handle("project:create", async () => {
    const win = getWindow();
    const options: Electron.SaveDialogOptions = {
      title: "Create EngineerForge project",
      defaultPath: "MyProject.efproj",
      buttonLabel: "Create",
    };
    const result = win
      ? await dialog.showSaveDialog(win, options)
      : await dialog.showSaveDialog(options);
    if (result.canceled || !result.filePath) return null;
    const bundle = await projects.createProject(result.filePath);
    allowlist.approveDir(bundle.info.path);
    await recents.add(bundle.info);
    return bundle;
  });

  handle("project:open", async () => {
    const win = getWindow();
    const options: Electron.OpenDialogOptions = {
      title: "Open EngineerForge project (.efproj folder)",
      properties: ["openDirectory"],
    };
    const result = win
      ? await dialog.showOpenDialog(win, options)
      : await dialog.showOpenDialog(options);
    const dirPath = result.filePaths[0];
    if (result.canceled || !dirPath) return null;
    const bundle = await projects.openProject(dirPath);
    allowlist.approveDir(bundle.info.path);
    await recents.add(bundle.info);
    return bundle;
  });

  handle("project:openPath", async (req) => {
    const { path: dirPath } = req as { path: string };
    const bundle = await projects.openProject(dirPath);
    allowlist.approveDir(bundle.info.path);
    await recents.add(bundle.info);
    return bundle;
  });

  handle("project:save", async (req) => {
    const { path: dirPath, doc } = req as { path: string; doc: ProjectDoc };
    if (!allowlist.isApproved(path.join(dirPath, "project.json"))) {
      throw new Error("Cannot save to a project that was not opened in this session.");
    }
    const info = await projects.saveProject(dirPath, doc);
    await recents.add(info);
    return info;
  });

  handle("project:recent", async () => await recents.list());

  handle("project:importAsset", async (req) => {
    const { projectPath, sourcePath } = req as { projectPath: string; sourcePath: string };
    if (!allowlist.isApproved(sourcePath)) {
      throw new Error("Source file not approved: pick it via a dialog first.");
    }
    if (!allowlist.isApproved(path.join(projectPath, "project.json"))) {
      throw new Error("Project not opened in this session.");
    }
    return await projects.importAsset(projectPath, sourcePath);
  });

  // ── cloud (optional) ────────────────────────────────────────────────────────

  handle("cloud:status", async () => await cloud.status());

  handle("cloud:signIn", async (req) => {
    const { email, password } = req as { email: string; password: string };
    return await cloud.signIn(email, password);
  });

  handle("cloud:signOut", async () => await cloud.signOut());

  handle("cloud:pushProject", async (req) => {
    const { path: dirPath } = req as { path: string };
    const bundle = await projects.openProject(dirPath);
    return await cloud.pushProject(bundle.info, bundle.doc);
  });

  handle("cloud:queueProject", async (req) => {
    const { path: dirPath } = req as { path: string };
    const bundle = await projects.openProject(dirPath);
    return syncQueue.enqueue(bundle.info, bundle.doc);
  });

  handle("cloud:syncStatus", () => syncQueue.status());
}
