import { lineChart, type ChartSpec } from "./charts.ts";
import { LANGS, STRINGS, pickLang, type Lang } from "./i18n.ts";
import { CHAPTERS, STORY, type Ch } from "./i18n-story.ts";

type M = { load: number; tpp: number; net_import: number; md_ua: number; md_ro: number };
type Story = {
  monthly: Record<string, M>;
  profiles: Record<string, (number | null)[]>;
  blackout: { hours: (number | null)[] };
  solar: { month: string; hidden: { C: number; lo: number; hi: number }; visible: number | null }[];
  chapters: Ch;
};

const $ = (id: string) => document.getElementById(id)!;
const KEY = "gridmd.lang";
const stored = () => { try { return localStorage.getItem(KEY); } catch { return null; } };
const store = (l: Lang) => { try { localStorage.setItem(KEY, l); } catch { /* keep for this visit */ } };

function months(S: Story, from: string, to: string) {
  return Object.keys(S.monthly).filter((m) => m >= from && m <= to).sort();
}
function yearTicks(ms: string[]) {
  return ms.map((m, i) => ({ m, i })).filter(({ m }) => m.endsWith("-01")).map(({ m, i }) => ({ i, label: m.slice(0, 4) }));
}
const leg = (items: [string, string, boolean?][]) =>
  `<p class="legend">${items.map(([c, t, dash]) => `<span><i class="${dash ? "dash" : ""}" style="border-color:${c}"></i>${t}</span>`).join("")}</p>`;

function charts(S: Story, lang: Lang, width: number): Record<string, string> {
  const T = STORY[lang], unit = STRINGS[lang].unit, A = "var(--accent)", F = "var(--fg)", Mu = "var(--muted)";
  const out: Record<string, string> = {};
  const m1 = months(S, "2021-12", "2022-12");
  const mon = (m: string) => new Date(m + "-15T00:00:00Z").toLocaleDateString(STRINGS[lang].locale, { month: "short", timeZone: "UTC" });
  out.before = lineChart(width, { n: m1.length, unit, ymin: 0, xTicks: [0, 3, 6, 9, 12].map((i) => ({ i, label: mon(m1[i]) + (i === 0 || m1[i].endsWith("-01") ? " " + m1[i].slice(0, 4) : "") })),
    series: [{ values: m1.map((m) => S.monthly[m].tpp), color: A, area: true }, { values: m1.map((m) => S.monthly[m].load), color: F, width: 1.5, dash: "4 3" }] })
    + leg([[A, T.legend.tpp], [F, T.legend.load, true]]);
  out.blackout = lineChart(width, { n: 24, unit, ymin: 0, xTicks: [0, 6, 12, 15, 18, 23].map((i) => ({ i, label: `${String(i).padStart(2, "0")}:00` })),
    series: [{ values: S.blackout.hours, color: A, width: 2.5 }] }) + leg([[A, T.legend.load]]);
  const m3 = months(S, "2022-01", "2026-12");
  out.corridor = lineChart(width, { n: m3.length, unit, zero: true, xTicks: yearTicks(m3),
    series: [{ values: m3.map((m) => S.monthly[m].md_ro), color: A }, { values: m3.map((m) => S.monthly[m].md_ua), color: F, width: 1.5 }] })
    + leg([[A, T.legend.fromRo], [F, T.legend.toUa]]);
  const m4 = months(S, "2024-01", "2026-12");
  out.cutoff = lineChart(width, { n: m4.length, unit, ymin: 0, xTicks: yearTicks(m4),
    series: [{ values: m4.map((m) => S.monthly[m].tpp), color: F, width: 1.5 }, { values: m4.map((m) => S.monthly[m].net_import), color: A }] })
    + leg([[F, T.legend.tpp], [A, T.legend.netImport]]);
  const years = Object.keys(S.profiles).sort();
  out.duck = lineChart(width, { n: 24, unit, ymin: 0, xTicks: [0, 6, 13, 20, 23].map((i) => ({ i, label: `${String(i).padStart(2, "0")}:00` })),
    series: years.map((y, k) => ({ values: S.profiles[y], color: k === years.length - 1 ? A : F, width: k === years.length - 1 ? 2.5 : 1.2, opacity: k === years.length - 1 ? 1 : 0.25 + 0.15 * k })) })
    + `<p class="legend">${years.map((y, k) => `<span><i style="border-color:${k === years.length - 1 ? A : F};opacity:${k === years.length - 1 ? 1 : 0.25 + 0.15 * k}"></i>${y}</span>`).join("")}</p>`;
  const sm = S.solar.map((r) => r.month);
  const at = (m: string) => sm.indexOf(m);
  out.solar = lineChart(width, { n: sm.length, unit, ymin: 0, xTicks: yearTicks(sm),
    band: { lo: S.solar.map((r) => r.hidden.lo), hi: S.solar.map((r) => r.hidden.hi), color: A },
    series: [{ values: S.solar.map((r) => r.hidden.C), color: A, width: 2.5 }, { values: S.solar.map((r) => r.visible), color: F, width: 1.5, dash: "4 3" }],
    points: [{ i: at("2024-12"), v: 394, label: `394 ${T.legend.total}` }, { i: at("2025-12"), v: 710, label: `710 ${T.legend.total}` }, { i: at("2025-12"), v: 195, label: `195 ${T.legend.prosumers}` }].filter((p) => p.i >= 0) })
    + leg([[A, T.legend.hidden], [F, T.legend.metered, true]]).replace("</p>", `<span><b class="dot"></b>${T.legend.official}</span></p>`);
  return out;
}

