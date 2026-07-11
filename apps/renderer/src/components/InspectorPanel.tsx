import { meshStats } from "../features/viewport/stl";
import { useViewportStore } from "../state/viewportStore";

function fmt(n: number): string {
  return n.toFixed(n >= 100 ? 0 : n >= 10 ? 1 : 2);
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
    </dl>
  );
}
