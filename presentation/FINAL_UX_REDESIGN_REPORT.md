# FINAL UX REDESIGN REPORT

Status: PASSED — local website integration / 2026-11-23

## Main improvements

Presentation and Methods now share four large input → model → output diagrams: overall architecture, DD-MDN, XGBoost Survival AFT and observation R. The overall diagram shows parallel DD-MDN and XGBoost predictors, explicit XGBoost residual-time training labels, optional SPD/Kalman/FFBS analysis and separate PedPy statistics. It identifies where future observations enter labels/evaluation only.

Methods retains six navigable chapters. Each opens with a concrete question, short answer, visual flow, one central equation with variables/units and an example. Original calculations, source provenance, additional equations and model details remain in a closed Expert section. The HDR illustration is explicitly conceptual, not experimental geometry.

Presentation's architecture scene provides four diagram tabs. Existing five-scene controls, keyboard navigation, notes and real recorded demonstration remain available.

Compare now uses three vertically stacked chapters: large DD-MDN spatial scene; XGBoost completion-time CDF; observation R with large spatial replay and aligned Clean/Noisy/Filtered/FFBS overlay. One existing Babylon scene supplies all render views with matching event, origin, camera and playback time. XGBoost's recorded-scene inset is labeled as reference rather than a generated path. R is labeled as an SPD-based synthetic perturbation experiment.

The first outcome summary shows a plain Korean question, DD-MDN/XGBoost/R probabilities and observed completion. Central completion-time interpretation is expandable to keep the actual outcome above the fold at 1440×900. Query H and predicted median time remain distinct. Natural-language filters retrieve real saved cases; empty conditions are disabled/explained with reset. Expert mode retains broader availability information.

Results preserves four research questions and uses saved values only. The noise finding now shows ADE alongside Brier, Coverage95 and HDR95 area. A compact metric guide explains ADE/FDE, NLL, Brier, Reliability/ECE, Coverage+area and completion probability. Similar help is available in Compare and the existing recording/rolling simulation. Definitions do not imply that unsupported ECE or NLL values were computed.

## Actual data dependencies

