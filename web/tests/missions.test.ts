import * as THREE from "three";
import { describe, expect, it } from "vitest";
import { heliocentricPosition, longitudeDeg } from "../src/astro/ephemeris";
import { L2_AU, L2_MIN_SCENE_OFFSET, missionCurve, missionPointAt } from "../src/astro/missionpath";
import { MOONS, PLANETS } from "../src/data/bodies";
import { MISSIONS, type MissionData } from "../src/data/missions";
import { moonOffset, planetScenePosition, toScene } from "../src/astro/layout";

const MODES = ["compressed", "true"] as const;
const mission = (name: string): MissionData => MISSIONS.find((m) => m.name === name)!;
const utc = (y: number, m: number, d: number, h = 0, min = 0) => Date.UTC(y, m - 1, d, h, min);
const EARTH_KM = PLANETS.find((p) => p.name === "Earth")!.radiusKm;
const MOON = MOONS.find((m) => m.name === "Moon")!;

function at(name: string, ms: number, mode: (typeof MODES)[number]): THREE.Vector3 {
  const m = mission(name);
  return missionPointAt(m, missionCurve(m, mode), ms);
}

function planet(name: string, ms: number, mode: (typeof MODES)[number]): THREE.Vector3 {
  return new THREE.Vector3(...planetScenePosition(name, ms, mode));
}

/** Heliocentric ecliptic longitude of a scene-space point, in degrees. */
function sceneLongitude(v: THREE.Vector3): number {
  return longitudeDeg({ x: v.x, y: -v.z, z: v.y });
}

describe("mission paths meet the planets on the encounter dates", () => {
  const encounters: [string, number, string][] = [
    ["Voyager 1", utc(1979, 3, 5, 12, 5), "Jupiter"],
    ["Voyager 1", utc(1980, 11, 12, 23, 46), "Saturn"],
    ["Cassini-Huygens", utc(1998, 4, 26), "Venus"],
    ["Cassini-Huygens", utc(1999, 6, 24), "Venus"],
    ["Cassini-Huygens", utc(1999, 8, 18), "Earth"],
    ["Cassini-Huygens", utc(2000, 12, 30), "Jupiter"],
    ["Cassini-Huygens", utc(2004, 7, 1), "Saturn"],
    ["Parker Solar Probe", utc(2018, 10, 3), "Venus"],
    ["Parker Solar Probe", utc(2021, 10, 16), "Venus"],
    ["Parker Solar Probe", utc(2024, 11, 6), "Venus"],
    ["Voyager 1", utc(1977, 9, 5, 12, 56), "Earth"],
  ];
  for (const mode of MODES) {
    for (const [name, ms, body] of encounters) {
      it(`${name} is at ${body} on ${new Date(ms).toISOString().slice(0, 10)} (${mode})`, () => {
        expect(at(name, ms, mode).distanceTo(planet(body, ms, mode))).toBeLessThan(1e-6);
      });
    }
  }

  it("puts Voyager 1 near the real longitudes of Jupiter and Saturn, not at the old schematic angles", () => {
    const jup = at("Voyager 1", utc(1979, 3, 5, 12, 5), "true");
    const sat = at("Voyager 1", utc(1980, 11, 12, 23, 46), "true");
    expect(Math.abs(sceneLongitude(jup) - 127.5)).toBeLessThan(2);
    expect(Math.abs(sceneLongitude(sat) - 182)).toBeLessThan(2);
  });

  it("puts Cassini at Saturn's longitude (about 106 degrees) in July 2004", () => {
    const end = at("Cassini-Huygens", utc(2004, 7, 1), "true");
    expect(Math.abs(sceneLongitude(end) - 106)).toBeLessThan(2);
  });
});

describe("Voyager 1 leaves the ecliptic plane", () => {
  it("stays in the plane at Saturn and is well above it later", () => {
    const sat = at("Voyager 1", utc(1980, 11, 12, 23, 46), "true");
    const later = at("Voyager 1", utc(1990, 2, 14), "true");
    expect(Math.abs(sat.y)).toBeLessThan(0.6);
    expect(later.y).toBeGreaterThan(15);
    expect(later.length()).toBeCloseTo(40.5, 5);
  });
});

