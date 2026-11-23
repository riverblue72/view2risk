# Typography and Architecture Cleanup

Status: PASSED — local review revision, 2026-11-23.

## What was found

A replacement-character/encoding error was not reproduced on the local Methods, Compare, Presentation or Results screens. KaTeX reported no formula errors and used fonts loaded successfully. The old architecture had dense SVG text, crossing auxiliary paths and a minimum width that required horizontal scrolling on phones. A 1280×720 presentation check also exposed lower explanation text clipping against the footer during this revision; that layout was corrected and retested.

## Changes

- Replaced the large fixed-coordinate SVG with responsive HTML cards. The central story is observations → two parallel predictors → evaluation. Only two short input connectors remain.
- Kept the essential distinction: DD-MDN is pretrained and spatial; XGBoost is separately trained and time-distribution based. XGBoost training labels remain explicit. No predictor-to-predictor arrow.
- Moved R and PedPy into short supporting descriptions rather than competing boxes or long crossing arrows. Full geometry/GT math remains in Methods.
- Added explicit Korean font fallbacks, word-preserving line breaks, and overflow handling for long formulas without overriding KaTeX's internal font metrics.
- Removed architecture minimum widths and made phone cards stack naturally. Compact presentation styles preserve the full explanation at 720p.

## Executed verification

`typography_check.json`: 30/30 checks passed; 0 JS exceptions, 0 HTTP failures. Tested 1440×900, 1280×720 and 390×900. All six Methods chapters, including expanded equations, rendered without errors or page overflow. Presentation diagram remained above the footer on desktop; mobile reflow passed. Compare still loaded the exact public-imptc-01 / origin +8 s identity and rendered its formulas. Scientific artifact checks passed unchanged.

Original broad browser evidence remains 72 redesign and 43 regression checks from the prior iteration. This follow-up specifically executed the 30 typography/layout checks; it does not claim that all 115 were rerun.

## Files changed in this follow-up

- `presentation/site/pres/shared.js`
- `presentation/site/pres/style.css`
- Synchronized mirrors in `docs/presentation/pres/`
- `presentation/tools/typography_browser_check.mjs`
- Review reports and evidence only

## Reproduce

```sh
python3 presentation/tools/verify_static.py --sync
python3 presentation/tools/verify_static.py
# Existing local preview on 18779, Chrome CDP on 18776
V2R_CHECK_OUTPUT=presentation/redesign-evidence node presentation/tools/typography_browser_check.mjs
```

Evidence: `/Users/gwondohyeon/view2risk_redesign_review_20261123/typography_check.json`.
Screenshots under the same directory's `screenshots/`: `clean_architecture_1440.png`, `clean_architecture_390.png`, `clean_presentation_1280.png`, `clean_presentation_1440.png`, and `clean_text_390.png`.

No predictions, geometry, GT, statistical results or previous final releases were edited. This revision is not pushed to GitHub. The public site remains the previous release. Review at http://127.0.0.1:18779/presentation/methods.html and http://127.0.0.1:18779/presentation/presentation.html .
