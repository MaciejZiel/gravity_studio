import type { Tour, TourStep } from "./data/tours";

export interface TourHooks {
  /** Called when a step becomes active. */
  enter(step: TourStep, tour: Tour, index: number): void;
  /** Called when the tour ends or is stopped. */
  exit(tour: Tour): void;
}

/** Steps through a tour on a timer. Time is fed in by the frame loop. */
export class TourRunner {
  active: Tour | null = null;
  index = 0;
  elapsed = 0;

  constructor(private readonly hooks: TourHooks) {}

  start(tour: Tour): void {
    if (this.active) this.hooks.exit(this.active);
    this.active = tour;
    this.go(0);
  }

  stop(): void {
    if (!this.active) return;
    const t = this.active;
    this.active = null;
    this.hooks.exit(t);
  }

  next(): void {
    if (!this.active) return;
    if (this.index + 1 >= this.active.steps.length) this.stop();
    else this.go(this.index + 1);
  }

  prev(): void {
    if (this.active) this.go(Math.max(0, this.index - 1));
  }

  get step(): TourStep | null {
    return this.active ? this.active.steps[this.index]! : null;
  }

  get progress(): number {
    const s = this.step;
    return s ? Math.min(1, this.elapsed / s.duration) : 0;
  }

  update(dt: number): void {
    const s = this.step;
    if (!s) return;
    this.elapsed += dt;
    if (this.elapsed >= s.duration) this.next();
  }

  private go(i: number): void {
    if (!this.active) return;
    this.index = i;
    this.elapsed = 0;
    this.hooks.enter(this.active.steps[i]!, this.active, i);
  }
}
