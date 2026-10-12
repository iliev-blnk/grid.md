# Data facts (checked 2026-10-12)

Evidence: Moldelectrica months 2024-07..2026-10 downloaded through `archive2.php` (79,938 15-min
rows), and a reachability workflow run on GitHub Actions.

## 1. Moldelectrica timestamps

- Local wall-clock time (Europe/Chisinau), labelled at the **start** of each 15-min interval:
  on spring days exactly the `03:00..03:45` labels are missing, which only fits start labels.
- The archive's date window is half-open. A request for 2024-01-01..2024-01-02 returns the
  labels `2024-01-01 00:15` … `2024-01-03 00:00`, so each day's `00:00` interval arrives with the
  previous request. Ingest concatenates and de-duplicates.
- **Spring change** (2025-03-30, 2026-03-29): the `03:00..03:45` labels are missing, giving a
  23-hour day (91–92 rows).
- **Autumn change** (2024-10-27, 2025-10-26): the repeated hour appears **once**, so the day has
  96 rows (24 labels), not 100.
- Consequence: the load day is defined in wall-clock hour labels, 24 in autumn and 23 in spring.
  The repeated autumn hour is a single target.

## 2. What changed in 2025

| | 2024-07..12 | 2025-04..09 | 2025-11..2026-02 | 2026-04..09 |
| --- | ---: | ---: | ---: | ---: |
| mean load, MW | 627–761 | 498–612 | 728–812 | 459–581 |
| TPP (Cuciurgan) output, MW | 580–645 | 136–174 | 309–374 | 124–184 |
| net import (Balance), MW | −19..145 | 279–356 | 371–391 | 228–336 |

- The **Load ≈ Generation + Balance** identity holds on 97% of rows, so the definition of Load
  did not change.
- From January 2025 (the Transnistria gas cutoff) the TPP output falls by ~450 MW and imports
  replace it. Summer load falls by ~150–200 MW, while winter 2025-26 is *higher* than winter
  2024-25. That is consistent with industry shutting and electric heating replacing gas, but the
  data alone cannot prove it.
- Consequence: keep training from 2022 with a `post2025` regime flag. The recent-lag features
  (D−1, D−7, last-24-h mean) carry the level.

## 3. The operator plan ("Load Shedule")

- Plan rows appear in the archive **only together with the actuals** (at 00:30 local on 12 Oct the
  archive ended at `2026-10-12 00:15`; no future rows). We cannot see when the plan was made.
  Consequence: the plan is a **benchmark only**, never a feature.
- **The plan is biased upward:** the mean signed error (plan − load) is +47..+119 MW in most
  months, and only −10..+14 MW in 2025-11..2026-02. MAPE: 7.6–12% in 2024-H2, 16–29% in
  2025-03..09, 5.5–8% in winter 2025-26, 22–41% in 2026-03..10.
- Consequence: add a fairer benchmark as well, the **bias-corrected plan**: plan − its mean error
  over the 28 days before the issue date. If the model only beats the raw plan, the report says
  so.

## 4. Reachability

- From GitHub Actions: Energy-Charts 200 and Open-Meteo 200, but **Moldelectrica 403 (a
  Cloudflare "Just a moment…" challenge)**, also with full browser headers.
- From home (a residential IP in Romania/Moldova): 200.
- Consequence: the daily pipeline runs from a **systemd user timer on the user's machine**
  (spec fallback). GitHub Actions does CI and Pages only.
- If the machine is asleep at 09:00 local, the timer fires on wake, as long as it is still before
  23:00 local on D. The inputs are still cut at 09:00 and the file records the actual
  `issued_at`. Days with no run are gaps in the record, not back-filled.

## 5. Archive gaps

- Hourly table 2021-12-01..2026-10-11: 42,583 hours.
- Two multi-day outages in the source, which are blank in the archive itself:
  - 2022-09-23..26: 42 hours;
  - 2024-11-06..11: 114 hours.
- All other complete months miss ≤ 4%.
- Missing hours are dropped from training and left unscored.

## 6. Cross-border flow signs

- `balance ≈ md_ua + md_ro` on 94.6% of hours (within 5 MW), and `balance ≈ load − gen` on
  93.2%.
- **Positive = power flowing into Moldova.**
- Yearly means, MD–UA / MD–RO, MW: 2022 −120 / +224; 2023 −238 / +243; 2024 −226 / +255;
  2025 −24 / +357; 2026 −245 / +555.
- **Moldova is a corridor.** The share of hours importing from Romania while exporting to
  Ukraine: 56% (2022), 79% (2023), 74% (2024), 49% (2025), 74% (2026).

## 7. The blackout of 23 November 2022

- Hourly load that day: 851–884 MW from 09:00 to 13:00, 724 MW at 14:00, **290 MW at 15:00**,
  then 405 / 440 / 600 MW and back to 715 MW by 19:00.
- Both border flows fell to almost zero in the 15:00 hour (MD–UA +24, MD–RO +12, against −365 /
  +1,005 an hour earlier): the system was cut off from its neighbours.
- That morning, Moldova was carrying up to ~1,100 MW in from Romania and ~830 MW out to Ukraine.
- These are hourly means, so the true 15-minute low was deeper.
