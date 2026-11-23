# XGBoost AFT Integration Check

Status: COMPLETE_WITH_LIMITATIONS

## PASSED

- Official xgboost.train survival:aft, normal AFT, DMatrix survival bounds;8 executed numerical/API tests.

- 21 numerical/data/provenance checks: date/event/track isolation, causal feature timestamp and future-mutation invariance, saved-model reload, native margin→time transform, monotone CDF, aligned GT and matched origins.

- Three variants ×4 predefined configurations; selected M1 by Validation. Separate Calibration. Frozen hashes/timestamp saved before Test. No neural retraining or GPU job.

- Existing linear AFT artifacts reproduce their saved p5/p10 to1e-10 on retained landmarks. Original models and calibration parameters unchanged.

- 23 actual Chrome checks; no runtime errors. Desktop/mobile screenshots: reports/aft_desktop.png and reports/aft_mobile.png.

- Optional Clearance-Time UQ panel uses private precomputed236IMPTC-origin predictions; same event/origin as actual3D. Four measured plots and aggregate table loaded. Unknown GT preserved, inD Exit blocked. Main3D Q-only default and prior R/condition/modeling routes preserved.

- Preservation: 790 existing source/result/config/GT files checked. Only website/index.html and scripts/serve.py changed, with exact before backups. No unexpected source changes.

- No GitHub push, no licensed inD data in new payload. Per-origin CSV not in static website; private API remains localhost-bound.

## LIMITATION

- Historically reused Test;3 dates, no new external validation. Calibration2dates; Validation has no censored events. Recording bootstrap conditional on fixed fitted models; not full training uncertainty.

- Landmark Train distance minimum2.19190m;39/236matchedorigins are closer. All26H1completeorigins fall belowTrain minimum. Strong near-Exit underprediction; retained in all results, no favorable population filtering.

- Acceleration and joint context gains not established by paired Test CIs. M2 adds crowding and location together; permutation diagnostic is not causal or retrained crowding ablation.

- Calibration worsened selected model matched Test Brier. No automatic replacement/default change or Validated badge.

- IPCW depends on independent, transferable censoring. Interval brackets and unknown outcomes remain explicit. NLL is interval mass/survival, not old density NLL. CRPS is truncated0–4s. U95 only within4s/known support, not population guarantee.

- Optional R reuses unchanged SPD/FilterPy/FFBS. Acceleration1s window has0.1s clean prefix before existing0.9s perturbation history; not full-window physical detector noise. Some noisy features outside spatial/training support. Noisy-to-filter Brier recovery CIs may includezero.

- GT operational coordinate/semantic-boundary rules are not independently annotated anatomy/intent. Unresolved/returned events excluded with counts; target population conditional on resolvable non-return events.

## BLOCKED / NOT_APPLICABLE

- Independent population-calibration or fresh-date generalization claim: BLOCKED by current data/protocol; no new data requested.

- inD clearance event: BLOCKED, semantic Exit not validated. No inD per-origin export was added.

- Continuous event-density NLL for CV or finite empirical DD-MDN first-passage samples: NOT_APPLICABLE; reportedNA, no invented density.

- Clearance beyond4s validation: NOT_EVALUATED; no extrapolated validated completion claim.

## Changed files and routes

- Modified with backup: website/index.html, scripts/serve.py.

- Added: website/aft_panel.js, website/xgb_aft/{aggregate JSON,CSV,reports,4plots}.

- Read-only private endpoint: data/public/aft-clearance.json.

- Viewer: http://127.0.0.1:18773/#clearance-aft

- Reports: FINAL report and this checklist at project root and xgb_aft_20261121/.

## Resolved implementation issues

- Isolated environment initially lacked seaborn. Original environment reused with separate XGBoost package path; no original packages changed.

- Empty U95 bootstrap denominator now returnsNA. Frozen training source snapshot retained; no model or hyperparameter adjustment.

- R aggregation pandas mode-column collision corrected; frozen posterior/model and numeric rules unchanged. Original failure logs retained.

## Final decision

Bounded experiment and simulator integration complete. Keep DD-MDN default. XGBoost M1 remains optional exploratory comparison; no follow-on search or model expansion.
