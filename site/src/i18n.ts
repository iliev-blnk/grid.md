export const LANGS = ["en", "ro", "ru"] as const;
export type Lang = (typeof LANGS)[number];

export interface Strings {
  locale: string;
  langName: string;
  tldrTitle: string;
  tldr: string;
  kicker: (day: string, hour: string) => string;
  unit: string;
  range: (lo: string, hi: string, unit: string) => string;
  chartNote: string;
  issued: (time: string) => string;
  late: string;
  recordTitle: string;
  recordNone: string;
  recordSummary: (n: number, model: string, plan: string, in90: string) => string;
  colDay: string;
  colModel: string;
  colPlan: string;
  colIn90: string;
  linkMethod: string;
  linkForecasts: string;
  linkCode: string;
  credits: string;
}

export const STRINGS: Record<Lang, Strings> = {
  en: {
    locale: "en-GB",
    langName: "English",
    tldrTitle: "In short",
    tldr: "Every morning at 9:00 this page estimates how much electricity Moldova will use tomorrow, hour by hour. It shows a likely range, not just one number. Over the past year it was off by about 9% on average, roughly half the error of the grid operator's own plan (19%).",
    kicker: (day, hour) => `Moldova tomorrow, ${day} · peak around ${hour}`,
    unit: "MW",
    range: (lo, hi, u) => `90% sure it lands between ${lo} and ${hi} ${u}`,
    chartNote: "Tomorrow hour by hour. Dark band: 50% likely. Light band: 90% likely. Line: the most likely value.",
    issued: (t) => `Issued ${t}, Moldova time`,
    late: "after 9:00, but using only data available at 9:00",
    recordTitle: "How it has done",
    recordNone: "No day has been checked yet. Each day is checked once Moldelectrica has published all of its hours.",
    recordSummary: (n, m, p, i) => `${n} ${n === 1 ? "day" : "days"} checked · average error: this forecast ${m}, the grid operator's plan ${p} · hours inside the 90% range: ${i}`,
    colDay: "day",
    colModel: "this forecast",
    colPlan: "operator plan",
    colIn90: "inside 90%",
    linkMethod: "How it works and how well",
    linkForecasts: "All past forecasts",
    linkCode: "Source code",
    credits: "Data: Moldelectrica, Open-Meteo.",
  },
  ro: {
    locale: "ro-RO",
    langName: "Română",
    tldrTitle: "Pe scurt",
    tldr: "În fiecare dimineață la ora 9:00, această pagină estimează cât curent electric va consuma Moldova mâine, oră cu oră. Arată un interval probabil, nu doar o singură cifră. În ultimul an a greșit în medie cu circa 9%, cam jumătate din eroarea planului operatorului rețelei (19%).",
    kicker: (day, hour) => `Moldova mâine, ${day} · vârf în jurul orei ${hour}`,
    unit: "MW",
    range: (lo, hi, u) => `90% sigur că va fi între ${lo} și ${hi} ${u}`,
    chartNote: "Mâine, oră cu oră. Banda închisă: 50% probabil. Banda deschisă: 90% probabil. Linia: valoarea cea mai probabilă.",
    issued: (t) => `Emis ${t}, ora Moldovei`,
    late: "după ora 9:00, dar doar cu datele disponibile la 9:00",
    recordTitle: "Cum s-a descurcat",
    recordNone: "Nicio zi nu a fost verificată încă. Fiecare zi este verificată după ce Moldelectrica publică toate orele ei.",
    recordSummary: (n, m, p, i) => `${n} ${n === 1 ? "zi verificată" : "zile verificate"} · eroare medie: această prognoză ${m}, planul operatorului rețelei ${p} · ore în intervalul de 90%: ${i}`,
    colDay: "ziua",
    colModel: "această prognoză",
    colPlan: "planul operatorului",
    colIn90: "în intervalul de 90%",
    linkMethod: "Cum funcționează (în engleză)",
    linkForecasts: "Toate prognozele",
    linkCode: "Cod sursă",
    credits: "Date: Moldelectrica, Open-Meteo.",
  },
  ru: {
    locale: "ru-RU",
    langName: "Русский",
    tldrTitle: "Коротко",
    tldr: "Каждое утро в 9:00 эта страница оценивает, сколько электроэнергии Молдова потребит завтра, по часам. Она показывает вероятный диапазон, а не одно число. За последний год средняя ошибка составила около 9%, примерно вдвое меньше, чем у плана оператора сети (19%).",
    kicker: (day, hour) => `Молдова завтра, ${day} · пик около ${hour}`,
    unit: "МВт",
    range: (lo, hi, u) => `С вероятностью 90%: от ${lo} до ${hi} ${u}`,
    chartNote: "Завтра по часам. Тёмная полоса: вероятность 50%. Светлая полоса: 90%. Линия: наиболее вероятное значение.",
    issued: (t) => `Выпущен ${t} по времени Молдовы`,
    late: "позже 9:00, но только по данным, доступным в 9:00",
    recordTitle: "Как он справлялся",
    recordNone: "Ещё ни один день не проверен. День проверяется, когда Moldelectrica опубликует все его часы.",
    recordSummary: (n, m, p, i) => `Проверено дней: ${n} · средняя ошибка: этот прогноз ${m}, план оператора сети ${p} · часов внутри 90% диапазона: ${i}`,
    colDay: "день",
    colModel: "этот прогноз",
    colPlan: "план оператора",
    colIn90: "внутри 90%",
    linkMethod: "Как это работает (на английском)",
    linkForecasts: "Все прогнозы",
    linkCode: "Исходный код",
    credits: "Данные: Moldelectrica, Open-Meteo.",
  },
};

/** Stored choice wins, then the first supported browser language, then English. */
export function pickLang(stored: string | null, browser: readonly string[]): Lang {
  if (stored && (LANGS as readonly string[]).includes(stored)) return stored as Lang;
  for (const b of browser) {
    const base = b.toLowerCase().split("-")[0];
    if ((LANGS as readonly string[]).includes(base)) return base as Lang;
  }
  return "en";
}
