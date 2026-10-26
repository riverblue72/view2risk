# Validation and reproducibility checks

{
  "passed": true,
  "SPD_pairs": 253,
  "SPD_tracks": 9,
  "IMPTC_sample_rows": 56374,
  "IMPTC_valid_rows": 54314,
  "valid_segments": 87,
  "evaluable_tracks": 60,
  "test_sequences": 4,
  "common_origins": 8688,
  "predictions": 69504,
  "all_models_same_origins": true,
  "no_outer_test_in_fitting": true,
  "filter_future_perturbation_causality_test": true,
  "exact_constant_velocity_slope_test": true,
  "positive_covariances": true,
  "input_hashes_unchanged": true,
  "no_SPD_R_in_IMPTC": true,
  "excluded_conditions_not_used": true,
  "figures_verified": 12,
  "parameter_boundary_diagnostics": {
    "0000_20230322_081506": {
      "Fixed_noise_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Data_fitted_Q_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Joint_innovation_ML_KF": {
        "q_near_lower": false,
        "r_near_lower": true
      }
    },
    "0001_20230523_105516": {
      "Fixed_noise_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Data_fitted_Q_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Joint_innovation_ML_KF": {
        "q_near_lower": false,
        "r_near_lower": true
      }
    },
    "0002_20230523_111106": {
      "Fixed_noise_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Data_fitted_Q_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Joint_innovation_ML_KF": {
        "q_near_lower": false,
        "r_near_lower": true
      }
    },
    "0003_20230523_111514": {
      "Fixed_noise_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Data_fitted_Q_KF": {
        "q_near_lower": false,
        "r_near_lower": false
      },
      "Joint_innovation_ML_KF": {
        "q_near_lower": false,
        "r_near_lower": true
      }
    }
  }
}

Input hashes compare both Parquet tables and existing reports before/after the run; no audit re-run or download was performed. This is not an external validation of physical R/Q.

LOSO forecasts, by sequence:

