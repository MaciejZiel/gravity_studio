import { describe, expect, it } from "vitest";
import { TOURS } from "../src/data/tours";
import { TourRunner } from "../src/tour";

describe("TourRunner", () => {
  it("walks every step of the grand tour and exits", () => {
    const entered: string[] = [];
    let exited = 0;
    const r = new TourRunner({ enter: (s) => entered.push(s.key), exit: () => exited++ });
    const tour = TOURS[0]!;
    r.start(tour);
    for (let i = 0; i < 200 && r.active; i++) r.update(0.5);
    expect(entered).toEqual(tour.steps.map((s) => s.key));
    expect(exited).toBe(1);
    expect(r.active).toBeNull();
  });
  it("supports back and stop", () => {
    const entered: string[] = [];
    const r = new TourRunner({ enter: (s) => entered.push(s.key), exit: () => {} });
    r.start(TOURS[1]!);
    r.next();
    r.next();
    r.prev();
    expect(entered).toEqual(["apollo", "voyager", "equinox", "voyager"]);
    r.stop();
    expect(r.step).toBeNull();
  });
  it("reports progress within a step", () => {
    const r = new TourRunner({ enter: () => {}, exit: () => {} });
    r.start(TOURS[0]!);
    r.update(2.5);
    expect(r.progress).toBeCloseTo(0.5, 6);
  });
});
