# Entry-Origin Default Verification

Status: PASSED — local change only, not pushed.

The comparison default previously selected o0008/f2 at +8s, which is approximately 8.015656s after operational Entry. It therefore began mid-crossing by design, but this was confusing as a default crossing demonstration.

The default now selects o0000/public-imptc-02/f1 at origin +0s, approximately 0.015622s after operational Entry. This is the available matched DD-MDN/XGBoost/R prediction at the actual crossing entrance. The person remains at the original recorded XY; predictions are not transferred from the near-Exit case.

Two explicit presets select the entry f1 event or the different near-Exit f2 event. Query ?case=o0008 preserves explicit presentation links to the original example. Reset returns to the entry example.

At entry, actual residual Exit is 7.782994s. The current model window is four seconds, so H1–H4 GT labels are all zero. The UI explicitly states that the actual Exit line is outside the displayed CDF window. The full recorded crossing / Rolling Forecast route remains linked. No probabilities beyond the stored horizon were created.

10 browser checks passed: real Entry time, exact native XY, exact origin matching across predictors, beyond-window outcome disclosure, both presets, explicit query link, reset, mobile layout, no JS/HTTP errors. Scientific artifact verification passed unchanged.

URL: http://127.0.0.1:18779/presentation/compare.html
Near-Exit example: http://127.0.0.1:18779/presentation/compare.html?case=o0008
Evidence: /Users/gwondohyeon/view2risk_entry_default_20261123/
Command: node /private/tmp/v2r_entry_default_check.mjs
