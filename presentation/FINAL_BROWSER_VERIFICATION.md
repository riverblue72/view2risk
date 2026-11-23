# Final Browser Verification

Status: PASSED — local desktop/mobile browser verification; publication authorized by the user.

## Executed checks

| Suite | Passed |
|---|---:|
| Seven-scene narrative, real iframe, CDF/GT/R/Methods/Results | 54 |
| Existing case filters, probabilities, M0/M1/M2, missing GT/results, mobile | 46 |
| Existing recording/rolling simulation, legacy routes, notes/math compatibility | 43 |
| Dedicated 1440×900 architecture fit | 1 |
| Total | 144 |

No uncaught JavaScript exceptions or failed HTTP responses in the completed suites. Local testing used Chrome CDP. Desktop: 1440×1000 and 1440×900. Mobile: 390×844 (and existing 756px/390px replay checks).

The browser verified all seven scenes, seven reveals of the same o0008 origin, actual persistent iframe event/origin/horizon, real GT reveal, full saved DD/XGBoost curves, exact individual squared probability errors, all five saved R scenarios, eight FFBS histories, correct horizon-indexed containment, case changes, actual grouped Reliability points, six continuous five-field Methods sections, keyboard navigation, presenter notes, no page-level mobile horizontal overflow and conclusion navigation.

The iframe initially reloaded when moved between scene containers. This was discovered by the older integration check and corrected with a persistent iframe parent. Both parent metadata and the actual iframe now remain at the selected origin across reveals. The old suite's internal API checks were adapted to the seven-scene interface; its scientific and route assertions remain.

Static verification: 208 identical canonical/deployment files. No private API/checkpoint files. Scientific verification: all protected experimental artifacts unchanged, exact origins/GT, monotonic stored CDF and causal timestamp checks passed.

## Sources and routes

Canonical: presentation/site/ → docs/presentation/ via tools/verify_static.py --sync.
Pages setting read from GitHub: main branch /docs, legacy build. No Pages configuration replacement.

Public destinations after publication:
- https://riverblue72.github.io/view2risk/presentation/presentation.html
- https://riverblue72.github.io/view2risk/presentation/methods.html
- https://riverblue72.github.io/view2risk/presentation/compare.html
- https://riverblue72.github.io/view2risk/presentation/results.html

Local equivalents: http://127.0.0.1:18779/presentation/ followed by the same filenames.
Compatibility tested: /#condition-analysis, /#r-analysis, /#clearance-aft, /#exit-final, /modeling.html, and existing /?case=o0008#/simulation.

## Modified-file summary

The capstone implementation changes presentation.html; methods.html; compare.html; results.html; pres/story.js (new); pres/story.css (new); pres/research-ui.js (new); pres/methods.js; pres/compare.js; pres/findings.js; pres/extension.js; and their docs/presentation mirrors. It includes previously local-only comparison/UX modules and documentation needed to make those pages publishable. The canonical and deploy index route still opens Presentation. Exact cumulative changed paths are stored in review/changed_files.txt after staging.

New verification entry point: presentation/tools/capstone_browser_check.mjs. Existing static/scientific/UX workflows are retained. New report names: FINAL_PRESENTATION_STORYBOARD.md, FINAL_METHODS_EXPLANATION.md, FINAL_SIMULATION_UX_REPORT.md, FINAL_RESULTS_INTERPRETATION.md, FINAL_BROWSER_VERIFICATION.md.

## Evidence and reproduction

Screenshots are in review/screenshots/. All seven scene images, CDF+GT, Methods architecture, R, Results, Reliability and mobile images are included. review/verification_summary.json contains check names/status only. review/aggregate_results.json contains aggregate results only.

Executed:
- node /private/tmp/v2r_capstone_check.mjs
- node /private/tmp/v2r_capstone_ux_check.mjs
- node /private/tmp/v2r_capstone_legacy.mjs
- node /private/tmp/v2r_capstone_layout.mjs
- python3 presentation/tools/verify_static.py --sync
- python3 presentation/tools/verify_redesign.py /Users/gwondohyeon/view2risk_capstone_20261123/scientific_check.json

Portable primary check: V2R_CHECK_OUTPUT=presentation/capstone-evidence node presentation/tools/capstone_browser_check.mjs (Chrome CDP on 18776, local preview on 18779). Optional V2R_PUBLIC_URL targets static deployment.

## Honest limits

Five-to-six minutes is the allocated speaker timing, not a measured audience study. Browser checks establish behavior/rendering/numerical linkage, not guaranteed first-visit understanding. Public R CDF packets contain H1–H4 only; no intermediate values were fabricated. No independent completion calibration, fresh-date generalization, real-camera R transfer, causal acceleration/crowding benefit, long-horizon DD-MDN validation or deployed safety capability is claimed.

No models were trained or inferred, no operational GT was changed, no restricted inD data were included. Existing final/ and docs/final/ releases are preserved.
