/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig, type PluginOption } from "vite";

/**
 * Injects a strict CSP into the built index.html only. In dev, Vite/React
 * need inline preamble scripts and websockets, so the CSP is production-only;
 * the packaged app is what ships.
 */
function productionCsp(): PluginOption {
  const csp = [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "connect-src 'self' http://127.0.0.1:* http://localhost:*",
    "worker-src 'self' blob:",
    "font-src 'self' data:",
    "object-src 'none'",
    "base-uri 'self'",
  ].join("; ");
  return {
    name: "efc-production-csp",
    apply: "build",
    transformIndexHtml(html: string) {
      return html.replace(
        "<head>",
        `<head>\n    <meta http-equiv="Content-Security-Policy" content="${csp}" />`,
      );
    },
  };
}

export default defineConfig({
  plugins: [react(), productionCsp()],
  base: "./",
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: "dist",
    target: "chrome120",
  },
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
