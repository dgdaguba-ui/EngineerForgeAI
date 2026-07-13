import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useParametricStore } from "../parametric/parametricStore";
import { ChatPanel } from "./ChatPanel";
import { useChatStore, type ChatActionState } from "./chatStore";

function pendingUpdateAction(over: Partial<ChatActionState> = {}): ChatActionState {
  return {
    tool: "update_part_parameters",
    ok: true,
    summary: "Proposed change to part p1: Width 40→65 mm",
    partId: "p1",
    diff: [{ paramId: "W", label: "Width", oldValue: 40, newValue: 65, unit: "mm" }],
    pending: true,
    ...over,
  };
}

function seedAssistantWith(action: ChatActionState): void {
  useChatStore.setState({
    items: [
      { id: "u1", role: "user", content: "make it 65 wide", status: "sent" },
      {
        id: "a1",
        role: "assistant",
        content: "Proposed the change.",
        status: "sent",
        actions: [action],
      },
    ],
  });
}

afterEach(() => {
  useChatStore.getState().clear();
  vi.restoreAllMocks();
});

describe("ChatPanel diff card", () => {
  it("renders a diff card with old→new for a pending proposal", () => {
    seedAssistantWith(pendingUpdateAction());
    render(<ChatPanel />);

    const card = screen.getByTestId("diff-card");
    expect(card).toHaveTextContent("Width");
    expect(card).toHaveTextContent("40mm");
    expect(card).toHaveTextContent("65mm");
    expect(screen.getByRole("button", { name: "Apply" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Discard" })).toBeInTheDocument();
  });

  it("Apply calls applyDiff and collapses the card into an applied chip", async () => {
    const applyDiff = vi
      .spyOn(useParametricStore.getState(), "applyDiff")
      .mockResolvedValue(undefined);
    seedAssistantWith(pendingUpdateAction());
    render(<ChatPanel />);

    fireEvent.click(screen.getByRole("button", { name: "Apply" }));

    await waitFor(() =>
      expect(useChatStore.getState().items[1]!.actions![0]!.resolved).toBe("applied"),
    );
    expect(applyDiff).toHaveBeenCalledWith("p1", { W: 65 });
    expect(screen.queryByTestId("diff-card")).not.toBeInTheDocument();
    expect(screen.getByText(/Edit applied/)).toBeInTheDocument();
  });

  it("Discard resolves without applying and shows a discarded chip", () => {
    const applyDiff = vi.spyOn(useParametricStore.getState(), "applyDiff");
    seedAssistantWith(pendingUpdateAction());
    render(<ChatPanel />);

    fireEvent.click(screen.getByRole("button", { name: "Discard" }));

    expect(useChatStore.getState().items[1]!.actions![0]!.resolved).toBe("discarded");
    expect(applyDiff).not.toHaveBeenCalled();
    expect(screen.queryByTestId("diff-card")).not.toBeInTheDocument();
    expect(screen.getByText(/Edit discarded/)).toBeInTheDocument();
  });

  it("a created-part action still renders as a simple chip, not a diff card", () => {
    seedAssistantWith({
      tool: "create_part_from_template",
      ok: true,
      summary: "Created L-Bracket",
      partId: "p2",
      diff: [],
      pending: false,
    });
    render(<ChatPanel />);
    expect(screen.queryByTestId("diff-card")).not.toBeInTheDocument();
    expect(screen.getByText(/Part created/)).toBeInTheDocument();
  });
});
