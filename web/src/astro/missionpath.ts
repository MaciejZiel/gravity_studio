/**
 * Turns the dated, ephemeris-anchored waypoints of a mission into scene
 * geometry. The result is shared by the renderer and by the tests, so the
 * tests check exactly what is drawn.
 */
import * as THREE from "three";
import { MOONS, PLANETS } from "../data/bodies";
import type { Anchor, MissionData, Waypoint } from "../data/missions";
import { heliocentricPosition, type Vec3 } from "./ephemeris";
import { type DistanceMode, moonOffset, toScene } from "./layout";

/** Real distance of the Sun-Earth L2 point from Earth, in au (about 1.5 million km). */
export const L2_AU = 0.01;
/** Smallest drawn L2 offset, in scene units; the marker would otherwise sit inside Earth's enlarged disc. */
export const L2_MIN_SCENE_OFFSET = 0.16;

const DEG = Math.PI / 180;
const EARTH_RADIUS_KM = PLANETS.find((p) => p.name === "Earth")!.radiusKm;
const MOON = MOONS.find((m) => m.name === "Moon")!;

function sphericalToVec(lonDeg: number, latDeg: number, r: number): Vec3 {
  const cl = Math.cos(latDeg * DEG);
  return { x: r * cl * Math.cos(lonDeg * DEG), y: r * cl * Math.sin(lonDeg * DEG), z: r * Math.sin(latDeg * DEG) };
}

function sceneVec(t: [number, number, number]): THREE.Vector3 {
  return new THREE.Vector3(t[0], t[1], t[2]);
}

/** Scene position of the Sun-Earth L2 point (or a fraction of the way to it) on `ms`. */
export function l2ScenePosition(ms: number, mode: DistanceMode, fraction = 1): THREE.Vector3 {
  const earth = heliocentricPosition("Earth", ms);
  const r = Math.hypot(earth.x, earth.y, earth.z);
  const k = 1 + (L2_AU * fraction) / r;
  const e = sceneVec(toScene(earth, mode));
  const l2 = sceneVec(toScene({ x: earth.x * k, y: earth.y * k, z: earth.z * k }, mode));
  const dir = e.clone().normalize();
  const offset = Math.max(l2.length() - e.length(), L2_MIN_SCENE_OFFSET * fraction);
  return e.addScaledVector(dir, offset);
}

export function anchorPosition(anchor: Anchor, ms: number, mode: DistanceMode): THREE.Vector3 {
  if ("body" in anchor) return sceneVec(toScene(heliocentricPosition(anchor.body, ms), mode));
  if ("bodyDir" in anchor) {
    const p = heliocentricPosition(anchor.bodyDir, ms);
    const k = anchor.radiusAu / Math.hypot(p.x, p.y, p.z);
    return sceneVec(toScene({ x: p.x * k, y: p.y * k, z: p.z * k }, mode));
  }
  if ("sphere" in anchor) return sceneVec(toScene(sphericalToVec(...anchor.sphere), mode));
  if ("l2" in anchor) return l2ScenePosition(ms, mode, anchor.l2);
  if ("moon" in anchor) return sceneVec(moonOffset(MOON, EARTH_RADIUS_KM, ms));
  return sceneVec(moonOffset(MOON, EARTH_RADIUS_KM, anchor.refMs)).multiplyScalar(anchor.towardMoon);
}

export function waypointPosition(w: Waypoint, mode: DistanceMode): THREE.Vector3 {
  return anchorPosition(w.anchor, w.at, mode);
}

export function missionPoints(m: MissionData, mode: DistanceMode): THREE.Vector3[] {
  return m.waypoints.map((w) => waypointPosition(w, mode));
}

export function missionCurve(m: MissionData, mode: DistanceMode): THREE.CatmullRomCurve3 {
  return new THREE.CatmullRomCurve3(missionPoints(m, mode), false, "centripetal");
}

/**
 * Position at time `ms`. Time is mapped piecewise-linearly onto the curve so
 * the spacecraft is exactly at each waypoint on its date; before the first
 * and after the last waypoint it stays at the end.
 */
export function missionPointAt(m: MissionData, curve: THREE.CatmullRomCurve3, ms: number, out = new THREE.Vector3()): THREE.Vector3 {
  const w = m.waypoints;
  const last = w.length - 1;
  if (ms <= w[0]!.at) return curve.getPoint(0, out);
  if (ms >= w[last]!.at) return curve.getPoint(1, out);
  let i = 0;
  while (i < last - 1 && ms >= w[i + 1]!.at) i++;
  const frac = (ms - w[i]!.at) / (w[i + 1]!.at - w[i]!.at);
  return curve.getPoint((i + frac) / last, out);
}
