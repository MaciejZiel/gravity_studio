/** Time helpers. All instants are UTC milliseconds since the Unix epoch. */

export const MS_PER_DAY = 86_400_000;
export const J2000_JD = 2451545.0;

/** Timeline supported by the viewer, same range as the desktop app. */
export const TIMELINE_START_MS = Date.UTC(1960, 0, 1);
export const TIMELINE_END_MS = Date.UTC(2165, 0, 1);

export function julianDate(ms: number): number {
  return ms / MS_PER_DAY + 2440587.5;
}

/** Julian centuries since J2000.0 (the time is treated as TDB; the ~69 s offset from UTC is ignored). */
export function centuriesSinceJ2000(ms: number): number {
  return (julianDate(ms) - J2000_JD) / 36525;
}

export function daysSinceJ2000(ms: number): number {
  return julianDate(ms) - J2000_JD;
}

export function clampToTimeline(ms: number): number {
  return Math.min(TIMELINE_END_MS, Math.max(TIMELINE_START_MS, ms));
}

export const J2000_MS = Date.UTC(2000, 0, 1, 12, 0, 0);
