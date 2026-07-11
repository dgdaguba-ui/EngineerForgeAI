/**
 * Minimal .env loader for the dev workflow (Electron does not load .env).
 * Parses KEY=value lines; existing process env always wins. No dependency.
 */
import { existsSync, readFileSync } from "node:fs";

export function parseDotenv(content: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq <= 0) continue;
    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    // strip inline comments only for unquoted values
    const quoted =
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"));
    if (quoted) {
      value = value.slice(1, -1);
    } else {
      const hash = value.indexOf(" #");
      if (hash >= 0) value = value.slice(0, hash).trim();
    }
    if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) {
      out[key] = value;
    }
  }
  return out;
}

/** Load a .env file into process.env without overriding existing variables. */
export function loadDotenvFile(filePath: string): void {
  if (!existsSync(filePath)) return;
  const parsed = parseDotenv(readFileSync(filePath, "utf8"));
  for (const [key, value] of Object.entries(parsed)) {
    if (process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}
