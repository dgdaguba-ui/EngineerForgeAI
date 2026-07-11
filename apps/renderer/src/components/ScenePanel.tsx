import { useState } from "react";

import { importStlViaDialog } from "../features/viewport/import";
import { getBridge } from "../ipc/efc";
import { useViewportStore } from "../state/viewportStore";

export function ScenePanel() {
  const objects = useViewportStore((s) => s.objects);
  const selectedId = useViewportStore((s) => s.selectedId);
  const select = useViewportStore((s) => s.select);
  const toggleVisible = useViewportStore((s) => s.toggleVisible);
  const removeObject = useViewportStore((s) => s.removeObject);
  const addMesh = useViewportStore((s) => s.addMesh);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onImport = async () => {
    const bridge = getBridge();
    if (!bridge) {
      setError("File import requires the desktop shell.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const imported = await importStlViaDialog(bridge);
      if (imported) addMesh(imported);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-surface-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Scene</h2>
        <button
          onClick={() => void onImport()}
          disabled={busy}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1 text-xs text-zinc-200 hover:border-accent-dim disabled:opacity-50"
        >
          {busy ? "Importing…" : "Import STL"}
        </button>
      </div>
      {error && <p className="px-3 py-2 text-xs text-red-400">{error}</p>}
      <ul className="flex-1 overflow-auto p-1">
        {objects.length === 0 && (
          <li className="px-2 py-1 text-xs text-zinc-600">No objects loaded</li>
        )}
        {objects.map((o) => (
          <li key={o.id}>
            <div
              role="button"
              tabIndex={0}
              onClick={() => select(o.id)}
              onKeyDown={(e) => e.key === "Enter" && select(o.id)}
              className={`group flex w-full cursor-pointer items-center gap-2 rounded px-2 py-1 text-left text-sm ${
                selectedId === o.id
                  ? "bg-accent-dim/25 text-accent"
                  : "text-zinc-300 hover:bg-surface-raised"
              }`}
            >
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-sm"
                style={{ backgroundColor: o.color }}
              />
              <span className="flex-1 truncate" title={o.sourcePath ?? o.name}>
                {o.name}
              </span>
              <button
                aria-label={o.visible ? "Hide" : "Show"}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleVisible(o.id);
                }}
                className="text-xs text-zinc-500 opacity-0 hover:text-zinc-200 group-hover:opacity-100"
              >
                {o.visible ? "👁" : "🚫"}
              </button>
              <button
                aria-label="Remove"
                onClick={(e) => {
                  e.stopPropagation();
                  removeObject(o.id);
                }}
                className="text-xs text-zinc-500 opacity-0 hover:text-red-400 group-hover:opacity-100"
              >
                ✕
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
