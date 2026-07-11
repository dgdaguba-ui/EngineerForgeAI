/**
 * Engine REST API types — mirrors the engine's Pydantic models
 * (apps/engine/engineerforge_engine/domain/ai.py and api routers).
 */

export type ChatRole = "system" | "user" | "assistant" | "tool";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ChatRequestBody {
  messages: ChatMessage[];
  system?: string | null;
  model?: string | null;
  max_tokens?: number | null;
}

export interface ChatUsage {
  input_tokens: number;
  output_tokens: number;
}

export interface ChatResponseBody {
  content: string;
  provider: string;
  model: string;
  stop_reason: string | null;
  thinking: string | null;
  usage: ChatUsage;
}

export interface ProviderHealth {
  provider: string;
  available: boolean;
  detail: string;
}

export interface EngineHealth {
  status: string;
  app: string;
  version: string;
  python: string;
  provider: ProviderHealth;
}

export interface EngineCapabilities {
  version: string;
  ai: {
    active_provider: string;
    providers: string[];
    planned_providers: string[];
    model: string;
  };
  features: Record<string, boolean>;
}

export interface EngineErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    retryable: boolean;
  };
}
