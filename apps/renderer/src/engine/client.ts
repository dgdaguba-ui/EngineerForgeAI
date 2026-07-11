/**
 * Typed client for the engine REST API. Errors are normalized to
 * EngineApiError using the engine's single error envelope.
 */
import type {
  ChatRequestBody,
  ChatResponseBody,
  EngineCapabilities,
  EngineErrorEnvelope,
  EngineHealth,
} from "./types";

export interface EngineConnectionInfo {
  baseUrl: string | null;
  token: string | null;
}

export class EngineApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly httpStatus: number,
    readonly retryable: boolean,
  ) {
    super(message);
    this.name = "EngineApiError";
  }
}

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export class EngineClient {
  private readonly fetchFn: FetchLike;

  constructor(
    private readonly conn: EngineConnectionInfo,
    fetchFn?: FetchLike,
  ) {
    this.fetchFn = fetchFn ?? ((input, init) => globalThis.fetch(input, init));
  }

  get connected(): boolean {
    return Boolean(this.conn.baseUrl);
  }

  private headers(): Record<string, string> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (this.conn.token) {
      headers["Authorization"] = `Bearer ${this.conn.token}`;
    }
    return headers;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    if (!this.conn.baseUrl) {
      throw new EngineApiError("Engine is not connected", "NOT_CONNECTED", 0, true);
    }
    let res: Response;
    try {
      res = await this.fetchFn(`${this.conn.baseUrl}${path}`, {
        ...init,
        headers: { ...this.headers(), ...(init?.headers as Record<string, string> | undefined) },
      });
    } catch (cause) {
      throw new EngineApiError(
        `Engine unreachable: ${cause instanceof Error ? cause.message : String(cause)}`,
        "NETWORK_ERROR",
        0,
        true,
      );
    }
    if (!res.ok) {
      let code = "HTTP_ERROR";
      let message = `Engine request failed (${res.status})`;
      let retryable = res.status >= 500;
      try {
        const envelope = (await res.json()) as EngineErrorEnvelope;
        if (envelope?.error) {
          code = envelope.error.code;
          message = envelope.error.message;
          retryable = envelope.error.retryable;
        }
      } catch {
        // non-JSON error body — keep defaults
      }
      throw new EngineApiError(message, code, res.status, retryable);
    }
    return (await res.json()) as T;
  }

  async health(): Promise<EngineHealth> {
    return await this.request<EngineHealth>("/health");
  }

  async capabilities(): Promise<EngineCapabilities> {
    return await this.request<EngineCapabilities>("/api/v1/capabilities");
  }

  async chat(body: ChatRequestBody): Promise<ChatResponseBody> {
    return await this.request<ChatResponseBody>("/api/v1/ai/chat", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }
}
