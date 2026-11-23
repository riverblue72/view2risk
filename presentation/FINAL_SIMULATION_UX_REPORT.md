# Final Simulation UX Report

Status: IMPLEMENTED AND BROWSER VERIFIED

The primary question is a selected H-second completion probability for one real recorded pedestrian. Normal mode shows GT by default. Presentation mode hides/reveals the same GT; the saved values are identical.

## Interaction

- Plain Korean filters retrieve existing origins by distance, walking speed, acceleration category, neighbors and crosswalk. They do not change an individual's motion.
- Guided has exact complete matches o0000 (f1,+0s), o0008 (f2,+8s, default), o0011 (f3,+1s). These are origins, not necessarily independent people.
- Broader artifacts: 35 DD origins, 6 AFT comparison origins, 3 R packets across 3 public IMPTC events. Missing results and unknown/censored outcomes are distinct.
- Shared horizon H1–H4 updates prediction values, CDF annotations, region and GT containment at index 2H−1.
- Playback begins before recorded Entry, pauses at the fixed comparison origin and then reveals actual future. It does not create new inferences. The separate rolling viewer advances saved origins from new real observations.

## Visuals

One large spatial scene shows real history/person, Entry/Exit, saved DD paths, HDR68/95 and optional GT. Completion-time CDFs share one time/probability axis and mark the actual observed Exit time. Individual squared errors are shown for each H, labeled individual Brier contributions.

Observation R includes synchronized noisy/corrected/FFBS spatial views and aligned fixed-coordinate overlays, actual historical samples (8 FFBS trajectories), stored H1–H4 probabilities with the same Exit line, probability shifts in pp, ADE, region area and per-position containment. The optional R-fit control adjusts the same camera across all render views; default common scale is retained and resettable. Large regions can extend beyond the fixed view. No output is fabricated for unsupported origins.

## Important implementation correction

An end-to-end test found that moving the presentation iframe between DOM parents could reload its scene. It now stays in one persistent DOM parent and only its display coordinates change. Actual iframe event/origin/horizon and GT state are checked across reveal steps, not just parent metadata.

XGBoost never generates spatial paths. Its small scene is the same actual recording for reference. R is an optional observation robustness experiment, not a third trained forecasting model. Original full-recording/rolling routes remain available.

Screenshots: review/screenshots/simulation_cdf.png; simulation_r.png; cdf_gt_individual.png; r_comparison.png.

## Preview and provenance

- Presentation: http://127.0.0.1:18779/presentation/presentation.html
- Methods: http://127.0.0.1:18779/presentation/methods.html
- Simulation / Compare: http://127.0.0.1:18779/presentation/compare.html
- Results: http://127.0.0.1:18779/presentation/results.html
- Existing rolling replay: http://127.0.0.1:18779/presentation/?case=o0008#/simulation

Canonical source: presentation/site/; deployment copy: docs/presentation/. The public website replays saved outputs, not new browser inference. No model fitting or inference was run. No saved forecasts, GT, checkpoints, restricted inD trajectories or previous final releases were changed. Historical Test reuse is exploratory, not untouched external validation.

Read and cross-checked: site/METHODOLOGY.md; site/exit_aware/EXIT_AWARE_FINAL_REPORT.md; site/r_robustness/FINAL_R_ROBUSTNESS_REPORT.md; site/pres/PRESENTATION_METRIC_AUDIT.md; current source and public JSON. The old Brier 0.00000 / 0.04626 discrepancy remains resolved as H1 versus H4, not conflicting values at one horizon.
