/**
 * Access to the preload bridge (`window.efc`). Returns null when running
 * outside the Electron shell (e.g. plain-browser dev or component tests),
 * so callers can degrade gracefully.
 */
import type { EfcBridge } from "@efc/ipc-contracts";

export function getBridge(): EfcBridge | null {
  if (typeof window !== "undefined" && window.efc) {
    return window.efc;
  }
  return null;
}
