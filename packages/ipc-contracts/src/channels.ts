/**
 * Request/response IPC channels (renderer → main via ipcRenderer.invoke).
 *
 * Every channel declares a Zod schema for its request and response. The main
 * process validates requests before handling; the preload only forwards
 * channels present in this map. This file is the single source of truth for
 * the renderer↔main surface.
 */
import { z } from "zod";

import {
  CloudResultSchema,
  CloudStatusSchema,
  ProjectDocSchema,
  ProjectInfoSchema,
  SyncStatusSchema,
} from "./project.js";

// ── Engine ────────────────────────────────────────────────────────────────────

export const EngineStateSchema = z.enum([
  "stopped",
  "starting",
  "running",
  "restarting",
  "failed",
]);
export type EngineState = z.infer<typeof EngineStateSchema>;

export const EngineStatusSchema = z.object({
  state: EngineStateSchema,
  pid: z.number().nullable(),
  port: z.number().nullable(),
  baseUrl: z.string().nullable(),
  message: z.string(),
  restarts: z.number(),
});
export type EngineStatus = z.infer<typeof EngineStatusSchema>;

/** Connection info the renderer uses to call the engine REST API directly. */
export const EngineConnectionSchema = z.object({
  baseUrl: z.string().nullable(),
  token: z.string().nullable(),
});
export type EngineConnection = z.infer<typeof EngineConnectionSchema>;

// ── Files & dialogs ───────────────────────────────────────────────────────────

export const FileFilterSchema = z.object({
  name: z.string(),
  extensions: z.array(z.string()),
});
export type FileFilter = z.infer<typeof FileFilterSchema>;

export const OpenFileRequestSchema = z.object({
  title: z.string().optional(),
  filters: z.array(FileFilterSchema).optional(),
});

export const SaveFileRequestSchema = z.object({
  title: z.string().optional(),
  defaultName: z.string().optional(),
  filters: z.array(FileFilterSchema).optional(),
});

export const PickedFileSchema = z.object({
  path: z.string(),
  name: z.string(),
});
export type PickedFile = z.infer<typeof PickedFileSchema>;

export const ReadFileRequestSchema = z.object({ path: z.string() });

export const ReadFileResultSchema = z.object({
  name: z.string(),
  byteLength: z.number(),
  /** Raw file bytes, base64-encoded for structured-clone transport. */
  dataBase64: z.string(),
});
export type ReadFileResult = z.infer<typeof ReadFileResultSchema>;

// ── Channel map ───────────────────────────────────────────────────────────────

/** Payload for opening/saving a project (returned by project channels). */
export const ProjectBundleSchema = z.object({
  info: ProjectInfoSchema,
  doc: ProjectDocSchema,
});

export const channels = {
  "app:getVersion": {
    req: z.void(),
    res: z.object({ app: z.string(), electron: z.string() }),
  },
  "engine:getStatus": { req: z.void(), res: EngineStatusSchema },
  "engine:getConnection": { req: z.void(), res: EngineConnectionSchema },
  "engine:restart": { req: z.void(), res: EngineStatusSchema },
  "dialog:openFile": { req: OpenFileRequestSchema, res: PickedFileSchema.nullable() },
  "dialog:saveFile": { req: SaveFileRequestSchema, res: PickedFileSchema.nullable() },
  "fs:readFile": { req: ReadFileRequestSchema, res: ReadFileResultSchema },
  // ── projects (local-first .efproj bundles) ──────────────────────────────────
  "project:create": { req: z.void(), res: ProjectBundleSchema.nullable() },
  "project:open": { req: z.void(), res: ProjectBundleSchema.nullable() },
  "project:openPath": { req: z.object({ path: z.string() }), res: ProjectBundleSchema },
  "project:save": {
    req: z.object({ path: z.string(), doc: ProjectDocSchema }),
    res: ProjectInfoSchema,
  },
  "project:recent": { req: z.void(), res: z.array(ProjectInfoSchema) },
  "project:importAsset": {
    req: z.object({ projectPath: z.string(), sourcePath: z.string() }),
    res: z.object({ relPath: z.string(), name: z.string() }),
  },
  // ── cloud (optional; app is fully functional without it) ───────────────────
  "cloud:status": { req: z.void(), res: CloudStatusSchema },
  "cloud:signIn": {
    req: z.object({ email: z.string(), password: z.string() }),
    res: CloudStatusSchema,
  },
  "cloud:signOut": { req: z.void(), res: CloudStatusSchema },
  "cloud:pushProject": {
    req: z.object({ path: z.string() }),
    res: CloudResultSchema,
  },
  // enqueue a project for background backup (offline-first; retries on reconnect)
  "cloud:queueProject": {
    req: z.object({ path: z.string() }),
    res: SyncStatusSchema,
  },
  "cloud:syncStatus": { req: z.void(), res: SyncStatusSchema },
} as const;

export type Channels = typeof channels;
export type ChannelName = keyof Channels;
export type ChannelReq<C extends ChannelName> = z.infer<Channels[C]["req"]>;
export type ChannelRes<C extends ChannelName> = z.infer<Channels[C]["res"]>;

/** Channel names as a plain array — used by the preload allowlist and tests. */
export const channelNames = Object.keys(channels) as ChannelName[];
