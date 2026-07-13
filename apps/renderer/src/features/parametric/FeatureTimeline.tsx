/**
 * Feature Timeline — a read-only view of the selected parametric part's
 * ordered Feature Program (the IR recipe the AI and the parameter editor
 * manipulate). Makes the model's construction history visible.
 */
import { useViewportStore } from "../../state/viewportStore";
import { toFeatureView } from "./featureSummary";
import { useParametricStore } from "./parametricStore";

export function FeatureTimeline() {
  const active = useParametricStore((s) => s.active);
  const selectedId = useViewportStore((s) => s.selectedId);

  // only show for the selected parametric part
  if (!active || active.objectId !== selectedId || active.features.length === 0) {
    return null;
  }
  const views = active.features.map(toFeatureView);

  return (
    <section className="border-b border-surface-border" data-testid="feature-timeline">
      <div className="px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          Feature Timeline
        </h2>
      </div>
      <ol className="space-y-0.5 px-3 pb-3">
        {views.map((v, i) => (
          <li
            key={v.id}
            className="flex items-center gap-2 rounded px-1.5 py-1 text-xs hover:bg-surface-raised"
            data-testid={`feature-${v.id}`}
          >
            <span className="w-4 shrink-0 text-right text-[10px] text-zinc-600">{i + 1}</span>
            <span className="w-4 shrink-0 text-center text-accent" aria-hidden>
              {v.glyph}
            </span>
            <span className="flex-1 truncate">
              <span className="text-zinc-200">{v.op}</span>{" "}
              <span className="text-zinc-500">{v.id}</span>
            </span>
            <span className="shrink-0 text-[10px] text-zinc-500" title={v.detail}>
              {v.detail}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
