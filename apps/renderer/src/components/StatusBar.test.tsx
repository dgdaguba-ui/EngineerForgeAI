import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { EngineStatus } from "@efc/ipc-contracts";

import { StatusBar } from "./StatusBar";

const base: EngineStatus = {
  state: "running",
  pid: 1,
  port: 9001,
  baseUrl: "http://127.0.0.1:9001",
  message: "engine ready",
  restarts: 0,
};

describe("StatusBar", () => {
  it("shows browser mode when the bridge is missing", () => {
    render(<StatusBar status={null} bridgeAvailable={false} />);
    expect(screen.getByTestId("status-bar")).toHaveTextContent("Browser mode");
  });

  it("shows running state with the engine URL", () => {
    render(<StatusBar status={base} bridgeAvailable={true} />);
    expect(screen.getByTestId("status-bar")).toHaveTextContent("Engine running");
    expect(screen.getByTestId("status-bar")).toHaveTextContent("http://127.0.0.1:9001");
  });

  it("shows failure message and a retry button", () => {
    render(
      <StatusBar
        status={{ ...base, state: "failed", message: "python missing" }}
        bridgeAvailable={true}
        onRestart={() => undefined}
      />,
    );
    expect(screen.getByTestId("status-bar")).toHaveTextContent("Engine failed");
    expect(screen.getByTestId("status-bar")).toHaveTextContent("python missing");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
