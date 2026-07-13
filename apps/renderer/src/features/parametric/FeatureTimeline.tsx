/**
 * Feature Timeline — an interactive view of the selected parametric part's
 * ordered Feature Program (the IR recipe the AI and the parameter editor
 * manipulate). Features can be reordered (▲▼) and, when expanded, have their
 * scalar fields edited in place; each change recompiles through the engine.
 */
import { useEffect, useState } from "react";

import type { IrFeature } from "../../engine/types";
import { useViewportStore } from "../../state/viewportStore";
import { editableFields } from "./featureFields";
import { toFeatureView } from "./featureSummary";
import { useParametricStore } from "./parametricStore";

function ExprInput({
  value,
  disabled,
  onCommit,
}: {
  value: string;
  disabled: boolean;
  onCommit: (v: string) => void;
}) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  const commit = () => {
    const t = draft.trim();
    if (t && t !== value) onCommit(t);
  };
  return (
    <input
      value={draft}
      disabled={disabled}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          commit();
        }
      }}
      className="w-20 rounded border border-surface-border bg-surface px-1 py-0.5 text-[11px] text-zinc-200 focus:border-accent-dim focus:outline-none disabled:opacity-50"
    />
  );
}

function FeatureEditor({
  feature,
  disabled,
  onEdit,
}: {
  feature: IrFeature;
  disabled: boolean;
  onEdit: (fields: Record<string, unknown>) => void;
}) {
  const fields = editableFields(feature);
  if (fields.length === 0) {
    return (
      <p className="px-7 pb-2 text-[10px] text-zinc-600">
        No inline-editable fields for this feature.
      </p>
    );
  }
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 px-7 pb-2" data-testid={`editor-${feature.id}`}>
      {fields.map((f) => (
        <label key={f.key} className="flex items-center gap-1 text-[10px] text-zinc-500">
          <span className="uppercase tracking-wide">{f.label}</span>
          {f.kind === "enum" ? (
            <select
              value={f.value}
              disabled={disabled}
              onChange={(e) => onEdit({ [f.key]: e.target.value })}
              aria-label={`${feature.id} ${f.label}`}
              className="rounded border border-surface-border bg-surface px-1 py-0.5 text-[11px] text-zinc-200 focus:border-accent-dim focus:outline-none disabled:opacity-50"
            >
              {f.options!.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          ) : (
            <ExprInput
              value={f.value}
              disabled={disabled}
              onCommit={(v) => onEdit({ [f.key]: v })}
            />
          )}
        </label>
      ))}
    </div>
  );
}

export function FeatureTimeline() {
  const active = useParametricStore((s) => s.active);
  const moveFeature = useParametricStore((s) => s.moveFeature);
  const editFeature = useParametricStore((s) => s.editFeature);
  const rebuilding = useParametricStore((s) => s.rebuilding);
  const selectedId = useViewportStore((s) => s.selectedId);
  const [expanded, setExpanded] = useState<string | null>(null);

  // only show for the selected parametric part
  if (!active || active.objectId !== selectedId || active.features.length === 0) {
    return null;
  }
  const last = active.features.length - 1;

  return (
    <section className="border-b border-surface-border" data-testid="feature-timeline">
      <div className="px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          Feature Timeline
        </h2>
      </div>
      <ol className="space-y-0.5 px-3 pb-3">
        {active.features.map((feature, i) => {
          const v = toFeatureView(feature);
          const isOpen = expanded === feature.id;
          return (
            <li key={feature.id} data-testid={`feature-${feature.id}`}>
              <div className="group flex items-center gap-2 rounded px-1.5 py-1 text-xs hover:bg-surface-raised">
                <span className="w-4 shrink-0 text-right text-[10px] text-zinc-600">
                  {i + 1}
                </span>
                <span className="w-4 shrink-0 text-center text-accent" aria-hidden>
                  {v.glyph}
                </span>
                <button
                  type="button"
                  onClick={() => setExpanded(isOpen ? null : feature.id)}
                  aria-expanded={isOpen}
                  className="flex flex-1 items-center gap-1 truncate text-left"
                >
                  <span className="text-[9px] text-zinc-600">{isOpen ? "▾" : "▸"}</span>
                  <span className="truncate">
                    <span className="text-zinc-200">{v.op}</span>{" "}
                    <span className="text-zinc-500">{v.id}</span>
                  </span>
                </button>
                <span className="shrink-0 text-[10px] text-zinc-500" title={v.detail}>
                  {v.detail}
                </span>
                <span className="flex shrink-0 gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    type="button"
                    aria-label={`Move ${v.id} up`}
                    disabled={i === 0 || rebuilding}
                    onClick={() => void moveFeature(v.id, -1)}
                    className="rounded px-1 text-[10px] text-zinc-400 hover:bg-surface-border hover:text-zinc-100 disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    aria-label={`Move ${v.id} down`}
                    disabled={i === last || rebuilding}
                    onClick={() => void moveFeature(v.id, 1)}
                    className="rounded px-1 text-[10px] text-zinc-400 hover:bg-surface-border hover:text-zinc-100 disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    ▼
                  </button>
                </span>
              </div>
              {isOpen && (
                <FeatureEditor
                  feature={feature}
                  disabled={rebuilding}
                  onEdit={(fields) => void editFeature(feature.id, fields)}
                />
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
