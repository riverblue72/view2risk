# Completion-Time Interpretation Fix

Status: PASSED (2026-11-23)

The prior presentation emphasized three copies of the observed scene and a default H3 probability query, obscuring the difference between forecast time and the queried horizon.

- The primary question is now remaining crossing-completion time at the fixed prediction origin.
- The selected time model's median is read as a bracket from its stored CDF grid. This is neither a new fitted estimate nor an interval claimed to cover 50% of completion times.
- For default o0008, Exit-aware XGBoost M1's median is in (2.15, 2.20] seconds; its H3 probability is 0.9995645759508139; the observed Exit time is 2.063445091247559 seconds after origin.
- H3 is clearly labeled as a user-selected probability query, not the predicted completion time.
- XGBoost's main visualization is the time-distribution chart. Its actual-recording scene is secondary and explicitly not a generated spatial prediction.
- Before the prediction origin, the UI explains why three real-recorded scenes are identical and offers a direct jump to the prediction comparison.
- The CDF replay cursor shows an actual stored grid point. No uncomputed probabilities are interpolated.
- Quantiles not reached within the stored window are marked as not reached; missing curves remain unavailable. No time forecast beyond the saved support is fabricated.

12 browser checks passed: median/source equality, horizon/time distinction, pre-origin explanation, exact-origin jump, chart priority, unsupported quantiles, missing curves, unchanged median under H changes, saved CDF playback reading, mobile layout, no JS errors and no HTTP errors. Scientific artifact verification found no modifications.

Files: presentation/site/compare.html, pres/compare.js, pres/triptych.js, pres/ux.css and matching docs/presentation copies.
URL: http://127.0.0.1:18779/presentation/compare.html#dd-panel
Evidence: /Users/gwondohyeon/view2risk_time_clarity_20261123/browser_check.json
Screenshots: /Users/gwondohyeon/view2risk_time_clarity_20261123/screenshots/
Command: node /private/tmp/v2r_time_clarity_check.mjs
No training, inference, source-result modification or GitHub push.
