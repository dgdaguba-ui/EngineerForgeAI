/**
 * LocalOnlyCloud — the null cloud provider. Everything is local; every cloud
 * operation reports itself cleanly disabled instead of failing.
 */
import type { CloudResult, CloudStatus } from "@efc/ipc-contracts";

import type { CloudService } from "./service.js";

export class LocalOnlyCloud implements CloudService {
  readonly name = "local";

  private readonly statusValue: CloudStatus = {
    provider: "local",
    enabled: false,
    signedIn: false,
    email: null,
    detail: "Local-only mode. Configure SUPABASE_URL and SUPABASE_ANON_KEY to enable cloud sync.",
  };

  async status(): Promise<CloudStatus> {
    return { ...this.statusValue };
  }

  async signIn(): Promise<CloudStatus> {
    return { ...this.statusValue, detail: "Cloud is not configured; sign-in unavailable." };
  }

  async signOut(): Promise<CloudStatus> {
    return { ...this.statusValue };
  }

  async pushProject(): Promise<CloudResult> {
    return { ok: false, detail: "Cloud sync disabled (local-only mode). Project saved locally." };
  }
}
