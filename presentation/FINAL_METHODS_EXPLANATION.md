# Final Methods Explanation

Status: IMPLEMENTED AND BROWSER VERIFIED

Methods is a continuous six-section technical reference. The top architecture diagram distinguishes two parallel predictors, the training-label path, optional R experiment and separate PedPy descriptive analysis. Every section provides Dataset → Input → Method/Equation → Output → Evaluation. One central equation is visible; original details, extra equations and citations remain in expandable Expert sections.

| Component | Actual role | Inputs and output | Evaluation |
|---|---|---|---|
| Entry/Exit and GT | Mathematically computed | IMPTC semantic label5; f1/f2/f3; 20 transverse bins, median-3, piecewise A/B; direction-dependent Exit first passage | Separate first-passage frame interval and ≥0.12s confirmation; unresolved/censored not failures |
| Causal state | Mathematically computed | Past 0.6s axial displacement; 0.4s velocity difference; piecewise Exit distance; neighbors ≤3m | Unit checks, past support timestamps only |
| DD-MDN | Official pretrained, unchanged | 10 history positions/0.9s plus supported scene context → 8 position distributions and joint samples → Exit crossing fractions | Position errors, NLL, HDR coverage+area, completion scores |
| XGBoost AFT | Project-trained models, frozen here | M0 d+v; M1 +a; M2 +neighbors/location; residual-time interval/right-censored labels → CDF | Validation selection, separate calibration; proper completion scores |
| Observation R | Externally estimated proxy | SPD Train annotation disagreement → synthetic perturbations → Kalman/FFBS → same DD-MDN | Compare accuracy, completion probability, coverage and sharpness |
| PedPy | Separate descriptive library | Actual trajectories → speed/density/flow/motion summaries | Descriptive region definitions, not new DD-MDN training features |

Normalized Gaussian mixture weights are used for probability calculations; 20 hypothesis confidence scores are not normalized path probabilities. Joint histories and futures retain temporal dependence. HDR is positional uncertainty, not safety radius. Rolling forecasts use new actual history and do not validate 15–20s from the original origin.

All equations include variable meanings and units. The original expert material documents AFT censoring, parameter/calibration assumptions, R double-counting and transfer risks, causal state definitions, GT confirmation and cohort dependence. The architecture makes no claim of new mathematical theory or a new foundation model.

Official source links are retained in the Methods footer: DD-MDN and paper; XGBoost; PedPy; FilterPy; inD tools; V2X-Seq. Main architecture screenshot: review/screenshots/methods_architecture.png.

## Preview and provenance

- Presentation: http://127.0.0.1:18779/presentation/presentation.html
- Methods: http://127.0.0.1:18779/presentation/methods.html
- Simulation / Compare: http://127.0.0.1:18779/presentation/compare.html
- Results: http://127.0.0.1:18779/presentation/results.html
- Existing rolling replay: http://127.0.0.1:18779/presentation/?case=o0008#/simulation

Canonical source: presentation/site/; deployment copy: docs/presentation/. The public website replays saved outputs, not new browser inference. No model fitting or inference was run. No saved forecasts, GT, checkpoints, restricted inD trajectories or previous final releases were changed. Historical Test reuse is exploratory, not untouched external validation.

Read and cross-checked: site/METHODOLOGY.md; site/exit_aware/EXIT_AWARE_FINAL_REPORT.md; site/r_robustness/FINAL_R_ROBUSTNESS_REPORT.md; site/pres/PRESENTATION_METRIC_AUDIT.md; current source and public JSON. The old Brier 0.00000 / 0.04626 discrepancy remains resolved as H1 versus H4, not conflicting values at one horizon.
