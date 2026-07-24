/**
 * The `.efproj` project document — EngineerForge's transparent, local-first
 * project format (a directory bundle: project.json + assets/).
 *
 * Local files are the source of truth (ADR-0004); cloud sync serializes this
 * same document. Schema is versioned via the `schema` literal.
 */
import { z } from "zod";

export const EFPROJ_SCHEMA_VERSION = "efproj/1" as const;
export const PROJECT_FILE_NAME = "project.json" as const;
export const PROJECT_DIR_EXTENSION = ".efproj" as const;

/**
 * A part in the project. Two kinds:
 *  - "mesh": imported geometry; `asset` is a path relative to the project dir.
 *  - "parametric": an editable Feature Program (`efir/1`); `program` holds the
 *    IR document and the engine recompiles it on open.
 */
export const PartRefSchema = z
  .object({
    id: z.string().min(1),
    name: z.string().min(1),
    kind: z.enum(["mesh", "parametric"]).default("mesh"),
    asset: z.string().min(1).optional(),
    program: z.unknown().optional(),
    colorHex: z
      .string()
      .regex(/^#[0-9a-fA-F]{6}$/)
      .nullable()
      .default(null),
  })
  .superRefine((part, ctx) => {
    if (part.kind === "mesh" && !part.asset) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "mesh part requires asset" });
    }
    if (part.kind === "parametric" && part.program === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "parametric part requires program",
      });
    }
  });
export type PartRef = z.infer<typeof PartRefSchema>;

/** A material slot on the active printer (multi-material support, M0.8+). */
export const MaterialSlotSchema = z.object({
  index: z.number().int().min(0),
  materialId: z.string().nullable().default(null),
  colorHex: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/)
    .nullable()
    .default(null),
});
export type MaterialSlot = z.infer<typeof MaterialSlotSchema>;

export const ProjectDocSchema = z.object({
  schema: z.literal(EFPROJ_SCHEMA_VERSION),
  id: z.string().min(1),
  name: z.string().min(1),
  units: z.literal("mm").default("mm"),
  createdAt: z.string(),
  updatedAt: z.string(),
  parts: z.array(PartRefSchema).default([]),
  printerProfileId: z.string().nullable().default(null),
  materialSlots: z.array(MaterialSlotSchema).default([]),
  /** part id → material slot index */
  partSlotAssignments: z.record(z.string(), z.number().int().min(0)).default({}),
});
export type ProjectDoc = z.infer<typeof ProjectDocSchema>;

export const ProjectInfoSchema = z.object({
  id: z.string(),
  name: z.string(),
  /** Absolute path of the .efproj directory. */
  path: z.string(),
  updatedAt: z.string(),
});
export type ProjectInfo = z.infer<typeof ProjectInfoSchema>;

export function newProjectDoc(input: { id: string; name: string; now: string }): ProjectDoc {
  return {
    schema: EFPROJ_SCHEMA_VERSION,
    id: input.id,
    name: input.name,
    units: "mm",
    createdAt: input.now,
    updatedAt: input.now,
    parts: [],
    printerProfileId: null,
    materialSlots: [],
    partSlotAssignments: {},
  };
}

// ── Cloud service DTOs ────────────────────────────────────────────────────────

export const CloudStatusSchema = z.object({
  provider: z.string(),
  enabled: z.boolean(),
  signedIn: z.boolean(),
  email: z.string().nullable(),
  detail: z.string(),
});
export type CloudStatus = z.infer<typeof CloudStatusSchema>;

export const CloudResultSchema = z.object({
  ok: z.boolean(),
  detail: z.string(),
});
export type CloudResult = z.infer<typeof CloudResultSchema>;

/** Background cloud-sync queue state (offline-first project backup). */
export const SyncStatusSchema = z.object({
  /** Provider is active (a cloud backend is configured). */
  active: z.boolean(),
  /** Projects awaiting a successful push. */
  pending: z.number().int().nonnegative(),
  /** A push is currently in flight. */
  inFlight: z.boolean(),
  /** Epoch ms of the last successful push, or null. */
  lastSyncedAt: z.number().nullable(),
  /** Detail of the most recent failure, or null when healthy. */
  lastError: z.string().nullable(),
});
export type SyncStatus = z.infer<typeof SyncStatusSchema>;
