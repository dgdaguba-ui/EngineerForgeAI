/**
 * Chat state with an offline-first delivery queue.
 *
 * Send attempts go to the engine's /ai/chat (which itself falls back to the
 * offline StubProvider when no cloud AI is configured). If the engine is
 * unreachable or the AI provider is temporarily failing (retryable errors),
 * the user's message is kept as `queued` and re-delivered automatically —
 * on a backoff timer and whenever the engine transitions back to running.
 */
import { create } from "zustand";

import { EngineApiError } from "../../engine/client";
import type { ChatMessage, ChatToolAction } from "../../engine/types";
import { useEngineStore } from "../../state/engineStore";
import { useParametricStore } from "../parametric/parametricStore";

export const CHAT_SYSTEM_PROMPT =
  "You are the EngineerForge AI copilot: a mechanical-engineering and 3D-printing " +
  "assistant embedded in a desktop CAD workspace. Be precise and practical; use metric " +
  "units (mm, g, MPa) unless asked otherwise. When discussing strength, printability, " +
  "or materials, state your assumptions. You can CREATE and EDIT parametric parts with " +
  "your tools: use list_part_templates to discover parameters, " +
  "create_part_from_template for design requests, and update_part_parameters to propose " +
  "changes to existing parts. Proposed changes are validated but NOT applied — the user " +
  "reviews and approves or discards them in the UI. Every dimension and mass you state " +
  "must come from tool results — never invent numbers. Created parts stay fully editable " +
  "in the Parameters panel.";

export type ChatItemStatus = "sending" | "sent" | "queued" | "error";

/** A chat-turn action plus, for a pending edit proposal, whether the user has
 * since applied or discarded it. */
export type ChatActionState = ChatToolAction & {
  resolved?: "applied" | "discarded";
};

export interface ChatItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: ChatItemStatus;
  provider?: string;
  model?: string;
  thinking?: string | null;
  error?: string;
  actions?: ChatActionState[];
}

const INITIAL_RETRY_MS = 3000;
const MAX_RETRY_MS = 30_000;

let idCounter = 0;
function newId(): string {
  idCounter += 1;
  return `chat_${idCounter}_${Date.now()}`;
}

interface ChatState {
  items: ChatItem[];
  busy: boolean;
  retryDelayMs: number;
  retryTimer: ReturnType<typeof setTimeout> | null;
  send: (text: string) => Promise<void>;
  flushQueued: () => Promise<void>;
  /** Approve a pending update_part_parameters proposal: apply the diff via a
   * real PATCH and mark the action resolved. */
  applyProposedEdit: (itemId: string, actionIndex: number) => Promise<void>;
  /** Reject a pending proposal without touching the part. */
  discardProposedEdit: (itemId: string, actionIndex: number) => void;
  clear: () => void;
}

/**
 * React to engine tool invocations from a chat turn: created parts load into
 * the viewport (and the open project). Proposed parameter edits are left
 * pending for the user to review in the chat UI — never auto-applied.
 */
async function applyChatActions(actions: ChatToolAction[]): Promise<void> {
  const client = useEngineStore.getState().client;
  const parametric = useParametricStore.getState();
  for (const action of actions) {
    if (!action.ok || !action.partId || action.tool !== "create_part_from_template") continue;
    try {
      const detail = await client.getPart(action.partId);
      parametric.registerCompiledPart(detail);
    } catch {
      // the part summary is already in the chat text; scene sync is best-effort
    }
  }
}

function historyFor(items: ChatItem[], upToId: string): ChatMessage[] {
  const history: ChatMessage[] = [];
  for (const item of items) {
    if (item.id === upToId) {
      history.push({ role: "user", content: item.content });
      break;
    }
    if (item.status === "sent") {
      history.push({ role: item.role, content: item.content });
    }
  }
  return history;
}

