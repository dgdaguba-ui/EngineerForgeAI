import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EngineClient } from "../../engine/client";
import type { ChatRequestBody } from "../../engine/types";
import { useEngineStore } from "../../state/engineStore";
import { useViewportStore } from "../../state/viewportStore";
import { makePartDetail } from "../../test/fixtures";
import { useParametricStore } from "../parametric/parametricStore";
import { CHAT_SYSTEM_PROMPT, useChatStore } from "./chatStore";

function okResponse(content: string): Response {
  return new Response(
    JSON.stringify({
      content,
      provider: "stub",
      model: "stub",
      stop_reason: "end_turn",
      thinking: null,
      usage: { input_tokens: 1, output_tokens: 1 },
    }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  );
}

function installClient(fetchFn: (input: string, init?: RequestInit) => Promise<Response>): void {
  useEngineStore.setState({
    client: new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchFn),
  });
}

function sentBody(fetchMock: ReturnType<typeof vi.fn>, call = 0): ChatRequestBody {
  const init = fetchMock.mock.calls[call]![1] as RequestInit;
  return JSON.parse(init.body as string) as ChatRequestBody;
}

beforeEach(() => {
  useChatStore.getState().clear();
});

afterEach(() => {
  useChatStore.getState().clear();
  vi.useRealTimers();
});

describe("chatStore.send", () => {
  it("ignores empty input", async () => {
    await useChatStore.getState().send("   ");
    expect(useChatStore.getState().items).toHaveLength(0);
  });

  it("delivers a message and appends the assistant reply", async () => {
    const fetchMock = vi.fn().mockResolvedValue(okResponse("hello there"));
    installClient(fetchMock);

    await useChatStore.getState().send("How strong is PETG?");
    const items = useChatStore.getState().items;
    expect(items).toHaveLength(2);
    expect(items[0]).toMatchObject({ role: "user", status: "sent" });
    expect(items[1]).toMatchObject({
      role: "assistant",
      status: "sent",
      content: "hello there",
      provider: "stub",
    });
    expect(useChatStore.getState().busy).toBe(false);

    const body = sentBody(fetchMock);
    expect(body.system).toBe(CHAT_SYSTEM_PROMPT);
    expect(body.messages).toEqual([{ role: "user", content: "How strong is PETG?" }]);
  });

  it("includes prior sent turns as history", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okResponse("answer one"))
      .mockResolvedValueOnce(okResponse("answer two"));
    installClient(fetchMock);

    await useChatStore.getState().send("first");
    await useChatStore.getState().send("second");

    const body = sentBody(fetchMock, 1);
    expect(body.messages).toEqual([
      { role: "user", content: "first" },
      { role: "assistant", content: "answer one" },
      { role: "user", content: "second" },
    ]);
  });

  it("marks non-retryable failures as error", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: "INVALID_REQUEST", message: "bad", details: {}, retryable: false },
        }),
        { status: 400 },
      ),
    );
    installClient(fetchMock);

    await useChatStore.getState().send("hi");
    const item = useChatStore.getState().items[0]!;
    expect(item.status).toBe("error");
    expect(item.error).toContain("bad");
  });
});

describe("AI design actions", () => {
  it("a create action loads the new part into the viewport", async () => {
    useViewportStore.getState().clear();
    useParametricStore.getState().clear();
    const detail = makePartDetail({ partId: "eng-ai-1" });
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith("/api/v1/ai/chat")) {
        return new Response(
          JSON.stringify({
            content: "Created your bracket.",
            provider: "stub",
            model: "stub",
            stop_reason: "end_turn",
            thinking: null,
            usage: { input_tokens: 1, output_tokens: 1 },
            actions: [
              {
                tool: "create_part_from_template",
                ok: true,
                summary: "Created L-Bracket",
                partId: "eng-ai-1",
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/api/v1/parts/eng-ai-1")) {
        return new Response(JSON.stringify(detail), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      throw new Error(`unexpected url ${url}`);
    });
    useEngineStore.setState({
      client: new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchMock),
    });

    await useChatStore.getState().send("Design a bracket 50x70");

    const assistant = useChatStore.getState().items.find((i) => i.role === "assistant");
    expect(assistant?.actions).toHaveLength(1);
    expect(assistant?.actions?.[0]?.ok).toBe(true);

    const objects = useViewportStore.getState().objects;
    expect(objects).toHaveLength(1);
    expect(objects[0]!.parametricPartId).toBe("eng-ai-1");
    expect(useParametricStore.getState().active?.partId).toBe("eng-ai-1");
  });
});

describe("offline queueing", () => {
  it("queues retryable failures and schedules a retry", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("network down"));
    installClient(fetchMock);

    await useChatStore.getState().send("queued question");
    expect(useChatStore.getState().items[0]!.status).toBe("queued");
    expect(useChatStore.getState().retryTimer).not.toBeNull();
  });

  it("flushQueued re-delivers queued messages in order", async () => {
    vi.useFakeTimers(); // keep the backoff timer from firing mid-test
    // start offline
    const failing = vi.fn().mockRejectedValue(new TypeError("offline"));
    installClient(failing);
    await useChatStore.getState().send("first while offline");
    await useChatStore.getState().send("second while offline");
    await useChatStore.getState().flushQueued(); // still failing → both stay queued

    const queued = useChatStore.getState().items.filter((i) => i.status === "queued");
    expect(queued).toHaveLength(2);

    // network returns
    const working = vi
      .fn()
      .mockResolvedValueOnce(okResponse("reply 1"))
      .mockResolvedValueOnce(okResponse("reply 2"));
    installClient(working);

    await useChatStore.getState().flushQueued();
    const items = useChatStore.getState().items;
    const users = items.filter((i) => i.role === "user");
    const assistants = items.filter((i) => i.role === "assistant");
    expect(users.every((u) => u.status === "sent")).toBe(true);
    expect(assistants.map((a) => a.content)).toEqual(["reply 1", "reply 2"]);

    // first delivery's history contains only the first user message
    const firstBody = sentBody(working, 0);
    expect(firstBody.messages).toEqual([{ role: "user", content: "first while offline" }]);
    // second delivery sees the first exchange as history
    const secondBody = sentBody(working, 1);
    expect(secondBody.messages).toEqual([
      { role: "user", content: "first while offline" },
      { role: "assistant", content: "reply 1" },
      { role: "user", content: "second while offline" },
    ]);
  });

  it("retry backoff doubles up to the cap", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("offline"));
    installClient(fetchMock);

    await useChatStore.getState().send("q");
    const afterFirst = useChatStore.getState().retryDelayMs;
    expect(afterFirst).toBe(6000); // 3000 * 2 after scheduling
  });
});
