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

// ── Blender & conversion (engine /api/v1/blender, /api/v1/convert) ───────────

export interface BlenderInfo {
  executable: string;
  version: string;
}

export interface BlenderStatus {
  detected: boolean;
  info: BlenderInfo | null;
  detail: string;
}

export interface BlenderLaunchResult {
  pid: number;
  executable: string;
  file: string | null;
}

export interface ConvertResult {
  srcFormat: string;
  dstFormat: string;
  dstPath: string;
  engine: "native" | "blender" | "blender+native";
  triangles: number | null;
}

// ── Flashforge workspace: catalog, compatibility, estimates, export ──────────

export interface Material {
  id: string;
  name: string;
  category: "rigid" | "engineering" | "flexible" | "support";
  adhesionGroup: string;
  densityGCm3: number;
  tensileStrengthMpa: number | null;
  youngsModulusMpa: number | null;
  printTempMinC: number;
  printTempMaxC: number;
  bedTempC: number;
  shrinkagePct: number;
  costPerKg: number;
  colorHex: string;
  solubleSupport: boolean;
  supportFor: string[];
  notes: string;
}

export interface PrinterProfile {
  id: string;
  name: string;
  brand: string;
  buildVolume: { x: number; y: number; z: number };
  extruders: number;
  materialSlots: number;
  nozzleDiameterMm: number;
  maxNozzleTempC: number;
  maxBedTempC: number;
  enclosed: boolean;
  multiMaterialSystem: "none" | "idex" | "filament-switching";
  purgePerChangeMm3: number;
  slicer: string;
}

export type CompatibilityLevel = "ok" | "caution" | "incompatible";

export interface CompatibilityPair {
  a: string;
  b: string;
  level: CompatibilityLevel;
  reasons: string[];
  nozzleTempOverlapC: number;
  bedTempDeltaC: number;
}

export interface CompatibilityReport {
  pairs: CompatibilityPair[];
  worst: CompatibilityLevel;
}

export interface UsageEstimate {
  materialId: string;
  volumeCm3: number;
  solidVolumeCm3: number;
  massG: number;
  cost: number;
  currency: string;
  bboxMm: { x: number; y: number; z: number };
  watertight: boolean;
  fitsPrinter: boolean | null;
  printerId: string | null;
  assumptions: string[];
}

export interface PurgeEstimate {
  printerId: string;
  toolChanges: number;
  purgeVolumeMm3: number;
  purgeMassG: number;
  purgeCost: number;
  assumptions: string[];
}

export interface Export3mfPart {
  meshPath: string;
  name: string;
  colorHex?: string | null;
  materialName?: string | null;
}

export interface Export3mfResult {
  dstPath: string;
  parts: number;
  sizeBytes: number;
}
