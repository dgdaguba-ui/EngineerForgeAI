import { useEffect } from "react";

import { EngineCard } from "./components/EngineCard";
import { StatusBar } from "./components/StatusBar";
import { useEngineStore } from "./state/engineStore";

export default function App() {
  const init = useEngineStore((s) => s.init);
  const status = useEngineStore((s) => s.status);
  const bridgeAvailable = useEngineStore((s) => s.bridgeAvailable);
  const restart = useEngineStore((s) => s.restart);

  useEffect(() => {
    void init();
  }, [init]);

  return (
    <div className="flex h-full flex-col">
      <header className="flex h-11 shrink-0 items-center justify-between border-b border-surface-border bg-surface-panel px-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold tracking-tight text-zinc-100">
            EngineerForge <span className="text-accent">AI</span>
          </span>
          <span className="rounded bg-surface-raised px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-zinc-500">
            Phase 0
          </span>
        </div>
        <StatusBar status={status} bridgeAvailable={bridgeAvailable} onRestart={() => void restart()} />
      </header>

      <main className="grid flex-1 grid-cols-1 gap-4 overflow-auto p-4 lg:grid-cols-2">
        <EngineCard />
      </main>
    </div>
  );
}
