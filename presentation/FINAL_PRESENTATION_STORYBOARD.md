# Final Presentation Storyboard

Status: IMPLEMENTED AND BROWSER VERIFIED

The research question is: Can this recorded pedestrian complete the crossing within H=1,2,3,4 seconds, and how trustworthy is that probability? Seven scenes tell one story over approximately 330 seconds. Timing is a speaker allocation, not a measured audience comprehension result.

| Scene | Question / purpose | Main visual | Takeaway | Target time |
|---|---|---|---|---|
| 1 | 이 보행자는 앞으로 몇 초 안에 횡단보도를 다 건널까? | Actual saved f2 position and Exit; P(T≤H) | Location, completion probability and reliability are distinct | 35s |
| 2 | 횡단 완료를 어떻게 정의했을까? | Actual semantic boundary-fit map and GT catalog | First passage plus separate 0.12s confirmation; censoring is unknown future | 45s |
| 3 | 같은 보행자를 어떻게 예측했을까? | Two parallel input→method→output diagrams | Official pretrained DD-MDN and separately trained XGBoost AFT | 55s |
| 4 | 예측이 실제 기록과 일치했을까? | Main full CDF chart, actual Exit line, small locked 3D scene | Same event/origin, different probabilities, directly evaluated against GT | 65s |
| 5 | 관측 위치가 틀리면 어떻게 될까? | Actual/noisy/Kalman/8 FFBS histories; saved H1–H4 probabilities | R is an external synthetic proxy; correction and uncertainty are different | 45s |
| 6 | 전체 실험에서 무엇을 발견했을까? | Exactly three finding tabs with stored aggregate graphs | Position≠completion quality; near-Exit support; accuracy/area tradeoff | 50s |
| 7 | 무엇을 구현하고 배웠는가? | Build / learn / significance, concise limits | Reproducible evaluation and failure analysis, not a deployed safety system | 35s |

## Reveal and controls

Scene 4 has seven reveals: current observation → DD spatial forecast → XGBoost CDF → both CDFs → observed future/Exit → individual squared errors → transition to aggregate evidence. Next/Previous and arrow keys traverse scenes/reveals; progress bar opens each scene. Notes contain Korean spoken explanations and transitions; fullscreen is optional.

The example is o0008, public-imptc-01, f2, origin +8s. Distance≈3.42m, speed≈1.57m/s, acceleration≈−0.012m/s², 3m neighbors=2. H3: DD=.6625, Exit-aware M1=.9995645759508139, actual residual Exit≈2.063445s. Actual GT is a vertical line, never a Gaussian. The XGBoost median bracket 2.15–2.20s comes from the saved CDF grid; H3 is a query horizon rather than the predicted duration.

R scenes retain the same observed future. SPD Train n=2465, sqrt(Rxx)≈15.7cm, sqrt(Ryy)≈17.8cm. Clean does not inject bias. Filtered mean estimates one history; FFBS propagates eight temporally correlated histories. Public R artifacts contain H1–H4 probabilities only, so they are plotted as discrete points without invented intermediate CDF values.

## Scientific boundaries

The GT catalog is 1019 complete, 170 right-censored, 218 unresolved, 8 returned events, not Test sample size. DD-MDN uses 10 points/0.9s and predicts eight positions through +4s. XGBoost does not receive DD predictions. Future observations appear only in labels and evaluation. PedPy is descriptive analysis. Three principal findings preserve negative results and cohort distinctions.

Screenshots: review/screenshots/scene_1.png through scene_7.png; cdf_gt_individual.png; r_comparison.png. Presenter notes are implemented in pres/story.js, accessible through the page.

## Preview and provenance

- Presentation: http://127.0.0.1:18779/presentation/presentation.html
- Methods: http://127.0.0.1:18779/presentation/methods.html
- Simulation / Compare: http://127.0.0.1:18779/presentation/compare.html
- Results: http://127.0.0.1:18779/presentation/results.html
- Existing rolling replay: http://127.0.0.1:18779/presentation/?case=o0008#/simulation

Canonical source: presentation/site/; deployment copy: docs/presentation/. The public website replays saved outputs, not new browser inference. No model fitting or inference was run. No saved forecasts, GT, checkpoints, restricted inD trajectories or previous final releases were changed. Historical Test reuse is exploratory, not untouched external validation.

Read and cross-checked: site/METHODOLOGY.md; site/exit_aware/EXIT_AWARE_FINAL_REPORT.md; site/r_robustness/FINAL_R_ROBUSTNESS_REPORT.md; site/pres/PRESENTATION_METRIC_AUDIT.md; current source and public JSON. The old Brier 0.00000 / 0.04626 discrepancy remains resolved as H1 versus H4, not conflicting values at one horizon.
