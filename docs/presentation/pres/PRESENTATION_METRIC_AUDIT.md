# Presentation Metric Audit

Status: RESOLVED — same cohort, different horizons; no historical metric overwritten.

## Direct answer

The disputed original-landmark entries compare H4 (old report) with H1 (Exit-aware supplementary table). Counts 936 origins / 354 events are the same; horizon eligibility differs. No probability, GT, weight or Brier-contribution differences were found at matching origin/model/horizon keys.

## Recomputed constant-speed results

| cohort             | model          |   horizon_s |   n_origins |   n_events |   n_known |   n_complete |   n_unknown |     brier |   event_weighted_brier |   sum_eligible_event_weights |
|:-------------------|:---------------|------------:|------------:|-----------:|----------:|-------------:|------------:|----------:|-----------------------:|-----------------------------:|
| original_landmarks | constant_speed |           1 |         936 |        354 |       922 |            0 |          14 | 0         |              0         |                      343.167 |
| original_landmarks | constant_speed |           2 |         936 |        354 |       901 |          149 |          35 | 0.0188679 |              0.0197069 |                      329.833 |
| original_landmarks | constant_speed |           3 |         936 |        354 |       892 |          333 |          44 | 0.044843  |              0.0433213 |                      323.167 |
| original_landmarks | constant_speed |           4 |         936 |        354 |       888 |          471 |          48 | 0.0461712 |              0.0462578 |                      320.667 |

The exact outcome rule is y=1 if upper_s≤H; y=0 if lower_s>H, or right-censored lower_s≥H; otherwise unknown. Eligible denominator changes with H. Each event contributes weight1 across its origins; only known outcomes enter each horizon denominator.

## Exact audit

| field         |     n |   different |   max_abs_diff |
|:--------------|------:|------------:|---------------:|
| origin_s      | 52512 |           0 |    0           |
| probability   | 52512 |           0 |    3.38813e-21 |
| outcome       | 52512 |           0 |    0           |
| lower_s       | 52512 |           0 |    0           |
| upper_s       | 52512 |           0 |    0           |
| event_weight  | 52512 |           0 |    0           |
| squared_error | 52512 |           0 |    3.38813e-21 |
| event_id      | 52512 |           0 |  nan           |
| track_id      | 52512 |           0 |  nan           |
| recording     | 52512 |           0 |  nan           |
| date          | 52512 |           0 |  nan           |

52,512 shared prediction rows matched one-to-one by cohort, split, uid, model and horizon; all 52,512 old Test prediction rows are represented. IDs, recording/date, origin timestamp, bounds, probabilities, weights and squared errors match. Independent reconstruction used original features.csv bounds and distance/longitudinal speed.

## 236-origin /120-event matched cohort

