import { describe, expect, it } from "vitest";
import { MOONS } from "../src/data/bodies";
import { moonOffset, moonVisualDistance, scaleDistance, spinAngle, toScene, visualRadius } from "../src/astro/layout";
import { J2000_MS } from "../src/astro/time";

describe("layout", () => {
  it("compresses distance with a square root and keeps true mode linear", () => {
    expect(scaleDistance(4, "compressed")).toBeCloseTo(2, 12);
    expect(scaleDistance(4, "true")).toBe(4);
  });
  it("converts ecliptic coordinates to y-up scene coordinates", () => {
    const [x, y, z] = toScene({ x: 1, y: 2, z: 3 }, "true");
    expect([x, y, z]).toEqual([1, 3, -2]);
  });
  it("preserves direction under compression", () => {
    const [x, y, z] = toScene({ x: 4, y: 0, z: 0 }, "compressed");
    expect(x).toBeCloseTo(2, 12);
    expect(y).toBeCloseTo(0, 12);
    expect(z).toBeCloseTo(0, 12);
  });
  it("sizes Earth at 0.06 scene units", () => {
    expect(visualRadius(6371)).toBeCloseTo(0.06, 12);
  });
  it("places every moon outside its parent and inside a few radii", () => {
    const parents: Record<string, number> = { Earth: 6371, Jupiter: 69911, Saturn: 58232 };
    for (const m of MOONS) {
      const pr = parents[m.parent]!;
      const d = moonVisualDistance(m, pr);
      expect(d / visualRadius(pr)).toBeGreaterThan(2);
      expect(d / visualRadius(pr)).toBeLessThan(5);
    }
  });
  it("keeps the moon at a constant distance on its orbit", () => {
    const m = MOONS[0]!;
    const d0 = Math.hypot(...moonOffset(m, 6371, J2000_MS));
    const d1 = Math.hypot(...moonOffset(m, 6371, J2000_MS + 9 * 86_400_000));
    expect(d1).toBeCloseTo(d0, 10);
  });
  it("puts the Moon at its J2000 mean longitude (218.3 degrees)", () => {
    const [x, , z] = moonOffset(MOONS[0]!, 6371, J2000_MS);
    const lon = ((Math.atan2(-z, x) * 180) / Math.PI + 360) % 360;
    // The 5.1 degree tilt of the orbit plane shifts the projected longitude by about 0.1 degrees.
    expect(Math.abs(lon - 218.316)).toBeLessThan(0.3);
  });
  it("turns the Earth's Greenwich meridian to the Sun at 12:00 UTC", () => {
    const sun: [number, number] = [1, 0];
    const noon = spinAngle("Earth", 23.934, Date.UTC(2024, 5, 1, 12), sun);
    expect(Math.cos(noon)).toBeCloseTo(1, 9);
    const midnight = spinAngle("Earth", 23.934, Date.UTC(2024, 5, 1, 0), sun);
    expect(Math.cos(midnight)).toBeCloseTo(-1, 9);
  });
});
