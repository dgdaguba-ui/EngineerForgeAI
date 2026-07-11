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

/** A part in the project. `asset` is a path relative to the project directory. */
export const PartRefSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  asset: z.string().min(1),
  colorHex: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/)
    .nullable()
    .default(null),
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
