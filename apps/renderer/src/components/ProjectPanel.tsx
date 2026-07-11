import { useEffect } from "react";

import { useProjectStore } from "../state/projectStore";

export function ProjectPanel() {
  const info = useProjectStore((s) => s.info);
  const dirty = useProjectStore((s) => s.dirty);
  const recent = useProjectStore((s) => s.recent);
  const busy = useProjectStore((s) => s.busy);
  const error = useProjectStore((s) => s.error);
  const createProject = useProjectStore((s) => s.createProject);
  const openProject = useProjectStore((s) => s.openProject);
  const openRecent = useProjectStore((s) => s.openRecent);
  const save = useProjectStore((s) => s.save);
  const closeProject = useProjectStore((s) => s.closeProject);
  const refreshRecent = useProjectStore((s) => s.refreshRecent);

  useEffect(() => {
    void refreshRecent();
  }, [refreshRecent]);

  return (
    <section className="border-b border-surface-border" data-testid="project-panel">
      <div className="flex items-center justify-between px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Project</h2>
        {info && (
          <div className="flex gap-1">
            <button
              onClick={() => void save()}
              disabled={busy || !dirty}
              className="rounded border border-surface-border bg-surface-raised px-2 py-0.5 text-[11px] text-zinc-200 hover:border-accent-dim disabled:opacity-40"
            >
              Save
            </button>
            <button
              onClick={closeProject}
              disabled={busy}
              className="rounded border border-surface-border px-2 py-0.5 text-[11px] text-zinc-500 hover:text-zinc-300"
            >
              Close
            </button>
          </div>
        )}
      </div>

      {error && <p className="px-3 pb-2 text-xs text-red-400">{error}</p>}

      {info ? (
        <div className="px-3 pb-2">
          <p className="flex items-center gap-1.5 text-sm text-zinc-200" title={info.path}>
            <span className="truncate">{info.name}</span>
            {dirty && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" title="Unsaved changes" />}
          </p>
          <p className="truncate text-[10px] text-zinc-600">{info.path}</p>
        </div>
      ) : (
        <div className="space-y-2 px-3 pb-3">
          <div className="flex gap-2">
            <button
              onClick={() => void createProject()}
              disabled={busy}
              className="flex-1 rounded border border-surface-border bg-surface-raised px-2 py-1 text-xs text-zinc-200 hover:border-accent-dim disabled:opacity-50"
            >
              New Project
            </button>
            <button
              onClick={() => void openProject()}
              disabled={busy}
              className="flex-1 rounded border border-surface-border bg-surface-raised px-2 py-1 text-xs text-zinc-200 hover:border-accent-dim disabled:opacity-50"
            >
              Open…
            </button>
          </div>
          {recent.length > 0 && (
            <div>
              <p className="mb-1 text-[10px] uppercase tracking-wider text-zinc-600">Recent</p>
              <ul className="space-y-0.5">
                {recent.slice(0, 6).map((r) => (
                  <li key={r.path}>
                    <button
                      onClick={() => void openRecent(r.path)}
                      disabled={busy}
                      className="w-full truncate rounded px-1.5 py-0.5 text-left text-xs text-zinc-400 hover:bg-surface-raised hover:text-zinc-200"
                      title={r.path}
                    >
                      {r.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
