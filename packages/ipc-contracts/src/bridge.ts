/**
 * The `window.efc` surface exposed by the preload script.
 *
 * Declared here so preload (implementation) and renderer (consumer) share one
 * definition and cannot drift.
 */
import type { ChannelName, ChannelReq, ChannelRes } from "./channels.js";
import type { EventName, EventPayload } from "./events.js";

export interface EfcBridge {
  invoke<C extends ChannelName>(channel: C, payload: ChannelReq<C>): Promise<ChannelRes<C>>;
  /** Subscribe to a push event. Returns an unsubscribe function. */
  on<E extends EventName>(event: E, listener: (payload: EventPayload<E>) => void): () => void;
}

declare global {
  interface Window {
    efc?: EfcBridge;
  }
}
