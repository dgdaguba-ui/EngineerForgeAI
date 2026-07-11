import { describe, expect, it } from "vitest";

import {
  channelNames,
  channels,
  EngineStatusSchema,
  OpenFileRequestSchema,
  ReadFileResultSchema,
} from "./channels.js";
import { eventNames, events } from "./events.js";

describe("channel map", () => {
  it("every channel has req and res schemas", () => {
    for (const name of channelNames) {
      const def = channels[name];
      expect(def.req, `${name}.req`).toBeDefined();
      expect(def.res, `${name}.res`).toBeDefined();
    }
  });

  it("channelNames matches the map keys exactly", () => {
    expect(channelNames.sort()).toEqual(Object.keys(channels).sort());
  });

  it("event names match the event map", () => {
    expect(eventNames.sort()).toEqual(Object.keys(events).sort());
  });
});

describe("EngineStatusSchema", () => {
  it("accepts a valid running status", () => {
    const parsed = EngineStatusSchema.parse({
      state: "running",
      pid: 1234,
      port: 8971,
      baseUrl: "http://127.0.0.1:8971",
      message: "ready",
      restarts: 0,
    });
    expect(parsed.state).toBe("running");
  });

  it("rejects unknown states", () => {
    expect(() =>
      EngineStatusSchema.parse({
        state: "sleeping",
        pid: null,
        port: null,
        baseUrl: null,
        message: "",
        restarts: 0,
      }),
    ).toThrow();
  });
});

describe("file schemas", () => {
  it("openFile request allows empty object", () => {
    expect(OpenFileRequestSchema.parse({})).toEqual({});
  });

  it("readFile result requires base64 payload fields", () => {
    expect(() => ReadFileResultSchema.parse({ name: "a.stl" })).toThrow();
  });
});
