/**
 * Heliocentric planet positions from the JPL approximate Keplerian elements
 * (E. M. Standish, "Keplerian Elements for Approximate Positions of the Major
 * Planets", https://ssd.jpl.nasa.gov/planets/approx_pos.html).
 *
 * Table 1 is used inside its validity window (1800-2050), Table 2a with the
 * extra M terms of Table 2b after that. Output is in the mean ecliptic and
 * equinox of J2000, in astronomical units, +z towards the ecliptic north.
 */
import { centuriesSinceJ2000 } from "./time";

export interface Elements {
  a: number; // au
  e: number;
  I: number; // deg
  L: number; // deg
  varpi: number; // deg, longitude of perihelion
  Omega: number; // deg, longitude of ascending node
}

export interface ElementSet {
  at: Elements;
  rate: Elements; // per Julian century
  /** Table 2b terms, only for Jupiter to Neptune in the long-range set. */
  extra?: { b: number; c: number; s: number; f: number };
}

export interface PlanetElements {
  table1: ElementSet;
  table2a: ElementSet;
}

const el = (a: number, e: number, I: number, L: number, varpi: number, Omega: number): Elements => ({
  a,
  e,
  I,
  L,
  varpi,
  Omega,
});

/** Keys match planet names; "Earth" uses the Earth-Moon barycentre elements. */
export const PLANET_ELEMENTS: Record<string, PlanetElements> = {
  Mercury: {
    table1: {
      at: el(0.38709927, 0.20563593, 7.00497902, 252.2503235, 77.45779628, 48.33076593),
      rate: el(0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081),
    },
    table2a: {
      at: el(0.38709843, 0.20563661, 7.00559432, 252.25166724, 77.45771895, 48.33961819),
      rate: el(0.0, 0.00002123, -0.00590158, 149472.67486623, 0.15940013, -0.12214182),
    },
  },
  Venus: {
    table1: {
      at: el(0.72333566, 0.00677672, 3.39467605, 181.9790995, 131.60246718, 76.67984255),
      rate: el(0.0000039, -0.00004107, -0.0007889, 58517.81538729, 0.00268329, -0.27769418),
    },
    table2a: {
      at: el(0.72332102, 0.00676399, 3.39777545, 181.9797085, 131.76755713, 76.67261496),
      rate: el(-0.00000026, -0.00005107, 0.00043494, 58517.8156026, 0.05679648, -0.27274174),
    },
  },
  Earth: {
    table1: {
      at: el(1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
      rate: el(0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0),
    },
    table2a: {
      at: el(1.00000018, 0.01673163, -0.00054346, 100.46691572, 102.93005885, -5.11260389),
      rate: el(-0.00000003, -0.00003661, -0.01337178, 35999.37306329, 0.3179526, -0.24123856),
    },
  },
  Mars: {
    table1: {
      at: el(1.52371034, 0.0933941, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
      rate: el(0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343),
    },
    table2a: {
      at: el(1.52371243, 0.09336511, 1.85181869, -4.56813164, -23.91744784, 49.71320984),
      rate: el(0.00000097, 0.00009149, -0.00724757, 19140.29934243, 0.45223625, -0.26852431),
    },
  },
  Jupiter: {
    table1: {
      at: el(5.202887, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
      rate: el(-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106),
    },
    table2a: {
      at: el(5.20248019, 0.0485359, 1.29861416, 34.33479152, 14.27495244, 100.29282654),
      rate: el(-0.00002864, 0.00018026, -0.00322699, 3034.90371757, 0.18199196, 0.13024619),
      extra: { b: -0.00012452, c: 0.0606406, s: -0.35635438, f: 38.35125 },
    },
  },
  Saturn: {
    table1: {
      at: el(9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
      rate: el(-0.0012506, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794),
    },
    table2a: {
      at: el(9.54149883, 0.05550825, 2.49424102, 50.07571329, 92.86136063, 113.63998702),
      rate: el(-0.00003065, -0.00032044, 0.00451969, 1222.11494724, 0.54179478, -0.25015002),
      extra: { b: 0.00025899, c: -0.13434469, s: 0.87320147, f: 38.35125 },
    },
  },
  Uranus: {
    table1: {
      at: el(19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.9542763, 74.01692503),
      rate: el(-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589),
    },
    table2a: {
      at: el(19.18797948, 0.0468574, 0.77298127, 314.20276625, 172.43404441, 73.96250215),
      rate: el(-0.00020455, -0.0000155, -0.00180155, 428.49512595, 0.09266985, 0.05739699),
      extra: { b: 0.00058331, c: -0.97731848, s: 0.17689245, f: 7.67025 },
    },
  },
  Neptune: {
    table1: {
      at: el(30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574),
      rate: el(0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664),
    },
    table2a: {
      at: el(30.06952752, 0.00895439, 1.7700552, 304.22289287, 46.68158724, 131.78635853),
      rate: el(0.00006447, 0.00000818, 0.000224, 218.46515314, 0.01009938, -0.00606302),
      extra: { b: -0.00041348, c: 0.68346318, s: -0.10162547, f: 7.67025 },
    },
  },
};

const DEG = Math.PI / 180;
/** Table 1 is valid 1800-2050; T in centuries from J2000 so 2050 is T = 0.5. */
export const TABLE1_LAST_T = 0.5;

/** Wrap an angle in degrees to (-180, 180]. */
export function wrapDeg(x: number): number {
  const r = ((x + 180) % 360 + 360) % 360 - 180;
  return r === -180 ? 180 : r;
}

/** Solve Kepler's equation M = E - e sin E (radians) with Newton iteration. */
export function solveKepler(M: number, e: number): number {
  let m = M % (2 * Math.PI);
  if (m > Math.PI) m -= 2 * Math.PI;
  if (m < -Math.PI) m += 2 * Math.PI;
  let E = e < 0.8 ? m : Math.PI * Math.sign(m || 1);
  for (let i = 0; i < 50; i++) {
    const d = (E - e * Math.sin(E) - m) / (1 - e * Math.cos(E));
    E -= d;
    if (Math.abs(d) < 1e-13) break;
  }
  return E;
}

export interface OrbitState {
  /** Elements evaluated at the requested time. */
  a: number;
  e: number;
  I: number;
  omega: number; // argument of perihelion, rad
  Omega: number; // rad
  M: number; // mean anomaly, rad
}

export function orbitAt(name: string, ms: number): OrbitState {
  const set = PLANET_ELEMENTS[name];
  if (!set) throw new Error(`Unknown planet: ${name}`);
  const T = centuriesSinceJ2000(ms);
  const s = T <= TABLE1_LAST_T ? set.table1 : set.table2a;
  const at = (k: keyof Elements) => s.at[k] + s.rate[k] * T;
  const a = at("a");
  const e = at("e");
  const I = at("I");
  const L = at("L");
  const varpi = at("varpi");
  const Omega = at("Omega");
  let M = L - varpi;
  if (s.extra) {
    const { b, c, s: sn, f } = s.extra;
    M += b * T * T + c * Math.cos(f * T * DEG) + sn * Math.sin(f * T * DEG);
  }
  return { a, e, I: I * DEG, omega: (varpi - Omega) * DEG, Omega: Omega * DEG, M: wrapDeg(M) * DEG };
}

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

/** Position from the orbital plane (perifocal x', y') into the J2000 ecliptic frame. */
export function toEcliptic(xp: number, yp: number, o: OrbitState): Vec3 {
  const cw = Math.cos(o.omega);
  const sw = Math.sin(o.omega);
  const cO = Math.cos(o.Omega);
  const sO = Math.sin(o.Omega);
  const cI = Math.cos(o.I);
  const sI = Math.sin(o.I);
  return {
    x: (cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp,
    y: (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp,
    z: sw * sI * xp + cw * sI * yp,
  };
}

/** Heliocentric ecliptic J2000 position in au. */
export function heliocentricPosition(name: string, ms: number): Vec3 {
  const o = orbitAt(name, ms);
  const E = solveKepler(o.M, o.e);
  return toEcliptic(o.a * (Math.cos(E) - o.e), o.a * Math.sqrt(1 - o.e * o.e) * Math.sin(E), o);
}

/** Closed orbit outline sampled uniformly in eccentric anomaly. */
export function orbitOutline(name: string, ms: number, samples = 360): Vec3[] {
  const o = orbitAt(name, ms);
  const b = o.a * Math.sqrt(1 - o.e * o.e);
  const pts: Vec3[] = [];
  for (let i = 0; i <= samples; i++) {
    const E = (i / samples) * 2 * Math.PI;
    pts.push(toEcliptic(o.a * (Math.cos(E) - o.e), b * Math.sin(E), o));
  }
  return pts;
}

export function distanceAu(p: Vec3): number {
  return Math.hypot(p.x, p.y, p.z);
}

/** Heliocentric ecliptic longitude in degrees, 0..360. */
export function longitudeDeg(p: Vec3): number {
  return (Math.atan2(p.y, p.x) / DEG + 360) % 360;
}
