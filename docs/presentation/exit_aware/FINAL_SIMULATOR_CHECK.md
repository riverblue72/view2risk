# Final Simulator Check — Exit-aware v1

Status: PASSED implementation; LIMITATION scientific generalization/calibration

## PASSED

- CPU-only fixed-config M0/M1/M2 retraining; no GPU, new neural predictor, unrestricted search, or GitHub push.
- Same semantic Exit geometry, 0.12 s confirmation and original date splits. Future GT used only for residual labels/outcomes; causal-feature future-mutation check passed. Event weights, maximum 8 origins/event and split separation verified.
- Training code SHA256 remains frozen: `54dfebd20c31ff3efaf4eb2f263eb51eb73879ade9d8a70b0f9aa30f48ba94d9`. Model and selected-manifest hashes passed; selection precedes Test evaluation.
- 13 numerical checks passed, including exact 236-origin ID matching, unchanged original predictions/GT, probability bounds and unknown-label handling.
- 39 browser assertions passed; zero uncaught runtime exceptions. Saved evidence: `reports/browser_check.json`, `plots/simulator_final_screenshot.png`, `reports/comparison_desktop.png`, `reports/simulator_mobile.png`.
- Desktop 1440×1800 and 1440×1050, mobile 390×844 tested. Mobile document has no horizontal overflow; wide tables have local scrolling. Screenshots visually inspected.
- Default DD-MDN Q-only and optional comparison OFF preserved. Original XGBoost remains available; optional new candidate is Validation-selected M1, not Test-best M2.
- Real-case explorer checks stored event and exact origin. Concurrent case changes are locked until the saved R packet is loaded; this avoids overlapping async selection callbacks. Saved forecast timestamps and selected cases match.
- Clean, IID 0.5×/1×/2×, correlated and last-0.4 s dropout controls use existing computed packets. No synthetic predictions interpolated between scenarios. Filtered mean and FFBS R+Q remain distinct.
- H1/H2/H3/H4 complete and remain probabilities are complementary; table shows actual GT or Unknown, Brier, pointwise positional inclusion and HDR area. Single-case inclusion is not population Coverage.
- Rolling timeline explains 10 observations at 0.1 s (0.9 s elapsed), 8 predictions at 0.5 s through 4 s, and actual-history refresh. No 15–20 s validation claim.
- Condition Analysis, R Analysis, Results, original AFT, Modeling Guide and report routes retained. Five numerical figures load. inD Exit remains blocked; no inD raw data or screenshots added to shareable figures.
- Private raw audit URL and arbitrary private API suffix return 404. New endpoint is within existing local-access guard. No licensed data published.
- Source preservation: 2186 previously hashed files checked, 2184 unchanged; only intended index/server integration edits below. No missing source files. Original XGBoost models/results and GT hashes preserved.

## Exact integration changes and routes

Modified existing files (backed up under `[private-source]`):
- `[private-source]` — additive CSS/JS references.
- `[private-source]` — local `data/public/exit-aware.json` endpoint.

New assets:
- `[private-source]`
- `[private-source]`
- `[private-source]` — aggregate JSON/CSV, report, figures and this check.
- `[private-source]` — private saved per-origin model CDFs; not public static data.

Working URL: http://127.0.0.1:18773/#exit-final

Existing routes: `/`, `./modeling.html`, `./#condition-analysis`, `./#r-analysis`, `./#clearance-aft`.
New aggregate route: `./exit_aware/exit_aware_summary.json`; new private local API: `data/public/exit-aware.json`.

Recorded explorer counts (origins; repeated origins are not independent events): `{"slow": 75, "fast": 157, "decelerating": 6, "stopped": 0, "restart": 1, "large_error": 5, "noise_sensitive": 5, "near_exit": 36}`.

## LIMITATION

- Historical Test reuse: 236 matched origins, 120 events, 116 tracks, 55 recordings, 3 dates. No new independent benchmark. Separate larger landmark/exit-aware cohorts are not pooled with this cohort.
- Repeated origins are event-weighted; intervals cluster by recording (400 resamples), conditional on fitted models/censor reference. Censoring independence/transport is an assumption.
- Near-Exit support repair improves original XGBoost but neither DD-MDN nor constant speed is conclusively beaten. Existing conditional linear AFT is stronger on this cohort. Acceleration/context gains are not supported; M2 combines crowding and location and cannot isolate crowding.
- Calibration improves mean Brier/ECE, but calibrated U95 conditional coverage is 90.8163% on 97 evaluable origins (103 within 4 s, 6 unknown); this is not proof of 95% population coverage. Raw/calibrated supported subsets differ.
- Stopping has no eligible stored example and is disabled; restart/deceleration examples are illustrative sparse groups. Large-error and high-noise-sensitivity selections are explicitly retrospective.
- SPD noise is an annotation-disagreement proxy, not verified IMPTC detector noise. Existing R experiments are unchanged; their 237-origin aggregation differs from 236 matched AFT origins.
- Displayed probabilities remain simulation/model estimates, not independently population-calibrated. Rounding may cause displayed complements to differ slightly from 100%; unrounded sums equal 1.

## BLOCKED / not claimed

- Independent new Test/generalization evidence: unavailable within this bounded task.
- inD semantic Exit probability: GT not validated.
- Long-horizon 15–20 s validation and population U95 calibration: unsupported.
- Optional weather panel: not implemented; no observed weather labels, no invented attributes.

## Reproduction and completion boundary

See `EXIT_AWARE_FINAL_REPORT.md`, `configs/protocol.json`, `configs/decision_policy.json`, `models/frozen.json`, `reports/preservation_after.json`, `reports/artifact_hashes.json` and `DELIVERABLE_INDEX.md`.
Executed CPU audit → fixed retraining → Calibration → matched evaluation → numerical checks → local-browser checks. Browser command on the tunnel host: `node [local-path]`.
No further modeling/search is running or scheduled. Retain DD-MDN default; keep exit-aware M1 as an optional measured comparison. Ready for presentation with these limitations.
