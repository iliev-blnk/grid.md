import type { Lang } from "./i18n.ts";

export const CHAPTERS = ["before", "blackout", "corridor", "cutoff", "duck", "solar", "tomorrow"] as const;
export type Chapter = (typeof CHAPTERS)[number];

// the `chapters` block of data/story.json
export interface Ch {
  before: { tpp_share: number; load: number; tpp: number };
  blackout: { day: string; hour: number; low: number; before: number };
  corridor: { year: string; share: number; export_share: number; md_ro: number; md_ua: number };
  cutoff: { tpp_before: number; tpp_after: number; import_before: number; import_after: number };
  duck: { first_year: string; first: number; last_year: string; last: number; min_load: number };
  solar: { C: number; lo: number; hi: number; visible: number; prosumers: number };
}

export interface Block { label: string; big: string; text: string }

interface StoryStrings {
  title: string;
  intro: string;
  back: string;
  sources: string;
  legend: { load: string; tpp: string; fromRo: string; toUa: string; netImport: string; hidden: string; metered: string; official: string; total: string; prosumers: string };
  chapters: Record<Chapter, (c: Ch) => Block>;
}

const n0 = (v: number) => String(Math.round(v));
const pc = (v: number) => String(Math.round(v * 100));
const dec = (v: number, l: Lang) => (l === "en" ? v.toFixed(2) : v.toFixed(2).replace(".", ","));

