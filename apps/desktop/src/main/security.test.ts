import path from "node:path";

import { describe, expect, it } from "vitest";

import { newSessionToken, PathAllowlist } from "./security.js";

describe("newSessionToken", () => {
  it("is 64 hex chars and unique per call", () => {
    const a = newSessionToken();
    const b = newSessionToken();
    expect(a).toMatch(/^[0-9a-f]{64}$/);
    expect(a).not.toBe(b);
  });
});

describe("PathAllowlist", () => {
  it("denies by default and approves exact paths", () => {
    const list = new PathAllowlist();
    const p = path.join("C:", "data", "part.stl");
    expect(list.isApproved(p)).toBe(false);
    list.approve(p);
    expect(list.isApproved(p)).toBe(true);
  });

  it("normalizes traversal segments so equivalent paths match", () => {
    const list = new PathAllowlist();
    list.approve(path.join("C:", "data", "part.stl"));
    expect(list.isApproved(path.join("C:", "data", "sub", "..", "part.stl"))).toBe(true);
  });

  it("does not approve sibling files", () => {
    const list = new PathAllowlist();
    list.approve(path.join("C:", "data", "part.stl"));
    expect(list.isApproved(path.join("C:", "data", "other.stl"))).toBe(false);
  });

  it("approveDir approves everything under the tree, not outside it", () => {
    const list = new PathAllowlist();
    const proj = path.join("C:", "work", "Bracket.efproj");
    list.approveDir(proj);
    expect(list.isApproved(path.join(proj, "project.json"))).toBe(true);
    expect(list.isApproved(path.join(proj, "assets", "part.stl"))).toBe(true);
    expect(list.isApproved(path.join("C:", "work", "other.txt"))).toBe(false);
    // traversal out of the approved dir must not pass
    expect(list.isApproved(path.join(proj, "..", "secret.txt"))).toBe(false);
    // sibling with the approved dir as a name prefix must not pass
    expect(list.isApproved(path.join("C:", "work", "Bracket.efproj-evil", "x"))).toBe(false);
  });
});
