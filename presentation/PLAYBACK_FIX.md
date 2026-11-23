# Comparison Playback Fix — 2026-11-23

Status: PASSED

## Cause
The comparison page's play button cycled H1–H4. Every cycle called compareSet, which deliberately pinned the pedestrian at the fixed prediction origin. This did not replay walking.

## Change
The main button and the transport next to the 3D canvas now replay the actual recorded future, with pause, reset and a seek slider. Playback uses existing timestamped XY observations, stops at four seconds or the first observation gap, and never generates new predictions. A display-only clock moves the pedestrian mesh; the causal history, prediction packet, selected horizon, features and all comparison probabilities remain anchored to the original observation time. The label explicitly identifies this as GT replay. In Presentation mode, pressing Play reveals GT before playback; seeking remains disabled while GT is hidden.

The existing full-recording / Rolling Forecast viewer is linked separately for advancing both the recording and the saved prediction origins. Existing standalone playback behavior is preserved.

## Browser verification
14 playback checks passed: actual mesh matches saved future XY, movement exceeds 0.3 m, exact origin and probability preservation, pause, seek, reset, GT reveal, four-second endpoint, horizon/case changes, mobile overflow, no JS/HTTP errors.
43 legacy regression checks passed, including actual standalone walking and rolling origin advance, saved predictions, older routes, equations and mobile layouts.
Static canonical/deployment verification: 202 files identical. Scientific artifact verification: no protected artifact modifications.

## Changed files in this fix
- presentation/site/compare.html
- presentation/site/pres/compare.js
- presentation/site/pres/extension.js
- presentation/site/pres/ux.css
- Matching docs/presentation/ deployment copies.

## URLs
- http://127.0.0.1:18779/presentation/compare.html
- http://127.0.0.1:18779/presentation/?case=o0008#/simulation

## Evidence
/Users/gwondohyeon/view2risk_playback_fix_20261123/browser_check.json
/Users/gwondohyeon/view2risk_playback_fix_20261123/legacy_browser_check.json
/Users/gwondohyeon/view2risk_playback_fix_20261123/scientific_check.json
/Users/gwondohyeon/view2risk_playback_fix_20261123/screenshots/recorded_future_desktop.png
/Users/gwondohyeon/view2risk_playback_fix_20261123/screenshots/recorded_future_mobile.png

## Reproduction
node /private/tmp/v2r_playback_check.mjs
node /private/tmp/v2r_ux_legacy.mjs
python3 presentation/tools/verify_static.py
python3 presentation/tools/verify_redesign.py /Users/gwondohyeon/view2risk_playback_fix_20261123/scientific_check.json

No training, inference, source data changes or GitHub push occurred.
