# Final Simulation Redesign Report

Status: PASSED — local implementation and browser verification. **Not pushed to GitHub.**

## Entry-first default update

The default is now o0000 / public-imptc-02 / f1, origin +0s, approximately 0.015622s after the saved operational Entry. All DD-MDN/AFT/R predictions are available at that same origin. Actual residual Exit time is 7.782994s, outside the four-second model window; H1–H4 outcomes are all 0. The original o0008 table below remains a valid separate near-Exit example, available with ?case=o0008 or the explicit f2 preset. Presets select different real recorded events, not a repositioned pedestrian. This update is local-only and not pushed.

## 1. What changed

The simulation now follows observation → spatial forecast versus recorded reality → time forecast → individual error → observation uncertainty → aggregate evidence.

- The first block states the current recorded pedestrian state and a concise actual-outcome summary.
- The main DD-MDN scene overlays native recorded future XY for the full next four seconds before Play. A separate option reveals only the played segment. GT is magenta, the actual Exit first-passage point is a larger magenta sphere, and the selected-horizon GT point is smaller. Observed input/origin is blue, representative predictions teal, alternatives translucent cyan, HDR68 green and HDR95 purple.
- The default camera frames the clean input, representative forecast and opposite Exit, using no future GT to set that focus. It is shared across methods/scenarios. Top-down, whole-crosswalk, focus reset and optional R-fit controls are available. Entry remains in the world geometry but can be outside the close-up view; whole-crosswalk view shows the full geometry. Original blue/green markings embedded in the map are identified as map annotations.
- The main timeline runs from the selected forecast origin through +4s. Earlier recorded history is optional. Play/Pause/Restart/seek share one recorded clock. The origin and input features stay fixed; optional horizon following selects the next available whole-second H and labels it separately from the continuous replay time. Moving prediction markers interpolate stored path points for display only; no new probability or inference is generated.
- XGBoost has a real input→method→output diagram. Default M1 uses distance, speed and acceleration. Neighbor count/location are clearly scene context unless M2 is selected. No SHAP or causal contribution is invented. Its spatial inset replays the same actual observations and GT; it contains no XGBoost forecast path.
- A single large shared CDF compares saved DD-MDN and selected time-model curves. A GT Exit line and selected H marker are distinct. An optional observed 0→1 step marks this individual's passage, not a probability distribution. Duplicate main CDFs are removed; detailed values remain expandable.
- The horizon-wise table gives actual outcome, model probabilities, exact individual squared errors and the smaller-error model. Tiny nonzero probabilities are not presented as exact zero or one. Near equality uses an explicit absolute error difference tolerance of 1e-12, solely for display.
- Single-case interpretation is calculated from those rows. The default example explicitly shows DD-MDN better at H2 and XGBoost better at H3/H4. The aggregate 236-origin/120-event comparison is a separate block and link.
- R first shows Clean/Noisy/Kalman/eight FFBS past histories, then the propagated spatial distribution. Aligned four-mode overlays, saved completion probabilities, pp shifts, ADE, HDR area and actual GT containment are linked to the same event/origin/H. Common camera scale does not change when noise scenario changes.

## 2. Verified data and ground truth

Default: public-imptc-01 / o0008 / f2 / prediction start +8s. Native actual Exit at recording +10.063445091s, residual +2.063445091s. The observed frame bracket is +2.040009022–+2.080018044s after origin. Exit position is interpolated at that stored time between the existing adjacent native recorded points; the UI does not replace the future with a straight line to Exit.

The main future GT polyline consists of existing actual_observations.xy whose timestamps fall in [origin, origin+4s], preserving gaps. Its coordinates were compared point-for-point in the browser. Selected-H GT coordinates come from the saved future_GT_xy sample, not predicted hypotheses. Actual Exit is operational semantic-boundary first passage with continued-observation confirmation, not independently annotated foot crossing.

| H | Actual y | DD-MDN | Exit-aware M1 | DD individual (p−y)² | M1 individual (p−y)² |
|---|---:|---:|---:|---:|---:|
| 1s | 0 | 0.00000% | 0.00000000% | 0 | 4.21663978052e-33 |
| 2s | 0 | 2.53125% | 17.02796674% | 0.00064072265625 | 0.0289951651301 |
| 3s | 1 | 66.25000% | 99.95645760% | 0.11390625 | 1.8959410261e-07 |
| 4s | 1 | 66.96875% | 99.99999999% | 0.109106347656 | 9.2201544049e-21 |

The H3 probabilities differ in confidence for one case, not model accuracies. A single-case squared error is not cohort Brier.

## 3. Actual saved sources

