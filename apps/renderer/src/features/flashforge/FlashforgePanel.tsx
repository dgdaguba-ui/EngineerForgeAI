import { useEffect, useState } from "react";

import type { PurgeEstimate, UsageEstimate } from "../../engine/types";
import { getBridge } from "../../ipc/efc";
import { useEngineStore } from "../../state/engineStore";
import { useProjectStore } from "../../state/projectStore";
import { combinedBoundingBox, useViewportStore } from "../../state/viewportStore";
import { useFlashforgeStore } from "./flashforgeStore";

const LEVEL_STYLES: Record<string, string> = {
  ok: "text-emerald-400",
  caution: "text-amber-400",
  incompatible: "text-red-400",
};

export function FlashforgePanel() {
  const engineState = useEngineStore((s) => s.status?.state);
  const client = useEngineStore((s) => s.client);
  const projectId = useProjectStore((s) => s.info?.id ?? null);
  const objects = useViewportStore((s) => s.objects);

  const store = useFlashforgeStore();
  const [estimate, setEstimate] = useState<UsageEstimate | null>(null);
  const [purge, setPurge] = useState<PurgeEstimate | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // load catalogs once the engine is up; re-sync when the project changes
  useEffect(() => {
    if (engineState === "running" && !store.loaded) void store.load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [engineState, store.loaded]);

  useEffect(() => {
    if (store.loaded) store.syncFromProject();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, store.loaded]);

  useEffect(() => {
    void store.refreshCompat();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.slots]);

  const printer = store.printers.find((p) => p.id === store.printerId) ?? null;
  const selectedId = useViewportStore((s) => s.selectedId);
  const selected = objects.find((o) => o.id === selectedId) ?? null;

  const runEstimate = async () => {
    if (!selected?.sourcePath) return;
    const slotIndex = store.assignments[selected.id];
    const slot = slotIndex !== undefined ? store.slots[slotIndex] : undefined;
    if (!slot?.materialId) {
      setMessage("Assign this part to a material slot first.");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      setEstimate(
        await client.printEstimate({
          meshPath: selected.sourcePath,
          materialId: slot.materialId,
          printerId: store.printerId,
        }),
      );
      // purge estimate when 2+ distinct materials are assigned
      const activeIds = [
        ...new Set(
          Object.values(store.assignments)
            .map((i) => store.slots[i]?.materialId)
            .filter((id): id is string => Boolean(id)),
        ),
      ];
      const bbox = combinedBoundingBox(objects);
      if (store.printerId && activeIds.length >= 2 && bbox) {
        const heightMm = bbox.max.y - bbox.min.y;
        setPurge(
          await client.purgeEstimate({
            printerId: store.printerId,
            materialIds: activeIds,
            heightMm: Math.max(heightMm, 1),
          }),
        );
      } else {
        setPurge(null);
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const exportJob = async () => {
    const bridge = getBridge();
    if (!bridge) {
      setMessage("Export requires the desktop shell.");
      return;
    }
    const exportable = objects.filter((o) => o.visible && o.sourcePath);
    if (exportable.length === 0) {
      setMessage("Nothing to export — import at least one model.");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const picked = await bridge.invoke("dialog:saveFile", {
        title: "Export FlashPrint 3MF",
        defaultName: "print-job.3mf",
        filters: [{ name: "3MF", extensions: ["3mf"] }],
      });
      if (picked) {
        const parts = exportable.map((o) => {
          const slotIndex = store.assignments[o.id];
          const slot = slotIndex !== undefined ? store.slots[slotIndex] : undefined;
          const material = store.materials.find((m) => m.id === slot?.materialId);
          return {
            meshPath: o.sourcePath as string,
            name: o.name,
            colorHex: slot?.colorHex ?? material?.colorHex ?? null,
            materialName: material?.name ?? null,
          };
        });
        const result = await client.export3mf(parts, picked.path);
        setMessage(`Exported ${result.parts} part(s) → ${picked.name} (open in FlashPrint)`);
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="border-t border-surface-border" data-testid="flashforge-panel">
      <div className="flex items-center justify-between px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          Flashforge
        </h2>
        <button
          onClick={() => void exportJob()}
          disabled={busy || objects.length === 0}
          className="rounded border border-surface-border bg-surface-raised px-2 py-0.5 text-[11px] text-zinc-200 hover:border-accent-dim disabled:opacity-40"
        >
          Export 3MF
        </button>
      </div>

      <div className="space-y-3 px-3 pb-3 text-sm">
        {store.loadError && <p className="text-xs text-red-400">{store.loadError}</p>}
        {!store.loaded && !store.loadError && (
          <p className="text-xs text-zinc-600">Waiting for engine catalogs…</p>
        )}

        {store.loaded && (
          <>
            <div>
              <label className="mb-1 block text-[10px] uppercase tracking-wider text-zinc-600">
                Printer
              </label>
              <select
                value={store.printerId ?? ""}
                onChange={(e) => store.selectPrinter(e.target.value || null)}
                className="w-full rounded border border-surface-border bg-surface-raised px-2 py-1 text-xs text-zinc-200"
                data-testid="printer-select"
              >
                <option value="">— none —</option>
                {store.printers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              {printer && (
                <p className="mt-1 text-[10px] text-zinc-600">
                  {printer.buildVolume.x}×{printer.buildVolume.y}×{printer.buildVolume.z} mm ·{" "}
                  {printer.materialSlots} slot{printer.materialSlots > 1 ? "s" : ""} ·{" "}
                  {printer.multiMaterialSystem}
                </p>
              )}
            </div>

            {store.slots.length > 0 && (
              <div>
                <p className="mb-1 text-[10px] uppercase tracking-wider text-zinc-600">
                  Material slots
                </p>
                <div className="space-y-1">
                  {store.slots.map((slot) => (
                    <div key={slot.index} className="flex items-center gap-1.5">
                      <span className="w-4 text-[10px] text-zinc-600">{slot.index + 1}</span>
                      <select
                        value={slot.materialId ?? ""}
                        onChange={(e) =>
                          store.setSlotMaterial(slot.index, e.target.value || null)
                        }
                        className="min-w-0 flex-1 rounded border border-surface-border bg-surface-raised px-1.5 py-1 text-xs text-zinc-200"
                        data-testid={`slot-material-${slot.index}`}
                      >
                        <option value="">— empty —</option>
                        {store.materials.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name}
                          </option>
                        ))}
                      </select>
                      <input
                        type="color"
                        value={slot.colorHex ?? "#b0b0b0"}
                        onChange={(e) => store.setSlotColor(slot.index, e.target.value)}
                        className="h-6 w-7 cursor-pointer rounded border border-surface-border bg-transparent"
                        aria-label={`Slot ${slot.index + 1} color`}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {store.compat && store.compat.pairs.length > 0 && (
              <div data-testid="compat-report">
                <p className="mb-1 text-[10px] uppercase tracking-wider text-zinc-600">
                  Compatibility{" "}
                  <span className={LEVEL_STYLES[store.compat.worst]}>
                    ({store.compat.worst})
                  </span>
                </p>
                <ul className="space-y-1">
                  {store.compat.pairs
                    .filter((pair) => pair.level !== "ok")
                    .map((pair) => (
                      <li key={`${pair.a}-${pair.b}`} className="text-[11px] leading-tight">
                        <span className={LEVEL_STYLES[pair.level]}>
                          {pair.a} + {pair.b}:
                        </span>{" "}
                        <span className="text-zinc-500">{pair.reasons[0]}</span>
                      </li>
                    ))}
                  {store.compat.worst === "ok" && (
                    <li className="text-[11px] text-emerald-400">All pairings compatible.</li>
                  )}
                </ul>
              </div>
            )}

            {objects.length > 0 && store.slots.length > 0 && (
              <div>
                <p className="mb-1 text-[10px] uppercase tracking-wider text-zinc-600">
                  Part assignments
                </p>
                <div className="space-y-1">
                  {objects.map((o) => (
                    <div key={o.id} className="flex items-center gap-1.5">
                      <span className="min-w-0 flex-1 truncate text-xs text-zinc-300">
                        {o.name}
                      </span>
                      <select
                        value={store.assignments[o.id] ?? ""}
                        onChange={(e) =>
                          store.assignObject(
                            o.id,
                            e.target.value === "" ? null : Number(e.target.value),
                          )
                        }
                        className="rounded border border-surface-border bg-surface-raised px-1.5 py-0.5 text-[11px] text-zinc-200"
                        data-testid={`assign-${o.id}`}
                      >
                        <option value="">—</option>
                        {store.slots.map((slot) => (
                          <option key={slot.index} value={slot.index}>
                            Slot {slot.index + 1}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selected?.sourcePath && (
              <div>
                <button
                  onClick={() => void runEstimate()}
                  disabled={busy}
                  className="rounded border border-surface-border bg-surface-raised px-2 py-1 text-xs text-zinc-200 hover:border-accent-dim disabled:opacity-50"
                >
                  Estimate usage ({selected.name})
                </button>
                {estimate && (
                  <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px]">
                    <dt className="text-zinc-500">Volume</dt>
                    <dd>{estimate.volumeCm3.toFixed(1)} cm³</dd>
                    <dt className="text-zinc-500">Mass</dt>
                    <dd>{estimate.massG.toFixed(1)} g</dd>
                    <dt className="text-zinc-500">Cost</dt>
                    <dd>
                      {estimate.cost.toFixed(2)} {estimate.currency}
                    </dd>
                    <dt className="text-zinc-500">Fits printer</dt>
                    <dd
                      className={
                        estimate.fitsPrinter === false ? "text-red-400" : "text-emerald-400"
                      }
                    >
                      {estimate.fitsPrinter === null ? "n/a" : estimate.fitsPrinter ? "yes" : "NO"}
                    </dd>
                    {!estimate.watertight && (
                      <>
                        <dt className="text-amber-400">Mesh</dt>
                        <dd className="text-amber-400">not watertight (upper bound)</dd>
                      </>
                    )}
                    {purge && purge.toolChanges > 0 && (
                      <>
                        <dt className="text-zinc-500">Purge waste</dt>
                        <dd>
                          ~{purge.purgeMassG.toFixed(1)} g ({purge.toolChanges} changes)
                        </dd>
                      </>
                    )}
                  </dl>
                )}
              </div>
            )}
          </>
        )}

        {message && <p className="break-words text-xs text-zinc-400">{message}</p>}
      </div>
    </section>
  );
}
