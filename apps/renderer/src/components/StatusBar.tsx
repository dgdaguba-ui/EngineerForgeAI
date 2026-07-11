import type { EngineStatus } from "@efc/ipc-contracts";

const stateStyles: Record<EngineStatus["state"], { dot: string; label: string }> = {
  running: { dot: "bg-emerald-400", label: "Engine running" },
  starting: { dot: "bg-amber-400 animate-pulse", label: "Engine starting…" },
  restarting: { dot: "bg-amber-400 animate-pulse", label: "Engine restarting…" },
  stopped: { dot: "bg-zinc-500", label: "Engine stopped" },
  failed: { dot: "bg-red-500", label: "Engine failed" },
};

export interface StatusBarProps {
  status: EngineStatus | null;
  bridgeAvailable: boolean;
  onRestart?: () => void;
}

export function StatusBar({ status, bridgeAvailable, onRestart }: StatusBarProps) {
  if (!bridgeAvailable) {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-400" data-testid="status-bar">
        <span className="h-2 w-2 rounded-full bg-zinc-600" />
        Browser mode — desktop shell not detected
      </div>
    );
  }
  const info = status ? stateStyles[status.state] : { dot: "bg-zinc-600", label: "Connecting…" };
  return (
    <div className="flex items-center gap-3 text-xs text-zinc-300" data-testid="status-bar">
      <span className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${info.dot}`} />
        {info.label}
      </span>
      {status?.baseUrl && status.state === "running" && (
        <span className="text-zinc-500">{status.baseUrl}</span>
      )}
      {status?.state === "failed" && (
        <>
          <span className="max-w-96 truncate text-red-400" title={status.message}>
            {status.message}
          </span>
          {onRestart && (
            <button
              onClick={onRestart}
              className="rounded border border-surface-border bg-surface-raised px-2 py-0.5 text-zinc-200 hover:border-accent-dim"
            >
              Retry
            </button>
          )}
        </>
      )}
    </div>
  );
}
