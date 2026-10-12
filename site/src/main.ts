import { fanPaths, scale, type Q } from "./fan.ts";
import { fmtMW, peak, pct } from "./format.ts";

type Hour = { day: string; hour: number; load: number | null; plan: number | null };
type Score = { target_day: string; mape: number; plan_mape: number | null; plan_bc_mape: number | null; in90: number; late: boolean };
type Data = {
  latest: { target_day: string; issued_at: string; issue_cutoff: string; late: boolean; hours: number[]; q: Q[] };
  recent: Hour[];
  scores: Score[];
};

const $ = (id: string) => document.getElementById(id)!;
const day = (iso: string) => new Date(iso + "T12:00:00Z").toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
const time = (iso: string) => new Date(iso).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Chisinau" });
const SHOW_DAYS = 3;
const hh = (h: number) => `${String(h).padStart(2, "0")}:00`;

function chart(d: Data): string {
  const f = d.latest;
  // real time on the x axis: hours since the start of the window (3 days before the target day)
  const t0 = Date.parse(f.target_day + "T00:00:00Z") - SHOW_DAYS * 86400e3;
  const at = (dd: string, h: number) => (Date.parse(dd + "T00:00:00Z") - t0) / 3600e3 + h;
  const firstDay = new Date(t0).toISOString().slice(0, 10);
  const past = d.recent.filter((h) => h.day < f.target_day && h.day >= firstDay);
  const xsPast = past.map((h) => at(h.day, h.hour));
  const x0 = at(f.target_day, 0);
  const xsF = f.hours.map((h) => at(f.target_day, h));
  const vals = [...past.flatMap((h) => [h.load, h.plan]), ...f.q.flat()].filter((v): v is number => v !== null);
  const ymax = Math.ceil(Math.max(...vals) / 100) * 100;
  const W = 940, H = 300, L = 44, R = 8, T = 10, B = 26;
  const s = scale({ x0: L, x1: W - R, y0: H - B, y1: T, xmin: 0, xmax: x0 + 23, ymin: 0, ymax });
  const p = fanPaths(xsF, f.q, s);
  const line = (xs: number[], ys: (number | null)[]) => {
    let out = "", pen = false;
    xs.forEach((x, i) => {
      const y = ys[i];
      if (y === null || (i > 0 && x - xs[i - 1] > 1)) pen = false;
      if (y === null) return;
      out += `${pen ? "L" : "M"}${s.x(x).toFixed(1)},${s.y(y).toFixed(1)}`;
      pen = true;
    });
    return out;
  };
  const grid = Array.from({ length: ymax / 100 + 1 }, (_, i) => i * 100)
    .map((v) => `<line x1="${L}" x2="${W - R}" y1="${s.y(v)}" y2="${s.y(v)}" stroke="#eee"/><text x="4" y="${s.y(v) + 3}">${v}</text>`).join("");
  const days = Array.from({ length: SHOW_DAYS }, (_, k) => new Date(t0 + k * 86400e3).toISOString().slice(0, 10)).map((dd) => {
    const x = s.x(at(dd, 0));
    return `<line x1="${x}" x2="${x}" y1="${T}" y2="${H - B}" stroke="#eee"/><text x="${x + 3}" y="${H - 8}">${day(dd)}</text>`;
  }).join("");
  return `<svg class="fan" viewBox="0 0 ${W} ${H}" role="img" aria-label="Moldova load, last 7 days and tomorrow's forecast">
    ${grid}${days}
    <path d="${p.band90}" fill="#000" fill-opacity="0.10"/>
    <path d="${p.band80}" fill="#000" fill-opacity="0.12"/>
    <path d="${p.band50}" fill="#000" fill-opacity="0.18"/>
    <path d="${p.median}" fill="none" stroke="#000" stroke-width="2"/>
    <path d="${line(xsPast, past.map((h) => h.plan))}" fill="none" stroke="#000" stroke-width="1" stroke-dasharray="3 3"/>
    <path d="${line(xsPast, past.map((h) => h.load))}" fill="none" stroke="#000" stroke-width="1.2"/>
    <line x1="${s.x(x0)}" x2="${s.x(x0)}" y1="${T}" y2="${H - B}" stroke="#000"/>
    <text x="${s.x(x0) + 3}" y="${H - 8}" style="fill:#000">${day(f.target_day)}</text>
    <text x="${L}" y="${T + 2}">MW</text>
  </svg>`;
}

function record(d: Data): string {
  const sc = d.scores;
  if (!sc.length) {
    return `<p class="muted">No day has been scored yet. A day is scored once all its hours are in Moldelectrica's archive.</p>`;
  }
  const mean = (a: (number | null)[]) => { const v = a.filter((x): x is number => x !== null); return v.length ? v.reduce((x, y) => x + y, 0) / v.length : null; };
  const rows = [...sc].reverse().map((s) =>
    `<tr class="scored"><td>${day(s.target_day)}</td><td>${pct(s.mape)}</td><td>${pct(s.plan_mape)}</td><td>${Math.round(100 * s.in90)}%</td><td class="muted">${s.late ? "late" : ""}</td></tr>`).join("");
  return `<p>${sc.length} scored day${sc.length === 1 ? "" : "s"} · mean error: model ${pct(mean(sc.map((s) => s.mape)))}, operator plan ${pct(mean(sc.map((s) => s.plan_mape)))} · hours inside the 90% range: ${Math.round(100 * (mean(sc.map((s) => s.in90)) ?? 0))}%</p>
    <table><tr><th>day</th><th>model</th><th>plan</th><th>in 90%</th><th></th></tr>${rows}</table>`;
}

async function start() {
  const d: Data = await (await fetch(import.meta.env.BASE_URL + "data/site.json")).json();
  const f = d.latest;
  const pk = peak(f.hours, f.q);
  $("head").innerHTML =
    `<p>sarcina — Moldova's electricity load tomorrow, ${day(f.target_day)}.</p>` +
    `<p class="muted">Forecast every morning at 09:00 from data available then, as a range. Shaded: 50%, 80% and 90% ranges; thick line: median. ` +
    `To the left, the last three days: actual load (solid) and the grid operator's plan (dashed).</p>` +
    `<nav><a href="https://github.com/iliev-blnk/sarcina/blob/main/research/REPORT.md">method and backtest</a><a href="https://github.com/iliev-blnk/sarcina/tree/main/forecasts">all forecasts</a><a href="https://github.com/iliev-blnk/sarcina">github</a></nav>`;
  $("fan").innerHTML = chart(d);
  $("summary").innerHTML =
    `<p>Peak around ${hh(pk.hour)}: ${fmtMW(pk.median)} (90%: ${Math.round(pk.lo)}–${fmtMW(pk.hi)}).</p>` +
    `<p class="muted">Issued ${time(f.issued_at)} Moldova time${f.late ? " (after 09:00; inputs are still cut at 09:00)" : ""}. ` +
    `In the backtest (Oct 2025–Sep 2026) the median was off by 8.6% on average, against 18.7% for the operator's plan.</p>`;
  $("record").innerHTML = `<p>Record</p>` + record(d);
}

start().catch((e) => ($("head").textContent = "sarcina: could not load data (" + String(e) + ")"));
