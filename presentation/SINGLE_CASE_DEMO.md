# One-case research demonstration

Local URL: http://127.0.0.1:18779/presentation/demo.html

## Purpose and fixed case

One real allowlisted IMPTC f2 record, public-imptc-01 / o0008, remains selected throughout. The prediction origin is +8 seconds in the saved event reference. The presentation starts with actual observations before Entry, rather than relocating the forecast or fabricating an earlier prediction.

1. Press **시연 시작** to replay actual pre-origin observations.
2. Playback pauses at the saved prediction origin and reveals DD-MDN and XGBoost predictions.
3. Press **실제 정답 공개**, then replay the recorded future.
4. Select **관측오차** to inspect the same origin's saved IID scale-1 FFBS R+Q evidence.

The four supported horizons remain selectable. There are no counterfactual feature sliders or alternate-person substitutions.

## Verified evidence

- Actual residual Exit time: 2.063445091247559 seconds.
- DD-MDN H3 probability: 0.6625.
- Exit-aware XGBoost M1 H3 probability: 0.99956457595 (displayed approximately 99.96%).
- IID scale-1 FFBS R+Q H3 probability: 0.4384375.
- GT H1/H2 = 0; GT H3/H4 = 1.

DD-MDN samples future spatial paths; XGBoost separately predicts the remaining-time CDF. R is an SPD annotation-disagreement synthetic-noise experiment on DD-MDN. It is not a third learned predictor. At H2 this case favors DD-MDN's individual squared probability error; H3/H4 favor XGBoost. One case does not establish population calibration or universal superiority.

## Sources and changes

Canonical public source is presentation/site; deployment mirror is docs/presentation.

New: demo.html, pres/single-case.js, pres/single-case.css.
Updated: compare.html (demo link), pres/shared.js (main navigation), pres/extension.js and pres/triptych.js (staged prediction visibility).

The demo reuses compare.html's existing exact event/origin joins, original Babylon renderer, saved future XY, saved DD-MDN/AFT CDFs and matched R packets. It does not add inference, fitting, or new saved scientific results. Original hidden renderer keeps its layout dimensions so spatial snapshots continue updating.

## Verification actually run

- Browser: 11/11 checks passed; no observed JavaScript errors or failed HTTP requests in the completed run.
- Verified actual movement, origin auto-pause, same identity across stages, GT reveal, future replay, matched R evidence, shared horizon, reset and mobile parent/child overflow.
- Scientific verifier: PASSED. Exact event/origin joins, identical matched future XY and GT, saved CDF agreement, monotonic valid probabilities, causal input timestamps and unchanged protected artifacts.
- Static verification synchronized canonical and deployment copies.

Evidence: browser_check.json, scientific_check.json, browser_check.mjs and screenshots/ in this review directory.

Screenshots: one_case_history.png, one_case_predictions.png, one_case_gt.png, one_case_r.png, one_case_mobile.png.

## Boundaries

This is replay of stored outputs, not live inference. The origin stays fixed while actual pedestrian positions animate. Large R regions may extend beyond the fixed comparison view; numerical region area remains available. The case does not prove overall model ranking. No model training, GT changes, checkpoint changes, restricted inD publication, commit, or GitHub push was performed for this demo.
