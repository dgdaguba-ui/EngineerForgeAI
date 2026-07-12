/**
 * Flashforge workspace state: printer selection, material slots, per-object
 * slot assignments, and compatibility analysis.
 *
 * When a project is open, printer/slots/assignments are mirrored into the
 * project document (persisted on save); scene-only sessions keep them local.
 */
import { create } from "zustand";

import type { MaterialSlot } from "@efc/ipc-contracts";

import type { CompatibilityReport, Material, PrinterProfile } from "../../engine/types";
import { useEngineStore } from "../../state/engineStore";
import { useProjectStore } from "../../state/projectStore";
import { useViewportStore } from "../../state/viewportStore";

interface FlashforgeState {
  printers: PrinterProfile[];
  materials: Material[];
  loaded: boolean;
  loadError: string | null;
  printerId: string | null;
  slots: MaterialSlot[];
  /** viewport object id → slot index */
  assignments: Record<string, number>;
  compat: CompatibilityReport | null;

  load: () => Promise<void>;
  selectPrinter: (printerId: string | null) => void;
  setSlotMaterial: (index: number, materialId: string | null) => void;
  setSlotColor: (index: number, colorHex: string | null) => void;
  assignObject: (objectId: string, slotIndex: number | null) => void;
  refreshCompat: () => Promise<void>;
  /** Adopt printer/slots/assignments from the open project document. */
  syncFromProject: () => void;
}

function resizeSlots(slots: MaterialSlot[], count: number): MaterialSlot[] {
  const next: MaterialSlot[] = [];
  for (let i = 0; i < count; i++) {
    next.push(slots[i] ?? { index: i, materialId: null, colorHex: null });
  }
  return next;
}

/** Mirror printer/slots into the project doc when one is open. */
function pushDocPrinterState(printerId: string | null, slots: MaterialSlot[]): void {
  const project = useProjectStore.getState();
  if (!project.doc) return;
  project.updateDoc((doc) => ({
    ...doc,
    printerProfileId: printerId,
    materialSlots: slots,
  }));
}

export const useFlashforgeStore = create<FlashforgeState>((set, get) => ({
  printers: [],
  materials: [],
  loaded: false,
  loadError: null,
  printerId: null,
  slots: [],
  assignments: {},
  compat: null,

  load: async () => {
    const client = useEngineStore.getState().client;
    if (!client.connected) return;
    try {
      const [printers, materials] = await Promise.all([client.printers(), client.materials()]);
      set({ printers, materials, loaded: true, loadError: null });
    } catch (e) {
      set({ loadError: e instanceof Error ? e.message : String(e) });
    }
  },

  selectPrinter: (printerId) => {
    const profile = get().printers.find((p) => p.id === printerId) ?? null;
    const slots = profile ? resizeSlots(get().slots, profile.materialSlots) : [];
    set({ printerId: profile?.id ?? null, slots, compat: null });
    useViewportStore.getState().setBuildVolume(profile ? profile.buildVolume : null);
    pushDocPrinterState(profile?.id ?? null, slots);
  },

  setSlotMaterial: (index, materialId) => {
    const material = get().materials.find((m) => m.id === materialId) ?? null;
    const slots = get().slots.map((slot) =>
      slot.index === index
        ? {
            ...slot,
            materialId,
            // adopt the material's natural color unless the user customized one
            colorHex: slot.colorHex ?? material?.colorHex ?? null,
          }
        : slot,
    );
    set({ slots, compat: null });
    pushDocPrinterState(get().printerId, slots);
  },

  setSlotColor: (index, colorHex) => {
    const slots = get().slots.map((slot) =>
      slot.index === index ? { ...slot, colorHex } : slot,
    );
    set({ slots });
    pushDocPrinterState(get().printerId, slots);
  },

  assignObject: (objectId, slotIndex) => {
    const assignments = { ...get().assignments };
    if (slotIndex === null) {
      delete assignments[objectId];
    } else {
      assignments[objectId] = slotIndex;
    }
    set({ assignments });

    // persist by partId when the object belongs to the open project
    const project = useProjectStore.getState();
    const object = useViewportStore.getState().objects.find((o) => o.id === objectId);
    if (project.doc && object?.partId) {
      const partId = object.partId;
      project.updateDoc((doc) => {
        const partSlotAssignments = { ...doc.partSlotAssignments };
        if (slotIndex === null) {
          delete partSlotAssignments[partId];
        } else {
          partSlotAssignments[partId] = slotIndex;
        }
        return { ...doc, partSlotAssignments };
      });
    }
  },

  refreshCompat: async () => {
    const client = useEngineStore.getState().client;
    const ids = [
      ...new Set(
        get()
          .slots.map((s) => s.materialId)
          .filter((id): id is string => id !== null),
      ),
    ];
    if (ids.length < 2 || !client.connected) {
      set({ compat: null });
      return;
    }
    try {
      set({ compat: await client.materialCompatibility(ids) });
    } catch {
      set({ compat: null });
    }
  },

  syncFromProject: () => {
    const doc = useProjectStore.getState().doc;
    if (!doc) {
      set({ printerId: null, slots: [], assignments: {}, compat: null });
      useViewportStore.getState().setBuildVolume(null);
      return;
    }
    const profile = get().printers.find((p) => p.id === doc.printerProfileId) ?? null;
    const slots = profile
      ? resizeSlots(doc.materialSlots, profile.materialSlots)
      : doc.materialSlots;
    // map part-keyed assignments back to scene object ids
    const assignments: Record<string, number> = {};
    for (const object of useViewportStore.getState().objects) {
      if (object.partId && doc.partSlotAssignments[object.partId] !== undefined) {
        assignments[object.id] = doc.partSlotAssignments[object.partId]!;
      }
    }
    set({ printerId: profile?.id ?? null, slots, assignments, compat: null });
    useViewportStore.getState().setBuildVolume(profile ? profile.buildVolume : null);
  },
}));