| model                       |   horizon_s |   n_origins |   n_events |   n_known |   event_weighted_brier |   brier_ci_low |   brier_ci_high |        ece |
|:----------------------------|------------:|------------:|-----------:|----------:|-----------------------:|---------------:|----------------:|-----------:|
| constant_speed              |           1 |         236 |        120 |       236 |             0.00833333 |    0           |      0.021566   | 0.00833333 |
| constant_speed              |           2 |         236 |        120 |       224 |             0.00888889 |    0           |      0.0241665  | 0.00888889 |
| constant_speed              |           3 |         236 |        120 |       222 |             0.0269058  |    0.0052249   |      0.0495121  | 0.0269058  |
| constant_speed              |           4 |         236 |        120 |       217 |             0.0183486  |    0.00446281  |      0.0360825  | 0.0183486  |
| conditional_AFT__calibrated |           1 |         236 |        120 |       236 |             0.0098267  |    0.00105349  |      0.0222618  | 0.0106087  |
| conditional_AFT__calibrated |           2 |         236 |        120 |       224 |             0.00534996 |    0.000673996 |      0.0141635  | 0.00900056 |
| conditional_AFT__calibrated |           3 |         236 |        120 |       222 |             0.0143898  |    0.00459182  |      0.0249555  | 0.0185625  |
| conditional_AFT__calibrated |           4 |         236 |        120 |       217 |             0.0177252  |    0.00717417  |      0.0303321  | 0.0194676  |
| M1__calibrated              |           1 |         236 |        120 |       236 |             0.10827    |    0.073711    |      0.147956   | 0.108296   |
| M1__calibrated              |           2 |         236 |        120 |       224 |             0.0463438  |    0.0226446   |      0.0751838  | 0.0417934  |
| M1__calibrated              |           3 |         236 |        120 |       222 |             0.0271441  |    0.0133852   |      0.0399521  | 0.0254027  |
| M1__calibrated              |           4 |         236 |        120 |       217 |             0.0441012  |    0.0234522   |      0.0700078  | 0.0538414  |
| EA_M1__calibrated           |           1 |         236 |        120 |       236 |             0.00618322 |    0.0011671   |      0.0139361  | 0.00651837 |
| EA_M1__calibrated           |           2 |         236 |        120 |       224 |             0.0102101  |    0.00273458  |      0.0202146  | 0.00907687 |
| EA_M1__calibrated           |           3 |         236 |        120 |       222 |             0.0250276  |    0.0124176   |      0.0382167  | 0.0191285  |
| EA_M1__calibrated           |           4 |         236 |        120 |       217 |             0.0239602  |    0.0115657   |      0.0364984  | 0.0244632  |
| DDMDN                       |           1 |         236 |        120 |       236 |             0.00324418 |    4.60072e-05 |      0.00960454 | 0.00638932 |
| DDMDN                       |           2 |         236 |        120 |       224 |             0.00659745 |    0.00028957  |      0.0176098  | 0.0072     |
| DDMDN                       |           3 |         236 |        120 |       222 |             0.0201287  |    0.00869945  |      0.0322595  | 0.0222295  |
| DDMDN                       |           4 |         236 |        120 |       217 |             0.0347182  |    0.0255454   |      0.0459874  | 0.0487916  |

All 72 matched model/horizon metric rows recomputed from saved per-origin probabilities (18 models ×4 horizons), including new Exit-aware models. The 48 original shared matched rows (12 models×4) have identical predictions/GT/weights across runs. No model inference or refitting was needed.

## Why the report looked inconsistent

Original report context:
```
Do not compare these936landmarks/354events to the236-origin DD-MDN cohort. This supplementary cohort uses frozen models and same protocol.

| method | n_origins | n_events | n_known | brier | ci_low | ci_high | brier_ipcw | ece |
|---|---|---|---|---|---|---|---|---|
| constant_speed | 936 | 354 | 888 | 0.04626 | 0.03289 | 0.06003 | 0.04600 | 0.04626 |
| distance_speed__raw | 936 | 354 | 888 | 0.02650 | 0.01898 | 0.03474 | 0.02632 | 0.01704 |
```

Exit-aware finalize.py explicitly filters supplementary table with met.horizon_s==1, but omitted the horizon column from the displayed table. Original report table is H4. The presentation will display H1/H4 explicitly and will not use supplementary landmark statistics as matched-cohort evidence. This is a presentation-label omission, not evidence of an evaluation bug.

## Definitions that must stay separate

Origin-average Brier and event-weighted Brier differ. Mean H1–H4 is an equal mean of four horizon-specific event-weighted scores; it is not a pooled sum over all valid rows. DD-MDN full-Test positional cohort (120,871 windows), R cohort (237 origins), matched AFT cohort (236 origins),936 landmark origins and exit-aware supplementary cohort are never pooled. Historical Test is reused/exploratory. IPCW/CRPS and U95 definitions differ from complete-case Brier and are labeled separately.

## Preservation and reproduction

Run: `../.venv/bin/python [private-source]` from [private-source] Read-only sources: [private-source] [private-source] [private-source] original metric/report/code files. Exact private comparison: [private-source] Aggregate: [private-source] No model/checkpoint/GT changes.