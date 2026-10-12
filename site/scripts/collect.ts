/** Build public/data/site.json: the latest forecast, the last 7 days of load + plan, all scores. */
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";

const root = new URL("../..", import.meta.url).pathname;
const out = join(root, "site", "public", "data");
mkdirSync(out, { recursive: true });

const read = (dir: string) =>
  existsSync(join(root, dir))
    ? readdirSync(join(root, dir)).filter((f) => f.endsWith(".json")).sort().map((f) => JSON.parse(readFileSync(join(root, dir, f), "utf8")))
    : [];
const forecasts = read("forecasts");
const scores = read("scores");
if (!forecasts.length) throw new Error("no forecasts");
const latest = forecasts.at(-1);

const csv = gunzipSync(readFileSync(join(root, "data", "load.csv.gz"))).toString("utf8").trim().split("\n");
const head = csv[0].split(",");
const iDay = head.indexOf("day"), iHour = head.indexOf("hour"), iLoad = head.indexOf("load"), iPlan = head.indexOf("plan");
const first = new Date(Date.parse(latest.target_day) - 8 * 86400e3).toISOString().slice(0, 10);
const recent = csv.slice(1).map((l) => l.split(",")).filter((p) => p[iDay] >= first)
  .map((p) => ({ day: p[iDay], hour: Number(p[iHour]), load: p[iLoad] === "" ? null : Number(p[iLoad]), plan: p[iPlan] === "" ? null : Number(p[iPlan]) }));

const issued = forecasts.map((f) => ({ day: f.target_day, issued_at: f.issued_at, late: f.late }));
copyFileSync(join(root, "data", "story.json"), join(out, "story.json"));
writeFileSync(join(out, "site.json"), JSON.stringify({ latest, recent, scores, issued }));
console.log(`collect: latest ${latest.target_day}, ${recent.length} recent hours, ${scores.length} scores`);