- data/inference.json: allowlisted catalog and semantic geometry.
- data/public/cases/public-imptc-01.json (and other two allowlisted cases): actual timestamps/XY, histories, saved DD forecasts and future GT.
- data/public/demo-evidence.json: causal features, expert event/origin mapping and operational GT bracket/confirmation.
- data/public/exit-aware.json: complete saved 0–4s DD-MDN and XGBoost CDF grids and horizon outcomes.
- data/public/ui-completion.json: existing Conditional AFT outputs where available.
- data/public/r-index.json and data/public/r/*.json: matched synthetic noise scenarios, corrected/FFBS histories and existing DD-MDN outputs.
- pres/evidence.json: actual matched cohort means and grouped reliability evidence; Results links preserve source traceability.
- r_robustness/r_robustness_summary.json: separate aggregate R evidence, with its own denominators.

R public artifacts only contain H1–H4 completion probabilities. These are plotted as points, without fabricated intermediate CDF values. The observation-error proxy remains the SPD Train camera–virtual-LiDAR annotation disagreement, not verified IMPTC detector noise. No older XGBoost R results are relabeled as Exit-aware XGBoost R results.

## 4. Browser verification

33 checks passed on the final local implementation. No uncaught JavaScript exceptions or HTTP failures.

Verified: default exact matched case; future GT visible at t=0; native GT coordinate identity; Exit time/position interpolation; recorded camera alignment; M1 excludes neighbors; M2 declares them; complete saved CDF values; H-specific winning errors; aggregate means; optional actual GT step; synchronized person/forecast/H/CDF clocks; pause/reset/seek; full versus progressive GT; top-down view; same camera and GT across Clean/IID0.5/IID1/IID2; eight FFBS histories before region display; all four R overlays; containment indexing; normal and Presentation GT hide/reveal; recorded-case change; existing seven-scene Presentation origin and GT; 390px mobile no page-level overflow.

Desktop tested at 1440×1000; existing Presentation checked at 1440×900. Static source/deployment verification passes: 210 identical files. Scientific checks found no protected-artifact modifications, exact event/origin/GT linkage and causal input timestamp preservation.

## 5. Modified files

Canonical root: /Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/
- compare.html
- pres/compare.js
- pres/extension.js
- pres/triptych.js
- pres/research-ui.js
- pres/simulation.js (new UI composition and saved-data interpretation)
- pres/simulation.css (new layout)

Corresponding files under docs/presentation/ are synchronized using verify_static.py --sync. Added presentation/tools/simulation_redesign_browser_check.mjs and ignored its generated local evidence directory. Existing releases and experimental outputs remain unchanged. No commit or push was made for this task.

## 6. Screenshots and artifacts

Evidence directory: /Users/gwondohyeon/view2risk_simulation_redesign_20261123/
- screenshots/spatial_gt_detail.png — full focused GT-versus-DD spatial comparison
- screenshots/dd_prediction_actual_gt.png — playback/legend and main scene
- screenshots/xgb_input_output.png — actual model inputs and output
- screenshots/cdf_gt.png — same-origin model CDF and actual Exit
- screenshots/horizon_table.png — H1–H4 predictions/individual errors
- screenshots/r_uncertainty.png — uncertainty comparison
- screenshots/complete_layout.png — full page (capture limit 18000px)
- screenshots/mobile_spatial.png
- screenshots/mobile_comparison.png
- browser_check.json
- scientific_check.json
- source_hashes.json
- changed_files.txt
- browser_check.mjs

## 7. Reproduction and local URLs

Executed:
node /private/tmp/v2r_simulation_redesign_check.mjs
python3 presentation/tools/verify_static.py --sync
python3 presentation/tools/verify_redesign.py /Users/gwondohyeon/view2risk_simulation_redesign_20261123/scientific_check.json

Portable entry:
V2R_CHECK_OUTPUT=presentation/simulation-evidence node presentation/tools/simulation_redesign_browser_check.mjs

Preview: http://127.0.0.1:18779/presentation/compare.html
Direct spatial view: http://127.0.0.1:18779/presentation/compare.html#dd-panel
Direct CDF/error view: http://127.0.0.1:18779/presentation/compare.html#comparison-panel
R: http://127.0.0.1:18779/presentation/compare.html#r-panel
Existing Presentation: http://127.0.0.1:18779/presentation/presentation.html

## 8. Limitations

This is a static replay, with three public matched R origins; it does not support counterfactual speed changes or live inference. Missing predictions are unavailable, not incorrect. Missing/censored outcomes remain unknown. Large R contours can leave the default fixed-scale viewport; optional common R-fit zoom makes this inspectable. The close-up may omit Entry from the visible viewport, while retaining its true world geometry and whole-crosswalk control. CDF numeric queries use saved values only; continuous cursor interpolation is visual and does not create forecasts. Representative hypothesis scores remain distinct from normalized probabilities. Coverage/HDR are positional, not collision-risk measures. H1–H4 is not a validated 15–20s rollout. No training, relabeling, registration, raw inD publication or GitHub push occurred.
