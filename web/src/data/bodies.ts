/**
 * Physical data for the Sun, planets and major moons. Values follow the desktop
 * app (orbit_sim/solar_system.py and satellites.py); moon periods are given to
 * more digits than the app uses.
 */

export interface PlanetData {
  name: string;
  radiusKm: number;
  rotationHours: number; // negative = retrograde
  axialTiltDeg: number;
  color: string;
  accent: string;
  texture: string | null; // file under textures/, null = procedural
  rings: boolean;
  fact: string;
}

export interface MoonData {
  name: string;
  parent: string;
  radiusKm: number;
  orbitalDistanceKm: number;
  periodDays: number;
  inclinationDeg: number;
  /** Mean longitude at J2000 in degrees. Only the Moon's is a real value; the others are arbitrary phases. */
  phaseDeg: number;
  phaseIsReal: boolean;
  color: string;
  accent: string;
  fact: string;
}

export const SUN = {
  name: "Sun",
  radiusKm: 695700,
  color: "#ffcf70",
  accent: "#fff1c4",
  rotationHours: 609.12,
  fact: "The Sun holds 99.86 percent of the mass of the Solar System.",
};

export const PLANETS: PlanetData[] = [
  { name: "Mercury", radiusKm: 2439.7, rotationHours: 1407.6, axialTiltDeg: 0.03, color: "#948f88", accent: "#cec7bc", texture: "mercury.jpg", rings: false, fact: "The smallest planet and the closest one to the Sun." },
  { name: "Venus", radiusKm: 6051.8, rotationHours: -5832.5, axialTiltDeg: 2.6, color: "#b69870", accent: "#dfc69c", texture: "venus.jpg", rings: false, fact: "A dense atmosphere traps heat, making Venus the hottest planet." },
  { name: "Earth", radiusKm: 6371.0, rotationHours: 23.934, axialTiltDeg: 23.44, color: "#5c78a8", accent: "#b6d1a2", texture: "earth.jpg", rings: false, fact: "Earth is the only known planet with stable liquid water at the surface." },
  { name: "Mars", radiusKm: 3389.5, rotationHours: 24.62, axialTiltDeg: 25.19, color: "#a26c52", accent: "#d6aa8e", texture: "mars.jpg", rings: false, fact: "Mars hosts Olympus Mons, the tallest volcano known in the Solar System." },
  { name: "Jupiter", radiusKm: 69911, rotationHours: 9.925, axialTiltDeg: 3.13, color: "#b79576", accent: "#e4d2ba", texture: "jupiter.jpg", rings: false, fact: "Jupiter is the largest planet and has a powerful magnetosphere." },
  { name: "Saturn", radiusKm: 58232, rotationHours: 10.7, axialTiltDeg: 26.73, color: "#c4b187", accent: "#e7dcbd", texture: "saturn.jpg", rings: true, fact: "Saturn's rings are made mostly of water ice with traces of rocky debris." },
  { name: "Uranus", radiusKm: 25362, rotationHours: 17.24, axialTiltDeg: 97.77, color: "#8ebac6", accent: "#cee8ee", texture: "uranus.jpg", rings: false, fact: "Uranus rotates on its side, likely due to an ancient impact." },
  { name: "Neptune", radiusKm: 24622, rotationHours: 16.11, axialTiltDeg: 28.32, color: "#5c79b6", accent: "#afc9ec", texture: "neptune.jpg", rings: false, fact: "Neptune has supersonic winds and was discovered through mathematics first." },
];

export const MOONS: MoonData[] = [
  { name: "Moon", parent: "Earth", radiusKm: 1737.4, orbitalDistanceKm: 384400, periodDays: 27.3217, inclinationDeg: 5.1, phaseDeg: 218.316, phaseIsReal: true, color: "#b8babe", accent: "#e4e4e8", fact: "Earth's Moon stabilizes the planet's axial tilt and drives the tides." },
  { name: "Io", parent: "Jupiter", radiusKm: 1821.6, orbitalDistanceKm: 421700, periodDays: 1.769, inclinationDeg: 0.04, phaseDeg: 40, phaseIsReal: false, color: "#d8c470", accent: "#f4e6a8", fact: "Io is the most volcanically active world known in the Solar System." },
  { name: "Europa", parent: "Jupiter", radiusKm: 1560.8, orbitalDistanceKm: 671100, periodDays: 3.551, inclinationDeg: 0.47, phaseDeg: 130, phaseIsReal: false, color: "#c6baae", accent: "#e6e0d6", fact: "Europa likely hides a global salty ocean beneath its icy shell." },
  { name: "Ganymede", radiusKm: 2634.1, parent: "Jupiter", orbitalDistanceKm: 1070400, periodDays: 7.155, inclinationDeg: 0.2, phaseDeg: 250, phaseIsReal: false, color: "#9c9084", accent: "#cec2b4", fact: "Ganymede is the largest moon in the Solar System and has its own magnetic field." },
  { name: "Callisto", parent: "Jupiter", radiusKm: 2410.3, orbitalDistanceKm: 1882700, periodDays: 16.689, inclinationDeg: 0.28, phaseDeg: 320, phaseIsReal: false, color: "#78726c", accent: "#b8b2aa", fact: "Callisto preserves one of the oldest and most cratered surfaces in the Solar System." },
  { name: "Titan", parent: "Saturn", radiusKm: 2574.7, orbitalDistanceKm: 1221870, periodDays: 15.945, inclinationDeg: 0.35, phaseDeg: 90, phaseIsReal: false, color: "#c6a87c", accent: "#e8d6ae", fact: "Titan has a thick nitrogen atmosphere and lakes of liquid methane and ethane." },
];

export const KM_PER_AU = 149_597_870.7;