describe("JWST follows Earth at Sun-Earth L2", () => {
  for (const mode of MODES) {
    it(`sits on the Sun-Earth line beyond Earth on the 2022-01-24 bookmark (${mode})`, () => {
      const ms = utc(2022, 1, 24, 19, 0);
      const j = at("JWST", ms, mode);
      const e = planet("Earth", ms, mode);
      expect(j.clone().normalize().angleTo(e.clone().normalize())).toBeLessThan(1e-6);
      expect(j.length()).toBeGreaterThan(e.length());
      expect(Math.abs(sceneLongitude(j) - sceneLongitude(e))).toBeLessThan(1e-4);
    });
    it(`keeps following Earth months later (${mode})`, () => {
      for (const ms of [utc(2022, 6, 3), utc(2022, 9, 14), utc(2022, 12, 20)]) {
        const j = at("JWST", ms, mode);
        const e = planet("Earth", ms, mode);
        // The path is interpolated between monthly waypoints, so allow a degree.
        expect(Math.abs(sceneLongitude(j) - sceneLongitude(e))).toBeLessThan(1);
        expect(j.length()).toBeGreaterThan(e.length());
      }
    });
  }

  it("uses the real distance when it is large enough to see, about 1.5 million km", () => {
    expect(L2_AU * 149_597_870.7).toBeGreaterThan(1.4e6);
    expect(L2_AU * 149_597_870.7).toBeLessThan(1.6e6);
    const ms = utc(2022, 1, 24, 19, 0);
    const j = at("JWST", ms, "true");
    const e = planet("Earth", ms, "true");
    expect(j.distanceTo(e)).toBeCloseTo(L2_MIN_SCENE_OFFSET, 6);
  });
});

describe("Apollo 11 reaches the Moon", () => {
  const m = mission("Apollo 11");
  const moonAt = (ms: number) => new THREE.Vector3(...moonOffset(MOON, EARTH_KM, ms));

  it("is at the Moon at landing and at lunar liftoff", () => {
    const curve = missionCurve(m, "compressed");
    for (const ms of [utc(1969, 7, 20, 20, 17), utc(1969, 7, 21, 17, 54)]) {
      expect(missionPointAt(m, curve, ms).distanceTo(moonAt(ms))).toBeLessThan(1e-9);
    }
  });

  it("is next to Earth at launch and at splashdown, and between Earth and the Moon on the way", () => {
    const curve = missionCurve(m, "compressed");
    const start = missionPointAt(m, curve, m.launchMs);
    const end = missionPointAt(m, curve, m.endMs);
    const moonDist = moonAt(utc(1969, 7, 20, 20, 17)).length();
    expect(start.length()).toBeLessThan(0.4 * moonDist);
    expect(end.length()).toBeLessThan(0.4 * moonDist);
    const mid = missionPointAt(m, curve, utc(1969, 7, 18, 3));
    expect(mid.length()).toBeGreaterThan(0.3 * moonDist);
    expect(mid.length()).toBeLessThan(0.7 * moonDist);
  });
});

describe("mission data", () => {
  it("has waypoints in time order, starting at launch and ending at the end date", () => {
    for (const m of MISSIONS) {
      expect(m.waypoints[0]!.at).toBe(m.launchMs);
      expect(m.waypoints[m.waypoints.length - 1]!.at).toBe(m.endMs);
      for (let i = 1; i < m.waypoints.length; i++) expect(m.waypoints[i]!.at).toBeGreaterThan(m.waypoints[i - 1]!.at);
    }
  });
  it("only references known planets", () => {
    for (const m of MISSIONS) {
      for (const w of m.waypoints) {
        const a = w.anchor;
        const name = "body" in a ? a.body : "bodyDir" in a ? a.bodyDir : null;
        if (name) expect(() => heliocentricPosition(name, w.at)).not.toThrow();
      }
    }
  });
  it("converts heliocentric anchors with the same mapping as the planets", () => {
    const p = heliocentricPosition("Jupiter", utc(1979, 3, 5));
    expect(toScene(p, "true")[0]).toBeCloseTo(planetScenePosition("Jupiter", utc(1979, 3, 5), "true")[0], 12);
  });
});
