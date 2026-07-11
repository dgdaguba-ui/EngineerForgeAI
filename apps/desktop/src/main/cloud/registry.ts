/**
 * Cloud provider selection — mirrors the engine's AI registry policy:
 * configuration chooses the adapter; missing configuration degrades to the
 * always-working local provider, never to an error.
 */
import { LocalOnlyCloud } from "./local.js";
import type { CloudService } from "./service.js";
import { SupabaseCloud } from "./supabase.js";

export interface CloudEnv {
  SUPABASE_URL?: string | undefined;
  SUPABASE_ANON_KEY?: string | undefined;
}

export function buildCloudService(env: CloudEnv): CloudService {
  const url = env.SUPABASE_URL?.trim();
  const key = env.SUPABASE_ANON_KEY?.trim();
  if (url && key) {
    return new SupabaseCloud(url, key);
  }
  return new LocalOnlyCloud();
}
