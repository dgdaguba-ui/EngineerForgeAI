import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// RTL auto-cleanup only registers with vitest globals enabled; do it explicitly.
afterEach(() => {
  cleanup();
});
