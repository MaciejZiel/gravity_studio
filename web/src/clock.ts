import { MS_PER_DAY, TIMELINE_END_MS, TIMELINE_START_MS, clampToTimeline } from "./astro/time";

export interface Speed {
  id: string;
  label: string;
  /** Simulated seconds per real second. */
  rate: number;
}

export const SPEEDS: Speed[] = [
  { id: "1x", label: "1x", rate: 1 },
  { id: "1m", label: "1 min/s", rate: 60 },
  { id: "1h", label: "1 h/s", rate: 3600 },
  { id: "1d", label: "1 d/s", rate: MS_PER_DAY / 1000 },
  { id: "10d", label: "10 d/s", rate: (10 * MS_PER_DAY) / 1000 },
  { id: "100d", label: "100 d/s", rate: (100 * MS_PER_DAY) / 1000 },
  { id: "1000d", label: "1000 d/s", rate: (1000 * MS_PER_DAY) / 1000 },
];

/** Simulation clock. In live mode it follows the wall clock 1:1; any manual change leaves live mode. */
export class Clock {
  ms: number;
  speedIndex = 0;
  reverse = false;
  playing = true;
  live = true;

  constructor(now = Date.now()) {
    this.ms = clampToTimeline(now);
  }

  get rate(): number {
    return SPEEDS[this.speedIndex]!.rate;
  }

  tick(dtSeconds: number, now = Date.now()): void {
    if (this.live) {
      this.ms = clampToTimeline(now);
      return;
    }
    if (!this.playing) return;
    const next = this.ms + (this.reverse ? -1 : 1) * this.rate * dtSeconds * 1000;
    if (next >= TIMELINE_END_MS || next <= TIMELINE_START_MS) {
      this.ms = clampToTimeline(next);
      this.playing = false;
      return;
    }
    this.ms = next;
  }

  goLive(now = Date.now()): void {
    this.live = true;
    this.playing = true;
    this.reverse = false;
    this.speedIndex = 0;
    this.ms = clampToTimeline(now);
  }

  setTime(ms: number): void {
    this.live = false;
    this.ms = clampToTimeline(ms);
  }

  setSpeed(index: number): void {
    const i = Math.max(0, Math.min(SPEEDS.length - 1, index));
    if (this.live && i === 0) return;
    this.live = false;
    this.speedIndex = i;
    this.playing = true;
  }

  togglePlay(): void {
    this.live = false;
    // Restart from the end when pressing play at a boundary.
    if (!this.playing && ((!this.reverse && this.ms >= TIMELINE_END_MS) || (this.reverse && this.ms <= TIMELINE_START_MS))) {
      this.reverse = !this.reverse;
    }
    this.playing = !this.playing;
  }

  toggleReverse(): void {
    this.live = false;
    this.reverse = !this.reverse;
    this.playing = true;
  }

  /** Slider position 0..1 along the timeline. */
  get fraction(): number {
    return (this.ms - TIMELINE_START_MS) / (TIMELINE_END_MS - TIMELINE_START_MS);
  }
}

export function formatUtc(ms: number): string {
  const d = new Date(ms);
  const p = (n: number, w = 2) => String(n).padStart(w, "0");
  return `${p(d.getUTCFullYear(), 4)}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}:${p(d.getUTCSeconds())}`;
}

export function dateInputValue(ms: number): string {
  return formatUtc(ms).slice(0, 10);
}
