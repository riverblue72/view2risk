# Final Scientific Consistency Check

Status: PASSED with explicit scientific limitations.

## Executed checks

- Exact event/origin joins: 35 saved DD origins, 6 AFT matches, 3 R matches, 48 R results.
- All matched R future XY arrays equal the clean future GT; per-horizon labels agree.
- DD completion probabilities agree with the saved CDF representation.
- Saved CDFs are monotonic and remain in [0,1].
- Saved input source timestamps are at or before prediction origin.
- 188 protected files have identical SHA-256 before/after, including prior releases, saved evidence and the completed metric audit.
- No GT, eligibility, calibration, model, checkpoint, or prediction artifact was changed.
- Public case gating is IMPTC-only; static checks reject private API/model exports. No new raw data were added.

## Preserved metric audit

The original-landmark cohort has 936 origins / 354 events. The previously confusing constant-speed values describe different horizons: H1 has 922 known outcomes and Brier 0.00000; H4 has 888 known outcomes and Brier about 0.0462578. The original `pres/PRESENTATION_METRIC_AUDIT.md` remains unchanged. Neither value was silently overwritten or pooled across horizons.

The DD-MDN official full-Test 120,871-window evaluation remains separate from the 236-origin/120-event completion comparison and the 237-origin/120-event R analysis. Historically reused Test is not presented as a fresh external validation set.

## Preserved conclusions

The saved matched mean H1–H4 Brier values are approximately DD-MDN 0.016172, constant speed 0.015619, Conditional AFT 0.011823, and Exit-aware M1 calibrated 0.016345. Exit-aware M1 H1 improves relative to original M1 (0.108270 to 0.006183), not conclusively relative to every baseline. No new significance or superiority claim is made. Independent acceleration/crowding gains are not established.

## R fit and assumptions

SPD Train fit uses 2,465 pairs, bias [−0.0069668423, −0.0221235760] m, covariance [[0.0245972043, −0.0039023702], [−0.0039023702, 0.0315137272]] m². These are not the full SPD statistics (10,109 pairs). Synthetic transfer is not independently validated IMPTC detector error. Kalman process noise is distinct from behavioral Q; annotation noise may already be represented in the trained predictor. FFBS histories preserve temporal dependence, but no physically identifiable R/Q decomposition is claimed.

## LIMITATION

- Only three public excerpt events; 6 AFT origins and 3 R origins. Missing matches remain unavailable.
- All 3,200 joint path coordinates are not exported; only stored summaries and representative spatial paths are replayed.
- Conditional AFT has four saved horizon probabilities rather than a complete public continuous curve.
- Independent completion calibration, fresh-date generalization and inD semantic Exit GT are not established.
- Sparse stopping/restarting and high-crowding support does not establish subgroup reliability.
- Coverage is positional inclusion, not completion calibration or safety certification.
- Displayed individual squared error is not an aggregate Brier Score.
- No validated 15–20 s DD-MDN forecast, collision-risk estimate or deployment claim.

## BLOCKED / not in scope

Publication is intentionally pending user authorization. Unsupported origins cannot be filled without new saved evidence; no inference was run to fill gaps.

## Release boundary

This is a local review revision dated 2026-11-23. No commit or push was performed. The public GitHub Pages release is unchanged. Canonical files are in `presentation/site/`; the deployment mirror is `docs/presentation/`. Existing `final/`, `docs/final/`, saved experimental results and model artifacts were not edited. No fitting, inference, calibration or GPU work was run.

The static website replays already saved inference outputs. It does not run DD-MDN or XGBoost in the browser. Only existing allowlisted IMPTC excerpts are used for individual demonstrations; no new individual inD records or private inference packets were exported.
