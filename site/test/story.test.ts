import { readFileSync } from "node:fs";
import { describe, expect, test } from "vitest";
import { LANGS } from "../src/i18n.ts";
import { CHAPTERS, STORY } from "../src/i18n-story.ts";

const S = JSON.parse(readFileSync(new URL("../../data/story.json", import.meta.url), "utf8"));
const c = S.chapters;

describe("story text", () => {
  test("every language has every chapter and string", () => {
    const keys = Object.keys(STORY.en).sort();
    for (const l of LANGS) {
      expect(Object.keys(STORY[l]).sort()).toEqual(keys);
      for (const ch of CHAPTERS) {
        const t = STORY[l].chapters[ch](c);
        expect(t.label.length && t.big.length && t.text.length).toBeTruthy();
      }
    }
  });

  test("chapter numbers match story.json in every language", () => {
    for (const l of LANGS) {
      const t = (ch: (typeof CHAPTERS)[number]) => { const x = STORY[l].chapters[ch](c); return x.big + " " + x.text; };
      expect(t("before")).toContain(String(Math.round(c.before.tpp_share * 100)));
      expect(t("blackout")).toContain(String(Math.round(c.blackout.low)));
      expect(t("blackout")).toContain(String(Math.round(c.blackout.before)));
      expect(t("corridor")).toContain(String(Math.round(c.corridor.share * 100)));
      expect(t("cutoff")).toContain(String(Math.round(c.cutoff.tpp_before)));
      expect(t("cutoff")).toContain(String(Math.round(c.cutoff.tpp_after)));
      expect(t("duck")).toContain(c.duck.last.toFixed(2).replace(".", l === "en" ? "." : ","));
      expect(t("solar")).toContain(String(c.solar.C));
      expect(t("solar")).toContain(String(c.solar.prosumers));
    }
  });
});
