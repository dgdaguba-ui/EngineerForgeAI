/**
 * STL import flow: native dialog → allowlisted read → parse → scene object.
 * Takes the bridge as a parameter so the flow is unit-testable with a fake.
 */
import type { EfcBridge } from "@efc/ipc-contracts";
import type { BufferGeometry } from "three";

import { base64ToArrayBuffer, parseStlToGeometry } from "./stl";

export interface ImportedMesh {
  name: string;
  sourcePath: string;
  geometry: BufferGeometry;
}

export async function importStlViaDialog(bridge: EfcBridge): Promise<ImportedMesh | null> {
  const picked = await bridge.invoke("dialog:openFile", {
    title: "Import STL model",
    filters: [{ name: "STL model", extensions: ["stl", "STL"] }],
  });
  if (!picked) return null;

  const file = await bridge.invoke("fs:readFile", { path: picked.path });
  const geometry = parseStlToGeometry(base64ToArrayBuffer(file.dataBase64));
  return { name: picked.name, sourcePath: picked.path, geometry };
}
