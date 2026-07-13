/**
 * Human-readable summaries of IR features for the read-only feature timeline.
 * Pure functions over the loosely-typed IrFeature (op-specific fields are
 * read defensively).
 */
import type { IrFeature } from "../../engine/types";

export interface FeatureView {
  op: string;
  id: string;
  /** Short glyph shown in the timeline gutter. */
  glyph: string;
  /** One-line detail describing the feature's key fields. */
  detail: string;
}

const GLYPHS: Record<string, string> = {
  sketch: "✎",
  extrude: "⤒",
  hole: "◎",
  fillet: "◜",
  shell: "▣",
};

function str(feature: IrFeature, key: string): string | null {
  const v = feature[key];
  if (v === null || v === undefined) return null;
  if (typeof v === "number") return String(v);
  if (typeof v === "string") return v;
  return null;
}

export function featureDetail(feature: IrFeature): string {
  switch (feature.op) {
    case "sketch": {
      const plane = str(feature, "plane") ?? "XY";
      const profile = feature["profile"];
      const kind =
        profile && typeof profile === "object" && "kind" in profile
          ? String((profile as { kind: unknown }).kind)
          : "profile";
      return `${plane} · ${kind}`;
    }
    case "extrude":
      return `distance ${str(feature, "distance") ?? "?"}`;
    case "hole": {
      const dia = str(feature, "diameter") ?? "?";
      const count = str(feature, "count");
      const axis = str(feature, "axis") ?? "Z";
      return count && count !== "1"
        ? `⌀${dia} ×${count} along ${axis}`
        : `⌀${dia} through ${axis}`;
    }
    case "fillet":
      return `r ${str(feature, "radius") ?? "?"} ∥${str(feature, "axis") ?? "?"}`;
    case "shell": {
      const wall = str(feature, "thickness") ?? "?";
      const open = feature["openFaces"] ?? feature["open_faces"];
      const faces = Array.isArray(open) && open.length > 0 ? ` open ${open.join(",")}` : "";
      return `wall ${wall}${faces}`;
    }
    default:
      return feature.op;
  }
}

export function toFeatureView(feature: IrFeature): FeatureView {
  return {
    op: feature.op,
    id: feature.id,
    glyph: GLYPHS[feature.op] ?? "•",
    detail: featureDetail(feature),
  };
}
