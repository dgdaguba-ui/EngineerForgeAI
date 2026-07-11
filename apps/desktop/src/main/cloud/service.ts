/**
 * CloudService port — the ONLY surface business logic sees for cloud
 * functionality (auth, backup/sync). Local files remain the source of truth;
 * the app must be fully functional when the provider is disabled or offline.
 *
 * Implementations: LocalOnlyCloud (always available), SupabaseCloud
 * (enabled by SUPABASE_URL + SUPABASE_ANON_KEY). Future: Firebase/AWS/Azure
 * behind this same interface.
 */
import type { CloudResult, CloudStatus, ProjectDoc, ProjectInfo } from "@efc/ipc-contracts";

export interface CloudService {
  readonly name: string;
  status(): Promise<CloudStatus>;
  signIn(email: string, password: string): Promise<CloudStatus>;
  signOut(): Promise<CloudStatus>;
  /** Backup/sync one project document (assets sync arrives in Phase 2). */
  pushProject(info: ProjectInfo, doc: ProjectDoc): Promise<CloudResult>;
}
