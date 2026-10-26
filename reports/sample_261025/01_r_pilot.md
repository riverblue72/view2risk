# SPD R_pair_proxy pilot

Track-level leave-one-out: 8 development tracks, 1 held-out track; no frame shuffle.

Residual e = camera world XY - virtual-LiDAR world XY; no camera transform inversion or orthogonalization in this pilot.

Full-sample descriptive estimates (not an external evaluation):

| metric | value |
| --- | --- |
| n | 253 |
| bias_m | [0.06764941296809619, 0.0563976946639529] |
| covariance_m2 | [[0.017016474520828086, 0.0034660330824037265], [0.0034660330824037265, 0.009519132337001907]] |
| RMSE_m | 0.18518301729955286 |
| MAE_m | 0.15664702138968734 |
| median_m | 0.1359954127932981 |
| p90_m | 0.2829947440385015 |
| p95_m | 0.34334002873542974 |
| max_m | 0.5357067821498414 |

Covariance uses maximum-likelihood ddof=0 after subtraction of the fitted bias; uncentered zero-bias Gaussian uses E[eeᵀ].

LOTO metrics, macro over 9 test tracks:

| model | coverage90 | coverage95 | area90_m2 | area95_m2 | NLL |
| --- | --- | --- | --- | --- | --- |
| Empirical_track_bootstrap | 0.709017 | 0.821786 | 0.217578 | 0.292608 | N/A |
| Gaussian_with_bias | 0.686084 | 0.764572 | 0.176537 | 0.229679 | -0.773773 |
| Gaussian_zero_bias | 0.853836 | 0.871992 | 0.214845 | 0.27952 | -1.03562 |

Empirical model: resample complete development tracks, then draw a predictive residual from their pooled rows (5,000 particles/fold). Ellipse axes use particle covariance; 90/95 radial thresholds are empirical training-particle quantiles. No continuous empirical NLL is asserted. It is a demonstration, not robust density validation.

Cluster bootstrap: 2,000 whole-track resamples, conditional on this single sequence. Full-sample parameter confidence intervals are in models/r_pair_proxy_params.json.

| track_uid | sequence_id | pairs | n | RMSE_m | MAE_m | median_m | p90_m | p95_m | max_m | lag1_valid_pairs | dx_lag1 | dy_lag1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0058/003999 | 0058 | 162 | 162 | 0.183299 | 0.153713 | 0.136915 | 0.287976 | 0.353005 | 0.535707 | 157 | 0.276492 | 0.171279 |
| 0058/004001 | 0058 | 67 | 67 | 0.183401 | 0.156811 | 0.135115 | 0.27476 | 0.321326 | 0.521811 | 57 | 0.193166 | -0.0355113 |
| 0058/004011 | 0058 | 2 | 2 | 0.351433 | 0.31479 | 0.31479 | 0.439786 | 0.455411 | 0.471035 | 1 | N/A | N/A |
| 0058/004021 | 0058 | 1 | 1 | 0.218541 | 0.218541 | 0.218541 | 0.218541 | 0.218541 | 0.218541 | 0 | N/A | N/A |
| 0058/004033 | 0058 | 1 | 1 | 0.251445 | 0.251445 | 0.251445 | 0.251445 | 0.251445 | 0.251445 | 0 | N/A | N/A |
| 0058/004037 | 0058 | 2 | 2 | 0.238266 | 0.220765 | 0.220765 | 0.292469 | 0.301432 | 0.310395 | 1 | N/A | N/A |
| 0058/004039 | 0058 | 2 | 2 | 0.122722 | 0.0972531 | 0.0972531 | 0.157134 | 0.164619 | 0.172104 | 0 | N/A | N/A |
| 0058/004041 | 0058 | 1 | 1 | 0.270168 | 0.270168 | 0.270168 | 0.270168 | 0.270168 | 0.270168 | 0 | N/A | N/A |
| 0058/004043 | 0058 | 15 | 15 | 0.164293 | 0.147868 | 0.134863 | 0.218645 | 0.2676 | 0.337121 | 14 | 0.112623 | -0.175886 |

| field | spearman_rho |
| --- | --- |
| timestamp_gap_s | 0.0346797 |
| distance_to_sensor_m | -0.271403 |
| abs_timestamp_gap_s | 0.260682 |

Correlations are descriptive; dependent rows invalidate naive independent-frame significance. Timing differences are not compensated. Camera transform nonorthogonality and K/P projection disagreement remain unresolved. Shared 2D boxes and paired annotation dependencies prevent pure R_camera identification.

Distribution (서버 원본에서 확인: `../figures/r_distribution.png`)

Conditions (서버 원본에서 확인: `../figures/r_conditions_time.png`)