function render(S: Story, lang: Lang) {
  const T = STORY[lang];
  document.documentElement.lang = lang;
  document.title = `${T.title} · grid.md`;
  $("langs").innerHTML = LANGS.map((l) => `<button type="button" data-lang="${l}" aria-pressed="${l === lang}" title="${STRINGS[l].langName}">${l.toUpperCase()}</button>`).join("");
  $("intro").innerHTML = `<h1>${T.title}</h1><p>${T.intro}</p>`;
  const width = $("chapters").clientWidth || 960;
  const ch = charts(S, lang, width);
  $("chapters").innerHTML = CHAPTERS.map((k) => {
    const b = T.chapters[k](S.chapters);
    const extra = k === "tomorrow" ? `<a class="cta" href="./">${T.back} →</a>` : `<div class="chart">${ch[k]}</div>`;
    const m = /^(≈?[\d.,:%×]+)\s*(.*)$/.exec(b.big);
    const big = m && m[2] ? `${m[1]}<small>${m[2]}</small>` : b.big;
    return `<section class="chapter" id="${k}"><p class="label">${b.label}</p><div class="num">${big}</div><p class="text">${b.text}</p>${extra}</section>`;
  }).join("");
  $("foot").innerHTML = `<span>${T.sources}</span><a href="https://github.com/iliev-blnk/grid.md/blob/main/research/SOLAR.md">SOLAR.md</a><a href="https://github.com/iliev-blnk/grid.md">${STRINGS[lang].linkCode}</a>`;
}

async function start() {
  const S: Story = await (await fetch(import.meta.env.BASE_URL + "data/story.json")).json();
  let lang = pickLang(stored(), navigator.languages ?? [navigator.language]);
  render(S, lang);
  let t: number | undefined;
  addEventListener("resize", () => { clearTimeout(t); t = window.setTimeout(() => render(S, lang), 150); });
  $("langs").addEventListener("click", (e) => {
    const b = (e.target as HTMLElement).closest("[data-lang]") as HTMLElement | null;
    if (!b) return;
    lang = b.dataset.lang as Lang;
    store(lang);
    render(S, lang);
  });
}

start().catch((e) => ($("intro").textContent = "grid.md: could not load the story (" + String(e) + ")"));
