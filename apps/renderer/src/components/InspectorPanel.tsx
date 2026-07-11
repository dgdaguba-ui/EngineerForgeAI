import { useState } from "react";

import { meshStats } from "../features/viewport/stl";
import { getBridge } from "../ipc/efc";
import { useEngineStore } from "../state/engineStore";
import { useViewportStore } from "../state/viewportStore";

function fmt(n: number): string {
  return n.toFixed(n >= 100 ? 0 : n >= 10 ? 1 : 2);
}

const EXPORT_FILTERS = [
  { name: "3MF (FlashPrint compatible)", extensions: ["3mf"] },
  { name: "STL", extensions: ["stl"] },
  { name: "OBJ", extensions: ["obj"] },
  { name: "PLY", extensions: ["ply"] },
  { name: "glTF binary", extensions: ["glb"] },
  { name: "FBX (via Blender)", extensions: ["fbx"] },
];

/** Blender + export actions for a mesh that has a source file on disk. */
function ObjectActions({ sourcePath, name }: { sourcePath: string; name: string }) {
  const client = useEngineStore((s) => s.client);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const openInBlender = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const result = await client.blenderLaunch(sourcePath);
      setMessage(`Opened in Blender (pid ${result.pid})`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const exportAs = async () => {
    const bridge = getBridge();
    if (!bridge) {
      setMessage("Export requires the desktop shell.");
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const stem = name.replace(/\.[^.]+$/, "");
      const picked = await bridge.invoke("dialog:saveFile", {
        title: "Export as…",
        defaultName: `${stem}.3mf`,
        filters: EXPORT_FILTERS,
      });
      if (picked) {
        const result = await client.convertMesh(sourcePath, picked.path);
        setMessage(`Exported ${result.dstFormat.toUpperCase()} (${result.engine}) → ${picked.name}`);
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="object-actions">
      <dt className="text-xs text-zinc-500">Actions</dt>
      <dd className="mt-1 flex flex-wrap gap-1.5">
        <button
          onClick={() => void openInBlender()}
          disabled={busy}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1 text-xs text-zinc-200 hover:border-accent-dim disabled:opacity-50"
        >
          Open in Blender
        </button>
        <button
          onClick={() => void exportAs()}
          disabled={busy}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1 text-xs text-zinc-200 hover:border-accent-dim disabled:opacity-50"
        >
          Export As…
        </button>
      </dd>
      {message && <dd className="mt-1 break-words text-xs text-zinc-400">{message}</dd>}
    </div>
  );
}

export function InspectorPanel() {
  const objects = useViewportStore((s) => s.objects);
  const selectedId = useViewportStore((s) => s.selectedId);
  const selected = objects.find((o) => o.id === selectedId) ?? null;

  return (
    <section className="flex h-full flex-col">
      <div className="border-b border-surface-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Inspector</h2>
      </div>
      <div className="flex-1 overflow-auto p-3">
        {!selected && <p className="text-xs text-zinc-600">Select an object to inspect it.</p>}
        {selected && <SelectedDetails id={selected.id} />}
      </div>
    </section>
  );
}

function SelectedDetails({ id }: { id: string }) {
  const object = useViewportStore((s) => s.objects.find((o) => o.id === id));
  if (!object) return null;
  const stats = meshStats(object.geometry);
  return (
    <dl className="space-y-2 text-sm">
      <div>
        <dt className="text-xs text-zinc-500">Name</dt>
        <dd className="text-zinc-200">{object.name}</dd>
      </div>
      {object.sourcePath && (
        <div>
          <dt className="text-xs text-zinc-500">Source</dt>
          <dd className="break-all text-xs text-zinc-400">{object.sourcePath}</dd>
        </div>
      )}
      <div>
        <dt className="text-xs text-zinc-500">Dimensions (mm)</dt>
        <dd className="text-zinc-200" data-testid="dims">
          {fmt(stats.size.x)} × {fmt(stats.size.z)} × {fmt(stats.size.y)}
          <span className="ml-1 text-xs text-zinc-500">(X × Y × Z)</span>
        </dd>
      </div>
      <div>
        <dt className="text-xs text-zinc-500">Triangles</dt>
        <dd className="text-zinc-200">{stats.triangles.toLocaleString()}</dd>
      </div>
      {object.sourcePath && (
        <ObjectActions sourcePath={object.sourcePath} name={object.name} />
      )}
    </dl>
  );
}
