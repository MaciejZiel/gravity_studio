import { describe, expect, it } from "vitest";
import { motionPreference, shouldFreezeSpin } from "../src/motion";
import { TOURS } from "../src/data/tours";
import { TourRunner } from "../src/tour";

function fakeWindow(initial: boolean) {
  let matches = initial;
  const handlers: (() => void)[] = [];
  const mq = {
    get matches() {
      return matches;
    },
    addEventListener: (_: string, cb: () => void) => handlers.push(cb),
  };
  return {
    win: { matchMedia: () => mq } as unknown as Window,
    set: (v: boolean) => {
      matches = v;
      handlers.forEach((h) => h());
    },
  };
}

describe("motionPreference", () => {
  it("reads the media query and reports changes", () => {
    const f = fakeWindow(true);
    const pref = motionPreference(f.win);
    const seen: boolean[] = [];
    pref.onChange((r) => seen.push(r));
    expect(pref.reduced).toBe(true);
    f.set(false);
    expect(pref.reduced).toBe(false);
    expect(seen).toEqual([false]);
  });
  it("defaults to full motion without matchMedia", () => {
    expect(motionPreference({} as unknown as Window).reduced).toBe(false);
  });
});

describe("shouldFreezeSpin", () => {
  it("freezes only for reduced motion while the clock runs faster than real time", () => {
    expect(shouldFreezeSpin(true, { live: false, playing: true, rate: 3600 })).toBe(true);
    expect(shouldFreezeSpin(true, { live: true, playing: true, rate: 1 })).toBe(false);
    expect(shouldFreezeSpin(true, { live: false, playing: false, rate: 3600 })).toBe(false);
    expect(shouldFreezeSpin(true, { live: false, playing: true, rate: 1 })).toBe(false);
    expect(shouldFreezeSpin(false, { live: false, playing: true, rate: 3600 })).toBe(false);
  });
});

describe("TourRunner without auto-advance", () => {
  it("stays on a step until next() is called", () => {
    const entered: string[] = [];
    const r = new TourRunner({ enter: (s) => entered.push(s.key), exit: () => {} });
    r.autoAdvance = false;
    r.start(TOURS[0]!);
    for (let i = 0; i < 100; i++) r.update(1);
    expect(entered).toHaveLength(1);
    expect(r.progress).toBe(0);
    r.next();
    expect(entered).toHaveLength(2);
  });
});
