/**
 * SupabaseCloud — auth + project backup on Supabase.
 *
 * Design constraints (offline-first, ADR-0004):
 *  - construction never touches the network; the SDK client is created lazily;
 *  - every operation catches transport errors and returns a typed result —
 *    a dead network must never break local work;
 *  - only the anon key is used here; service-role keys never ship in the app.
 *
 * Project backups land in a storage bucket (default `efproject`, overridable
 * via SUPABASE_BUCKET) at `<userId>/<projectId>/project.json` — RLS scopes
 * access per user.
 */
import type { SupabaseClient } from "@supabase/supabase-js";
import { createClient } from "@supabase/supabase-js";

import type { CloudResult, CloudStatus, ProjectDoc, ProjectInfo } from "@efc/ipc-contracts";

import type { CloudService } from "./service.js";

export const DEFAULT_BUCKET = "efproject";

export class SupabaseCloud implements CloudService {
  readonly name = "supabase";
  private client: SupabaseClient | null = null;

  constructor(
    private readonly url: string,
    private readonly anonKey: string,
    private readonly bucket: string = DEFAULT_BUCKET,
  ) {}

  private getClient(): SupabaseClient {
    if (!this.client) {
      this.client = createClient(this.url, this.anonKey, {
        auth: { persistSession: false, autoRefreshToken: true },
      });
    }
    return this.client;
  }

  private base(): Omit<CloudStatus, "signedIn" | "email" | "detail"> {
    return { provider: "supabase", enabled: true };
  }

  async status(): Promise<CloudStatus> {
    try {
      const { data, error } = await this.getClient().auth.getSession();
      if (error) {
        return { ...this.base(), signedIn: false, email: null, detail: error.message };
      }
      const session = data.session;
      return {
        ...this.base(),
        signedIn: Boolean(session),
        email: session?.user?.email ?? null,
        detail: session ? "Signed in" : "Not signed in",
      };
    } catch (e) {
      return {
        ...this.base(),
        signedIn: false,
        email: null,
        detail: `Supabase unreachable: ${e instanceof Error ? e.message : String(e)}`,
      };
    }
  }

  async signIn(email: string, password: string): Promise<CloudStatus> {
    try {
      const { data, error } = await this.getClient().auth.signInWithPassword({ email, password });
      if (error) {
        return { ...this.base(), signedIn: false, email: null, detail: error.message };
      }
      return {
        ...this.base(),
        signedIn: true,
        email: data.user?.email ?? email,
        detail: "Signed in",
      };
    } catch (e) {
      return {
        ...this.base(),
        signedIn: false,
        email: null,
        detail: `Sign-in failed: ${e instanceof Error ? e.message : String(e)}`,
      };
    }
  }

  async signOut(): Promise<CloudStatus> {
    try {
      await this.getClient().auth.signOut();
    } catch {
      // signing out offline is fine — local session is discarded either way
    }
    return { ...this.base(), signedIn: false, email: null, detail: "Signed out" };
  }

  async pushProject(info: ProjectInfo, doc: ProjectDoc): Promise<CloudResult> {
    try {
      const client = this.getClient();
      const { data: sessionData } = await client.auth.getSession();
      const userId = sessionData.session?.user?.id;
      if (!userId) {
        return { ok: false, detail: "Not signed in — project saved locally only." };
      }
      const key = `${userId}/${doc.id}/project.json`;
      const body = JSON.stringify(doc, null, 2);
      const { error } = await client.storage
        .from(this.bucket)
        .upload(key, new Blob([body], { type: "application/json" }), { upsert: true });
      if (error) {
        return { ok: false, detail: `Cloud backup failed: ${error.message}` };
      }
      return { ok: true, detail: `Backed up ${info.name} to Supabase (${key})` };
    } catch (e) {
      return {
        ok: false,
        detail: `Cloud unreachable: ${e instanceof Error ? e.message : String(e)}`,
      };
    }
  }
}
