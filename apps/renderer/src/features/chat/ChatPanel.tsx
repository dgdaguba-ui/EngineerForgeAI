import { useEffect, useRef, useState } from "react";

import { useChatStore, wireChatToEngine, type ChatActionState, type ChatItem } from "./chatStore";

function actionLabel(action: ChatActionState): string {
  if (action.tool === "create_part_from_template") return "Part created";
  if (action.tool === "update_part_parameters") {
    if (action.resolved === "applied") return "Edit applied";
    if (action.resolved === "discarded") return "Edit discarded";
    if (!action.ok) return "Edit failed";
    if (action.diff.length === 0) return "No change";
    return "Edit proposed";
  }
  return action.tool;
}

function DiffCard({
  itemId,
  action,
  actionIndex,
}: {
  itemId: string;
  action: ChatActionState;
  actionIndex: number;
}) {
  const applyProposedEdit = useChatStore((s) => s.applyProposedEdit);
  const discardProposedEdit = useChatStore((s) => s.discardProposedEdit);
  return (
    <div
      className="mt-1.5 rounded border border-accent-dim/40 bg-surface-raised p-2 text-xs"
      data-testid="diff-card"
    >
      <p className="mb-1 text-[10px] uppercase tracking-wide text-zinc-500">
        Proposed parameter change
      </p>
      <ul className="space-y-0.5">
        {action.diff.map((d) => (
          <li key={d.paramId} className="text-zinc-300">
            {d.label}: {d.oldValue}
            {d.unit} → <span className="text-accent">{d.newValue}{d.unit}</span>
          </li>
        ))}
      </ul>
      <div className="mt-2 flex gap-2">
        <button
          onClick={() => void applyProposedEdit(itemId, actionIndex)}
          className="rounded bg-accent-dim px-2 py-0.5 text-[10px] font-medium text-zinc-950 hover:bg-accent"
        >
          Apply
        </button>
        <button
          onClick={() => discardProposedEdit(itemId, actionIndex)}
          className="rounded border border-surface-border px-2 py-0.5 text-[10px] text-zinc-400 hover:text-zinc-200"
        >
          Discard
        </button>
      </div>
    </div>
  );
}

function MessageBubble({ item }: { item: ChatItem }) {
  const isUser = item.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-accent-dim/30 text-zinc-100"
            : "border border-surface-border bg-surface-raised text-zinc-200"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{item.content}</p>
        {item.actions && item.actions.length > 0 && (
          <div className="mt-1.5 flex flex-col gap-1" data-testid="chat-actions">
            {item.actions.map((action, i) =>
              action.tool === "update_part_parameters" &&
              action.pending &&
              !action.resolved &&
              action.diff.length > 0 ? (
                <DiffCard key={`${action.tool}-${i}`} itemId={item.id} action={action} actionIndex={i} />
              ) : (
                <span
                  key={`${action.tool}-${i}`}
                  title={action.summary}
                  className={`w-fit rounded px-1.5 py-0.5 text-[10px] ${
                    action.ok
                      ? "bg-emerald-500/15 text-emerald-400"
                      : "bg-red-500/15 text-red-400"
                  }`}
                >
                  {action.ok ? "✓" : "✗"} {actionLabel(action)}
                </span>
              ),
            )}
          </div>
        )}
        {item.thinking && (
          <details className="mt-1 text-xs text-zinc-500">
            <summary className="cursor-pointer select-none">Reasoning</summary>
            <p className="mt-1 whitespace-pre-wrap">{item.thinking}</p>
          </details>
        )}
        <div className="mt-1 flex items-center gap-2 text-[10px] text-zinc-500">
          {item.status === "sending" && <span className="animate-pulse">sending…</span>}
          {item.status === "queued" && (
            <span className="rounded bg-amber-500/20 px-1 text-amber-400">
              queued — will retry
            </span>
          )}
          {item.status === "error" && (
            <span className="text-red-400" title={item.error}>
              failed: {item.error}
            </span>
          )}
          {item.provider && <span>{item.provider === "stub" ? "offline stub" : item.provider}</span>}
          {item.model && item.model !== "stub" && <span>· {item.model}</span>}
        </div>
      </div>
    </div>
  );
}

export function ChatPanel() {
  const items = useChatStore((s) => s.items);
  const busy = useChatStore((s) => s.busy);
  const send = useChatStore((s) => s.send);
  const flushQueued = useChatStore((s) => s.flushQueued);
  const clear = useChatStore((s) => s.clear);
  const [draft, setDraft] = useState("");
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => wireChatToEngine(), []);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [items.length]);

  const hasQueued = items.some((it) => it.status === "queued");

  const submit = () => {
    const text = draft;
    setDraft("");
    void send(text);
  };

  return (
    <section className="flex h-full flex-col" data-testid="chat-panel">
      <div className="flex items-center justify-between border-b border-surface-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">
          AI Copilot
        </h2>
        <div className="flex items-center gap-2">
          {hasQueued && (
            <button
              onClick={() => void flushQueued()}
              className="rounded border border-amber-600/50 px-2 py-0.5 text-[10px] text-amber-400 hover:bg-amber-500/10"
            >
              Retry queued
            </button>
          )}
          {items.length > 0 && (
            <button
              onClick={clear}
              className="rounded border border-surface-border px-2 py-0.5 text-[10px] text-zinc-500 hover:text-zinc-300"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div ref={listRef} className="flex-1 space-y-2 overflow-auto p-3">
        {items.length === 0 && (
          <div className="space-y-1 text-xs text-zinc-600">
            <p>Ask about strength, materials, printability, or your printer setup.</p>
            <p>
              Without an <code className="text-zinc-500">ANTHROPIC_API_KEY</code> the offline
              stub provider answers deterministically; requests queue and retry automatically
              if the engine or cloud AI is unavailable.
            </p>
          </div>
        )}
        {items.map((item) => (
          <MessageBubble key={item.id} item={item} />
        ))}
      </div>

      <div className="border-t border-surface-border p-2">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          rows={2}
          placeholder="Ask the copilot… (Enter to send, Shift+Enter for newline)"
          className="w-full resize-none rounded border border-surface-border bg-surface-raised p-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-accent-dim focus:outline-none"
          data-testid="chat-input"
        />
        <div className="mt-1 flex justify-end">
          <button
            onClick={submit}
            disabled={busy || draft.trim() === ""}
            className="rounded bg-accent-dim px-3 py-1 text-xs font-medium text-zinc-950 hover:bg-accent disabled:opacity-40"
          >
            {busy ? "Working…" : "Send"}
          </button>
        </div>
      </div>
    </section>
  );
}
