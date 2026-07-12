/**
 * Parameter editor — the parametric heart of the MVP. Shows editable
 * parameters for the selected parametric part with live rebuild, undo/redo,
 * mass properties, and DFM warnings; offers template creation otherwise.
 */
import { useEffect, useState } from "react";

import type { IrParameter, TemplateInfo } from "../../engine/types";
import { useEngineStore } from "../../state/engineStore";
import { useViewportStore } from "../../state/viewportStore";
import { useParametricStore } from "./parametricStore";

function ParamRow({
  param,
  onChange,
  disabled,
}: {
  param: IrParameter;
  onChange: (value: number) => void;
  disabled: boolean;
}) {
  const step = param.step ?? (param.integer ? 1 : 0.5);
  const parse = (raw: string): number | null => {
    const n = Number(raw);
    if (Number.isNaN(n)) return null;
    return param.integer ? Math.round(n) : n;
  };
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between gap-2">
        <label className="text-xs text-zinc-400" htmlFor={`param-${param.id}`}>
          {param.label}
          {param.unit && <span className="ml-1 text-zinc-600">({param.unit})</span>}
        </label>
        <input
          id={`param-${param.id}`}
          type="number"
          value={param.value}
          min={param.min ?? undefined}
          max={param.max ?? undefined}
          step={step}
          disabled={disabled}
          onChange={(e) => {
            const value = parse(e.target.value);
            if (value !== null) onChange(value);
          }}
          className="w-20 rounded border border-surface-border bg-surface-raised px-1.5 py-0.5 text-right text-xs text-zinc-100 disabled:opacity-50"
          data-testid={`param-input-${param.id}`}
        />
      </div>
      {param.min !== null && param.max !== null && (
        <input
          type="range"
          value={param.value}
          min={param.min}
          max={param.max}
          step={step}
          disabled={disabled}
          onChange={(e) => {
            const value = parse(e.target.value);
            if (value !== null) onChange(value);
          }}
          className="h-1 w-full cursor-pointer accent-cyan-500"
          aria-label={`${param.label} slider`}
        />
      )}
    </div>
  );
}

export function ParametricPanel() {
  const engineState = useEngineStore((s) => s.status?.state);
  const client = useEngineStore((s) => s.client);
  const selectedId = useViewportStore((s) => s.selectedId);
  const selected = useViewportStore((s) =>
    s.objects.find((o) => o.id === s.selectedId),
  );

  const active = useParametricStore((s) => s.active);
  const rebuilding = useParametricStore((s) => s.rebuilding);
  const error = useParametricStore((s) => s.error);
  const undoDepth = useParametricStore((s) => s.undoStack.length);
  const redoDepth = useParametricStore((s) => s.redoStack.length);
  const createFromTemplate = useParametricStore((s) => s.createFromTemplate);
  const adopt = useParametricStore((s) => s.adopt);
  const setParam = useParametricStore((s) => s.setParam);
  const undo = useParametricStore((s) => s.undo);
  const redo = useParametricStore((s) => s.redo);

  const [templates, setTemplates] = useState<TemplateInfo[]>([]);

  useEffect(() => {
    if (engineState !== "running" || templates.length > 0 || !client.connected) return;
    void client
      .listTemplates()
      .then(setTemplates)
      .catch(() => undefined);
  }, [engineState, client, templates.length]);

  // selecting a different parametric object re-adopts its engine part
  useEffect(() => {
    if (
      selected?.parametricPartId &&
      active?.objectId !== selected.id &&
      client.connected
    ) {
      const objectId = selected.id;
      const projectPartId = selected.partId;
      void client
        .getPart(selected.parametricPartId)
        .then((detail) => adopt(detail, objectId, projectPartId))
        .catch(() => undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const showEditor = Boolean(selected?.parametricPartId && active?.objectId === selected?.id);

  return (
    <section className="border-b border-surface-border" data-testid="parametric-panel">
      <div className="flex items-center justify-between px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          Parameters
        </h2>
        {showEditor && (
          <div className="flex items-center gap-1">
            {rebuilding && (
              <span className="animate-pulse text-[10px] text-accent">rebuilding…</span>
            )}
            <button
              onClick={undo}
              disabled={undoDepth === 0}
              title="Undo parameter change"
              className="rounded border border-surface-border px-1.5 py-0.5 text-[10px] text-zinc-400 hover:text-zinc-100 disabled:opacity-30"
            >
              ↩
            </button>
            <button
              onClick={redo}
              disabled={redoDepth === 0}
              title="Redo"
              className="rounded border border-surface-border px-1.5 py-0.5 text-[10px] text-zinc-400 hover:text-zinc-100 disabled:opacity-30"
            >
              ↪
            </button>
          </div>
        )}
      </div>

      <div className="space-y-2 px-3 pb-3">
        {error && <p className="text-xs text-red-400">{error}</p>}

        {showEditor && active ? (
          <>
            <div className="space-y-2" data-testid="param-editor">
              {active.parameters.map((param) => (
                <ParamRow
                  key={param.id}
                  param={param}
                  disabled={false}
                  onChange={(value) => setParam(param.id, value)}
                />
              ))}
            </div>
            <dl className="grid grid-cols-2 gap-x-3 gap-y-0.5 border-t border-surface-border pt-2 text-[11px]">
              <dt className="text-zinc-500">Volume</dt>
              <dd data-testid="part-volume">{active.massProps.volumeCm3.toFixed(2)} cm³</dd>
              {active.massProps.massG !== null && (
                <>
                  <dt className="text-zinc-500">Mass (solid)</dt>
                  <dd>{active.massProps.massG.toFixed(1)} g</dd>
                </>
              )}
              <dt className="text-zinc-500">Bounds</dt>
              <dd>
                {active.massProps.bboxMm.x}×{active.massProps.bboxMm.y}×
                {active.massProps.bboxMm.z} mm
              </dd>
            </dl>
            {active.warnings.length > 0 && (
              <ul className="space-y-0.5">
                {active.warnings.map((w) => (
                  <li key={w} className="text-[11px] leading-tight text-amber-400">
                    ⚠ {w}
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <div className="space-y-1.5">
            <p className="text-xs text-zinc-600">
              {engineState === "running"
                ? "Create a parametric part, or select one to edit its parameters."
                : "Waiting for the engine…"}
            </p>
            {templates.map((t) => (
              <button
                key={t.id}
                onClick={() => void createFromTemplate(t.id)}
                disabled={rebuilding || engineState !== "running"}
                title={t.description}
                className="w-full rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-left text-xs text-zinc-200 hover:border-accent-dim disabled:opacity-50"
                data-testid={`new-part-${t.id}`}
              >
                + New {t.name}
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
