# Public Case Availability Audit

Status: PASSED — runtime index and independent read-only Python audit agree.

## Exact identity

The runtime index (`pres/availability.js`) identifies dataset, event ID, exact saved origin timestamp, forecast horizon, model variant, noise scenario and GT eligibility. It enumerates 3,220 availability rows across 35 saved origins. Source packets are joined by exact numeric timestamp, not rounded display time or case nickname. The underlying replay accessor's tolerance is additionally checked for exact equality before an entry enters the index. R future XY and per-horizon GT are checked against the clean forecast.

## Inventory

| Evidence | Available origins | Total saved origins |
|---|---:|---:|
| DD-MDN spatial forecast | 35 | 35 |
| XGBoost / Conditional AFT time probabilities | 6 | 35 |
| R experiment packet | 3 | 35 |
| Exact causal AFT feature packet | 6 | 35 |

| Horizon | DD completion probability saved | GT known | Guided fully matched |
| 1s | 6/35 | 6/35 | 3/35 |
| 2s | 6/35 | 5/35 | 3/35 |
| 3s | 6/35 | 6/35 | 3/35 |
| 4s | 35/35 | 25/35 | 3/35 |

These are prediction origins, not counts of independent patients/pedestrians. The three complete public examples happen to represent three different event IDs; that does not generalize to arbitrary origin inventories.

| UID | Event | Crosswalk | Relative origin | Remaining distance | Longitudinal speed | Acceleration | 3m neighbors |
|---|---|---|---:|---:|---:|---:|---:|
| o0000 | public-imptc-02 | f1 | 0s | 10.051756 m | 1.317859 m/s | 0.893584 m/s² | 0 |
| o0008 | public-imptc-01 | f2 | 8s | 3.419044 m | 1.566085 m/s | −0.011914 m/s² | 2 |
| o0011 | public-imptc-03 | f3 | 1s | 7.651423 m | 1.526429 m/s | 0.179182 m/s² | 0 |

## Missing-data causes discovered

1. **Prediction not saved:** 29 origins have no public AFT output. Spatial DD playback does not imply a saved AFT CDF.
2. **Noise experiment not run/exported at that origin:** 32 origins lack an R packet. A packet at another time of the same event must not substitute.
3. **Horizon summary not saved:** 29 legacy DD origins have a saved H4 completion estimate but no H1–H3 completion summary. Spatial points at those times do not authorize deriving new completion probabilities.
4. **Unknown GT:** H2 for `o0012` is unknown at the operational confirmation/interval boundary. It remains null. Ten H4 origins also lack a usable exported H4 GT. Their precise censoring subtype is not reconstructed from eventual event outcome.
5. **Different feature definitions:** legacy DD condition-state packets contain descriptive motion quantities, but 29 lack the exact AFT longitudinal feature packet. The case finder does not silently mix those speed/acceleration definitions. In Expert mode these origins remain selectable with all filters open; feature filters exclude unknown features.
6. **Unsupported dataset metric:** no public inD per-origin/Exit demonstration exists; only permitted aggregate evidence remains available in the old Results routes.
7. **Incomplete continuous curve:** Conditional AFT has four saved horizon probabilities; it is shown as points rather than an invented continuous curve.

No missing value becomes zero. Existing explicit boolean H4 GT is read as its equivalent 0/1 value; null stays null. No new GT was generated.

## Guided policy and display thresholds

Guided eligibility requires a saved DD H probability, Exit-aware M1 probability, causal AFT features, all basic Clean/IID 0.5/1/2 comparison packets, a known horizon GT and a pre-Exit origin. It yields `o0000`, `o0008`, `o0011` at every H1–H4.

- Distance: <2 m / 2≤d<4 m / ≥4 m. Guided mode has no <2 m case; it is disabled.
- Longitudinal speed: <1.2 / 1.2≤v<1.5 / ≥1.5 m/s. Fixed display categories, not optimized using Test outcomes.
- Acceleration: <−0.3 / [−0.3,+0.3] / >+0.3 m/s². The middle band explicitly abstains from a confident acceleration/deceleration claim. This is not a measured sensor noise floor or intention annotation.
- Neighbors: 0 / 1–2 / ≥3 within the saved 3 m radius.
- Crosswalk: f1/f2/f3.

These UI thresholds do not replace the existing research group's Train/Validation terciles or distance bins. Counts are recomputed conditional on the other selected filters. Impossible combinations hide stale predictions and offer working Reset Filters.

## Reproduce

```sh
python3 presentation/tools/audit_case_availability.py /Users/gwondohyeon/view2risk_ux_20261123
```

Outputs: `availability_audit.json`, `availability_by_origin_horizon.csv`; executed browser output: `availability_runtime.json` (including all 3,220 model/scenario rows). All are in `/Users/gwondohyeon/view2risk_ux_20261123/`. Source hashes are recorded in the audit JSON. The runtime index is constructed from existing public packets; no new per-origin static dataset was exported.

## Preservation and publication boundary

Canonical source: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/`.
Deployment mirror: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/docs/presentation/`.
The 202 static files are byte-identical across those directories. This is a local, uncommitted review revision on `presentation/synchronized-three-panel-20261123`; no push was performed. The current GitHub Pages release is unchanged.

188 previously protected files remain byte-identical, including `final/`, `docs/final/`, saved prediction/metric artifacts and the resolved historical metric audit. No model training, inference, hyperparameter selection, calibration, GT modification or new private-data export occurred. Individual replay still uses only existing allowlisted IMPTC excerpts. The website is a static replay, not a browser inference service.
