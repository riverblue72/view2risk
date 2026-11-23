# Final UI Browser Check

Status: PASSED — actually executed in Chrome, not a markup-only check.

## Results

| Suite | Passed / executed | JS exceptions | HTTP failures |
|---|---:|---:|---:|
| New redesign interactions | 72 / 72 | 0 | 0 |
| Existing viewer regression | 43 / 43 | 0 | 0 |

Desktop: 1440×900, with additional 1920×1080 overflow check. Mobile: 390×844. The previous viewer also passed its 756 px layout check. No page-level horizontal overflow was observed in comparison/Methods mobile views.

Tests covered exact identities across all panels, H1–H4 updates and HDR index, saved probabilities, same GT and individual error, five AFT/baseline choices, all 16 R scenario/method selections, absent-origin behavior, unknown GT, f1/f2/f3 changes, fixed-origin horizon playback, reset, rendering count, mathematical rendering, five presentation scenes, keyboard navigation and no private API requests.

Existing regression covered real recording playback, rolling origin advancement, pin/seek, stale probability clearing, absent AFT, GT reveal, pending case selection, old R/results pages, legacy hash aliases and Modeling Guide. `/#condition-analysis`, `/#r-analysis`, `/#clearance-aft` and `/#exit-final` remain compatibility routes. The comparison does not replace the original simulator.

## Routes

| Destination | Local review URL |
|---|---|
| Presentation | http://127.0.0.1:18779/presentation/presentation.html |
| Methods | http://127.0.0.1:18779/presentation/methods.html |
| Compare Models | http://127.0.0.1:18779/presentation/compare.html |
| Results | http://127.0.0.1:18779/presentation/#/results/trajectory |
| Legacy simulation | http://127.0.0.1:18779/presentation/#/simulation |
| Legacy Modeling Guide | http://127.0.0.1:18779/presentation/modeling.html |
| Legacy How It Works | http://127.0.0.1:18779/presentation/how-it-works.html |

## Source and deployment

Canonical `presentation/site/` and `docs/presentation/` are byte-identical (197 files). New comparison uses one Babylon renderer and SVG CDF/R views. The measured FPS reading was 59.70 on this local Chrome environment; no claim is made for every device.

## Reproduction

From the repository root:

```sh
python3 presentation/tools/verify_static.py --sync
python3 presentation/tools/verify_static.py
python3 presentation/tools/verify_redesign.py presentation/redesign-evidence/scientific_check.json
# Serve docs on local port 18779; Chrome CDP must be available on 18776.
V2R_CHECK_OUTPUT=presentation/redesign-evidence node presentation/tools/redesign_browser_check.mjs
```

Actual execution used equivalent local copies in `/Users/gwondohyeon/view2risk_redesign_review_20261123/`: `redesign_check.mjs` and `legacy_check.mjs`. Evidence is `browser_check.json`, `legacy/browser_check.json`, `scientific_check.json`, and `preserved_sources.json` in that directory. The final small post-Exit notice was syntax/static checked; the full 72-check suite preceded that text-only notice and the expanded SPD-fit explanation, while the 43-check regression followed them.

## Screenshots

Saved under `/Users/gwondohyeon/view2risk_redesign_review_20261123/screenshots/`:

- `model_architecture.png`
- `methods_overview.png`, `methods_coordinates.png`, `methods_mobile.png`
- `ddmdn_panel.png`, `xgboost_panel.png`, `observation_r_panel.png`
- `three_panel_full.png`, `compare_mobile.png`
- `presentation_opening.png`, `presentation_architecture.png`, `presentation_findings.png`

The review ZIP excludes an old failed-test capture. Failures encountered during development (async case loading and an overflowing redundant presentation formula) were fixed before successful browser runs.

## Files changed

The exact repository-relative list follows below. No prior release file is included.

## Release boundary

This is a local review revision dated 2026-11-23. No commit or push was performed. The public GitHub Pages release is unchanged. Canonical files are in `presentation/site/`; the deployment mirror is `docs/presentation/`. Existing `final/`, `docs/final/`, saved experimental results and model artifacts were not edited. No fitting, inference, calibration or GPU work was run.

The static website replays already saved inference outputs. It does not run DD-MDN or XGBoost in the browser. Only existing allowlisted IMPTC excerpts are used for individual demonstrations; no new individual inD records or private inference packets were exported.

```text
docs/presentation/compare.html
docs/presentation/how-it-works.html
docs/presentation/methods.html
docs/presentation/modeling.html
docs/presentation/pres/compare-data.js
docs/presentation/pres/compare.css
docs/presentation/pres/compare.js
docs/presentation/pres/extension.js
docs/presentation/pres/methods.js
docs/presentation/pres/presentation.js
docs/presentation/pres/shared.js
docs/presentation/pres/style.css
presentation/.gitignore
presentation/FINAL_METHODS_REDESIGN.md
presentation/FINAL_PRESENTATION_REDESIGN.md
presentation/FINAL_SCIENTIFIC_CONSISTENCY_CHECK.md
presentation/FINAL_THREE_PANEL_COMPARISON.md
presentation/FINAL_UI_BROWSER_CHECK.md
presentation/README.md
presentation/site/compare.html
presentation/site/how-it-works.html
presentation/site/methods.html
presentation/site/modeling.html
presentation/site/pres/compare-data.js
presentation/site/pres/compare.css
presentation/site/pres/compare.js
presentation/site/pres/extension.js
presentation/site/pres/methods.js
presentation/site/pres/presentation.js
presentation/site/pres/shared.js
presentation/site/pres/style.css
presentation/tools/browser_check.mjs
presentation/tools/redesign_browser_check.mjs
presentation/tools/verify_redesign.py
```

## Follow-up typography revision

See `UI_TYPOGRAPHY_CLEANUP.md`: 30 additional executed layout/math checks passed after simplifying the architecture to responsive HTML. The prior SVG description is superseded. No publication performed.
