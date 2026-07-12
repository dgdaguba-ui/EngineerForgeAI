/**
 * Typed client for the engine REST API. Errors are normalized to
 * EngineApiError using the engine's single error envelope.
 */
import type {
  BlenderLaunchResult,
  BlenderStatus,
  ChatRequestBody,
  ChatResponseBody,
  CompatibilityReport,
  ConvertResult,
  EngineCapabilities,
  EngineErrorEnvelope,
  EngineHealth,
  Export3mfPart,
  Export3mfResult,
  FeatureProgramDoc,
  Material,
  PartDetail,
  PartExportResult,
  PrinterProfile,
  PurgeEstimate,
  TemplateInfo,
  UsageEstimate,
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

  async blenderStatus(): Promise<BlenderStatus> {
    return await this.request<BlenderStatus>("/api/v1/blender/status");
  }

  async blenderLaunch(file?: string): Promise<BlenderLaunchResult> {
    return await this.request<BlenderLaunchResult>("/api/v1/blender/launch", {
      method: "POST",
      body: JSON.stringify({ file: file ?? null }),
    });
  }

  async convertMesh(srcPath: string, dstPath: string): Promise<ConvertResult> {
    return await this.request<ConvertResult>("/api/v1/convert", {
      method: "POST",
      body: JSON.stringify({ srcPath, dstPath }),
    });
  }

  async materials(): Promise<Material[]> {
    return await this.request<Material[]>("/api/v1/materials");
  }

  async printers(): Promise<PrinterProfile[]> {
    return await this.request<PrinterProfile[]>("/api/v1/printers");
  }

  async materialCompatibility(materialIds: string[]): Promise<CompatibilityReport> {
    return await this.request<CompatibilityReport>("/api/v1/materials/compatibility", {
      method: "POST",
      body: JSON.stringify({ materialIds }),
    });
  }

  async printEstimate(input: {
    meshPath?: string;
    partId?: string;
    materialId: string;
    infill?: number;
    printerId?: string | null;
  }): Promise<UsageEstimate> {
    return await this.request<UsageEstimate>("/api/v1/print/estimate", {
      method: "POST",
      body: JSON.stringify({
        meshPath: input.meshPath ?? null,
        partId: input.partId ?? null,
        materialId: input.materialId,
        infill: input.infill ?? 0.2,
        printerId: input.printerId ?? null,
      }),
    });
  }

  async purgeEstimate(input: {
    printerId: string;
    materialIds: string[];
    heightMm: number;
    layerHeightMm?: number;
  }): Promise<PurgeEstimate> {
    return await this.request<PurgeEstimate>("/api/v1/print/purge-estimate", {
      method: "POST",
      body: JSON.stringify({
        printerId: input.printerId,
        materialIds: input.materialIds,
        heightMm: input.heightMm,
        layerHeightMm: input.layerHeightMm ?? 0.2,
      }),
    });
  }

  async export3mf(parts: Export3mfPart[], dstPath: string): Promise<Export3mfResult> {
    return await this.request<Export3mfResult>("/api/v1/export/3mf", {
      method: "POST",
      body: JSON.stringify({ parts, dstPath }),
    });
  }

  async listTemplates(): Promise<TemplateInfo[]> {
    return await this.request<TemplateInfo[]>("/api/v1/templates");
  }

  async createPartFromTemplate(
    templateId: string,
    values?: Record<string, number>,
    materialId?: string | null,
  ): Promise<PartDetail> {
    return await this.request<PartDetail>("/api/v1/parts/from-template", {
      method: "POST",
      body: JSON.stringify({ templateId, values: values ?? {}, materialId: materialId ?? null }),
    });
  }

  async compilePart(
    program: FeatureProgramDoc | unknown,
    materialId?: string | null,
  ): Promise<PartDetail> {
    return await this.request<PartDetail>("/api/v1/parts/compile", {
      method: "POST",
      body: JSON.stringify({ program, materialId: materialId ?? null }),
    });
  }

  async getPart(partId: string): Promise<PartDetail> {
    return await this.request<PartDetail>(`/api/v1/parts/${partId}`);
  }

  async patchPartParams(
    partId: string,
    values: Record<string, number>,
    materialId?: string | null,
  ): Promise<PartDetail> {
    return await this.request<PartDetail>(`/api/v1/parts/${partId}/params`, {
      method: "PATCH",
      body: JSON.stringify({ values, materialId: materialId ?? null }),
    });
  }

  async exportPart(
    partId: string,
    format: string,
    dstPath: string,
  ): Promise<PartExportResult> {
    return await this.request<PartExportResult>(`/api/v1/parts/${partId}/export`, {
      method: "POST",
      body: JSON.stringify({ format, dstPath }),
    });
  }
}
