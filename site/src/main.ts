import { fanPaths, scale, type Q } from "./fan.ts";
import { peak } from "./format.ts";
import { LANGS, STRINGS, pickLang, type Lang } from "./i18n.ts";

type Score = { target_day: string; mape: number; plan_mape: number | null; in90: number };
type Data = { latest: { target_day: string; issued_at: string; late: boolean; hours: number[]; q: Q[] }; scores: Score[] };

const $ = (id: string) => document.getElementById(id)!;
const hh = (h: number) => `${String(h).padStart(2, "0")}:00`;
const pct = (v: number | null) => (v === null || v === undefined ? "–" : `${v.toFixed(1)}%`);
const KEY = "gridmd.lang";

function storedLang(): string | null {
  try { return localStorage.getItem(KEY); } catch { return null; }
}
function storeLang(l: Lang) {
  try { localStorage.setItem(KEY, l); } catch { /* private window: keep the choice for this visit only */ }
}

function chart(d: Data, s: (typeof STRINGS)[Lang]): string {
  const f = d.latest;
  const vals = f.q.flat().filter((v): v is number => v !== null);
  const ymin = Math.floor((Math.min(...vals) - 30) / 100) * 100;
  const ymax = Math.ceil((Math.max(...vals) + 30) / 100) * 100;
  // draw at the real width so axis text stays 12px on phones
  const W = Math.max(320, Math.round($("chart").clientWidth || 960)), H = Math.round(Math.min(260, Math.max(200, W * 0.32))), L = 40, R = 8, T = 10, B = 26;
  const sc = scale({ x0: L, x1: W - R, y0: H - B, y1: T, xmin: 0, xmax: 23, ymin, ymax });
  const p = fanPaths(f.hours, f.q, sc);
  let grid = "";
  for (let v = ymin; v <= ymax; v += 100)
    grid += `<line x1="${L}" x2="${W - R}" y1="${sc.y(v)}" y2="${sc.y(v)}" stroke="var(--line)"/><text x="0" y="${sc.y(v) + 4}">${v}${v === ymax ? " " + s.unit : ""}</text>`;
  const ticks = W < 560 ? [0, 12, 23] : [0, 6, 12, 18, 23];
  for (const h of ticks) grid += `<text x="${sc.x(h)}" y="${H - 6}" text-anchor="${h === 0 ? "start" : h === 23 ? "end" : "middle"}">${hh(h)}</text>`;
  const pk = peak(f.hours, f.q);
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${s.chartNote}">${grid}
    <path d="${p.band90}" fill="var(--accent)" style="fill-opacity:var(--o90)"/>
    <path d="${p.band50}" fill="var(--accent)" style="fill-opacity:var(--o50)"/>
    <path d="${p.median}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>
    <circle cx="${sc.x(pk.hour)}" cy="${sc.y(pk.median)}" r="5" fill="var(--accent)"/>
    </svg>`;
}

function render(d: Data, lang: Lang) {
  const s = STRINGS[lang];
  document.documentElement.lang = lang;
  const f = d.latest;
  const day = new Date(f.target_day + "T12:00:00Z").toLocaleDateString(s.locale, { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
  const issued = new Date(f.issued_at).toLocaleString(s.locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Chisinau" });
  const pk = peak(f.hours, f.q);
  $("langs").innerHTML = LANGS.map((l) => `<button type="button" data-lang="${l}" aria-pressed="${l === lang}" title="${STRINGS[l].langName}">${l.toUpperCase()}</button>`).join("");
  $("tldr").innerHTML = `<p><b>${s.tldrTitle}.</b> ${s.tldr}</p><p><a class="storylink" href="story.html">${s.storyLink} →</a></p>`;
  $("hero").innerHTML =
    `<p class="kick">${s.kicker(day, hh(pk.hour))}</p>` +
    `<div class="num">${Math.round(pk.median)}<small>${s.unit}</small></div>` +
    `<p class="range">${s.range(String(Math.round(pk.lo)), String(Math.round(pk.hi)), s.unit)}</p>`;
  $("chart").innerHTML = chart(d, s);
  $("notes").innerHTML = `<p>${s.chartNote}</p><p>${s.issued(issued)}${f.late ? ` (${s.late})` : ""}.</p>`;
  const sc = d.scores;
  let rec = `<h2>${s.recordTitle}</h2>`;
  if (!sc.length) rec += `<p class="muted">${s.recordNone}</p>`;
  else {
    const mean = (a: (number | null)[]) => { const v = a.filter((x): x is number => x !== null); return v.length ? v.reduce((x, y) => x + y, 0) / v.length : null; };
    rec += `<p>${s.recordSummary(sc.length, pct(mean(sc.map((x) => x.mape))), pct(mean(sc.map((x) => x.plan_mape))), `${Math.round(100 * (mean(sc.map((x) => x.in90)) ?? 0))}%`)}</p>`;
    const rows = [...sc].reverse().slice(0, 30).map((x) => {
      const dd = new Date(x.target_day + "T12:00:00Z").toLocaleDateString(s.locale, { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
      return `<tr class="scored"><td>${dd}</td><td>${pct(x.mape)}</td><td>${pct(x.plan_mape)}</td><td>${Math.round(100 * x.in90)}%</td></tr>`;
    }).join("");
    rec += `<div class="tablewrap"><table><tr><th>${s.colDay}</th><th>${s.colModel}</th><th>${s.colPlan}</th><th>${s.colIn90}</th></tr>${rows}</table></div>`;
  }
  $("record").innerHTML = rec;
  $("foot").innerHTML =
    `<a href="https://github.com/iliev-blnk/grid.md/blob/main/research/REPORT.md">${s.linkMethod}</a>` +
    `<a href="https://github.com/iliev-blnk/grid.md/tree/main/forecasts">${s.linkForecasts}</a>` +
    `<a href="https://github.com/iliev-blnk/grid.md">${s.linkCode}</a><span>${s.credits}</span>`;
}

async function start() {
  const d: Data = await (await fetch(import.meta.env.BASE_URL + "data/site.json")).json();
  let lang = pickLang(storedLang(), navigator.languages ?? [navigator.language]);
  render(d, lang);
  let t: number | undefined;
  addEventListener("resize", () => { clearTimeout(t); t = window.setTimeout(() => render(d, lang), 150); });
  $("langs").addEventListener("click", (e) => {
    const b = (e.target as HTMLElement).closest("[data-lang]") as HTMLElement | null;
    if (!b) return;
    lang = b.dataset.lang as Lang;
    storeLang(lang);
    render(d, lang);
  });
}

start().catch((e) => ($("tldr").textContent = "grid.md: could not load data (" + String(e) + ")"));
