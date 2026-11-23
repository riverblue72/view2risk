# View2Risk — Final R Integration Check

Status: PASSED implementation; LIMITATION/BLOCKED scientific scope

## PASSED
- All planned origins retained
- All16 modes and4 horizons present
- No duplicated matched records
- Frozen conversion code unchanged
- All reused source packets unchanged
- SPD Train fit unchanged
- Two dataset Clean distributions exactly reproduced
- No future source timestamps
- No inD completion
- Probabilities in0..1
- All probability CDFs monotone
- Unknown GT never scored failure
- Brier equals saved probability error
- Shifts correctly in percentage points
- Matched recovery identity
- Original GT catalog and geometry hashes
- Existing results/source preserved
- imptc checkpoint SHA unchanged
- ind checkpoint SHA unchanged
- All mixtures, histories and scenario transforms valid
- No failed prediction combinations
- Per-metric denominators present
- No licensed predictions in static web
-18 synthetic/legacy implementation checks passed. Fixtures are not real model-performance evidence.
- Actual browser checks: 33; passed=True.

## LIMITATION
- SPD annotation proxy transferred directly to target XY, not independently measured detector noise. Context assumed exact.
- AR rho0.8 has stationary covariance but Legacy filter still assumes white measurement noise.
- Single synthetic-noise seed per origin; FFBS8 finite samples,3200 joint futures, HDR grid approximation.
- Historically reused Test, complete-case GT, recording-cluster CI; no independent completion Calibration or IPCW.
- Sparse stop/restart/crowding groups marked insufficient. Density regions differ. No causal or demographic claims.
- DD-MDN noise double-counting and physical R/Q identification unresolved. No predictor replacement.
- Initial official loader collided on an empty runtime test.log; resumed with isolated result_path. No model/data/numerical settings changed; initial logs retained.

## BLOCKED / NOT_IMPLEMENTED
- inD semantic Exit unverified: position-only analysis.
- XGBoost AFT: no independently trained/evaluated artifact found; NOT_IMPLEMENTED, not trained.
- Population-level calibrated completion probability and15–20s forecasts not supported.

## Integration
Default Q-only unchanged. Added website/r_robustness.js, r_robustness.css and aggregate r_robustness/ directory. Existing index.html only adds assets; serve.py adds whitelisted data/public/r-index.json and data/public/r/<file>. Existing condition and Modeling Guide preserved.

Private viewer: http://127.0.0.1:18773/#r-analysis. Observation selector includes Clean, Noisy, filtered mean, FFBS R+Q and side-by-side; noise controls only evaluated scales0.5/1/2, AR0.8 and last0.4s dropout. Recorded cases only. Unavailable origins/modes are explicit. All comparison plots use actual saved outputs.

## Reproduction
`../../.venv/bin/python robustness.py test`

`bash run_cpu4.sh` resumes completed origin files, then aggregates.

`../../.venv/bin/python deploy_r.py` only after all eligible origins completed; restart existing web process.

`../../.venv/bin/python verify_r.py` validates manifests/hashes/counts and browser evidence.

Per-origin CSV and private files stay server-only. No GPU job, training, GitHub push, new model or dataset. Analysis outputs and frozen config are in r_robustness_20261121/. Stop expansion after this integration.
