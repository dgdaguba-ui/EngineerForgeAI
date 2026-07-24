/**
 * Electron main process — window lifecycle, hardened renderer, engine
 * supervision, IPC wiring.
 *
 * `electron . --smoke` runs headless: start the engine, wait for health,
 * print a JSON status line, exit 0/1. Used as an automated end-to-end gate.
 */
import path from "node:path";

import { app, BrowserWindow } from "electron";
import { events, type EngineStatus } from "@efc/ipc-contracts";

import { buildCloudService } from "./cloud/registry.js";
import { CloudSyncQueue } from "./cloud/syncQueue.js";
import { loadDotenvFile } from "./dotenv.js";
import { resolveEngineDir } from "./engine-locator.js";
import { registerIpc } from "./ipc.js";
import { LocalProjectStore } from "./projects/local-store.js";
import { RecentProjects } from "./projects/recents.js";
import { newSessionToken, PathAllowlist } from "./security.js";
import { EngineSupervisor } from "./supervisor.js";

// Dev convenience: pick up the repo-root .env (Supabase/AI keys). Existing
// process env always wins; packaged builds read the OS environment only.
if (!app.isPackaged) {
  loadDotenvFile(path.resolve(app.getAppPath(), "..", "..", ".env"));
}

const SMOKE_MODE = process.argv.includes("--smoke");
const RENDERER_DEV_URL = process.env.EFC_RENDERER_URL ?? "http://localhost:5173";

let mainWindow: BrowserWindow | null = null;

const engineDir = resolveEngineDir({
  appPath: app.getAppPath(),
  isPackaged: app.isPackaged,
  resourcesPath: process.resourcesPath,
});

const supervisor = new EngineSupervisor({
  engineDir,
  token: newSessionToken(),
  onStatus: (status: EngineStatus) => {
    const payload = events["engine:statusChanged"].parse(status);
    mainWindow?.webContents.send("engine:statusChanged", payload);
  },
  log: (line) => console.log(line),
});

const allowlist = new PathAllowlist();
const projects = new LocalProjectStore();
const recents = new RecentProjects(
  path.join(app.getPath("userData"), "recent-projects.json"),
);
const cloud = buildCloudService({
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY,
  SUPABASE_BUCKET: process.env.SUPABASE_BUCKET,
});
const syncQueue = new CloudSyncQueue(cloud);

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: "#09090b",
    title: "EngineerForge AI",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  // Hardening: no popups, no external navigation inside the app window.
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  mainWindow.webContents.on("will-navigate", (event, url) => {
    const allowed =
      (!app.isPackaged && url.startsWith(RENDERER_DEV_URL)) || url.startsWith("file://");
    if (!allowed) event.preventDefault();
  });

  if (app.isPackaged) {
    void mainWindow.loadFile(path.join(__dirname, "..", "..", "renderer", "dist", "index.html"));
  } else {
    loadDevRendererWithRetry(mainWindow);
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

/** The Vite dev server may still be starting when Electron launches — retry. */
function loadDevRendererWithRetry(win: BrowserWindow, attempt = 0): void {
  void win.loadURL(RENDERER_DEV_URL).catch(() => {
    if (attempt < 60 && !win.isDestroyed()) {
      setTimeout(() => loadDevRendererWithRetry(win, attempt + 1), 1000);
    }
  });
}

async function runSmoke(): Promise<void> {
  const status = await supervisor.start();
  console.log(`SMOKE_RESULT ${JSON.stringify(status)}`);
  await supervisor.stop();
  app.exit(status.state === "running" ? 0 : 1);
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock && !SMOKE_MODE) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  void app.whenReady().then(async () => {
    if (SMOKE_MODE) {
      await runSmoke();
      return;
    }
    registerIpc({
      supervisor,
      allowlist,
      projects,
      recents,
      cloud,
      syncQueue,
      getWindow: () => mainWindow,
    });
    createWindow();
    void supervisor.start();

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
  });

  app.on("before-quit", () => {
    syncQueue.dispose();
    void supervisor.stop();
  });
}
