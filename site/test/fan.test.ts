import { describe, expect, test } from "vitest";
import { fanPaths, scale } from "../src/fan.ts";
import { fmtMW, peak } from "../src/format.ts";

describe("fan", () => {
  const q = [
    [1, 2, 3, 4, 5, 6, 7],
    [2, 3, 4, 5, 6, 7, 8],
    [3, 4, 5, 6, 7, 8, 9],
  ];
  const s = scale({ x0: 0, x1: 200, y0: 100, y1: 0, xmin: 0, xmax: 2, ymin: 0, ymax: 10 });

  test("band polygons go up one edge and back the other", () => {
    const p = fanPaths([0, 1, 2], q, s);
    expect(p.band90.split(/[ML]/).filter(Boolean)).toHaveLength(6);
    expect(p.band50.startsWith("M0,")).toBe(true);
    expect(p.median.split(/[ML]/).filter(Boolean)).toHaveLength(3);
  });

  test("rows with null quantiles are skipped", () => {
    const p = fanPaths([0, 1, 2], [q[0], [null, null, null, null, null, null, null], q[2]], s);
    expect(p.median.split(/[ML]/).filter(Boolean)).toHaveLength(2);
  });
});

test("format", () => {
  expect(fmtMW(612.4)).toBe("612 MW");
  const pk = peak([0, 1, 2], [[1, 2, 3, 4, 5, 6, 7], [5, 6, 7, 9, 9, 10, 11], [3, 4, 5, 6, 7, 8, 9]]);
  expect(pk).toEqual({ hour: 1, median: 9, lo: 5, hi: 11 });
});
