import { describe, expect, it } from "vitest";
import { fbm, rng, valueNoise3 } from "../src/render/procedural";

describe("procedural noise", () => {
  it("is deterministic and bounded", () => {
    expect(valueNoise3(1.3, 2.7, 3.1, 5)).toBe(valueNoise3(1.3, 2.7, 3.1, 5));
    for (let i = 0; i < 200; i++) {
      const v = fbm(i * 0.37, i * 0.11, i * 0.23, 5, 3);
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    }
  });
  it("differs between seeds", () => {
    expect(valueNoise3(1.5, 1.5, 1.5, 1)).not.toBe(valueNoise3(1.5, 1.5, 1.5, 2));
  });
  it("seeded rng repeats", () => {
    const a = rng(9);
    const b = rng(9);
    expect([a(), a(), a()]).toEqual([b(), b(), b()]);
  });
});
