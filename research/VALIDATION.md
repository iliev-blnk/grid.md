# Validation (issue dates 2025-04-01..2025-09-30) — design choices made before the test window

## Grid

Grid over num_leaves × learning rate × min_data_in_leaf, using the original features (variant A)
and early stopping on validation. Full table: `tune_load.csv`. Best: 15 / 0.03 / 100 at 638
trees (pinball 17.6, median MAPE 12.4%, 90% coverage 0.73).

## Why A was not good enough

- The median MAPE was 12.4% and the 90% band covered only 73% of hours.
- The naive baselines on the same window were: same hour latest known 14.4%, same hour last
  week 14.7%, operator plan 23.4%, bias-corrected plan 16.3%.
- The lag error is 6–7% at night but 25–28% at midday. Moldelectrica's Load is **net of
  distributed solar**: on Easter Sunday 2025, 14:00 load was 133 MW against 362 MW the day
  before.
- Solar capacity grows quickly, so a model trained mostly on 2022–24 underestimates how much
  sunshine now cuts net load.

## Variants (same hyperparameters, 638 trees)

| variant | median MAPE | pinball | 80% cov | 90% cov |
| --- | ---: | ---: | ---: | ---: |
| A original features | 12.7 | 19.0 | – | 0.64 |
| B + radiation on the lag days (rad_d7, rad_l1, differences) | 12.7 | 19.0 | – | 0.63 |
| C + recent solar sensitivity k_solar (14-day slope of Δload on Δradiation, hours 9–16) | 12.3 | 18.5 | – | 0.65 |
| **D C, predicting y − (same hour last week)** | 10.0 | **14.7** | 0.65 | 0.78 |
| E as D with base = latest known same hour | 11.5 | 16.4 | 0.60 | 0.70 |
| F D + one-year half-life sample weights | 9.9 | 15.3 | 0.59 | 0.72 |
| **G D + rolling 8-week conformal shift per quantile** | **9.6** | 15.0 | **0.74** | **0.85** |

**Chosen: D + G.** G costs 0.3 pinball but brings the 90% band from 0.78 to 0.85 coverage. For a
published range, calibration matters more than a slightly lower loss. The hyperparameters stay
at the grid's best (they were not re-tuned for D). This was fixed and committed before the test
window was scored.
