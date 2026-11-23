# Outcome-First Comparison Page

Status: PASSED.

## Default example, verified from saved files

IMPTC f2, `o0008`, `public-imptc-01`, relative origin +8 s, H3:

| Quantity | Saved value |
|---|---:|
| DD-MDN completion probability | 0.6625 |
| Exit-aware M1 calibrated probability | 0.9995645759508139 |
| IID 1× FFBS R+Q probability | 0.4384375 |
| Observed residual first Exit time | 2.063445091247559 s |
| Actual completion within H3 | 1 |

The interface displays 66.3%, 99.96%, 43.8% and approximately 2.06 s. A nonzero probability below 0.01% is displayed as `<0.01%`; a probability just below one is never rounded to 100%. True zero/one are 0%/100%. Exact stored values remain available on hover and in data attributes. Percentage-point changes are labeled separately.

## Interaction

1. Natural-language filters select saved origins. They do not alter motion.
2. Top outcome bars display DD-MDN, selected AFT/baseline and FFBS R+Q under the selected noise scenario.
3. Ordinary exploration reveals the actual outcome. Presentation mode can hide/reveal it without changing the event, origin or input history.
4. The horizon selector updates probability, CDF marker, GT outcome, HDR index and R metrics consistently. Horizon playback cycles H1–H4 at a fixed origin, not synthetic future observations.
5. Expert mode exposes all 35 origins, precise provenance, advanced correlated/dropout noise and missing-data reasons.

## Three explanatory panels

- **Where will the pedestrian move?** Existing single Babylon renderer, actual past, saved spatial hypotheses, Entry/Exit and selected-H HDR. Mathematical first passage is expandable. No explicit acceleration/neighbor retraining is attributed to DD-MDN.
- **How long until completion?** One shared 0–4 s, 0–100% CDF scale. The selected H and observed Exit time (if in chart range and revealed) are marked. Same-origin features are visible. There is no fabricated AFT spatial path.
- **What if observation is inaccurate?** A single top-down coordinate frame across all saved R scenarios, modes and horizons for the selected origin. Bounds use saved predictions and geometry, not GT or the selected answer. Clean/Noisy/Filtered/FFBS visibility toggles change rendering only. Region size differences remain visible on the same metric scale. Very broad noisy regions can make the actual crossing appear small; this is a real scale tradeoff, not corrected by independently zooming methods.

## Optional feature analysis

The saved Exit-aware calibrated variants at default H3 are:

| Variant | Inputs | Saved probability |
|---|---|---:|
| M0 | distance + longitudinal speed | 0.9990740495932974 |
| M1 | M0 + acceleration | 0.9995645759508139 |
| M2 | M1 + neighbors + location | 0.9996045738502951 |

Clicking a variant selects its actual saved CDF. They are independently trained models; M2 changes neighbors and location jointly. No causal effect or independently established incremental benefit is claimed. Single-origin squared error remains distinct from aggregate Brier.

## Source map

| Display | Existing source |
|---|---|
| DD scene, geometry, horizon HDR, future GT | `data/inference.json` → referenced `data/public/cases/*.json` |
| AFT variants and baseline CDF | `data/public/exit-aware.json` |
| Conditional AFT H1–H4 | `data/public/ui-completion.json` |
| Causal features and observed Exit interval | `data/public/demo-evidence.json` |
| Synthetic R predictions | `data/public/r-index.json` → existing `data/public/r/*.json` |
| Aggregate R coverage, area and Brier | `r_robustness/r_robustness_summary.json` |

The original XGBoost R experiment is never relabeled as Exit-aware XGBoost R. The R panel is the existing DD-MDN robustness experiment. It is an annotation-disagreement proxy, not verified IMPTC physical detector noise.

## Preservation and publication boundary

Canonical source: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/`.
Deployment mirror: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/docs/presentation/`.
The 202 static files are byte-identical across those directories. This is a local, uncommitted review revision on `presentation/synchronized-three-panel-20261123`; no push was performed. The current GitHub Pages release is unchanged.

188 previously protected files remain byte-identical, including `final/`, `docs/final/`, saved prediction/metric artifacts and the resolved historical metric audit. No model training, inference, hyperparameter selection, calibration, GT modification or new private-data export occurred. Individual replay still uses only existing allowlisted IMPTC excerpts. The website is a static replay, not a browser inference service.
