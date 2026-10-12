/** Small SVG line/area charts drawn at the container's real width (so text stays 12px on phones). */
export interface Series { values: (number | null)[]; color: string; width?: number; dash?: string; opacity?: number; area?: boolean }
export interface ChartSpec {
  n: number;
  series: Series[];
  band?: { lo: (number | null)[]; hi: (number | null)[]; color: string };
  points?: { i: number; v: number; label: string }[];
  ymin?: number;
  ymax?: number;
  xTicks: { i: number; label: string }[];
  unit: string;
  zero?: boolean;
}

export function lineChart(width: number, s: ChartSpec): string {
  const W = Math.max(300, Math.round(width)), H = Math.round(Math.min(240, Math.max(170, W * 0.3))), L = 42, R = 10, T = 12, B = 24;
  const all = [...s.series.flatMap((x) => x.values), ...(s.band ? [...s.band.lo, ...s.band.hi] : []), ...(s.points ?? []).map((p) => p.v)]
    .filter((v): v is number => v !== null && Number.isFinite(v));
  const lo = s.ymin ?? Math.min(0, ...all), hi = s.ymax ?? Math.max(...all);
  const step = niceStep((hi - lo) / 4);
  const y0 = Math.floor(lo / step) * step, y1 = Math.ceil(hi / step) * step;
  const x = (i: number) => L + (s.n <= 1 ? 0 : (i / (s.n - 1)) * (W - L - R));
  const y = (v: number) => T + (1 - (v - y0) / (y1 - y0 || 1)) * (H - T - B);
  const path = (vals: (number | null)[]) => {
    let d = "", pen = false;
    vals.forEach((v, i) => {
      if (v === null || !Number.isFinite(v)) { pen = false; return; }
      d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
      pen = true;
    });
    return d;
  };
  let g = "";
  for (let v = y0; v <= y1 + 1e-9; v += step)
    g += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)"/><text x="0" y="${y(v) + 4}">${Math.round(v)}${v + step > y1 + 1e-9 ? " " + s.unit : ""}</text>`;
  if (s.zero && y0 < 0) g += `<line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="var(--muted)"/>`;
  for (const t of s.xTicks) g += `<text x="${x(t.i)}" y="${H - 5}" text-anchor="${t.i === 0 ? "start" : t.i === s.n - 1 ? "end" : "middle"}">${t.label}</text>`;
  if (s.band) {
    const idx = s.band.lo.map((v, i) => [i, v, s.band!.hi[i]] as const).filter(([, a, b]) => a !== null && b !== null);
    const up = idx.map(([i, , b]) => `${x(i).toFixed(1)},${y(b as number).toFixed(1)}`);
    const dn = [...idx].reverse().map(([i, a]) => `${x(i).toFixed(1)},${y(a as number).toFixed(1)}`);
    if (up.length) g += `<path d="M${[...up, ...dn].join("L")}Z" fill="${s.band.color}" style="fill-opacity:var(--o90)"/>`;
  }
  for (const se of s.series) {
    if (se.area) {
      const d = path(se.values);
      if (d) g += `<path d="${d}L${x(se.values.length - 1)},${y(Math.max(y0, 0))}L${x(0)},${y(Math.max(y0, 0))}Z" fill="${se.color}" style="fill-opacity:var(--o90)"/>`;
    }
    g += `<path d="${path(se.values)}" fill="none" stroke="${se.color}" stroke-width="${se.width ?? 2}" ${se.dash ? `stroke-dasharray="${se.dash}"` : ""} ${se.opacity ? `stroke-opacity="${se.opacity}"` : ""}/>`;
  }
  for (const p of s.points ?? []) g += `<circle cx="${x(p.i)}" cy="${y(p.v)}" r="4.5" fill="var(--fg)"/><text x="${x(p.i) - 6}" y="${y(p.v) - 8}" text-anchor="end" style="fill:var(--fg)">${p.label}</text>`;
  return `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img">${g}</svg>`;
}

function niceStep(raw: number): number {
  const p = 10 ** Math.floor(Math.log10(Math.max(raw, 1e-9)));
  for (const m of [1, 2, 2.5, 5, 10]) if (raw <= m * p) return m * p;
  return 10 * p;
}
