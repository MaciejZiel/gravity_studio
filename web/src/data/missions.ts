/**
 * Mission paths. As in the desktop app these are schematic polylines, not
 * reconstructed trajectories: heliocentric paths are (x, y) in au in the
 * ecliptic plane, the Earth-local path is in units of the Earth marker scale.
 */

export interface MissionData {
  name: string;
  label: string;
  frame: "heliocentric" | "earth_local";
  launchMs: number;
  endMs: number;
  color: string;
  path: [number, number][];
  description: string;
}

export const MISSIONS: MissionData[] = [
  {
    name: "Parker Solar Probe", label: "Parker", frame: "heliocentric",
    launchMs: Date.UTC(2018, 7, 12, 7, 31), endMs: Date.UTC(2026, 11, 31),
    color: "#e4ae66",
    path: [[0.72, 0.0], [0.52, -0.22], [0.28, -0.08], [0.18, 0.06], [0.11, 0.0]],
    description: "Parker Solar Probe repeatedly dives into the Sun's corona.",
  },
  {
    name: "JWST", label: "JWST", frame: "heliocentric",
    launchMs: Date.UTC(2021, 11, 25, 12, 20), endMs: Date.UTC(2022, 1, 1),
    color: "#b6d6f4",
    path: [[1.0, 0.0], [1.01, -0.02], [1.018, 0.01], [1.022, 0.0]],
    description: "The James Webb Space Telescope sits near the Sun-Earth L2 point.",
  },
  {
    name: "Voyager 1", label: "Voyager 1", frame: "heliocentric",
    launchMs: Date.UTC(1977, 8, 5, 12, 56), endMs: Date.UTC(1990, 1, 14),
    color: "#aaccf4",
    path: [[1.0, 0.0], [2.1, 0.34], [5.2, 1.0], [9.6, 0.6], [18.0, -1.1], [30.0, -2.0]],
    description: "Voyager 1 used Jupiter and Saturn gravity assists to leave the planetary plane.",
  },
  {
    name: "Cassini-Huygens", label: "Cassini", frame: "heliocentric",
    launchMs: Date.UTC(1997, 9, 15, 8, 43), endMs: Date.UTC(2004, 6, 1),
    color: "#d6c498",
    path: [[1.0, 0.0], [0.72, -0.28], [0.95, 0.18], [5.2, 0.92], [9.58, 0.44]],
    description: "Cassini reached Saturn after a complex sequence of inner-planet flybys.",
  },
  {
    name: "Apollo 11", label: "Apollo 11", frame: "earth_local",
    launchMs: Date.UTC(1969, 6, 16, 13, 32), endMs: Date.UTC(1969, 6, 24, 16, 50),
    color: "#e4e4ec",
    path: [[0.0, 0.0], [0.18, -0.12], [0.48, 0.0], [0.28, 0.16], [0.0, 0.0]],
    description: "Apollo 11 carried humans from low Earth orbit to the lunar surface and back.",
  },
];
