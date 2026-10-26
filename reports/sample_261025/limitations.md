# Pilot limitations

SPD: one sequence, 9 track groups, 253 paired annotations; shared boxes, asynchronous observations, and unresolved camera calibration/projection. R_pair_proxy describes pair disagreement, never pure camera prediction error.

IMPTC: 4 sequences and 61 tracks, all from provided sensing/tracking data. Q_effective mixes motion-model mismatch, observation/processing effects, initialization and assumed white Gaussian structure. Scalar km/h-derived speed is not independent velocity GT. Future recorded-position forecasts are proxy validation only.

LOSO prevents sequence leakage, but 4 sequences do not support stable nested selection or broad generalization. Development criteria and bounds are fixed before evaluating outer tests. Test folds are not reused for tuning. Sequence and track identities are retained; real-person cross-sequence identity is unavailable.

Fixed-grid R selection and forecast-fitted q are operational predictive parameters. Optional joint innovation-ML R/Q can be confounded, hit bounds, or favor one-step smoothness while under-covering at 1/3s. Joint ML is not EM and not proof of identifiability.

Isotropic linear CV, zero initial velocity and a finite warmup are assumptions. Overlapping horizons and 0.2s origins remain autocorrelated. Paired-horizon eligibility excludes origins near track ends and very short segments. No performance is claimed for excluded frames.

Smoothing sensitivity uses only past data. Noise injection, external sensor fusion, signal-control optimization, G95, weather/age/violation models are not run. SPD and IMPTC rows/people are not pooled. Additional raw downloads are not required or performed by the pilot.
