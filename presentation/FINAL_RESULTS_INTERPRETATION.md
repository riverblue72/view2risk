# Final Results Interpretation

Status: IMPLEMENTED AND BROWSER VERIFIED

Results follows Question → Conclusion → Chart → Metric interpretation → Limitation. The presentation highlights exactly three principal findings; Results also retains M0/M1/M2 ablation and grouped Reliability details.

## A. Spatial accuracy and completion probabilities

The matched 236-origin / 120-event exploratory historical Test gives these event-weighted H1–H4 mean Brier scores (lower is better):

| Model | Mean Brier |
|---|---:|
| DDMDN | 0.01617 |
| EA_M1__calibrated | 0.01635 |
| conditional_AFT__calibrated | 0.01182 |
| constant_speed | 0.01562 |

This does not support universal superiority of DD-MDN or XGBoost. It is distinct from the official 120,871-window positional Test. A case's probability, such as 99.96%, is not model accuracy.

## B. Near-Exit training support

Minimum Train remaining distance changed from approximately 2.1919m to 0.0585m. Existing M1 H1 Brier improved approximately 0.10827 → 0.00618 on the historically reused matched cohort. Training origin/event composition also changed: this is not a controlled causal distance-only effect. Extra acceleration or crowding features did not establish independent gains. M2 jointly adds neighbors and location.

## C. Observation correction and uncertainty quality

IMPTC R cohort, 237 origins / 120 events, IID scale1:

| Method | ADE m | H4 Brier | Endpoint Coverage95 | Endpoint HDR95 m² |
|---|---:|---:|---:|---:|
| clean | 0.283 | 0.03472 | 96.05% | 7.37 |
| noisy | 3.925 | 0.33527 | 74.12% | 748.20 |
| filtered_mean | 0.742 | 0.08594 | 78.51% | 10.27 |
| rq | 3.173 | 0.15922 | 100.00% | 331.61 |

ADE averages +0.5~4s on 215 eligible origins. Brier uses 218 known H4 outcomes (111 positive origins). Coverage95 uses 228 endpoint positions. Mean HDR95 area uses 237 origins. The denominators differ and are labeled near the figures.

Filtered mean recovered substantial accuracy but under-covered future positions. FFBS covered all evaluated endpoints with excessively large regions and did not restore clean accuracy. High coverage alone is not superior UQ.

## Required evidence

1. Horizon-specific Brier comparison: existing exit_aware_summary.json dd_matched metrics.
2. Training-distance distribution: existing training_distance_coverage and plot.
3. M0/M1/M2 ablation: existing key_table and paired Validation comparisons.
4. Clean/Noisy/Filtered/FFBS Brier and ADE: existing r_robustness_summary.json.
5. Coverage+area: paired cards for each same method; endpoint scope explicit.
6. Case CDF+GT: full saved DD/XGBoost curves; one vertical actual Exit time.
7. Aggregate Reliability: existing pres/evidence.json grouped predictions/observed frequencies with bin counts and stored cluster intervals. No artificial GT distribution.

Definitions are given next to charts or in compact expandable help. ECE is a bin-dependent weighted probability/frequency discrepancy, not accuracy. Reliability bins with few events remain unstable. Neither positional calibration nor one successful example proves completion calibration.

## Preview and provenance

- Presentation: http://127.0.0.1:18779/presentation/presentation.html
- Methods: http://127.0.0.1:18779/presentation/methods.html
- Simulation / Compare: http://127.0.0.1:18779/presentation/compare.html
- Results: http://127.0.0.1:18779/presentation/results.html
- Existing rolling replay: http://127.0.0.1:18779/presentation/?case=o0008#/simulation

Canonical source: presentation/site/; deployment copy: docs/presentation/. The public website replays saved outputs, not new browser inference. No model fitting or inference was run. No saved forecasts, GT, checkpoints, restricted inD trajectories or previous final releases were changed. Historical Test reuse is exploratory, not untouched external validation.

Read and cross-checked: site/METHODOLOGY.md; site/exit_aware/EXIT_AWARE_FINAL_REPORT.md; site/r_robustness/FINAL_R_ROBUSTNESS_REPORT.md; site/pres/PRESENTATION_METRIC_AUDIT.md; current source and public JSON. The old Brier 0.00000 / 0.04626 discrepancy remains resolved as H1 versus H4, not conflicting values at one horizon.
