# Results and Findings Redesign

Status: PASSED — new `results.html`; old experiment routes preserved.

## Four research questions

1. **Does better position prediction mean better completion prediction?** Official 120,871-window positional evaluation is separate and expandable. A primary H1–H4 Brier plot compares the same 236 origins / 120 events / 55 recordings. It uses saved event-weighted Brier, not accuracy. Horizon-known counts are 236/236, 224/236, 222/236 and 217/236.
2. **Why did Exit-aware training improve?** Stacked Train distance distributions use exact saved counts: original 1,113 origins / 404 events; Exit-aware 2,322 / 446. Distance bins 0–1 / 1–2 / ≥2 m are 0/0/1113 versus 393/385/1544. Minimum distance changes from 2.1919001 m to 0.0585043 m. Matched M1 H1 Brier changes from 0.1082696 to 0.0061832. This is improvement over original XGBoost, not universal superiority.
3. **Do more features help?** M0/M1/M2 mean Brier bars start at zero, with the conclusion that no robust independent gain was established. The expandable paired Validation table preserves recorded confidence intervals. M2 adds both crowding and location.
4. **What if observations are noisy?** Brier, Coverage95 and HDR95 area are adjacent charts with distinct labeled units/scales. Coverage is not interpreted without area.

## Verified H4 R evidence

IMPTC, IID 1×; 237 origins / 120 events; historically reused Test.

| Condition | H4 Brier | Coverage95 | HDR95 m² | n Brier | n position | n area |
| clean | 0.03471772 | 96.0526% | 7.3664 | 218 | 228 | 237 |
| noisy | 0.33527491 | 74.1228% | 748.1967 | 218 | 228 | 237 |
| filtered_mean | 0.08594072 | 78.5088% | 10.2724 | 218 | 228 | 237 |
| rq | 0.15922321 | 100.0000% | 331.6091 | 218 | 228 | 237 |

Coverage percentages have numerator/denominator 219/228 Clean, 169/228 Noisy, 179/228 Filtered mean, 228/228 FFBS. Brier uses 218 known outcomes; area uses all 237 origins. The 236-origin XGBoost cohort is not pooled with these records.

Filtered mean recovers substantial accuracy but has low empirical inclusion; FFBS includes more positions with very large regions. Neither observation-noise method establishes independent real-camera calibration. DD-MDN Q-only remains default.

## Traceability and presentation

Every figure has cohort, horizon, units, source link and interpretation. Technical tables expose exact values, known/positive counts and saved intervals. No metric is hardcoded from the task prompt. Charts read `pres/evidence.json`, `exit_aware/exit_aware_summary.json` and `r_robustness/r_robustness_summary.json` directly.

The matched event-weighted line chart, sampling comparison, ablation bars and R triple chart are separate. Historical Test reuse, sparse behavioral groups, operational GT and unvalidated inD Exit remain explicit. The completed H1/H4 metric-discrepancy audit is retained.

On narrow screens, R bars stack vertically; dense exact-value tables and the horizon line chart scroll inside their containers, not the whole page.

## Preservation and publication boundary

Canonical source: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/`.
Deployment mirror: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/docs/presentation/`.
The 202 static files are byte-identical across those directories. This is a local, uncommitted review revision on `presentation/synchronized-three-panel-20261123`; no push was performed. The current GitHub Pages release is unchanged.

188 previously protected files remain byte-identical, including `final/`, `docs/final/`, saved prediction/metric artifacts and the resolved historical metric audit. No model training, inference, hyperparameter selection, calibration, GT modification or new private-data export occurred. Individual replay still uses only existing allowlisted IMPTC excerpts. The website is a static replay, not a browser inference service.
