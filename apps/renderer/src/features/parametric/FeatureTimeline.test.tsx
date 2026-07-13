import { fireEvent, render, screen } from "@testing-library/react";
import { BufferGeometry } from "three";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { IrFeature } from "../../engine/types";
import { useViewportStore } from "../../state/viewportStore";
import { useParametricStore, type ActivePart } from "./parametricStore";
import { FeatureTimeline } from "./FeatureTimeline";

const FEATURES: IrFeature[] = [
  { op: "sketch", id: "footprint", plane: "XY", profile: { kind: "rect" } },
  { op: "extrude", id: "body", distance: "H" },
  { op: "shell", id: "cavity", thickness: "T", openFaces: ["+Z"] },
  { op: "fillet", id: "corner_fillet", radius: "R", axis: "Z" },
];

function makeActive(objectId: string, features: IrFeature[]): ActivePart {
  return {
    partId: "eng-1",
    objectId,
    projectPartId: null,
    templateId: "enclosure-box",
    name: "Enclosure",
    parameters: [],
    features,
    massProps: {
      volumeMm3: 1,
      volumeCm3: 0.001,
      massG: null,
      materialId: null,
      cogMm: [0, 0, 0],
      bboxMm: { x: 1, y: 1, z: 1 },
    },
    warnings: [],
  };
}

beforeEach(() => {
  useParametricStore.getState().clear();
  useViewportStore.getState().clear();
});

describe("FeatureTimeline", () => {
  it("renders nothing when no parametric part is active", () => {
    const { container } = render(<FeatureTimeline />);
    expect(container.firstChild).toBeNull();
  });

  it("lists the features in order when its part is selected", () => {
    const objectId = useViewportStore.getState().addMesh({
      name: "Enclosure",
      sourcePath: null,
      geometry: new BufferGeometry(),
      parametricPartId: "eng-1",
    });
    useParametricStore.setState({ active: makeActive(objectId, FEATURES) });
    useViewportStore.getState().select(objectId);

    render(<FeatureTimeline />);
    expect(screen.getByTestId("feature-timeline")).toBeInTheDocument();
    // ordered, one row per feature
    for (const f of FEATURES) {
      expect(screen.getByTestId(`feature-${f.id}`)).toBeInTheDocument();
    }
    expect(screen.getByTestId("feature-cavity")).toHaveTextContent("wall T open +Z");
    expect(screen.getByTestId("feature-timeline")).toHaveTextContent("shell");
  });

  it("reorders via the move buttons, disabling them at the boundaries", () => {
    const moveFeature = vi.fn().mockResolvedValue(undefined);
    const objectId = useViewportStore.getState().addMesh({
      name: "Enclosure",
      sourcePath: null,
      geometry: new BufferGeometry(),
      parametricPartId: "eng-1",
    });
    useParametricStore.setState({ active: makeActive(objectId, FEATURES), moveFeature });
    useViewportStore.getState().select(objectId);

    render(<FeatureTimeline />);

    // first feature can't move up; last can't move down
    expect(screen.getByLabelText("Move footprint up")).toBeDisabled();
    expect(screen.getByLabelText("Move corner_fillet down")).toBeDisabled();

    fireEvent.click(screen.getByLabelText("Move body down"));
    expect(moveFeature).toHaveBeenCalledWith("body", 1);

    fireEvent.click(screen.getByLabelText("Move cavity up"));
    expect(moveFeature).toHaveBeenCalledWith("cavity", -1);
  });

  it("edits a feature's fields when its row is expanded", () => {
    const editFeature = vi.fn().mockResolvedValue(undefined);
    const objectId = useViewportStore.getState().addMesh({
      name: "Enclosure",
      sourcePath: null,
      geometry: new BufferGeometry(),
      parametricPartId: "eng-1",
    });
    useParametricStore.setState({ active: makeActive(objectId, FEATURES), editFeature });
    useViewportStore.getState().select(objectId);

    render(<FeatureTimeline />);

    // editors are collapsed by default
    expect(screen.queryByTestId("editor-body")).not.toBeInTheDocument();

    // expand the extrude row and edit its distance expression
    fireEvent.click(screen.getByRole("button", { name: /extrude body/i }));
    const editor = screen.getByTestId("editor-body");
    const input = editor.querySelector("input")!;
    fireEvent.change(input, { target: { value: "H*2" } });
    fireEvent.blur(input);
    expect(editFeature).toHaveBeenCalledWith("body", { distance: "H*2" });

    // an enum change on the fillet commits immediately
    fireEvent.click(screen.getByRole("button", { name: /fillet corner_fillet/i }));
    fireEvent.change(screen.getByLabelText("corner_fillet Axis"), { target: { value: "X" } });
    expect(editFeature).toHaveBeenCalledWith("corner_fillet", { axis: "X" });
  });

  it("hides when a different object is selected", () => {
    const objectId = useViewportStore.getState().addMesh({
      name: "Enclosure",
      sourcePath: null,
      geometry: new BufferGeometry(),
      parametricPartId: "eng-1",
    });
    useParametricStore.setState({ active: makeActive(objectId, FEATURES) });
    // select nothing
    useViewportStore.getState().select(null);
    const { container } = render(<FeatureTimeline />);
    expect(container.firstChild).toBeNull();
  });
});
