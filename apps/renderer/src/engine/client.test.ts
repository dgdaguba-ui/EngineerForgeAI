import { describe, expect, it, vi } from "vitest";

import { EngineApiError, EngineClient } from "./client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("EngineClient", () => {
  it("throws NOT_CONNECTED when baseUrl is null", async () => {
    const client = new EngineClient({ baseUrl: null, token: null });
    await expect(client.health()).rejects.toMatchObject({ code: "NOT_CONNECTED" });
  });

  it("sends bearer token and parses health", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      jsonResponse({
        status: "ok",
        app: "EngineerForge Engine",
        version: "0.1.0",
        python: "3.12.11",
        provider: { provider: "stub", available: true, detail: "" },
      }),
    );
    const client = new EngineClient(
      { baseUrl: "http://127.0.0.1:9000", token: "tok123" },
      fetchFn,
    );
    const health = await client.health();
    expect(health.provider.provider).toBe("stub");
    const [url, init] = fetchFn.mock.calls[0]!;
    expect(url).toBe("http://127.0.0.1:9000/health");
    expect((init!.headers as Record<string, string>)["Authorization"]).toBe("Bearer tok123");
  });

  it("maps the engine error envelope to EngineApiError", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: "INVALID_REQUEST",
            message: "messages must not be empty",
            details: {},
            retryable: false,
          },
        },
        400,
      ),
    );
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchFn);
    const err = await client.chat({ messages: [] }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(EngineApiError);
    expect((err as EngineApiError).code).toBe("INVALID_REQUEST");
    expect((err as EngineApiError).httpStatus).toBe(400);
    expect((err as EngineApiError).retryable).toBe(false);
  });

  it("marks network failures retryable", async () => {
    const fetchFn = vi.fn().mockRejectedValue(new TypeError("fetch failed"));
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchFn);
    const err = await client.health().catch((e: unknown) => e);
    expect((err as EngineApiError).code).toBe("NETWORK_ERROR");
    expect((err as EngineApiError).retryable).toBe(true);
  });

  it("posts chat messages", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      jsonResponse({
        content: "hello",
        provider: "stub",
        model: "stub",
        stop_reason: "end_turn",
        thinking: null,
        usage: { input_tokens: 1, output_tokens: 2 },
      }),
    );
    const client = new EngineClient({ baseUrl: "http://127.0.0.1:9000", token: null }, fetchFn);
    const res = await client.chat({ messages: [{ role: "user", content: "hi" }] });
    expect(res.content).toBe("hello");
    const [url, init] = fetchFn.mock.calls[0]!;
    expect(url).toBe("http://127.0.0.1:9000/api/v1/ai/chat");
    expect(init!.method).toBe("POST");
  });
});
