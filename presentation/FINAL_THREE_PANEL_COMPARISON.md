# Final Three-Panel Comparison

Status: PASSED with saved-artifact availability limitations.

## Shared state and layout

`compare.html` contains a sticky case/crosswalk/origin/H control bar, DD-MDN spatial panel, XGBoost CDF panel, R sensitivity panel, and separate matched-origin and matched-noise tables. Floating section links provide direct panel navigation. Guided mode is default; Expert mode exposes detailed provenance.

A single exact `(event_id, origin_s)` key feeds all panels. Horizon is shared across H1–H4. Case loading locks controls until the new state is ready; an asynchronous result cannot silently select another origin. R joins additionally require identical future XY GT; horizon GT and saved DD probabilities are checked for agreement. A failed join is an error, never a nearest-origin substitution.

Play/Pause in this page advances the selected forecast horizon while preserving the prediction origin. It is explicitly distinct from normal recording playback. Reset restores H3 and hides future GT for the same case. The original Simulation recording playback remains operational.

One Babylon renderer is reused through a controlled bridge. Panel 2 uses SVG CDF/reference geometry; Panel 3 uses saved-coordinate SVG trajectories/HDR and a past-history enlargement. There are not three simultaneous WebGL renderers. An observed desktop reading was 59.70 FPS with one renderer; this is not a cross-device performance guarantee.

## Available saved evidence

| Availability | Count |
|---|---:|
| Public allowlisted IMPTC events | 3 |
| Saved DD-MDN rolling origins | 35 |
| Exact AFT/Conditional AFT matching origins | 6 |
| Exact R matching origins | 3 |
| R scenario/method results | 48 (16 for each of 3 origins) |

Default: f2 / `public-imptc-01` / +8 s / H3. Other matched R examples are f1 +0 s and f3 +1 s. Origins without AFT or R show `NOT EVALUATED FOR THIS ORIGIN`. Unknown GT stays `UNKNOWN`; its error is not zero. Already-completed origins are labeled as post-Exit replay rather than valid pre-Exit residual-time evaluation.

## Three different outputs

1. DD-MDN: saved future spatial hypotheses and selected-H HDR68/HDR95, plus completion probability from joint first passage. HDR is neither a safety radius nor itself a completion probability.
2. XGBoost: saved remaining-time CDF, never a fabricated XY trajectory. Exit-aware M1, original M1, constant speed and Conditional AFT are alternatives, not averaged into a hybrid. Conditional AFT has four saved horizon values, shown as points without inventing a continuous curve. Neighbor count is identified as an M2 feature.
3. R: same origin under Clean, IID 0.5/1/2, correlated or last-0.4-s dropout, with Noisy, Filtered mean or FFBS R+Q where stored. Reconstructed missing history is not presented as recovered real observations. Original-XGBoost R evidence is not relabeled as Exit-aware-XGBoost evidence.

## Actual default-origin example (H3)

GT completion is 1. This is one origin, not an aggregate performance estimate.

| Method | Saved probability | Single-origin squared error |
|---|---:|---:|
| DD-MDN | 0.6625 | 0.11390625 |
| Exit-aware M1 calibrated | 0.9995645759508139 | calculated from `(p−1)^2` in UI |
| Original M1 calibrated | 0.9999999973568025 | calculated from `(p−1)^2` in UI |
| Constant speed | 1 | 0 |
| Conditional AFT calibrated | 0.9998202329574384 | calculated from `(p−1)^2` in UI |

For IID 1× at this same origin/H3, probabilities are Clean 0.6625, Noisy 0.744375, Filtered mean 0.8575 and FFBS R+Q 0.4384375. The interface calculates signed percentage-point changes and individual squared errors. These values demonstrate that R-aware output need not improve a particular prediction.

## Matched versus aggregate statistics

Individual ADE is labeled over the full 4 s; selected-H spatial area is distinct. Aggregate R ADE is through H, and endpoint Coverage/area correspond to H. The R aggregate cohort is 237 origins / 120 events. The separate XGBoost matched cohort is 236 origins / 120 events. They are not pooled. Coverage and area appear together. GT stays hidden until requested in individual-case views.

## Source map

| Visualization | Saved source |
|---|---|
| DD trajectories, input, HDR and GT | `data/inference.json` and its referenced case JSON |
| AFT CDF and baseline values | `data/public/exit-aware.json`, `data/public/ui-completion.json` |
| Features and observation support | `data/public/demo-evidence.json` |
| R histories, paths, HDR and probabilities | `data/public/r-index.json` and its referenced `data/public/r/` JSON |
| R cohort comparison | `r_robustness/r_robustness_summary.json` |
| Main experimental findings | `pres/evidence.json`, `exit_aware/exit_aware_summary.json` |

No new predictions were computed. Stored sample-count/probability summaries are available, but the public export does not include every one of the 3,200 sampled XY paths. The website does not reconstruct them.

## Release boundary

This is a local review revision dated 2026-11-23. No commit or push was performed. The public GitHub Pages release is unchanged. Canonical files are in `presentation/site/`; the deployment mirror is `docs/presentation/`. Existing `final/`, `docs/final/`, saved experimental results and model artifacts were not edited. No fitting, inference, calibration or GPU work was run.

The static website replays already saved inference outputs. It does not run DD-MDN or XGBoost in the browser. Only existing allowlisted IMPTC excerpts are used for individual demonstrations; no new individual inD records or private inference packets were exported.
