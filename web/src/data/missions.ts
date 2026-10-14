/**
 * Mission paths. They are simplified, not reconstructed trajectories: each
 * path is a smooth curve through dated waypoints, and every waypoint is
 * anchored to the app's own ephemeris (a planet, Earth's L2 point, the Moon),
 * so a spacecraft is drawn at the body it met on the date of the encounter.
 * Between waypoints the curve is only an interpolation.
 */

export type Anchor =
  /** Heliocentric position of a planet on the waypoint date. */
  | { body: string }
  /** Direction of a planet on the date, at a fixed distance from the Sun (au). */
  | { bodyDir: string; radiusAu: number }
  /** Heliocentric ecliptic spherical position: longitude, latitude (degrees), distance (au). */
  | { sphere: [number, number, number] }
  /** Sun-Earth L2: on the Sun-Earth line beyond Earth, `l2` is the fraction of the full 0.01 au. */
  | { l2: number }
  /** Earth-local: the Moon's position on the waypoint date. */
  | { moon: true }
  /** Earth-local: a fraction of the way to where the Moon is on `refMs`. */
  | { towardMoon: number; refMs: number };

export interface Waypoint {
  at: number;
  anchor: Anchor;
  note?: string;
}

export interface MissionData {
  name: string;
  label: string;
  frame: "heliocentric" | "earth_local";
  launchMs: number;
  endMs: number;
  color: string;
  waypoints: Waypoint[];
  description: string;
}

const utc = (y: number, m: number, d: number, h = 0, min = 0): number => Date.UTC(y, m - 1, d, h, min);

export const MISSIONS: MissionData[] = [
  {
    name: "Parker Solar Probe", label: "Parker", frame: "heliocentric",
    launchMs: utc(2018, 8, 12, 7, 31), endMs: utc(2024, 12, 24, 11, 53),
    color: "#e4ae66",
    waypoints: [
      { at: utc(2018, 8, 12, 7, 31), anchor: { body: "Earth" }, note: "Launch" },
      { at: utc(2018, 10, 3), anchor: { body: "Venus" }, note: "Venus flyby 1" },
      { at: utc(2019, 12, 26), anchor: { body: "Venus" }, note: "Venus flyby 2" },
      { at: utc(2020, 7, 11), anchor: { body: "Venus" }, note: "Venus flyby 3" },
      { at: utc(2021, 2, 20), anchor: { body: "Venus" }, note: "Venus flyby 4" },
      { at: utc(2021, 10, 16), anchor: { body: "Venus" }, note: "Venus flyby 5" },
      { at: utc(2023, 8, 21), anchor: { body: "Venus" }, note: "Venus flyby 6" },
      { at: utc(2024, 11, 6), anchor: { body: "Venus" }, note: "Venus flyby 7" },
      { at: utc(2024, 12, 24, 11, 53), anchor: { bodyDir: "Venus", radiusAu: 0.046 }, note: "Closest perihelion, about 0.046 au" },
    ],
    description: "Parker Solar Probe uses seven Venus flybys to lower its orbit into the Sun's corona. Each Venus waypoint is placed at Venus on the flyby date; the closest-perihelion position is approximate.",
  },
  {
    name: "JWST", label: "JWST", frame: "heliocentric",
    launchMs: utc(2021, 12, 25, 12, 20), endMs: utc(2023, 1, 24, 19, 0),
    color: "#b6d6f4",
    waypoints: [
      { at: utc(2021, 12, 25, 12, 20), anchor: { body: "Earth" }, note: "Launch" },
      { at: utc(2022, 1, 9), anchor: { l2: 0.6 }, note: "Midcourse" },
      { at: utc(2022, 1, 24, 19, 0), anchor: { l2: 1 }, note: "L2 insertion" },
      ...Array.from({ length: 12 }, (_, i): Waypoint => ({ at: utc(2022, 2 + i, 24, 19, 0), anchor: { l2: 1 } })),
    ],
    description: "The James Webb Space Telescope travels with Earth around the Sun, about 1.5 million km beyond it on the Sun-Earth line (L2). The offset is drawn larger than life so the marker clears Earth.",
  },
  {
    name: "Voyager 1", label: "Voyager 1", frame: "heliocentric",
    launchMs: utc(1977, 9, 5, 12, 56), endMs: utc(1990, 2, 14),
    color: "#aaccf4",
    waypoints: [
      { at: utc(1977, 9, 5, 12, 56), anchor: { body: "Earth" }, note: "Launch" },
      { at: utc(1979, 3, 5, 12, 5), anchor: { body: "Jupiter" }, note: "Jupiter flyby" },
      { at: utc(1980, 11, 12, 23, 46), anchor: { body: "Saturn" }, note: "Saturn flyby" },
      { at: utc(1990, 2, 14), anchor: { sphere: [255, 32, 40.5] }, note: "Family portrait, about 40 au and 32 deg above the ecliptic (direction approximate)" },
    ],
    description: "Voyager 1 passed Jupiter and Saturn, then the Saturn flyby bent its path about 32 degrees north of the planetary plane. Jupiter and Saturn waypoints sit at those planets on the flyby dates; the last waypoint is an approximate direction.",
  },
  {
    name: "Cassini-Huygens", label: "Cassini", frame: "heliocentric",
    launchMs: utc(1997, 10, 15, 8, 43), endMs: utc(2004, 7, 1),
    color: "#d6c498",
    waypoints: [
      { at: utc(1997, 10, 15, 8, 43), anchor: { body: "Earth" }, note: "Launch" },
      { at: utc(1998, 4, 26), anchor: { body: "Venus" }, note: "Venus flyby 1" },
      { at: utc(1999, 6, 24), anchor: { body: "Venus" }, note: "Venus flyby 2" },
      { at: utc(1999, 8, 18), anchor: { body: "Earth" }, note: "Earth flyby" },
      { at: utc(2000, 12, 30), anchor: { body: "Jupiter" }, note: "Jupiter flyby" },
      { at: utc(2004, 7, 1), anchor: { body: "Saturn" }, note: "Saturn orbit insertion" },
    ],
    description: "Cassini reached Saturn after two Venus flybys, an Earth flyby and a Jupiter flyby. Each waypoint sits at that planet on the encounter date.",
  },
  {
    name: "Apollo 11", label: "Apollo 11", frame: "earth_local",
    launchMs: utc(1969, 7, 16, 13, 32), endMs: utc(1969, 7, 24, 16, 50),
    color: "#e4e4ec",
    waypoints: [
      { at: utc(1969, 7, 16, 13, 32), anchor: { towardMoon: 0.3, refMs: utc(1969, 7, 16, 17) }, note: "Launch" },
      { at: utc(1969, 7, 18, 3), anchor: { towardMoon: 0.5, refMs: utc(1969, 7, 20, 20, 17) }, note: "Outbound" },
      { at: utc(1969, 7, 20, 20, 17), anchor: { moon: true }, note: "Landing" },
      { at: utc(1969, 7, 21, 17, 54), anchor: { moon: true }, note: "Lunar liftoff" },
      { at: utc(1969, 7, 23, 6), anchor: { towardMoon: 0.5, refMs: utc(1969, 7, 21, 17, 54) }, note: "Return" },
      { at: utc(1969, 7, 24, 16, 50), anchor: { towardMoon: 0.3, refMs: utc(1969, 7, 21, 17, 54) }, note: "Splashdown" },
    ],
    description: "Apollo 11 flew from Earth to the Moon, landed on 20 July 1969 and returned. The path is aimed at where the Moon is on the landing date, at the app's enlarged Earth-Moon distance.",
  },
];
