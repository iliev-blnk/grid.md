import type { Q } from "./fan.ts";

export const fmtMW = (v: number) => `${Math.round(v)} MW`;

/** The hour with the highest median, with its 5–95% range. */
export function peak(hours: number[], q: Q[]) {
  let best = -1;
  q.forEach((row, i) => {
    if (row[3] !== null && (best < 0 || (row[3] as number) > (q[best][3] as number))) best = i;
  });
  return { hour: hours[best], median: q[best][3] as number, lo: q[best][0] as number, hi: q[best][6] as number };
}

export const pct = (v: number | null) => (v === null || v === undefined ? "–" : `${v.toFixed(1)}%`);
