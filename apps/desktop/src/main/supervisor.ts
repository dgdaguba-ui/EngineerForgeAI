/**
 * EngineSupervisor — spawns, monitors, and restarts the Python engine sidecar.
 *
 * Lifecycle: stopped → starting → running; crashes trigger restarting with
 * exponential backoff (max 5 attempts) before landing on failed. Every
 * transition is emitted to the provided listener (forwarded to the renderer).
 */
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import net from "node:net";

import type { EngineStatus } from "@efc/ipc-contracts";

import { buildEngineArgs, nextBackoffMs, resolvePythonPath } from "./engine-locator.js";

const MAX_RESTARTS = 5;
const HEALTH_TIMEOUT_MS = 30_000;
const HEALTH_POLL_MS = 500;

export interface SupervisorOptions {
  engineDir: string;
  token: string;
  pythonOverride?: string | null;
  onStatus?: (status: EngineStatus) => void;
  log?: (line: string) => void;
}

export async function getFreePort(): Promise<number> {
  return await new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.once("error", reject);
    srv.listen(0, "127.0.0.1", () => {
      const address = srv.address();
      if (address && typeof address === "object") {
        const port = address.port;
        srv.close(() => resolve(port));
      } else {
        srv.close(() => reject(new Error("could not allocate port")));
      }
    });
  });
}

export class EngineSupervisor {
  private child: ChildProcess | null = null;
  private stopping = false;
  private restarts = 0;
  private status: EngineStatus = {
    state: "stopped",
    pid: null,
    port: null,
    baseUrl: null,
    message: "not started",
    restarts: 0,
  };

  constructor(private readonly opts: SupervisorOptions) {}

  getStatus(): EngineStatus {
    return { ...this.status };
  }

  getToken(): string {
    return this.opts.token;
  }

  private setStatus(patch: Partial<EngineStatus>): void {
    this.status = { ...this.status, ...patch, restarts: this.restarts };
    this.opts.onStatus?.(this.getStatus());
  }

  private log(line: string): void {
    this.opts.log?.(line);
  }

  async start(): Promise<EngineStatus> {
    if (this.status.state === "running" || this.status.state === "starting") {
      return this.getStatus();
    }
    this.stopping = false;

    const python = resolvePythonPath({
      engineDir: this.opts.engineDir,
      envOverride: this.opts.pythonOverride ?? process.env.EFC_ENGINE_PYTHON,
      platform: process.platform,
      fs: { exists: (p) => existsSync(p) },
    });
    if (!python) {
      this.setStatus({
        state: "failed",
        message:
          "Python 3.12 interpreter not found. Run `uv venv --python 3.12 .venv && uv sync` " +
          `in ${this.opts.engineDir}, or set EFC_ENGINE_PYTHON.`,
      });
      return this.getStatus();
    }

    const port = await getFreePort();
    const baseUrl = `http://127.0.0.1:${port}`;
    this.setStatus({ state: "starting", port, baseUrl, message: "spawning engine" });

    const child = spawn(python, buildEngineArgs(port), {
      cwd: this.opts.engineDir,
      env: {
        ...process.env,
        EFC_ENGINE_TOKEN: this.opts.token,
        PYTHONUNBUFFERED: "1",
      },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    this.child = child;
    this.setStatus({ pid: child.pid ?? null, message: "waiting for engine health" });

    child.stdout?.on("data", (d: Buffer) => this.log(`[engine] ${d.toString().trimEnd()}`));
    child.stderr?.on("data", (d: Buffer) => this.log(`[engine] ${d.toString().trimEnd()}`));

    child.on("exit", (code, signal) => {
      this.log(`[engine] exited code=${code} signal=${signal}`);
      this.child = null;
      if (this.stopping) {
        this.setStatus({ state: "stopped", pid: null, message: "stopped" });
        return;
      }
      void this.handleCrash(code);
    });

    const healthy = await this.waitForHealth(baseUrl);
    // Re-read state through getStatus(): the guard at the top of start() would
    // otherwise leave TS with stale narrowing across the awaits above.
    const stateAfterWait = this.getStatus().state;
    if (healthy) {
      this.restarts = 0;
      this.setStatus({ state: "running", message: "engine ready" });
    } else if (!this.stopping && stateAfterWait === "starting") {
      this.log("[supervisor] engine did not become healthy in time; killing");
      this.killChild();
      this.setStatus({ state: "failed", message: "engine failed health check (30s timeout)" });
    }
    return this.getStatus();
  }

  private async handleCrash(code: number | null): Promise<void> {
    if (this.restarts >= MAX_RESTARTS) {
      this.setStatus({
        state: "failed",
        pid: null,
        message: `engine crashed (code=${code}); gave up after ${MAX_RESTARTS} restarts`,
      });
      return;
    }
    const delay = nextBackoffMs(this.restarts);
    this.restarts += 1;
    this.setStatus({
      state: "restarting",
      pid: null,
      message: `engine crashed (code=${code}); restart ${this.restarts}/${MAX_RESTARTS} in ${delay}ms`,
    });
    await new Promise((r) => setTimeout(r, delay));
    if (!this.stopping) {
      this.setStatus({ state: "stopped", message: "restarting" });
      await this.start();
    }
  }

  private async waitForHealth(baseUrl: string): Promise<boolean> {
    const deadline = Date.now() + HEALTH_TIMEOUT_MS;
    while (Date.now() < deadline && !this.stopping && this.child) {
      try {
        const res = await fetch(`${baseUrl}/health`, {
          signal: AbortSignal.timeout(2000),
        });
        if (res.ok) return true;
      } catch {
        // engine not up yet — keep polling
      }
      await new Promise((r) => setTimeout(r, HEALTH_POLL_MS));
    }
    return false;
  }

  private killChild(): void {
    if (!this.child) return;
    try {
      this.child.kill();
    } catch {
      // already gone
    }
    this.child = null;
  }

  async restart(): Promise<EngineStatus> {
    await this.stop();
    this.restarts = 0;
    return await this.start();
  }

  async stop(): Promise<void> {
    this.stopping = true;
    if (this.child) {
      const child = this.child;
      const exited = new Promise<void>((resolve) => child.once("exit", () => resolve()));
      child.kill();
      const timeout = new Promise<void>((resolve) => setTimeout(resolve, 3000));
      await Promise.race([exited, timeout]);
      if (this.child) {
        try {
          this.child.kill("SIGKILL");
        } catch {
          // already gone
        }
        this.child = null;
      }
    }
    this.setStatus({ state: "stopped", pid: null, message: "stopped" });
  }
}
