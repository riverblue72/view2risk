# Recorded Entry-to-Forecast Playback — 2026-11-23

Status: PASSED

## Why the pedestrian began mid-crosswalk
The comparison selects o0008 / public-imptc-01 with a fixed prediction origin of 8 seconds. The preceding playback implementation started at that origin. This was a selected forecast snapshot, not the beginning of the crossing.

The existing default-case recording starts at elapsed -3.1999850273 seconds, before operational Entry at -0.0156555176 seconds. No new observations or inferred starting positions were needed.

## Updated interaction
- Initially show the earliest uninterrupted stored observation connected to the selected origin. Do not reposition a pedestrian on an invented Entry coordinate.
- Replay actual recorded XY, including before Entry.
- Automatically pause at the fixed prediction origin; reveal the stored forecast paths and HDR there.
- Press Play again to replay actual future GT up to the existing four-second comparison window.
- Reset returns to the recording start; a separate button jumps directly to the prediction origin.
- Horizon changes retain the recorded playback position for the same event/origin.
- During earlier recording playback, later history and forecast meshes are hidden. Neighbor positions and visible history follow the replay clock.
- In Presentation mode, replaying past observations does not reveal future GT. Future replay explicitly reveals GT.
- The model inputs, probabilities, causal features and comparison origin remain fixed. Numbers are labeled as the selected forecast snapshot, not recomputed historical predictions.
- Stop at observation discontinuities; do not bridge missing records.

## Verified
16 actual Chrome browser checks passed on the local page, including all three public events starting before their recorded operational Entry, exact mesh-to-stored-coordinate equality, actual walking, pause/reset/seek, same-origin preservation, automatic origin stop, separate GT handling, mobile overflow and no JavaScript/HTTP errors.

Canonical/deployment synchronization: 202 identical files. Scientific source check: no protected-artifact modifications; stored event/origin joins and outcomes preserved.

## Files changed
presentation/site/compare.html
presentation/site/pres/compare.js
presentation/site/pres/extension.js
Matching docs/presentation/ deployment copies.

## Evidence and reproduction
Directory: /Users/gwondohyeon/view2risk_entry_replay_20261123
- browser_check.json
- browser_check.mjs
- scientific_check.json
- screenshots/pre_entry_desktop.png
- screenshots/forecast_origin_desktop.png
- screenshots/pre_entry_mobile.png

Executed: node /private/tmp/v2r_entry_check.mjs
Executed: python3 presentation/tools/verify_static.py --sync
Executed: python3 presentation/tools/verify_redesign.py /Users/gwondohyeon/view2risk_entry_replay_20261123/scientific_check.json

URL: http://127.0.0.1:18779/presentation/compare.html

This supersedes the comparison playback start/reset behavior in PLAYBACK_FIX.md. The standalone full-recording / Rolling Forecast route is unchanged. No training, inference, experiment changes or GitHub push.
