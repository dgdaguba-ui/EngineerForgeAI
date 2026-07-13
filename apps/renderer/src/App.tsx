import { useEffect } from "react";

import { EngineCard } from "./components/EngineCard";
import { InspectorPanel } from "./components/InspectorPanel";
import { ProjectPanel } from "./components/ProjectPanel";
import { ScenePanel } from "./components/ScenePanel";
import { StatusBar } from "./components/StatusBar";
import { ChatPanel } from "./features/chat/ChatPanel";
import { FlashforgePanel } from "./features/flashforge/FlashforgePanel";
import { FeatureTimeline } from "./features/parametric/FeatureTimeline";
import { ParametricPanel } from "./features/parametric/ParametricPanel";
import { Viewport } from "./features/viewport/Viewport";
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
            Phase 2
          </span>
        </div>
        <StatusBar
          status={status}
          bridgeAvailable={bridgeAvailable}
          onRestart={() => void restart()}
        />
      </header>

      <main className="flex min-h-0 flex-1">
        <aside className="flex w-72 shrink-0 flex-col border-r border-surface-border bg-surface-panel">
          <ProjectPanel />
          <div className="min-h-0 flex-1 overflow-auto">
            <ScenePanel />
            <FlashforgePanel />
          </div>
          <div className="border-t border-surface-border p-2">
            <EngineCard />
          </div>
        </aside>

        <section className="min-w-0 flex-1">
          <Viewport />
        </section>

        <aside className="flex w-80 shrink-0 flex-col border-l border-surface-border bg-surface-panel">
          <div className="max-h-[55%] shrink-0 overflow-auto border-b border-surface-border">
            <ParametricPanel />
            <FeatureTimeline />
            <InspectorPanel />
          </div>
          <div className="min-h-0 flex-1">
            <ChatPanel />
          </div>
        </aside>
      </main>
    </div>
  );
}
