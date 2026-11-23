# Synchronized Three-Simulation Verification

Status: PASSED — local browser integration, 2026-11-23

## What changed
The prior comparison moved only the recorded person while leaving the prediction display fixed. The color labels were a legend, not live values. The comparison now provides three side-by-side Babylon scene views with a common playback clock, camera, actual pedestrian coordinates, event, prediction origin and selected horizon:

1. **DD-MDN:** saved spatial hypotheses, selected HDR68/HDR95, a moving representative forecast cursor, and completion probability.
2. **XGBoost:** the same actual recorded scene for reference, without any generated spatial path; a separate saved completion CDF and probability.
3. **Observation R:** the same scene with saved Noisy / Filtered mean / FFBS R+Q histories, predictions and HDR. Synthetic noise level and processing method are selectable. Method selection updates the top summary and detailed R values consistently.

One Babylon engine/scene supplies all three canvas views. A render batch freezes the display clock, renders the respective layers and copies them to canvases. There are no three independent engine allocations. Dragging or zooming a canvas changes the common camera. Mobile stacks the views in the same order.

## Playback semantics
- Start from the earliest uninterrupted saved record before Entry; no artificial start position.
- Pause at the exact selected prediction origin.
- Resume to replay actual future GT up to four seconds.
- By default, the future replay follows H1–H4 saved distributions (next whole-second horizon), updating probabilities and HDR from those packets. Continuous marker motion uses display interpolation of the stored representative path, not new inference.
- Manual horizon selection disables automatic horizon following; the checkbox reenables it.
- Prediction origin remains fixed to maintain exact DD/AFT/R matching. This is distinct from Rolling Forecast; the full-recording viewer remains linked for the latter.
- Live legend values include current XY/time, forecast cursor XY, GT progress, distance to Exit, and the availability/validity of the actual preceding saved DD forecast.
- Entry/Exit geometry is physically fixed. The blue/green cross embedded in the original map image is explicitly identified as a fixed map annotation, not a model forecast.
- Future GT is not revealed by past playback in Presentation mode. Playing beyond the origin explicitly reveals it.

## Measured verification
- 20 new browser checks passed (desktop 1440×1000 and mobile 390×844).
- 46 condition-filter / Results / probability / missing-data regression checks passed.
- 43 existing Simulation / Presentation / Methods / older-route checks passed.
- No JavaScript exceptions or failed HTTP responses in these suites.
- Default origin o0008, H3: DD-MDN 0.6625; Exit-aware XGBoost M1 0.9995645759508139; IID 1× FFBS R+Q 0.4384375 — matched directly to existing saved sources.
- Final test's average synchronous three-view capture time: 1.404 ms. This measures render/copy calls in this local environment, not an end-to-end FPS guarantee. UI capture is requested approximately every 100 ms.
- Canonical/deployment verification: 203 identical files.
- Protected scientific artifact modifications: none.

## Limitations
The static website replays existing outputs. It does not rerun DD-MDN or XGBoost. Three matched public R origins are available. Missing R/method results remain unavailable rather than using another origin. Large R regions may extend outside the shared viewport; the shared zoom and full numeric area remain available. A single case does not establish calibration or model superiority. The historical/full-Test cohorts remain separate.

## Exact source changes
- /Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/compare.html
- /Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/pres/compare.js
- /Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/pres/extension.js
- /Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/pres/triptych.js
- /Users/gwondohyeon/view2risk_presentation_publish_20261123/presentation/site/pres/ux.css
- Corresponding copies under /Users/gwondohyeon/view2risk_presentation_publish_20261123/docs/presentation/

## Evidence
- /Users/gwondohyeon/view2risk_triptych_20261123/browser_check.json
- /Users/gwondohyeon/view2risk_triptych_20261123/legacy_browser_check.json
- /Users/gwondohyeon/view2risk_triptych_20261123/ux_regression.json
- /Users/gwondohyeon/view2risk_triptych_20261123/scientific_check.json
- /Users/gwondohyeon/view2risk_triptych_20261123/source_hashes.json
- /Users/gwondohyeon/view2risk_triptych_20261123/changed_files.txt
- /Users/gwondohyeon/view2risk_triptych_20261123/screenshots/three_models_detail.png
- /Users/gwondohyeon/view2risk_triptych_20261123/screenshots/three_at_origin.png
- /Users/gwondohyeon/view2risk_triptych_20261123/screenshots/three_playing.png
- /Users/gwondohyeon/view2risk_triptych_20261123/screenshots/before_origin.png
- /Users/gwondohyeon/view2risk_triptych_20261123/screenshots/three_mobile.png

## Commands
node /private/tmp/v2r_triptych_check.mjs
node /private/tmp/v2r_ux_check.mjs
node /private/tmp/v2r_ux_legacy.mjs
python3 presentation/tools/verify_static.py --sync
python3 presentation/tools/verify_redesign.py /Users/gwondohyeon/view2risk_triptych_20261123/scientific_check.json

URL: http://127.0.0.1:18779/presentation/compare.html#dd-panel

No model fitting, inference, data publication or GitHub push occurred. Prior final releases and experimental outputs are preserved.
