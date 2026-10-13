import { describe, expect, it } from "vitest";
import { Clock, SPEEDS, dateInputValue, formatUtc } from "../src/clock";
import { TIMELINE_END_MS, TIMELINE_START_MS } from "../src/astro/time";

describe("Clock", () => {
  it("follows the wall clock in live mode", () => {
    const c = new Clock(Date.UTC(2026, 0, 1));
    c.tick(5, Date.UTC(2026, 5, 1));
    expect(c.ms).toBe(Date.UTC(2026, 5, 1));
    expect(c.live).toBe(true);
  });
  it("advances 1:1 at 1x and leaves live mode when scrubbed", () => {
    const c = new Clock(Date.UTC(2026, 0, 1));
    c.setTime(Date.UTC(2000, 0, 1));
    c.tick(10);
    expect(c.live).toBe(false);
    expect(c.ms).toBe(Date.UTC(2000, 0, 1) + 10_000);
  });
  it("runs 100 days per second at the 100 d/s setting", () => {
    const c = new Clock();
    c.setTime(Date.UTC(2000, 0, 1));
    c.setSpeed(SPEEDS.findIndex((s) => s.id === "100d"));
    c.tick(0.5);
    expect(c.ms - Date.UTC(2000, 0, 1)).toBeCloseTo(50 * 86_400_000, -2);
  });
  it("stops at the timeline end", () => {
    const c = new Clock();
    c.setTime(TIMELINE_END_MS - 1000);
    c.setSpeed(SPEEDS.length - 1);
    c.tick(10);
    expect(c.ms).toBe(TIMELINE_END_MS);
    expect(c.playing).toBe(false);
  });
  it("clamps manual times to the timeline", () => {
    const c = new Clock();
    c.setTime(Date.UTC(1900, 0, 1));
    expect(c.ms).toBe(TIMELINE_START_MS);
  });
  it("runs backwards", () => {
    const c = new Clock();
    c.setTime(Date.UTC(2000, 0, 1));
    c.toggleReverse();
    c.tick(2);
    expect(c.ms).toBe(Date.UTC(2000, 0, 1) - 2000);
  });
  it("formats UTC timestamps", () => {
    expect(formatUtc(Date.UTC(1969, 6, 20, 20, 17, 3))).toBe("1969-07-20 20:17:03");
    expect(dateInputValue(Date.UTC(2024, 3, 8, 18, 18))).toBe("2024-04-08");
  });
});
