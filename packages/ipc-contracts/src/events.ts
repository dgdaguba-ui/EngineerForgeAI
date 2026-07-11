/**
 * Push-event channels (main → renderer via webContents.send).
 */
import { z } from "zod";

import { EngineStatusSchema } from "./channels.js";

export const events = {
  "engine:statusChanged": EngineStatusSchema,
} as const;

export type Events = typeof events;
export type EventName = keyof Events;
export type EventPayload<E extends EventName> = z.infer<Events[E]>;

export const eventNames = Object.keys(events) as EventName[];