export const STORY: Record<Lang, StoryStrings> = {
  en: {
    title: "Moldova's grid, 2021–2026",
    intro: "In five years Moldova's electricity changed more than in the thirty before. These are the hourly numbers from Moldelectrica, the grid operator, and what they show.",
    back: "Tomorrow's forecast",
    sources: "Data: Moldelectrica hourly archive, Open-Meteo (ERA5). Official solar figures: CNED via pv-magazine (March 2026).",
    legend: { load: "consumption", tpp: "Cuciurgan power station", fromRo: "in from Romania", toUa: "out to Ukraine", netImport: "net import", hidden: "hidden solar (estimate)", metered: "metered solar and wind", official: "official figures", total: "total", prosumers: "prosumers" },
    chapters: {
      before: (c) => ({ label: "Before the war · winter 2021–22", big: `${pc(c.before.tpp_share)}%`, text: `Almost all of Moldova's electricity came from one gas power station, Cuciurgan, in Transnistria. It produced ${n0(c.before.tpp)} MW on average while the country used ${n0(c.before.load)} MW.` }),
      blackout: (c) => ({ label: "23 November 2022", big: `${n0(c.blackout.low)} MW`, text: `Russian strikes on Ukraine's power grid took Moldova's down with it. At midday the country was using ${n0(c.blackout.before)} MW. In the hour from 15:00 the average fell to ${n0(c.blackout.low)} MW and both border links went quiet. Power was back by the evening.` }),
      corridor: (c) => ({ label: `${c.corridor.year} · the corridor`, big: `${pc(c.corridor.share)}%`, text: `In ${pc(c.corridor.share)}% of the hours of ${c.corridor.year}, power was coming in from Romania while power was going out to Ukraine. On average ${n0(c.corridor.md_ro)} MW came in and ${n0(-c.corridor.md_ua)} MW went out. Moldova became a corridor.` }),
      cutoff: (c) => ({ label: "1 January 2025 · the gas cutoff", big: `${n0(c.cutoff.tpp_after)} MW`, text: `Russian gas to Transnistria stopped. Cuciurgan's average output fell from ${n0(c.cutoff.tpp_before)} MW in 2024 to ${n0(c.cutoff.tpp_after)} MW in 2025, and imports rose from ${n0(c.cutoff.import_before)} to ${n0(c.cutoff.import_after)} MW on average.` }),
      duck: (c) => ({ label: "The midday dip", big: `${dec(c.duck.last, "en")}×`, text: `In May and June ${c.duck.first_year} the grid needed about as much power at 13:00 as at 20:00 (${dec(c.duck.first, "en")}×). In ${c.duck.last_year} it needed half as much (${dec(c.duck.last, "en")}×), because solar panels behind the meter now cover much of the middle of the day. The lowest hour of ${c.duck.last_year} so far: ${n0(c.duck.min_load)} MW.` }),
      solar: (c) => ({ label: "Hidden solar · summer 2026", big: `≈${c.solar.C} MW`, text: `That is our estimate of the solar power the grid operator cannot see, on rooftops and in small local parks, worked out from how much sunny days pull the midday load down. Likely range: ${c.solar.lo}–${c.solar.hi} MW. The official figure for rooftop prosumers is ${c.solar.prosumers} MW.` }),
      tomorrow: () => ({ label: "Tomorrow", big: "9:00", text: "Every morning at 9:00 grid.md forecasts tomorrow's consumption hour by hour. The midday dip is the hard part: it moves with the clouds." }),
    },
  },
  ro: {
    title: "Rețeaua Moldovei, 2021–2026",
    intro: "În cinci ani, energia electrică a Moldovei s-a schimbat mai mult decât în cei treizeci dinainte. Acestea sunt datele orare ale Moldelectrica, operatorul rețelei, și ce arată ele.",
    back: "Prognoza pentru mâine",
    sources: "Date: arhiva orară Moldelectrica, Open-Meteo (ERA5). Cifrele oficiale despre energia solară: CNED via pv-magazine (martie 2026).",
    legend: { load: "consum", tpp: "centrala de la Cuciurgan", fromRo: "intrare din România", toUa: "ieșire spre Ucraina", netImport: "import net", hidden: "solar ascuns (estimare)", metered: "solar și eolian contorizat", official: "cifre oficiale", total: "total", prosumers: "prosumatori" },
    chapters: {
      before: (c) => ({ label: "Înainte de război · iarna 2021–22", big: `${pc(c.before.tpp_share)}%`, text: `Aproape toată energia electrică a Moldovei venea de la o singură centrală pe gaz, Cuciurgan, din Transnistria. Producea în medie ${n0(c.before.tpp)} MW, iar țara consuma ${n0(c.before.load)} MW.` }),
      blackout: (c) => ({ label: "23 noiembrie 2022", big: `${n0(c.blackout.low)} MW`, text: `Atacurile rusești asupra rețelei Ucrainei au căzut și rețeaua Moldovei. La prânz țara consuma ${n0(c.blackout.before)} MW. În ora de la 15:00 media a scăzut la ${n0(c.blackout.low)} MW, iar ambele legături de la graniță au tăcut. Seara curentul revenise.` }),
      corridor: (c) => ({ label: `${c.corridor.year} · coridorul`, big: `${pc(c.corridor.share)}%`, text: `În ${pc(c.corridor.share)}% din orele anului ${c.corridor.year}, curentul intra din România în timp ce ieșea spre Ucraina. În medie intrau ${n0(c.corridor.md_ro)} MW și ieșeau ${n0(-c.corridor.md_ua)} MW. Moldova a devenit un coridor.` }),
      cutoff: (c) => ({ label: "1 ianuarie 2025 · oprirea gazului", big: `${n0(c.cutoff.tpp_after)} MW`, text: `Gazul rusesc spre Transnistria s-a oprit. Producția medie a centralei de la Cuciurgan a scăzut de la ${n0(c.cutoff.tpp_before)} MW în 2024 la ${n0(c.cutoff.tpp_after)} MW în 2025, iar importurile au crescut în medie de la ${n0(c.cutoff.import_before)} la ${n0(c.cutoff.import_after)} MW.` }),
      duck: (c) => ({ label: "Scăderea de la prânz", big: `${dec(c.duck.last, "ro")}×`, text: `În mai și iunie ${c.duck.first_year}, rețeaua avea nevoie la ora 13:00 de aproape la fel de mult curent ca la 20:00 (${dec(c.duck.first, "ro")}×). În ${c.duck.last_year} a avut nevoie de jumătate (${dec(c.duck.last, "ro")}×), pentru că panourile solare de după contor acoperă acum o mare parte din mijlocul zilei. Cea mai mică oră din ${c.duck.last_year} până acum: ${n0(c.duck.min_load)} MW.` }),
      solar: (c) => ({ label: "Solar ascuns · vara 2026", big: `≈${c.solar.C} MW`, text: `Aceasta este estimarea noastră pentru energia solară pe care operatorul rețelei nu o vede, pe acoperișuri și în parcuri locale mici, calculată din cât de mult scad zilele însorite consumul de la prânz. Interval probabil: ${c.solar.lo}–${c.solar.hi} MW. Cifra oficială pentru prosumatori este de ${c.solar.prosumers} MW.` }),
      tomorrow: () => ({ label: "Mâine", big: "9:00", text: "În fiecare dimineață la ora 9:00, grid.md prognozează consumul de mâine, oră cu oră. Scăderea de la prânz este partea grea: se mișcă odată cu norii." }),
    },
  },
  ru: {
    title: "Энергосистема Молдовы, 2021–2026",
    intro: "За пять лет электроэнергетика Молдовы изменилась сильнее, чем за тридцать лет до этого. Вот почасовые данные Moldelectrica, оператора сети, и что они показывают.",
    back: "Прогноз на завтра",
    sources: "Данные: почасовой архив Moldelectrica, Open-Meteo (ERA5). Официальные данные о солнечной энергии: CNED через pv-magazine (март 2026).",
    legend: { load: "потребление", tpp: "Кучурганская ГРЭС", fromRo: "из Румынии", toUa: "в Украину", netImport: "чистый импорт", hidden: "скрытая солнечная (оценка)", metered: "учтённые солнце и ветер", official: "официальные данные", total: "всего", prosumers: "просьюмеры" },
    chapters: {
      before: (c) => ({ label: "До войны · зима 2021–22", big: `${pc(c.before.tpp_share)}%`, text: `Почти вся электроэнергия Молдовы шла от одной газовой станции, Кучурганской ГРЭС в Приднестровье. Она давала в среднем ${n0(c.before.tpp)} МВт при потреблении страны ${n0(c.before.load)} МВт.` }),
      blackout: (c) => ({ label: "23 ноября 2022", big: `${n0(c.blackout.low)} МВт`, text: `Российские удары по энергосистеме Украины обесточили и Молдову. В полдень страна потребляла ${n0(c.blackout.before)} МВт. В час с 15:00 среднее упало до ${n0(c.blackout.low)} МВт, а обе связи на границе замолчали. К вечеру свет вернулся.` }),
      corridor: (c) => ({ label: `${c.corridor.year} · коридор`, big: `${pc(c.corridor.share)}%`, text: `В ${pc(c.corridor.share)}% часов ${c.corridor.year} года энергия шла из Румынии и одновременно уходила в Украину. В среднем входило ${n0(c.corridor.md_ro)} МВт и выходило ${n0(-c.corridor.md_ua)} МВт. Молдова стала коридором.` }),
      cutoff: (c) => ({ label: "1 января 2025 · газ отключён", big: `${n0(c.cutoff.tpp_after)} МВт`, text: `Поставки российского газа в Приднестровье прекратились. Средняя выработка Кучурганской ГРЭС упала с ${n0(c.cutoff.tpp_before)} МВт в 2024 году до ${n0(c.cutoff.tpp_after)} МВт в 2025-м, а импорт вырос в среднем с ${n0(c.cutoff.import_before)} до ${n0(c.cutoff.import_after)} МВт.` }),
      duck: (c) => ({ label: "Полуденный провал", big: `${dec(c.duck.last, "ru")}×`, text: `В мае и июне ${c.duck.first_year} года сети в 13:00 нужно было почти столько же энергии, сколько в 20:00 (${dec(c.duck.first, "ru")}×). В ${c.duck.last_year} году — вдвое меньше (${dec(c.duck.last, "ru")}×): солнечные панели за счётчиком теперь покрывают большую часть середины дня. Самый низкий час ${c.duck.last_year} года пока: ${n0(c.duck.min_load)} МВт.` }),
      solar: (c) => ({ label: "Скрытая солнечная · лето 2026", big: `≈${c.solar.C} МВт`, text: `Это наша оценка солнечной мощности, которую оператор сети не видит: на крышах и в небольших местных парках. Она рассчитана по тому, насколько солнечные дни снижают полуденное потребление. Вероятный диапазон: ${c.solar.lo}–${c.solar.hi} МВт. Официальная цифра для просьюмеров: ${c.solar.prosumers} МВт.` }),
      tomorrow: () => ({ label: "Завтра", big: "9:00", text: "Каждое утро в 9:00 grid.md прогнозирует потребление на завтра по часам. Полуденный провал — самая трудная часть: он движется вместе с облаками." }),
    },
  },
};
