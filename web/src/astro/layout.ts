/**
 * Maps real quantities to scene units. The scene is deliberately not to
 * scale: distances are compressed (square root of au) and bodies are enlarged
 * so that everything stays visible. A "true distance" mode keeps linear au.
 *
 * Scene axes are three.js axes (+y up), converted from the ecliptic frame as
 * (x, y, z)_ecl -> (x, z, -y).
 */
import { KM_PER_AU, MOONS, type MoonData } from "../data/bodies";
import { daysSinceJ2000 } from "./time";
import { heliocentricPosition, type Vec3 } from "./ephemeris";

export type DistanceMode = "compressed" | "true";

export const SUN_VISUAL_RADIUS = 0.2;

export function ecliptic(p: Vec3): [number, number, number] {
  return [p.x, p.z, -p.y];
}

export function scaleDistance(r: number, mode: DistanceMode): number {
  return mode === "compressed" ? Math.sqrt(r) : r;
}

/** Apply the distance mapping to a heliocentric ecliptic position, returning scene coordinates. */
export function toScene(p: Vec3, mode: DistanceMode): [number, number, number] {
  const r = Math.hypot(p.x, p.y, p.z);
  const k = r > 1e-9 ? scaleDistance(r, mode) / r : 0;
  return ecliptic({ x: p.x * k, y: p.y * k, z: p.z * k });
}

/** Enlarged display radius for a body, in scene units. Earth is 0.06. */
export function visualRadius(radiusKm: number): number {
  return 0.06 * Math.sqrt(radiusKm / 6371);
}

export function planetScenePosition(name: string, ms: number, mode: DistanceMode): [number, number, number] {
  return toScene(heliocentricPosition(name, ms), mode);
}

/** Distance of a moon from its parent in scene units, a log-compressed multiple of the parent's visual radius. */
export function moonVisualDistance(moon: MoonData, parentRadiusKm: number): number {
  const ratio = moon.orbitalDistanceKm / parentRadiusKm;
  return visualRadius(parentRadiusKm) * (1.2 + 0.7 * Math.log(ratio));
}

/** Point on a moon's orbit around its parent, `angle` in radians, in scene coordinates. */
export function moonOrbitPoint(moon: MoonData, parentRadiusKm: number, angle: number): [number, number, number] {
  const d = moonVisualDistance(moon, parentRadiusKm);
  const inc = (moon.inclinationDeg * Math.PI) / 180;
  // Circular orbit in the ecliptic plane, rotated about the x axis by the inclination.
  const x = d * Math.cos(angle);
  const yPlane = d * Math.sin(angle);
  return ecliptic({ x, y: yPlane * Math.cos(inc), z: yPlane * Math.sin(inc) });
}

/** Offset of a moon from its parent in scene coordinates at time `ms`. */
export function moonOffset(moon: MoonData, parentRadiusKm: number, ms: number): [number, number, number] {
  const angle = ((moon.phaseDeg + (360 / moon.periodDays) * daysSinceJ2000(ms)) * Math.PI) / 180;
  return moonOrbitPoint(moon, parentRadiusKm, angle);
}

export function moonsOf(parent: string): MoonData[] {
  return MOONS.filter((m) => m.parent === parent);
}

/** Real separation in au, used for info panels. */
export function auFromKm(km: number): number {
  return km / KM_PER_AU;
}

/**
 * Spin angle about the body's own axis, radians. Earth is phased to the
 * clock so that the Greenwich meridian faces the Sun at 12:00 UTC.
 */
export function spinAngle(name: string, rotationHours: number, ms: number, sunDirXZ: [number, number]): number {
  if (name === "Earth") {
    const hours = (ms / 3_600_000) % 24;
    return Math.atan2(-sunDirXZ[1], sunDirXZ[0]) + ((hours - 12) / 24) * 2 * Math.PI;
  }
  const turns = (daysSinceJ2000(ms) * 24) / rotationHours;
  return (turns % 1) * 2 * Math.PI;
}
