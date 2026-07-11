/**
 * Project state — local-first `.efproj` handling in the renderer.
 *
 * Opening a project loads its parts into the viewport; importing an STL while
 * a project is open copies the file into the project's assets and records a
 * part; saving persists the document through the main process.
 */
import { create } from "zustand";

import type { ProjectDoc, ProjectInfo } from "@efc/ipc-contracts";

import { importStlViaDialog } from "../features/viewport/import";
import { base64ToArrayBuffer, parseStlToGeometry } from "../features/viewport/stl";
import { getBridge } from "../ipc/efc";
import { useViewportStore } from "./viewportStore";

let partCounter = 0;
function newPartId(): string {
  partCounter += 1;
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `part_${partCounter}`;
}

interface ProjectState {
  info: ProjectInfo | null;
  doc: ProjectDoc | null;
  dirty: boolean;
  recent: ProjectInfo[];
  busy: boolean;
  error: string | null;
  refreshRecent: () => Promise<void>;
  createProject: () => Promise<void>;
  openProject: () => Promise<void>;
  openRecent: (path: string) => Promise<void>;
  save: () => Promise<void>;
  closeProject: () => void;
  /** Import an STL — into the open project if any, otherwise scene-only. */
  importStl: () => Promise<void>;
  /** Mutate the doc immutably and mark it dirty. */
  updateDoc: (mutate: (doc: ProjectDoc) => ProjectDoc) => void;
}

async function loadBundleIntoScene(info: ProjectInfo, doc: ProjectDoc): Promise<string | null> {
  const bridge = getBridge();
  if (!bridge) return "Desktop shell not available.";
  const viewport = useViewportStore.getState();
  viewport.clear();
  for (const part of doc.parts) {
    try {
      const file = await bridge.invoke("fs:readFile", {
        path: `${info.path}/${part.asset}`,
      });
      const geometry = parseStlToGeometry(base64ToArrayBuffer(file.dataBase64));
      useViewportStore.getState().addMesh({
        name: part.name,
        sourcePath: `${info.path}/${part.asset}`,
        geometry,
        partId: part.id,
      });
    } catch (e) {
      return `Failed to load part "${part.name}": ${e instanceof Error ? e.message : String(e)}`;
    }
  }
  useViewportStore.getState().select(null);
  return null;
}

export const useProjectStore = create<ProjectState>((set, get) => {
  async function withBusy(fn: () => Promise<void>): Promise<void> {
    set({ busy: true, error: null });
    try {
      await fn();
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) });
    } finally {
      set({ busy: false });
    }
  }

  return {
    info: null,
    doc: null,
    dirty: false,
    recent: [],
    busy: false,
    error: null,

    refreshRecent: async () => {
      const bridge = getBridge();
      if (!bridge) return;
      const recent = await bridge.invoke("project:recent", undefined);
      set({ recent });
    },

    createProject: async () =>
      await withBusy(async () => {
        const bridge = getBridge();
        if (!bridge) throw new Error("Projects require the desktop shell.");
        const bundle = await bridge.invoke("project:create", undefined);
        if (!bundle) return; // user cancelled
        useViewportStore.getState().clear();
        set({ info: bundle.info, doc: bundle.doc, dirty: false });
        await get().refreshRecent();
      }),

    openProject: async () =>
      await withBusy(async () => {
        const bridge = getBridge();
        if (!bridge) throw new Error("Projects require the desktop shell.");
        const bundle = await bridge.invoke("project:open", undefined);
        if (!bundle) return;
        const loadError = await loadBundleIntoScene(bundle.info, bundle.doc);
        set({ info: bundle.info, doc: bundle.doc, dirty: false, error: loadError });
        await get().refreshRecent();
      }),

    openRecent: async (path: string) =>
      await withBusy(async () => {
        const bridge = getBridge();
        if (!bridge) throw new Error("Projects require the desktop shell.");
        const bundle = await bridge.invoke("project:openPath", { path });
        const loadError = await loadBundleIntoScene(bundle.info, bundle.doc);
        set({ info: bundle.info, doc: bundle.doc, dirty: false, error: loadError });
        await get().refreshRecent();
      }),

    save: async () =>
      await withBusy(async () => {
        const bridge = getBridge();
        const { info, doc } = get();
        if (!bridge || !info || !doc) return;
        const updated = await bridge.invoke("project:save", { path: info.path, doc });
        set({ info: updated, doc: { ...doc, updatedAt: updated.updatedAt }, dirty: false });
        await get().refreshRecent();
      }),

    closeProject: () => {
      useViewportStore.getState().clear();
      set({ info: null, doc: null, dirty: false, error: null });
    },

    importStl: async () =>
      await withBusy(async () => {
        const bridge = getBridge();
        if (!bridge) throw new Error("File import requires the desktop shell.");
        const imported = await importStlViaDialog(bridge);
        if (!imported) return;

        const { info, doc } = get();
        if (info && doc) {
          const asset = await bridge.invoke("project:importAsset", {
            projectPath: info.path,
            sourcePath: imported.sourcePath,
          });
          const partId = newPartId();
          set({
            doc: {
              ...doc,
              parts: [
                ...doc.parts,
                { id: partId, name: asset.name, asset: asset.relPath, colorHex: null },
              ],
            },
            dirty: true,
          });
          useViewportStore.getState().addMesh({
            name: asset.name,
            sourcePath: imported.sourcePath,
            geometry: imported.geometry,
            partId,
          });
        } else {
          useViewportStore.getState().addMesh({
            name: imported.name,
            sourcePath: imported.sourcePath,
            geometry: imported.geometry,
          });
        }
      }),

    updateDoc: (mutate) => {
      const doc = get().doc;
      if (!doc) return;
      set({ doc: mutate(doc), dirty: true });
    },
  };
});
