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

export interface ParamDiffEntry {
  paramId: string;
  label: string;
  oldValue: number;
  newValue: number;
  unit: string;
}

export interface ChatToolAction {
  tool: string;
  ok: boolean;
  summary: string;
  partId: string | null;
  diff: ParamDiffEntry[];
  pending: boolean;
}

export interface ChatResponseBody {
  content: string;
  provider: string;
  model: string;
  stop_reason: string | null;
  thinking: string | null;
  usage: ChatUsage;
  actions: ChatToolAction[];
}

/** One event from POST /api/v1/ai/chat/stream (newline-delimited JSON). */
export interface ChatStreamEvent {
  type: "delta" | "action" | "done" | "error";
  text?: string | null;
  action?: ChatToolAction | null;
  response?: ChatResponseBody | null;
  error?: string | null;
  code?: string | null;
  retryable?: boolean;
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
  orientationHint: string;
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

/** One job part: either an imported mesh file or a live parametric part. */
export interface Export3mfPart {
  meshPath?: string;
  partId?: string;
  name: string;
  colorHex?: string | null;
  materialName?: string | null;
}

export interface Export3mfResult {
  dstPath: string;
  parts: number;
  sizeBytes: number;
}

// ── Parametric parts (Feature Program IR, engine /api/v1/parts) ──────────────

export interface IrParameter {
  id: string;
  label: string;
  value: number;
  unit: string;
  min: number | null;
  max: number | null;
  step: number | null;
  integer: boolean;
}

/** One IR feature. `op` and `id` are always present; the rest is op-specific
 * (kept loose — the renderer only reads it for a read-only timeline). */
export interface IrFeature {
  op: string;
  id: string;
  [key: string]: unknown;
}

/** The IR document is engine-owned; the renderer treats it as opaque JSON
 * apart from the parameter list it edits and the feature list it displays. */
export interface FeatureProgramDoc {
  schema: string;
  name: string;
  parameters: IrParameter[];
  features: IrFeature[];
  [key: string]: unknown;
}

export interface RawMeshPayload {
  positionsB64: string;
  indicesB64: string;
  vertexCount: number;
  triangleCount: number;
}

export interface PartMassProps {
  volumeMm3: number;
  volumeCm3: number;
  massG: number | null;
  materialId: string | null;
  cogMm: [number, number, number];
  bboxMm: { x: number; y: number; z: number };
}

export interface PartDetail {
  partId: string;
  name: string;
  templateId: string | null;
  program: FeatureProgramDoc;
  compiled: {
    mesh: RawMeshPayload;
    massProps: PartMassProps;
    warnings: string[];
  };
  materialId: string | null;
}

export interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  parameters: IrParameter[];
}

export interface PartExportResult {
  partId: string;
  format: string;
  dstPath: string;
  sizeBytes: number;
}
