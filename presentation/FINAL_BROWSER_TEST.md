# Final UX Browser Test

Status: PASSED — actual Chrome interactions on the local static server.

| Suite | Passed / executed | JS errors | HTTP failures |
|---|---:|---:|---:|
| New UX acceptance | 46/46 | 0 | 0 |
| Existing-route regression | 43/43 | 0 | 0 |

Desktop: 1440×900; mobile: 390×844. Existing viewer additionally checked 756 px and 390 px layouts. The main default outcome is visible within the 900 px desktop viewport. No page-level horizontal overflow was observed.

## Acceptance coverage

- Exact o0008 Guided default; all three saved probabilities and observed 2.06 s outcome.
- No NOT EVALUATED text in complete-case Guided workflow.
- Same dataset/event/origin across all panels and H1–H4; exact saved HDR index and GT.
- Crosswalk, speed, acceleration and combined neighbor filters; disabled unsupported categories.
- Forced empty filter intersection hides stale scene/probabilities; Reset restores a complete case.
- GT visible in ordinary exploration; Presentation hide/reveal preserves the origin.
- M0/M1/M2 switches read distinct saved CDFs at the same origin.
- Clean/IID 0.5/1/2 use saved packets; common spatial bounds remain identical.
- Four visibility toggles share one coordinate frame. No additional Babylon renderer.
- Expert correlated/dropout packets, absent R, absent AFT, unavailable horizon and unknown interval-boundary GT.
- Safe probability formatting including near-one and tiny nonzero values.
- Four Results conclusions, source metric equality and explicit cohort distinctions.
- Mobile selectors, comparison and Results bars readable; optional math accessible.
- Preserved old playback, rolling forecast, pin/seek, stale-output clearing, GT and all historical Results/hash aliases.

## Reproduction

```sh
python3 presentation/tools/verify_static.py --sync
python3 presentation/tools/verify_static.py
python3 presentation/tools/audit_case_availability.py presentation/ux-evidence
python3 presentation/tools/verify_redesign.py presentation/ux-evidence/scientific_check.json
# Local docs server on 18779, existing Chrome CDP on 18776
V2R_CHECK_OUTPUT=presentation/ux-evidence node presentation/tools/ux_browser_check.mjs
```

Actual execution copies: `/private/tmp/v2r_ux_check.mjs`, `/private/tmp/v2r_ux_legacy.mjs`.
Evidence root: `/Users/gwondohyeon/view2risk_ux_20261123/`.
`browser_check.json`, `legacy/browser_check.json`, `scientific_check.json`, `availability_runtime.json`, `availability_audit.json`, `availability_by_origin_horizon.csv` record results.

## Before and after

Before screenshots were preserved from the previous local browser inspection, whose comparison/results implementation was the starting point for this change. They are in `before/compare.png` and `before/results.png`.

After screenshots in `screenshots/`:

- `outcome_desktop.png` — top outcome-first comparison
- `natural_filters.png` — real-condition selector
- `ddmdn_explanation.png` — actual spatial replay
- `feature_ablation.png` — same-origin M0/M1/M2
- `r_overlays.png` — four saved conditions on shared axes
- `results_desktop.png`, `finding-support.png`, `finding-features.png`, `finding-noise.png`
- `compare_mobile.png`, `filters_mobile.png`, `results_mobile.png`, `r_results_mobile.png`

## Changed canonical website files (this UX revision)

```text
presentation/site/compare.html
presentation/site/pres/availability.js
presentation/site/pres/compare-data.js
presentation/site/pres/compare.js
presentation/site/pres/extension.js
presentation/site/pres/findings.js
presentation/site/pres/shared.js
presentation/site/pres/ux-spatial.js
presentation/site/pres/ux.css
presentation/site/results.html
```

Matching `docs/presentation/` files were synchronized. Additional files are the five requested reports, `presentation/tools/ux_browser_check.mjs`, `presentation/tools/audit_case_availability.py`, and the ignored evidence-directory entry in `presentation/.gitignore`.

## Preservation and publication boundary

Canonical source: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/`.
Deployment mirror: `/Users/gwondohyeon/view2risk_presentation_publish_20261123/docs/presentation/`.
The 202 static files are byte-identical across those directories. This is a local, uncommitted review revision on `presentation/synchronized-three-panel-20261123`; no push was performed. The current GitHub Pages release is unchanged.

188 previously protected files remain byte-identical, including `final/`, `docs/final/`, saved prediction/metric artifacts and the resolved historical metric audit. No model training, inference, hyperparameter selection, calibration, GT modification or new private-data export occurred. Individual replay still uses only existing allowlisted IMPTC excerpts. The website is a static replay, not a browser inference service.
