// Bundles the Electron main process and preload script with esbuild.
// Preload must be a single self-contained file because the renderer runs with
// sandbox: true (sandboxed preloads cannot require external modules).
import { build } from "esbuild";

await build({
  entryPoints: {
    main: "src/main/index.ts",
    preload: "src/preload/index.ts",
  },
  bundle: true,
  platform: "node",
  format: "cjs",
  target: "node20",
  outdir: "dist",
  external: ["electron"],
  sourcemap: true,
  logLevel: "info",
});
