# Full-data verification

{
  "passed": true,
  "original_sample_and_pilot_inputs_results_unchanged": true,
  "date_disjoint_folds": true,
  "all_models_common_origins": true,
  "independent_matrix_KF_checks": 15,
  "max_mean_difference_m": 8.881784197001252e-15,
  "max_covariance_difference_m2": 5.551115123125783e-17,
  "independent_past_OLS_checks": 80,
  "max_OLS_difference_m": 2.2737367544323206e-13,
  "all_coverage_area_recomputed": true,
  "future_perturbation_causality_test": true,
  "figures_verified": 12,
  "Q_forecasts": 2124624,
  "Q_origins": 265578,
  "Q_evaluable_tracks": 1906,
  "Q_evaluable_sequences": 264,
  "Q_dates": 15,
  "R_sites": 6,
  "R_eligible_pairs": 10109
}

Independent full-matrix Joseph-update Kalman and least-squares checks compare actual held-out forecasts. Original input/result hashes were checked again. Date/site grouping prevents within-group leakage in this extension. These numerical checks do not establish physical GT or prove unique R/Q identifiability.

The full protocol differs from sample4-sequence LOSO in population and stricter group granularity. The original sample results remain frozen. Q date bootstrap conditions on the fixed OOF predictions; it does not include model-refit/selection uncertainty. R bootstrap has only six site clusters.