| Page / figure | Sources |
|---|---|
| Diagrams and method examples | data/inference.json; data/public/demo-evidence.json; data/public/cases/*.json; data/public/exit-aware.json; pres/evidence.json; exit_aware/exit_aware_summary.json |
| Real DD-MDN spatial display | Existing app.js/demo/ui renderer; allowlisted IMPTC case forecast packets and semantic geometry |
| Completion CDF / median bracket | data/public/exit-aware.json; data/public/ui-completion.json; existing saved CDF grid, no extrapolation |
| R spatial and probability comparison | data/public/r-index.json; data/public/r/*.json; r_robustness/r_robustness_summary.json |
| Four Results findings | pres/evidence.json; exit_aware/exit_aware_summary.json; r_robustness/r_robustness_summary.json |

No saved predictions, GT, model weights or experimental metrics were changed. Static-site checks exclude private API paths, checkpoints and private inD records. Official full-position Test, 236-origin completion and 237-origin R cohorts remain explicitly separate. Historical Test reuse and negative acceleration/crowding findings remain visible. The metric audit's H1/H4 explanation remains preserved.

## Available demonstrations

| Guided origin | Crosswalk | Prediction start |
|---|---|---|
| o0000 | f1 | +0 s |
| o0008 (default) | f2 | +8 s |
| o0011 | f3 | +1 s |

These are prediction origins; do not equate origin count with distinct pedestrians. Guided mode has 3 fully matched origins at H1–H4. Broader static material has 35 DD-MDN origins, 6 AFT comparison origins and 3 R packets across 3 public IMPTC events. Exact dataset/event/origin/horizon/scenario joins are reused.

For default o0008 at H3, DD-MDN is 0.6625, Exit-aware M1 is 0.9995645759508139, IID1 FFBS R+Q is 0.4384375. The AFT median is bracketed by the saved 2.15–2.20 s grid interval, while observed Exit is about 2.06345 s after origin. These are individual-case outputs, not aggregate calibration evidence.

## Modified files

Canonical root: /Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/

- index.html
- compare.html
- methods.html
- presentation.html
- results.html
- pres/guide.js (new shared diagrams and metric guide)
- pres/guide.css (new responsive visual system)
- pres/methods.js
- pres/presentation.js
- pres/shared.js
- pres/compare.js
- pres/extension.js
- pres/findings.js

All matching copies are synchronized under /Users/gwondohyeon/view2risk_presentation_publish_20261123/docs/presentation/ using the existing verify_static.py --sync workflow. Full absolute changed paths and SHA256 values are in changed_files.txt and source_hashes.json next to this report.

compare.html exists in the local canonical source and local deployment copy but remains untracked by Git. git ls-files --error-unmatch confirms it is not in the current commit. No commit/push was performed. Prior final/ and docs/final/ releases are preserved.

## Before and after screenshots

Evidence root: /Users/gwondohyeon/view2risk_final_ux_20261123/

Before images are genuine captures from preceding local review runs, not reconstructed historical pages:
- before/presentation.png
- before/methods.png
- before/compare.png
- before/outcome.png
- before/results.png

After:
- screenshots/presentation_architecture.png
- screenshots/methods_overall.png
- screenshots/methods_dd.png
- screenshots/methods_aft.png
- screenshots/methods_r.png
- screenshots/compare_outcome.png
- screenshots/compare_ddmdn.png
- screenshots/compare_aft.png
- screenshots/compare_r.png
- screenshots/results_story.png
- screenshots/results_mobile.png
- screenshots/methods_mobile.png
- screenshots/compare_mobile.png

## Verification

- 27 new Chrome browser checks: page rendering; default matched origin; stored probabilities; vertical section placement; large spatial view; real CDF and R source identity; shared H; separate GT reveal; six chapter equations/expanders; diagram tabs; presentation keyboard; narrative Results and ADE; mobile layouts; no JS exceptions or HTTP failures.
- 46 existing UX regression checks: natural filters, all four horizon outputs, known/unknown GT, absent predictions, M0/M1/M2, all saved noise scenarios, reset, Results sources, scientific probability formatting and mobile charts. A first run detected an above-fold outcome regression; the layout was corrected and the full suite passed.
- 43 existing legacy checks: actual standalone pedestrian motion and rolling origins; valid saved values; Presentation; Methods equations; older Results and hash routes; mobile and Modeling compatibility.
- Static canonical/deployment verification: 205 identical files; public IMPTC-only packets; no checkpoint/private API files.
- Scientific source verification: exact origins/GT, normalized and monotonic CDF, causal input timestamps, no protected-artifact modifications.

Logs: browser_check.json, ux_regression.json, legacy_browser_check.json, scientific_check.json. Screenshots and test script are retained in the evidence root.

Executed commands:
node /private/tmp/v2r_final_ux_check.mjs
node /private/tmp/v2r_ux_check.mjs
node /private/tmp/v2r_ux_legacy.mjs
python3 presentation/tools/verify_static.py --sync
python3 presentation/tools/verify_redesign.py /Users/gwondohyeon/view2risk_final_ux_20261123/scientific_check.json

## Remaining limitations

The public website replays saved outputs, not browser inference. Matched examples are limited, and filtering cannot invent unavailable conditions. Fixed-origin comparison and real-observation Rolling Forecast remain different modes. Large R HDR regions may extend beyond the common camera view; numerical area and common zoom are available. Observational subgroup differences do not establish causal effects. No independent participant study established the three-minute comprehension goal; the UI is designed for that goal and browser behavior was verified. No new generalization or model-superiority evidence is claimed.

## Exact local preview URLs

- Presentation: http://127.0.0.1:18779/presentation/presentation.html
- Methods: http://127.0.0.1:18779/presentation/methods.html
- Compare: http://127.0.0.1:18779/presentation/compare.html
- Results: http://127.0.0.1:18779/presentation/results.html
- Existing real-recording / Rolling Forecast: http://127.0.0.1:18779/presentation/?case=o0008#/simulation

Compatibility preserved: /#condition-analysis, /#r-analysis, /#clearance-aft, /#exit-final and /modeling.html under the presentation base.
