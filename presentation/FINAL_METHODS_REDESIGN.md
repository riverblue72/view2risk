# Final Methods Redesign

Status: PASSED — local browser review; publication pending authorization.

## Information architecture

The primary header has four destinations: Presentation, Methods, Compare Models, Results. Methods is the definitive reference. How It Works and Modeling Guide remain compatibility pages with links to the definitive explanation; they no longer compete in the primary navigation.

## Six chapters

| Chapter | Concrete question and explanation | Actual source |
|---|---|---|
| Data and crossing GT | How was Exit constructed? Semantic label 5, f1/f2/f3, 20 transverse bins, median-3 smoothing, saved A/B boundaries and direction-dependent Entry/Exit. First passage is operationally confirmed by 0.12 s continuous opposite-side observation. | `demo/method_sources.json`, `pres/evidence.json`, `data/inference.json` |
| Causal pedestrian state | Which past coordinates determine velocity? Show saved coordinate evidence, 0.6 s longitudinal velocity, 0.4 s velocity-difference acceleration, 3 m neighbor count and piecewise Exit distance. PedPy descriptive statistics are separate. | `data/public/demo-evidence.json` |
| DD-MDN | How do sampled paths become a completion probability? 10 observations across 0.9 s, 8 future points through 4 s; normalized GMM, joint sampling, HDR and first passage. | `data/inference.json`, referenced `data/public/` case files |
| XGBoost Survival AFT | What was learned? Residual Exit time with interval/right-censored labels; M0 distance/speed, M1 acceleration, M2 neighbors/location; original versus Exit-aware sampling and Calibration. | `exit_aware/exit_aware_summary.json`, `data/public/exit-aware.json` |
| Observation R | How does positional error change the forecast? SPD Train bias/covariance, synthetic perturbation, Kalman Filter, FFBS and Monte Carlo. | `demo/method_sources.json`, `r_robustness/r_robustness_summary.json` |
| Evaluation and findings | What do error, probability quality and region area measure? ADE/FDE, Brier, Reliability, Coverage and HDR area are distinguished with saved examples and limitations. | `pres/evidence.json`, `pres/PRESENTATION_METRIC_AUDIT.md` |

Each chapter starts with a specific question and answer. One central equation is initially visible; detailed formulas and variable explanations are expandable. Actual coordinates and output values are loaded from saved JSON, rather than typed illustrative measurements.

## Architecture semantics

The responsive HTML diagram centers on common observations, two parallel predictors and evaluation. Geometry and causal features remain documented in the six chapters. DD-MDN is pretrained; XGBoost is separately project-trained. The XGBoost card explicitly identifies future-derived training labels; the diagram note restricts future GT to supervised labels/evaluation, not causal predictor inputs. There is no DD-MDN-output-to-XGBoost connection. R and PedPy are compact supporting explanations below the main flow: R tests existing predictors under modified histories; PedPy performs descriptive analysis. Neither is displayed as a third learned predictor.

The architecture and Methods page are rendered from shared components, avoiding divergent scientific explanations. Model names and metrics remain English; the main explanation is Korean.

## Verified example

The default f2 case uses public event `public-imptc-01`, relative origin +8 s. Its saved longitudinal speed is 1.5660854388 m/s, acceleration −0.0119138737 m/s², remaining distance 3.4190439247 m and 3 m neighbor count 2. At H3, DD-MDN probability 0.6625 equals 2,120/3,200 joint sampled first passages. Displayed discrete representative paths are not falsely labeled as all 3,200 Monte Carlo paths or as normalized-probability hypotheses.

## Browser evidence

All six chapters rendered their main and expanded mathematics without KaTeX errors. Desktop and mobile layouts had no page-level horizontal overflow. Screenshots: `model_architecture.png`, `methods_overview.png`, `methods_coordinates.png`, `methods_mobile.png`.

## Release boundary

This is a local review revision dated 2026-11-23. No commit or push was performed. The public GitHub Pages release is unchanged. Canonical files are in `presentation/site/`; the deployment mirror is `docs/presentation/`. Existing `final/`, `docs/final/`, saved experimental results and model artifacts were not edited. No fitting, inference, calibration or GPU work was run.

The static website replays already saved inference outputs. It does not run DD-MDN or XGBoost in the browser. Only existing allowlisted IMPTC excerpts are used for individual demonstrations; no new individual inD records or private inference packets were exported.
