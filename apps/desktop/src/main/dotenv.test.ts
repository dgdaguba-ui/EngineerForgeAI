import { describe, expect, it } from "vitest";

import { parseDotenv } from "./dotenv.js";

describe("parseDotenv", () => {
  it("parses simple KEY=value pairs", () => {
    expect(parseDotenv("A=1\nB=two\n")).toEqual({ A: "1", B: "two" });
  });

  it("skips comments and blank lines", () => {
    expect(parseDotenv("# comment\n\nA=1\n  # another\n")).toEqual({ A: "1" });
  });

  it("strips matching quotes", () => {
    expect(parseDotenv(`A="hello world"\nB='single'\n`)).toEqual({
      A: "hello world",
      B: "single",
    });
  });

  it("removes inline comments from unquoted values only", () => {
    expect(parseDotenv(`A=value # note\nB="kept # inside"\n`)).toEqual({
      A: "value",
      B: "kept # inside",
    });
  });

  it("ignores malformed lines and invalid keys", () => {
    expect(parseDotenv("=nokey\nnovalue\n9BAD=x\nGOOD=y")).toEqual({ GOOD: "y" });
  });

  it("keeps empty values", () => {
    expect(parseDotenv("EMPTY=\n")).toEqual({ EMPTY: "" });
  });
});
