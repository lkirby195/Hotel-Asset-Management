import { describe, it, expect } from "vitest";
import { formatCurrency, formatPercent, cn } from "../utils";

describe("formatCurrency", () => {
  it("formats positive cents to dollar string", () => {
    expect(formatCurrency(100000)).toBe("$1,000");
  });

  it("formats zero", () => {
    expect(formatCurrency(0)).toBe("$0");
  });

  it("formats negative values", () => {
    expect(formatCurrency(-50050)).toBe("-$501");
  });

  it("rounds to whole dollars", () => {
    expect(formatCurrency(99)).toBe("$1");
    expect(formatCurrency(49)).toBe("$0");
  });

  it("formats large values with commas", () => {
    expect(formatCurrency(1234567800)).toBe("$12,345,678");
  });
});

describe("formatPercent", () => {
  it("formats positive percentage with plus sign", () => {
    expect(formatPercent(25.0)).toBe("+25.0%");
  });

  it("formats negative percentage", () => {
    expect(formatPercent(-15.3)).toBe("-15.3%");
  });

  it("formats zero with plus sign", () => {
    expect(formatPercent(0)).toBe("+0.0%");
  });

  it("returns dash for null", () => {
    expect(formatPercent(null)).toBe("—");
  });

  it("rounds to one decimal", () => {
    expect(formatPercent(33.333)).toBe("+33.3%");
  });
});

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("px-2", "py-1")).toBe("px-2 py-1");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "always")).toBe("base always");
  });

  it("merges tailwind conflicts", () => {
    // tw-merge should resolve px-2 vs px-4
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
});
