import { describe, expect, it, vi } from "vitest";

import type { EfcBridge } from "@efc/ipc-contracts";

import { importStlViaDialog } from "./import";
import { makeBinaryStl } from "./stl.test";

function stlBase64(): string {
  const bytes = new Uint8Array(
    makeBinaryStl([
      [
        [0, 0, 0],
        [5, 0, 0],
        [0, 5, 0],
      ],
    ]),
  );
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

describe("importStlViaDialog", () => {
  it("returns null when the user cancels the dialog", async () => {
    const bridge: EfcBridge = {
      invoke: vi.fn(async (channel: string) =>
        channel === "dialog:openFile" ? null : undefined,
      ) as EfcBridge["invoke"],
      on: vi.fn() as unknown as EfcBridge["on"],
    };
    expect(await importStlViaDialog(bridge)).toBeNull();
  });

  it("reads the picked file and parses geometry", async () => {
    const b64 = stlBase64();
    const invoke = vi.fn(async (channel: string) => {
      if (channel === "dialog:openFile") {
        return { path: "C:\\parts\\tri.stl", name: "tri.stl" };
      }
      if (channel === "fs:readFile") {
        return { name: "tri.stl", byteLength: b64.length, dataBase64: b64 };
      }
      throw new Error(`unexpected channel ${channel}`);
    });
    const bridge: EfcBridge = {
      invoke: invoke as EfcBridge["invoke"],
      on: vi.fn() as unknown as EfcBridge["on"],
    };

    const result = await importStlViaDialog(bridge);
    expect(result).not.toBeNull();
    expect(result!.name).toBe("tri.stl");
    expect(result!.sourcePath).toBe("C:\\parts\\tri.stl");
    expect(result!.geometry.getAttribute("position").count).toBe(3);
    // the read must go through the dialog-approved path
    expect(invoke).toHaveBeenCalledWith("fs:readFile", { path: "C:\\parts\\tri.stl" });
  });
});
