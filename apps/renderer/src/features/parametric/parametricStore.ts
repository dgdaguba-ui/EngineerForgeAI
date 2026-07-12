/**
 * Parametric part state: template creation, live parameter edits (debounced
 * engine rebuild → geometry swap), IR-level undo/redo, and persistence of the
 * Feature Program into the open project document.
 */
import { create } from "zustand";

import type { IrParameter, PartDetail } from "../../engine/types";
import { useEngineStore } from "../../state/engineStore";
import { useProjectStore } from "../../state/projectStore";
import { useViewportStore } from "../../state/viewportStore";
import { rawMeshToGeometry } from "./rawMesh";

const REBUILD_DEBOUNCE_MS = 300;
const HISTORY_LIMIT = 50;

export interface ActivePart {
  partId: string; // engine session id
  objectId: string; // viewport object id
  projectPartId: string | null; // .efproj part id when a project is open
  templateId: string | null;
  name: string;
  parameters: IrParameter[];
  massProps: PartDetail["compiled"]["massProps"];
  warnings: string[];
}

type ParamValues = Record<string, number>;

interface ParametricState {
  active: ActivePart | null;
  rebuilding: boolean;
  error: string | null;
  undoStack: ParamValues[];
  redoStack: ParamValues[];
  pendingTimer: ReturnType<typeof setTimeout> | null;

  createFromTemplate: (templateId: string) => Promise<void>;
  /** Adopt an already-compiled part (e.g. loaded from a project). */
  adopt: (detail: PartDetail, objectId: string, projectPartId: string | null) => void;
  setParam: (paramId: string, value: number) => void;
  undo: () => void;
  redo: () => void;
  clear: () => void;
}

function valuesOf(parameters: IrParameter[]): ParamValues {
  return Object.fromEntries(parameters.map((p) => [p.id, p.value]));
}

let projectPartCounter = 0;
function newProjectPartId(): string {
  projectPartCounter += 1;
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `ppart_${projectPartCounter}`;
}

export const useParametricStore = create<ParametricState>((set, get) => {
  function applyDetail(
    detail: PartDetail,
    objectId: string,
    projectPartId: string | null,
  ): void {
    set({
      active: {
        partId: detail.partId,
        objectId,
        projectPartId,
        templateId: detail.templateId,
        name: detail.name,
        parameters: detail.program.parameters,
        massProps: detail.compiled.massProps,
        warnings: detail.compiled.warnings,
      },
    });
  }

  function persistProgram(detail: PartDetail, projectPartId: string | null): void {
    if (!projectPartId) return;
    const project = useProjectStore.getState();
    if (!project.doc) return;
    project.updateDoc((doc) => ({
      ...doc,
      parts: doc.parts.map((p) =>
        p.id === projectPartId ? { ...p, program: detail.program } : p,
      ),
    }));
  }

  async function rebuild(values: ParamValues): Promise<void> {
    const { active } = get();
    if (!active) return;
    const client = useEngineStore.getState().client;
    set({ rebuilding: true, error: null });
    try {
      const detail = await client.patchPartParams(active.partId, values);
      const geometry = rawMeshToGeometry(detail.compiled.mesh);
      useViewportStore.getState().replaceGeometry(active.objectId, geometry);
      applyDetail(detail, active.objectId, active.projectPartId);
      persistProgram(detail, active.projectPartId);
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) });
    } finally {
      set({ rebuilding: false });
    }
  }

  function scheduleRebuild(): void {
    const { pendingTimer, active } = get();
    if (pendingTimer) clearTimeout(pendingTimer);
    if (!active) return;
    const values = valuesOf(active.parameters);
    const timer = setTimeout(() => {
      set({ pendingTimer: null });
      void rebuild(values);
    }, REBUILD_DEBOUNCE_MS);
    set({ pendingTimer: timer });
  }

  return {
    active: null,
    rebuilding: false,
    error: null,
    undoStack: [],
    redoStack: [],
    pendingTimer: null,

    createFromTemplate: async (templateId: string) => {
      const client = useEngineStore.getState().client;
      set({ rebuilding: true, error: null });
      try {
        const detail = await client.createPartFromTemplate(templateId);
        const geometry = rawMeshToGeometry(detail.compiled.mesh);

        // record in the open project (if any) so save/reopen restores it
        let projectPartId: string | null = null;
        const project = useProjectStore.getState();
        if (project.doc) {
          projectPartId = newProjectPartId();
          const partId = projectPartId;
          project.updateDoc((doc) => ({
            ...doc,
            parts: [
              ...doc.parts,
              {
                id: partId,
                name: detail.name,
                kind: "parametric" as const,
                program: detail.program,
                colorHex: null,
              },
            ],
          }));
        }

        const objectId = useViewportStore.getState().addMesh({
          name: detail.name,
          sourcePath: null,
          geometry,
          partId: projectPartId,
          parametricPartId: detail.partId,
        });
        set({
          active: {
            partId: detail.partId,
            objectId,
            projectPartId,
            templateId: detail.templateId,
            name: detail.name,
            parameters: detail.program.parameters,
            massProps: detail.compiled.massProps,
            warnings: detail.compiled.warnings,
          },
          undoStack: [],
          redoStack: [],
        });
      } catch (e) {
        set({ error: e instanceof Error ? e.message : String(e) });
      } finally {
        set({ rebuilding: false });
      }
    },

    adopt: (detail, objectId, projectPartId) => {
      applyDetail(detail, objectId, projectPartId);
      set({ undoStack: [], redoStack: [] });
    },

    setParam: (paramId, value) => {
      const { active, undoStack } = get();
      if (!active) return;
      const parameter = active.parameters.find((p) => p.id === paramId);
      if (!parameter || parameter.value === value) return;
      const snapshot = valuesOf(active.parameters);
      set({
        active: {
          ...active,
          parameters: active.parameters.map((p) =>
            p.id === paramId ? { ...p, value } : p,
          ),
        },
        undoStack: [...undoStack.slice(-(HISTORY_LIMIT - 1)), snapshot],
        redoStack: [],
      });
      scheduleRebuild();
    },

    undo: () => {
      const { active, undoStack, redoStack } = get();
      if (!active || undoStack.length === 0) return;
      const previous = undoStack[undoStack.length - 1]!;
      const current = valuesOf(active.parameters);
      set({
        active: {
          ...active,
          parameters: active.parameters.map((p) => ({
            ...p,
            value: previous[p.id] ?? p.value,
          })),
        },
        undoStack: undoStack.slice(0, -1),
        redoStack: [...redoStack, current],
      });
      scheduleRebuild();
    },

    redo: () => {
      const { active, undoStack, redoStack } = get();
      if (!active || redoStack.length === 0) return;
      const next = redoStack[redoStack.length - 1]!;
      const current = valuesOf(active.parameters);
      set({
        active: {
          ...active,
          parameters: active.parameters.map((p) => ({
            ...p,
            value: next[p.id] ?? p.value,
          })),
        },
        redoStack: redoStack.slice(0, -1),
        undoStack: [...undoStack, current],
      });
      scheduleRebuild();
    },

    clear: () => {
      const { pendingTimer } = get();
      if (pendingTimer) clearTimeout(pendingTimer);
      set({
        active: null,
        rebuilding: false,
        error: null,
        undoStack: [],
        redoStack: [],
        pendingTimer: null,
      });
    },
  };
});
