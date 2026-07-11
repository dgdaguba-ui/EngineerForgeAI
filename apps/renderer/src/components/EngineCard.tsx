import { useEffect, useState } from "react";

import type { EngineCapabilities, EngineHealth } from "../engine/types";
import { useEngineStore } from "../state/engineStore";

/**
 * Live view of the engine: health, provider, and capability flags.
 * Proves the full renderer → IPC → supervisor → engine REST path.
 */
export function EngineCard() {
  const status = useEngineStore((s) => s.status);
  const client = useEngineStore((s) => s.client);
  const [health, setHealth] = useState<EngineHealth | null>(null);
  const [caps, setCaps] = useState<EngineCapabilities | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (status?.state !== "running" || !client.connected) {
      setHealth(null);
      setCaps(null);
      return;
    }
    (async () => {
      try {
        const [h, c] = await Promise.all([client.health(), client.capabilities()]);
        if (!cancelled) {
          setHealth(h);
          setCaps(c);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [status?.state, client]);

  return (
    <section className="rounded-lg border border-surface-border bg-surface-panel p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">
        Engine
      </h2>
      {error && <p className="mb-2 text-sm text-red-400">{error}</p>}
      {!health && !error && (
        <p className="text-sm text-zinc-500">
          {status?.state === "running" ? "Loading engine info…" : "Waiting for engine…"}
        </p>
      )}
      {health && (
        <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
          <dt className="text-zinc-500">App</dt>
          <dd>
            {health.app} v{health.version}
          </dd>
          <dt className="text-zinc-500">Python</dt>
          <dd>{health.python}</dd>
          <dt className="text-zinc-500">AI provider</dt>
          <dd>
            <span className={health.provider.available ? "text-emerald-400" : "text-amber-400"}>
              {health.provider.provider}
            </span>{" "}
            <span className="text-zinc-500">— {health.provider.detail}</span>
          </dd>
          {caps && (
            <>
              <dt className="text-zinc-500">Model</dt>
              <dd>{caps.ai.model}</dd>
              <dt className="text-zinc-500">Features</dt>
              <dd className="flex flex-wrap gap-1">
                {Object.entries(caps.features).map(([name, on]) => (
                  <span
                    key={name}
                    className={`rounded px-1.5 py-0.5 text-xs ${
                      on
                        ? "bg-accent-dim/30 text-accent"
                        : "bg-surface-raised text-zinc-600"
                    }`}
                  >
                    {name}
                  </span>
                ))}
              </dd>
            </>
          )}
        </dl>
      )}
    </section>
  );
}
