import { KM_PER_AU, MOONS, PLANETS, SUN } from "../data/bodies";
import { MISSIONS } from "../data/missions";
import { distanceAu, heliocentricPosition, orbitAt } from "../astro/ephemeris";
import { moonsOf } from "../astro/layout";

export interface InfoView {
  name: string;
  kind: string;
  fact: string;
  stats: [string, string][];
}

const fmt = (n: number, d = 0) => n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

function period(days: number): string {
  return days >= 730 ? `${fmt(days / 365.25, 1)} years` : `${fmt(days, days < 100 ? 1 : 0)} days`;
}

function utcDate(ms: number): string {
  return new Date(ms).toISOString().slice(0, 10);
}

export function describe(id: string, ms: number): InfoView {
  if (id === "Sun") {
    const earth = distanceAu(heliocentricPosition("Earth", ms));
    return {
      name: SUN.name,
      kind: "Star",
      fact: SUN.fact,
      stats: [
        ["Radius", `${fmt(SUN.radiusKm)} km`],
        ["Rotation", `${fmt(SUN.rotationHours / 24, 1)} days (equator)`],
        ["Earth distance", `${fmt(earth, 4)} au`],
        ["Light travel to Earth", `${fmt(earth * 499.0047 / 60, 2)} min`],
      ],
    };
  }
  const planet = PLANETS.find((p) => p.name === id);
  if (planet) {
    const r = distanceAu(heliocentricPosition(planet.name, ms));
    const o = orbitAt(planet.name, ms);
    const days = Math.pow(o.a, 1.5) * 365.25;
    const n = moonsOf(planet.name).length;
    return {
      name: planet.name,
      kind: "Planet",
      fact: planet.fact,
      stats: [
        ["Distance from Sun", `${fmt(r, 3)} au`],
        ["In kilometres", `${fmt((r * KM_PER_AU) / 1e6, 1)} million km`],
        ["Orbital period", period(days)],
        ["Eccentricity", fmt(o.e, 4)],
        ["Radius", `${fmt(planet.radiusKm)} km`],
        ["Day length", `${fmt(Math.abs(planet.rotationHours), 1)} h${planet.rotationHours < 0 ? " (retrograde)" : ""}`],
        ["Axial tilt", `${fmt(planet.axialTiltDeg, 1)} deg`],
        ["Major moons shown", String(n)],
      ],
    };
  }
  const moon = MOONS.find((m) => m.name === id);
  if (moon) {
    return {
      name: moon.name,
      kind: `Moon of ${moon.parent}`,
      fact: moon.fact,
      stats: [
        ["Orbit radius", `${fmt(moon.orbitalDistanceKm)} km`],
        ["Orbital period", period(moon.periodDays)],
        ["Radius", `${fmt(moon.radiusKm, 1)} km`],
        ["Orbit tilt", `${fmt(moon.inclinationDeg, 2)} deg`],
        ["Position", moon.phaseIsReal ? "from mean longitude" : "illustrative phase"],
        ["Orbit drawn", "enlarged, circular"],
      ],
    };
  }
  const mission = MISSIONS.find((m) => `mission:${m.name}` === id);
  if (mission) {
    return {
      name: mission.name,
      kind: "Mission",
      fact: mission.description,
      stats: [
        ["Launch", utcDate(mission.launchMs)],
        ["Path shown until", utcDate(mission.endMs)],
        ["Frame", mission.frame === "heliocentric" ? "around the Sun" : "around Earth"],
        ["Path", "simplified, anchored to real positions"],
      ],
    };
  }
  return { name: "Solar System", kind: "", fact: "", stats: [] };
}