export const useChatStore = create<ChatState>((set, get) => {
  function patchItem(id: string, patch: Partial<ChatItem>): void {
    set((s) => ({
      items: s.items.map((it) => (it.id === id ? { ...it, ...patch } : it)),
    }));
  }

  function patchAction(
    itemId: string,
    actionIndex: number,
    patch: Partial<ChatActionState>,
  ): void {
    set((s) => ({
      items: s.items.map((it) => {
        if (it.id !== itemId || !it.actions) return it;
        return {
          ...it,
          actions: it.actions.map((a, i) => (i === actionIndex ? { ...a, ...patch } : a)),
        };
      }),
    }));
  }

  function scheduleRetry(): void {
    const { retryTimer, retryDelayMs } = get();
    if (retryTimer) clearTimeout(retryTimer);
    const timer = setTimeout(() => {
      set({ retryTimer: null });
      void get().flushQueued();
    }, retryDelayMs);
    set({
      retryTimer: timer,
      retryDelayMs: Math.min(retryDelayMs * 2, MAX_RETRY_MS),
    });
  }

  async function deliver(userItemId: string): Promise<boolean> {
    const client = useEngineStore.getState().client;
    const messages = historyFor(get().items, userItemId);
    try {
      const res = await client.chat({ messages, system: CHAT_SYSTEM_PROMPT });
      patchItem(userItemId, { status: "sent" });
      // Insert the reply directly after its user message so conversation order
      // (and the history sent on later turns) stays correct even when other
      // messages were queued behind this one.
      set((s) => {
        const idx = s.items.findIndex((it) => it.id === userItemId);
        const assistant: ChatItem = {
          id: newId(),
          role: "assistant",
          content: res.content,
          status: "sent",
          provider: res.provider,
          model: res.model,
          thinking: res.thinking,
          actions: res.actions,
        };
        const items = [...s.items];
        items.splice(idx + 1, 0, assistant);
        return { items, retryDelayMs: INITIAL_RETRY_MS };
      });
      await applyChatActions(res.actions ?? []);
      return true;
    } catch (e) {
      if (e instanceof EngineApiError && e.retryable) {
        patchItem(userItemId, { status: "queued" });
        scheduleRetry();
      } else {
        patchItem(userItemId, {
          status: "error",
          error: e instanceof Error ? e.message : String(e),
        });
      }
      return false;
    }
  }

  return {
    items: [],
    busy: false,
    retryDelayMs: INITIAL_RETRY_MS,
    retryTimer: null,

    send: async (text: string) => {
      const content = text.trim();
      if (!content) return;
      const id = newId();
      const wasBusy = get().busy;
      set((s) => ({
        items: [
          ...s.items,
          { id, role: "user", content, status: wasBusy ? "queued" : "sending" },
        ],
        busy: true,
      }));
      if (wasBusy) return; // will be delivered by flushQueued in order
      const ok = await deliver(id);
      // on success, drain anything that was queued while we were busy;
      // on retryable failure the backoff timer owns redelivery
      if (ok && get().items.some((it) => it.status === "queued")) {
        await get().flushQueued();
      } else {
        set({ busy: false });
      }
    },

    flushQueued: async () => {
      const { retryTimer } = get();
      if (retryTimer) {
        clearTimeout(retryTimer);
        set({ retryTimer: null });
      }
      set({ busy: true });
      // deliver queued user messages strictly in order; stop on failure
      for (;;) {
        const next = get().items.find(
          (it) => it.role === "user" && it.status === "queued",
        );
        if (!next) break;
        patchItem(next.id, { status: "sending" });
        const ok = await deliver(next.id);
        if (!ok) break;
      }
      set({ busy: false });
    },

    applyProposedEdit: async (itemId: string, actionIndex: number) => {
      const item = get().items.find((it) => it.id === itemId);
      const action = item?.actions?.[actionIndex];
      if (!action || !action.partId || action.diff.length === 0) return;
      const values = Object.fromEntries(action.diff.map((d) => [d.paramId, d.newValue]));
      try {
        await useParametricStore.getState().applyDiff(action.partId, values);
        patchAction(itemId, actionIndex, { resolved: "applied" });
      } catch (e) {
        // leave the proposal unresolved so the user can retry; mark it failed
        patchAction(itemId, actionIndex, {
          ok: false,
          summary: e instanceof Error ? e.message : String(e),
        });
      }
    },

    discardProposedEdit: (itemId: string, actionIndex: number) => {
      patchAction(itemId, actionIndex, { resolved: "discarded" });
    },

    clear: () => {
      const { retryTimer } = get();
      if (retryTimer) clearTimeout(retryTimer);
      set({
        items: [],
        busy: false,
        retryTimer: null,
        retryDelayMs: INITIAL_RETRY_MS,
      });
    },
  };
});

/**
 * Re-deliver queued messages when the engine comes back. Called once from the
 * ChatPanel mount; returns an unsubscribe function.
 */
export function wireChatToEngine(): () => void {
  let prevState = useEngineStore.getState().status?.state;
  return useEngineStore.subscribe((s) => {
    const state = s.status?.state;
    if (state === "running" && prevState !== "running") {
      const hasQueued = useChatStore
        .getState()
        .items.some((it) => it.status === "queued");
      if (hasQueued) void useChatStore.getState().flushQueued();
    }
    prevState = state;
  });
}
