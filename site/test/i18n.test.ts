import { describe, expect, test } from "vitest";
import { LANGS, STRINGS, pickLang } from "../src/i18n.ts";

describe("i18n", () => {
  test("every language has every string, none empty", () => {
    const keys = Object.keys(STRINGS.en).sort();
    for (const l of LANGS) {
      expect(Object.keys(STRINGS[l]).sort()).toEqual(keys);
      for (const k of keys) {
        const v = (STRINGS[l] as unknown as Record<string, unknown>)[k];
        expect(typeof v === "function" || (typeof v === "string" && v.length > 0)).toBe(true);
      }
    }
  });

  test("language choice: stored wins, then browser, then English", () => {
    expect(pickLang("ru", ["ro-MD"])).toBe("ru");
    expect(pickLang(null, ["ro-MD", "en"])).toBe("ro");
    expect(pickLang(null, ["ru-RU"])).toBe("ru");
    expect(pickLang(null, ["de-DE"])).toBe("en");
    expect(pickLang("xx", ["fr"])).toBe("en");
  });

  test("the summary states the backtest numbers in every language", () => {
    for (const l of LANGS) expect(STRINGS[l].tldr).toMatch(/9\s?%.*19\s?%/s);
  });
});