| sequence_id | model | horizon_s | test_sequences | test_tracks | predictions | RMSE_m | MAE_m | p95_error_m | max_error_m | coverage90 | coverage95 | mean_area90_m2 | mean_area95_m2 | mean_radius95_m | NLL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0000_20230322_081506 | Data_fitted_Q_KF | 1 | 1 | 3 | 656 | 0.146096 | 0.0947086 | 0.354522 | 0.666246 | 0.926829 | 0.942073 | 0.255902 | 0.332936 | 0.325541 | -1.59365 |
| 0000_20230322_081506 | Data_fitted_Q_KF | 3 | 1 | 3 | 656 | 0.854741 | 0.529985 | 2.15082 | 3.33302 | 0.891768 | 0.89939 | 5.44077 | 7.0786 | 1.50106 | 1.83123 |
| 0000_20230322_081506 | Deterministic_CV | 1 | 1 | 3 | 656 | 0.159139 | 0.102726 | 0.385631 | 0.722822 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0000_20230322_081506 | Deterministic_CV | 3 | 1 | 3 | 656 | 0.882159 | 0.546327 | 2.23877 | 3.43544 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0000_20230322_081506 | Fixed_noise_KF | 1 | 1 | 3 | 656 | 0.138611 | 0.0899769 | 0.337841 | 0.630048 | 0.974085 | 0.990854 | 0.634486 | 0.825485 | 0.512601 | -1.06993 |
| 0000_20230322_081506 | Fixed_noise_KF | 3 | 1 | 3 | 656 | 0.840961 | 0.521378 | 2.12108 | 3.28887 | 0.949695 | 0.960366 | 14.2965 | 18.6002 | 2.43323 | 2.18382 |
| 0000_20230322_081506 | Joint_innovation_ML_KF | 1 | 1 | 3 | 656 | 0.120813 | 0.0786796 | 0.299145 | 0.546705 | 0.615854 | 0.678354 | 0.0143627 | 0.0186864 | 0.0771236 | 2.27406 |
| 0000_20230322_081506 | Joint_innovation_ML_KF | 3 | 1 | 3 | 656 | 0.807097 | 0.500157 | 2.03335 | 3.1716 | 0.588415 | 0.63872 | 0.374632 | 0.487407 | 0.393886 | 10.7622 |
| 0001_20230523_105516 | Data_fitted_Q_KF | 1 | 1 | 21 | 2398 | 0.137068 | 0.099749 | 0.276585 | 0.852547 | 0.959967 | 0.974145 | 0.27172 | 0.353515 | 0.335451 | -1.63685 |
| 0001_20230523_105516 | Data_fitted_Q_KF | 3 | 1 | 21 | 2398 | 0.699876 | 0.486865 | 1.31553 | 4.65016 | 0.952877 | 0.964137 | 5.80237 | 7.54906 | 1.55014 | 1.5349 |
| 0001_20230523_105516 | Deterministic_CV | 1 | 1 | 21 | 2398 | 0.147313 | 0.106897 | 0.295648 | 0.910009 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0001_20230523_105516 | Deterministic_CV | 3 | 1 | 21 | 2398 | 0.717532 | 0.497537 | 1.34955 | 4.8022 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0001_20230523_105516 | Fixed_noise_KF | 1 | 1 | 21 | 2398 | 0.130885 | 0.0953635 | 0.263684 | 0.810218 | 0.990826 | 0.994996 | 0.634487 | 0.825487 | 0.512602 | -1.09366 |
| 0001_20230523_105516 | Fixed_noise_KF | 3 | 1 | 21 | 2398 | 0.690452 | 0.480833 | 1.29131 | 4.58812 | 0.984153 | 0.987073 | 14.2965 | 18.6002 | 2.43323 | 2.0672 |
| 0001_20230523_105516 | Joint_innovation_ML_KF | 1 | 1 | 21 | 2398 | 0.11489 | 0.0839749 | 0.232773 | 0.712701 | 0.5196 | 0.576731 | 0.0135368 | 0.0176117 | 0.0748731 | 1.9173 |
| 0001_20230523_105516 | Joint_innovation_ML_KF | 3 | 1 | 21 | 2398 | 0.665335 | 0.464584 | 1.23267 | 4.44185 | 0.497498 | 0.554629 | 0.352907 | 0.459143 | 0.382295 | 7.19814 |
| 0002_20230523_111106 | Data_fitted_Q_KF | 1 | 1 | 22 | 2451 | 0.222667 | 0.146192 | 0.481114 | 1.94478 | 0.843737 | 0.878009 | 0.193232 | 0.251401 | 0.282884 | -0.621816 |
| 0002_20230523_111106 | Data_fitted_Q_KF | 3 | 1 | 22 | 2451 | 1.1572 | 0.766934 | 2.64551 | 6.39444 | 0.800082 | 0.827417 | 4.02024 | 5.23045 | 1.29031 | 2.96682 |
| 0002_20230523_111106 | Deterministic_CV | 1 | 1 | 22 | 2451 | 0.234346 | 0.15386 | 0.506641 | 2.05508 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0002_20230523_111106 | Deterministic_CV | 3 | 1 | 22 | 2451 | 1.17947 | 0.78182 | 2.70924 | 6.41496 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0002_20230523_111106 | Fixed_noise_KF | 1 | 1 | 22 | 2451 | 0.207662 | 0.136476 | 0.445339 | 1.81407 | 0.951448 | 0.97144 | 0.634487 | 0.825487 | 0.512602 | -0.797319 |
| 0002_20230523_111106 | Fixed_noise_KF | 3 | 1 | 22 | 2451 | 1.13382 | 0.751046 | 2.61361 | 6.32923 | 0.926153 | 0.940024 | 14.2965 | 18.6002 | 2.43323 | 2.47645 |
| 0002_20230523_111106 | Joint_innovation_ML_KF | 1 | 1 | 22 | 2451 | 0.182079 | 0.119876 | 0.390432 | 1.575 | 0.358629 | 0.410445 | 0.0104175 | 0.0135534 | 0.0656825 | 17.6227 |
| 0002_20230523_111106 | Joint_innovation_ML_KF | 3 | 1 | 22 | 2451 | 1.09273 | 0.723217 | 2.52484 | 6.32524 | 0.328845 | 0.375357 | 0.270924 | 0.352481 | 0.33496 | 29.7419 |
| 0003_20230523_111514 | Data_fitted_Q_KF | 1 | 1 | 14 | 3183 | 0.133587 | 0.0840507 | 0.308575 | 0.923299 | 0.944078 | 0.95853 | 0.26842 | 0.349223 | 0.333408 | -1.66831 |
| 0003_20230523_111514 | Data_fitted_Q_KF | 3 | 1 | 14 | 3183 | 0.753864 | 0.435909 | 1.85043 | 4.91192 | 0.923971 | 0.93591 | 5.72685 | 7.45081 | 1.54002 | 1.62899 |
| 0003_20230523_111514 | Deterministic_CV | 1 | 1 | 14 | 3183 | 0.144169 | 0.0903018 | 0.333366 | 1.00308 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0003_20230523_111514 | Deterministic_CV | 3 | 1 | 14 | 3183 | 0.776436 | 0.447516 | 1.88493 | 5.06339 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0003_20230523_111514 | Fixed_noise_KF | 1 | 1 | 14 | 3183 | 0.127191 | 0.080137 | 0.294861 | 0.883038 | 0.98869 | 0.995602 | 0.634487 | 0.825487 | 0.512602 | -1.10453 |
| 0003_20230523_111514 | Fixed_noise_KF | 3 | 1 | 14 | 3183 | 0.742102 | 0.429525 | 1.82354 | 4.84538 | 0.964499 | 0.978951 | 14.2965 | 18.6002 | 2.43323 | 2.10464 |
| 0003_20230523_111514 | Joint_innovation_ML_KF | 1 | 1 | 14 | 3183 | 0.110975 | 0.0701532 | 0.254369 | 0.771877 | 0.660383 | 0.706566 | 0.0144989 | 0.0188635 | 0.0774882 | 1.07672 |
| 0003_20230523_111514 | Joint_innovation_ML_KF | 3 | 1 | 14 | 3183 | 0.711377 | 0.412814 | 1.71508 | 4.70396 | 0.649702 | 0.687716 | 0.378212 | 0.492065 | 0.395764 | 7.87267 |

