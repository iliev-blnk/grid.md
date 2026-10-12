export type Q = (number | null)[];

export interface Scale {
  x: (v: number) => number;
  y: (v: number) => number;
}

export function scale(o: { x0: number; x1: number; y0: number; y1: number; xmin: number; xmax: number; ymin: number; ymax: number }): Scale {
  return {
    x: (v) => o.x0 + ((v - o.xmin) / (o.xmax - o.xmin || 1)) * (o.x1 - o.x0),
    y: (v) => o.y0 + ((v - o.ymin) / (o.ymax - o.ymin || 1)) * (o.y1 - o.y0),
  };
}

const r = (v: number) => Math.round(v * 10) / 10;

function band(xs: number[], q: Q[], lo: number, hi: number, s: Scale): string {
  const pts = xs.map((x, i) => [x, q[i]] as const).filter(([, row]) => row[lo] !== null && row[hi] !== null);
  if (!pts.length) return "";
  const up = pts.map(([x, row]) => `${r(s.x(x))},${r(s.y(row[hi] as number))}`);
  const down = [...pts].reverse().map(([x, row]) => `${r(s.x(x))},${r(s.y(row[lo] as number))}`);
  return "M" + [...up, ...down].join("L") + "Z";
}

/** SVG paths for the 5–95, 10–90 and 25–75 bands and the median of a quantile fan. */
export function fanPaths(xs: number[], q: Q[], s: Scale) {
  const med = xs.map((x, i) => [x, q[i][3]] as const).filter(([, v]) => v !== null);
  return {
    band90: band(xs, q, 0, 6, s),
    band80: band(xs, q, 1, 5, s),
    band50: band(xs, q, 2, 4, s),
    median: med.length ? "M" + med.map(([x, v]) => `${r(s.x(x))},${r(s.y(v as number))}`).join("L") : "",
  };
}
