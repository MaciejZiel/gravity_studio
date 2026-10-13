import { describe, expect, it } from "vitest";
import {
  distanceAu,
  heliocentricPosition,
  longitudeDeg,
  orbitOutline,
  solveKepler,
  wrapDeg,
} from "../src/astro/ephemeris";
import { J2000_MS, MS_PER_DAY, julianDate } from "../src/astro/time";

const HOUR = MS_PER_DAY / 24;

/** Find the instant of the minimum or maximum of f in [from, to] by coarse scan plus golden-section refinement. */
function extremum(f: (ms: number) => number, from: number, to: number, sign: 1 | -1): number {
  let best = from;
  let bestV = Infinity;
  for (let t = from; t <= to; t += 6 * HOUR) {
    const v = sign * f(t);
    if (v < bestV) {
      bestV = v;
      best = t;
    }
  }
  let lo = best - 6 * HOUR;
  let hi = best + 6 * HOUR;
  const g = (Math.sqrt(5) - 1) / 2;
  for (let i = 0; i < 60; i++) {
    const a = hi - g * (hi - lo);
    const b = lo + g * (hi - lo);
    if (sign * f(a) < sign * f(b)) hi = b;
    else lo = a;
  }
  return (lo + hi) / 2;
}

const earthR = (ms: number) => distanceAu(heliocentricPosition("Earth", ms));

describe("time", () => {
  it("maps the J2000 epoch to JD 2451545.0", () => {
    expect(julianDate(J2000_MS)).toBeCloseTo(2451545.0, 9);
  });
});

describe("Kepler solver", () => {
  it("satisfies M = E - e sin E across eccentricities", () => {
    for (const e of [0, 0.0167, 0.2056, 0.6, 0.95]) {
      for (let M = -3.1; M <= 3.1; M += 0.37) {
        const E = solveKepler(M, e);
        expect(E - e * Math.sin(E)).toBeCloseTo(M, 10);
      }
    }
  });
  it("wraps angles into (-180, 180]", () => {
    expect(wrapDeg(190)).toBeCloseTo(-170, 12);
    expect(wrapDeg(-540)).toBeCloseTo(180, 12);
    expect(wrapDeg(360)).toBeCloseTo(0, 12);
  });
});

describe("Earth at J2000", () => {
  // Reference: JPL Horizons, heliocentric ecliptic J2000, 2000-01-01 12:00 TDB:
  // x = -0.1771, y = 0.9672, z ~ 0, r = 0.98333 au.
  const p = heliocentricPosition("Earth", J2000_MS);
  it("has the reference heliocentric coordinates", () => {
    expect(p.x).toBeCloseTo(-0.1771, 2);
    expect(p.y).toBeCloseTo(0.9672, 2);
    expect(Math.abs(p.z)).toBeLessThan(1e-4);
  });
  it("is 0.98333 au from the Sun", () => {
    expect(Math.abs(distanceAu(p) - 0.98333)).toBeLessThan(0.0005);
  });
  it("sits at heliocentric longitude 100.37 degrees", () => {
    expect(Math.abs(longitudeDeg(p) - 100.37)).toBeLessThan(0.05);
  });
});

describe("Earth in 2024", () => {
  it("reaches perihelion on 3 Jan 2024 at 0.98330 au", () => {
    // Reference: perihelion 2024-01-03 00:38 UTC, 147.098 million km.
    const t = extremum(earthR, Date.UTC(2023, 11, 20), Date.UTC(2024, 0, 20), 1);
    const ref = Date.UTC(2024, 0, 3, 0, 38);
    expect(Math.abs(t - ref)).toBeLessThan(2 * MS_PER_DAY);
    expect(Math.abs(earthR(t) - 0.9833)).toBeLessThan(0.0005);
  });
  it("reaches aphelion on 5 Jul 2024 at 1.0167 au", () => {
    // Reference: aphelion 2024-07-05 05:06 UTC, 152.099 million km.
    const t = extremum(earthR, Date.UTC(2024, 5, 20), Date.UTC(2024, 6, 20), -1);
    const ref = Date.UTC(2024, 6, 5, 5, 6);
    expect(Math.abs(t - ref)).toBeLessThan(2 * MS_PER_DAY);
    expect(Math.abs(earthR(t) - 1.0167)).toBeLessThan(0.0005);
  });
  it("is at the March equinox longitude on 20 Mar 2024 03:06 UTC", () => {
    // At the equinox the Sun's apparent longitude is 0 in the equinox of date, so Earth's
    // heliocentric longitude is 180 degrees of date. Our frame is J2000, which differs by general
    // precession (50.29 arcsec/yr over 24.22 yr = 0.338 degrees).
    const lon = longitudeDeg(heliocentricPosition("Earth", Date.UTC(2024, 2, 20, 3, 6)));
    const expected = 180 - (50.29 * 24.22) / 3600;
    expect(Math.abs(lon - expected)).toBeLessThan(0.1);
  });
});

describe("other planets", () => {
  it("keep distances inside their perihelion and aphelion bounds over the whole timeline", () => {
    const bounds: Record<string, [number, number]> = {
      Mercury: [0.307, 0.467],
      Venus: [0.717, 0.730],
      Mars: [1.38, 1.67],
      Jupiter: [4.95, 5.46],
      Saturn: [9.0, 10.1],
      Uranus: [18.2, 20.1],
      Neptune: [29.7, 30.4],
    };
    for (const [name, [lo, hi]] of Object.entries(bounds)) {
      for (let y = 1960; y <= 2165; y += 3) {
        const r = distanceAu(heliocentricPosition(name, Date.UTC(y, 0, 1)));
        expect(r).toBeGreaterThan(lo);
        expect(r).toBeLessThan(hi);
      }
    }
  });
  it("switch from Table 1 to Table 2a at 2050 moves positions by less than 0.2 degrees", () => {
    const switchMs = (2469807.5 - 2440587.5) * MS_PER_DAY; // T = 0.5 Julian centuries
    for (const name of ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]) {
      const before = longitudeDeg(heliocentricPosition(name, switchMs - 60_000));
      const after = longitudeDeg(heliocentricPosition(name, switchMs + 60_000));
      let d = Math.abs(before - after);
      if (d > 180) d = 360 - d;
      expect(d).toBeLessThan(0.2);
    }
  });
  it("Mars is near opposition on 2025-01-16 (Earth and Mars on the same side)", () => {
    const t = Date.UTC(2025, 0, 16);
    const e = longitudeDeg(heliocentricPosition("Earth", t));
    const m = longitudeDeg(heliocentricPosition("Mars", t));
    let d = Math.abs(e - m);
    if (d > 180) d = 360 - d;
    expect(d).toBeLessThan(3);
  });
});

describe("orbit outline", () => {
  it("is closed and passes through the current position radius range", () => {
    const pts = orbitOutline("Mars", J2000_MS, 180);
    expect(pts).toHaveLength(181);
    expect(distanceAu(pts[0]!)).toBeCloseTo(distanceAu(pts[180]!), 9);
    const rs = pts.map(distanceAu);
    expect(Math.min(...rs)).toBeCloseTo(1.3814, 2);
    expect(Math.max(...rs)).toBeCloseTo(1.6660, 2);
  });
});
