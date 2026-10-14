/** Tracks the user's prefers-reduced-motion setting, including changes while the page is open. */
export interface MotionPreference {
  readonly reduced: boolean;
  onChange(cb: (reduced: boolean) => void): void;
}

export function motionPreference(win: Pick<Window, "matchMedia"> = window): MotionPreference {
  const mq = typeof win.matchMedia === "function" ? win.matchMedia("(prefers-reduced-motion: reduce)") : null;
  const listeners: ((reduced: boolean) => void)[] = [];
  mq?.addEventListener?.("change", () => {
    for (const cb of listeners) cb(mq.matches);
  });
  return {
    get reduced() {
      return mq?.matches ?? false;
    },
    onChange: (cb) => {
      listeners.push(cb);
    },
  };
}

/** Whether planet spin should be frozen: reduced motion is on and the clock runs fast enough for spin to strobe. */
export function shouldFreezeSpin(reduced: boolean, clock: { live: boolean; playing: boolean; rate: number }): boolean {
  return reduced && !clock.live && clock.playing && clock.rate > 1;
}
