/**
 * Editable-field descriptors for the Feature Timeline's inline editor.
 * Pure functions over the loosely-typed IrFeature. Only scalar fields are
 * exposed — expression/number fields as text and enum fields as selects.
 * Complex fields (sketch profiles, polygon points, shell open-faces,
 * hole spread axis, extrude sketch reference) are intentionally omitted here
 * rather than shown with a fake editor; they remain editable via the AI / IR.
 */
import type { IrFeature } from "../../engine/types";

export type FeatureFieldKind = "expr" | "enum";

export interface FeatureField {
  /** camelCase field key sent to the engine. */
  key: string;
  label: string;
  kind: FeatureFieldKind;
  /** Current value rendered as a string (expression text or enum literal). */
  value: string;
  /** Allowed values for enum fields. */
  options?: string[];
}

const AXES = ["X", "Y", "Z"];
const PLANES = ["XY", "YZ", "XZ"];

function raw(feature: IrFeature, key: string): string {
  const v = feature[key];
  if (typeof v === "number") return String(v);
  if (typeof v === "string") return v;
  return "";
}

function expr(feature: IrFeature, key: string, label: string): FeatureField {
  return { key, label, kind: "expr", value: raw(feature, key) };
}

function enumField(
  feature: IrFeature,
  key: string,
  label: string,
  options: string[],
): FeatureField {
  return { key, label, kind: "enum", value: raw(feature, key), options };
}

export function editableFields(feature: IrFeature): FeatureField[] {
  switch (feature.op) {
    case "sketch":
      return [enumField(feature, "plane", "Plane", PLANES)];
    case "extrude":
      return [expr(feature, "distance", "Distance")];
    case "hole":
      return [
        expr(feature, "diameter", "Diameter"),
        expr(feature, "u", "u"),
        expr(feature, "v", "v"),
        expr(feature, "count", "Count"),
        expr(feature, "spacing", "Spacing"),
        enumField(feature, "axis", "Axis", AXES),
      ];
    case "fillet":
      return [
        expr(feature, "radius", "Radius"),
        enumField(feature, "axis", "Axis", AXES),
      ];
    case "shell":
      return [expr(feature, "thickness", "Thickness")];
    default:
      return [];
  }
}