q_sequence_cluster_bootstrap.csv resamples the four existing out-of-fold sequence outputs without refitting; intervals are conditional and unstable. Track-macro and sequence-macro metrics are reported separately from correlated forecast-micro metrics. No naive frame-binomial CI is used.

Data-fitted Q optimizer runs and joint-ML convergence/messages/starting solutions are retained in models/q_effective_params.json. Boundary hits signal weak identifiability or smoothing assumptions, not a sensor-noise truth.

References: [Bayesian Filtering and Smoothing, authors' textbook](https://users.aalto.fi/~ssarkka/pub/bfs_book_2023_online.pdf); [SciPy chi-square quantiles](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html). Equations are implemented directly, with no external code copied.

## Independent implementation verification

{
  "passed": true,
  "OLS_spots": 64,
  "full_matrix_KF_forecasts_checked": 24,
  "max_OLS_position_difference_m": 9.947598300641403e-14,
  "max_KF_position_difference_m": 3.552713678800501e-15,
  "max_KF_covariance_difference_m2": 5.551115123125783e-17,
  "all_probabilistic_coverage_and_area_independently_recomputed": true,
  "all_overall_point_metrics_independently_recomputed": true,
  "R_mean_covariance_independently_recomputed": true,
  "frozen_predictions_params_original_inputs_unchanged": true
}
