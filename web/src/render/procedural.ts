/**
 * Procedural surface textures for bodies without a photographic map: the Sun and
 * the six major moons. Noise is evaluated on the unit sphere so the maps are
 * seamless at the date line and do not pinch at the poles.
 */

type RGB = [number, number, number];

function hexToRgb(hex: string): RGB {
  const v = parseInt(hex.slice(1), 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

/** Small deterministic PRNG (mulberry32). */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hash3(ix: number, iy: number, iz: number, seed: number): number {
  let h = Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263) ^ Math.imul(iz, 2147483647) ^ Math.imul(seed, 1274126177);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

const fade = (t: number) => t * t * (3 - 2 * t);

export function valueNoise3(x: number, y: number, z: number, seed: number): number {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const iz = Math.floor(z);
  const fx = fade(x - ix);
  const fy = fade(y - iy);
  const fz = fade(z - iz);
  const l = (a: number, b: number, t: number) => a + (b - a) * t;
  const c = (dx: number, dy: number, dz: number) => hash3(ix + dx, iy + dy, iz + dz, seed);
  return l(
    l(l(c(0, 0, 0), c(1, 0, 0), fx), l(c(0, 1, 0), c(1, 1, 0), fx), fy),
    l(l(c(0, 0, 1), c(1, 0, 1), fx), l(c(0, 1, 1), c(1, 1, 1), fx), fy),
    fz,
  );
}

export function fbm(x: number, y: number, z: number, octaves: number, seed: number): number {
  let sum = 0;
  let amp = 0.5;
  let f = 1;
  let norm = 0;
  for (let i = 0; i < octaves; i++) {
    sum += amp * valueNoise3(x * f, y * f, z * f, seed + i * 17);
    norm += amp;
    amp *= 0.5;
    f *= 2.03;
  }
  return sum / norm;
}

interface Crater {
  x: number;
  y: number;
  z: number;
  r: number; // angular radius, radians
}

function makeCraters(n: number, seed: number, minR: number, maxR: number): Crater[] {
  const rand = rng(seed);
  const out: Crater[] = [];
  for (let i = 0; i < n; i++) {
    const z = rand() * 2 - 1;
    const t = rand() * Math.PI * 2;
    const s = Math.sqrt(1 - z * z);
    // Many small craters, few large ones.
    const r = minR + (maxR - minR) * Math.pow(rand(), 3);
    out.push({ x: s * Math.cos(t), y: z, z: s * Math.sin(t), r });
  }
  return out;
}

export interface SurfaceSpec {
  seed: number;
  /** Colour ramp from dark to light (hex). */
  ramp: string[];
  scale: number;
  octaves: number;
  contrast?: number;
  craters?: { count: number; minR: number; maxR: number; depth: number };
  /** Dark patches where high-frequency noise passes a threshold (Io). */
  spots?: { color: string; threshold: number; scale: number };
  /** Thin ridged lines (Europa). */
  lines?: { color: string; scale: number; width: number; strength: number };
  /** Horizontal banding strength (Titan haze). */
  bands?: number;
}

function sampleRamp(ramp: RGB[], t: number): RGB {
  const x = Math.min(0.9999, Math.max(0, t)) * (ramp.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  const a = ramp[i]!;
  const b = ramp[i + 1]!;
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
}

export const SURFACES: Record<string, SurfaceSpec> = {
  Sun: { seed: 11, ramp: ["#c2410c", "#ea7a10", "#ffb02e", "#ffe08a", "#fff6d0"], scale: 5, octaves: 6, contrast: 1.15 },
  Moon: {
    seed: 21, ramp: ["#555559", "#8a8a8e", "#b4b4b8", "#d2d2d4"], scale: 2.2, octaves: 5, contrast: 1.2,
    craters: { count: 320, minR: 0.015, maxR: 0.11, depth: 0.34 },
  },
  Io: {
    seed: 31, ramp: ["#b8902a", "#dcc050", "#efdc7a", "#f6eaa8"], scale: 3, octaves: 5,
    spots: { color: "#3a2a1a", threshold: 0.7, scale: 9 },
  },
  Europa: {
    seed: 41, ramp: ["#c9b8a2", "#e2d8c8", "#f0ebe0"], scale: 2.5, octaves: 4,
    lines: { color: "#8a5a40", scale: 3.2, width: 0.06, strength: 0.75 },
  },
  Ganymede: {
    seed: 51, ramp: ["#5e5249", "#8a7d70", "#b4a799", "#d6cdc0"], scale: 3.2, octaves: 6, contrast: 1.25,
    craters: { count: 160, minR: 0.015, maxR: 0.08, depth: 0.22 },
  },
  Callisto: {
    seed: 61, ramp: ["#3c3733", "#5e5750", "#85796e", "#b0a698"], scale: 2.6, octaves: 5,
    craters: { count: 520, minR: 0.012, maxR: 0.09, depth: 0.3 },
  },
  Titan: { seed: 71, ramp: ["#a07a3c", "#c29a52", "#d9b574", "#e8cf98"], scale: 1.6, octaves: 3, bands: 0.18, contrast: 0.8 },
};

export function renderSurface(spec: SurfaceSpec, width = 512, height = 256): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;
  const img = ctx.createImageData(width, height);
  const ramp = spec.ramp.map(hexToRgb);
  const spot = spec.spots ? hexToRgb(spec.spots.color) : null;
  const line = spec.lines ? hexToRgb(spec.lines.color) : null;
  const craters = spec.craters ? makeCraters(spec.craters.count, spec.seed, spec.craters.minR, spec.craters.maxR) : [];
  const contrast = spec.contrast ?? 1;

  for (let py = 0; py < height; py++) {
    const lat = Math.PI * (0.5 - (py + 0.5) / height);
    const cy = Math.sin(lat);
    const cr = Math.cos(lat);
    for (let px = 0; px < width; px++) {
      const lon = 2 * Math.PI * ((px + 0.5) / width);
      const x = cr * Math.cos(lon);
      const z = cr * Math.sin(lon);
      const y = cy;
      const s = spec.scale;
      let n = fbm(x * s + 7, y * s + 7, z * s + 7, spec.octaves, spec.seed);
      n = 0.5 + (n - 0.5) * 2.2 * contrast;
      if (spec.bands) n += Math.sin(lat * 18 + fbm(x * 2, y * 2, z * 2, 2, spec.seed + 3) * 6) * spec.bands * 0.5;
      let col = sampleRamp(ramp, n);

      if (craters.length && spec.craters) {
        let shade = 0;
        for (const c of craters) {
          const dot = x * c.x + y * c.y + z * c.z;
          if (dot < 1 - c.r * c.r * 2.2) continue;
          const d = Math.acos(Math.min(1, dot)) / c.r; // 0 at centre, 1 at rim
          if (d < 0.85) shade -= spec.craters.depth * (1 - d * 0.5) * 0.6;
          else if (d < 1.25) shade += spec.craters.depth * 0.9 * (1 - Math.abs(d - 1.0) * 3);
        }
        const k = 1 + Math.max(-0.6, Math.min(0.5, shade));
        col = [col[0] * k, col[1] * k, col[2] * k];
      }
      if (spot && spec.spots) {
        const sn = fbm(x * spec.spots.scale, y * spec.spots.scale, z * spec.spots.scale, 3, spec.seed + 9);
        const m = Math.max(0, Math.min(1, (sn - spec.spots.threshold) * 9));
        col = [col[0] + (spot[0] - col[0]) * m, col[1] + (spot[1] - col[1]) * m, col[2] + (spot[2] - col[2]) * m];
      }
      if (line && spec.lines) {
        const ln = fbm(x * spec.lines.scale, y * spec.lines.scale, z * spec.lines.scale, 4, spec.seed + 5);
        const ridge = Math.max(0, 1 - Math.abs(ln - 0.5) / spec.lines.width);
        const m = ridge * spec.lines.strength;
        col = [col[0] + (line[0] - col[0]) * m, col[1] + (line[1] - col[1]) * m, col[2] + (line[2] - col[2]) * m];
      }
      const o = (py * width + px) * 4;
      img.data[o] = col[0];
      img.data[o + 1] = col[1];
      img.data[o + 2] = col[2];
      img.data[o + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return canvas;
}

/** Radial glow used behind the Sun. */
export function renderGlow(size = 256): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, "rgba(255,226,150,1)");
  g.addColorStop(0.18, "rgba(255,190,90,0.55)");
  g.addColorStop(0.5, "rgba(255,150,50,0.12)");
  g.addColorStop(1, "rgba(255,120,30,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  return canvas;
}
