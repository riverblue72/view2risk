# IMPTC Q_effective / motion-model-residual pilot

Only IMPTC Samples. Status=2 finite XYZ segments, original source order, break at dt<=0 or dt>60ms. No SPD parameters, signal, weather, age, or violation labels enter fitting.

Common paired 1s/3s origins: at least 1s valid past, 0.2s stride, nearest actual future observation within 20.1ms. Both horizons must exist in the same continuous segment; actual timestamp separation is used. End-of-track origins with no 3s future are excluded for every model and both horizons. This restriction is recorded and limits short/ending-track evaluation.

| sequence_id | valid_segments | tracks | status2_rows |
| --- | --- | --- | --- |
| 0000_20230322_081506 | 3 | 3 | 3574 |
| 0001_20230523_105516 | 36 | 22 | 16019 |
| 0002_20230523_111106 | 26 | 22 | 15618 |
| 0003_20230523_111514 | 22 | 14 | 19103 |

Evaluable tracks: 60; unique origins: 8688; predictions per horizon: 8688.

Deterministic CV: current measured position + actual horizon × causal OLS XY velocity from past 0.4s. No future smoothing. Sensitivity windows 0.12/0.4/1.0s use identical origins.

State [x,y,vx,vy]. F(dt)=[[I,dt I],[0,I]]. Continuous white-acceleration Q(dt)=q[[dt³/3 I,dt²/2 I],[dt²/2 I,dt I]]. q units m²/s³, R=r I units m². Forecast recorded-position variance includes filtered-state uncertainty, integrated future q, and future r. Initial velocity=0, P=diag(r,r,4,4), with 1s warmup. Isotropy and Gaussian white noise are modeling assumptions.

Outer LOSO: 4 tests, each with 3 development sequences. Fixed noise uses a predeclared grid (observation SD .01/.05/.2m; q .01/.1/1m²/s³), scored only on development sequences using sequence/horizon-macro forecast NLL. Since candidates have no learned parameters, scoring each development sequence is equivalent to the specified inner validation folds. Data-fitted Q fixes R to that selected grid value and estimates q from the same 3 development sequences using 1s/3s forecast NLL. The optional joint baseline estimates effective R and q by Kalman innovation ML with three initializations, using only IMPTC development trajectories; this is not EM and not a uniquely identified physical R/Q.

No held-out sequence is used in parameter selection, interval calibration, threshold choice, or convergence decisions. No model is selected as a final winner from these tests.

## Outer-test metrics by sequence

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

## Overall prediction micro

| model | horizon_s | test_sequences | test_tracks | predictions | RMSE_m | MAE_m | p95_error_m | max_error_m | coverage90 | coverage95 | mean_area90_m2 | mean_area95_m2 | mean_radius95_m | NLL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data_fitted_Q_KF | 1 | 4 | 60 | 8688 | 0.165295 | 0.106719 | 0.346419 | 1.94478 | 0.918854 | 0.938881 | 0.247174 | 0.321581 | 0.319125 | -1.35876 |
| Data_fitted_Q_KF | 3 | 4 | 60 | 8688 | 0.881109 | 0.550463 | 1.97084 | 6.39444 | 0.894567 | 0.910336 | 5.24464 | 6.82343 | 1.46943 | 1.99571 |
| Deterministic_CV | 1 | 4 | 60 | 8688 | 0.176096 | 0.113751 | 0.371654 | 2.05508 | N/A | N/A | N/A | N/A | N/A | N/A |
| Deterministic_CV | 3 | 4 | 60 | 8688 | 0.902326 | 0.563095 | 2.03941 | 6.41496 | N/A | N/A | N/A | N/A | N/A | N/A |
| Fixed_noise_KF | 1 | 4 | 60 | 8688 | 0.155794 | 0.100977 | 0.324327 | 1.81407 | 0.97767 | 0.98826 | 0.634487 | 0.825487 | 0.512602 | -1.01225 |
| Fixed_noise_KF | 3 | 4 | 60 | 8688 | 0.865689 | 0.541327 | 1.92909 | 6.32923 | 0.957988 | 0.968808 | 14.2965 | 18.6002 | 2.43323 | 2.20518 |
| Joint_innovation_ML_KF | 1 | 4 | 60 | 8688 | 0.136419 | 0.0886395 | 0.284436 | 1.575 | 0.533034 | 0.58506 | 0.0130716 | 0.0170066 | 0.0734084 | 6.06697 |
| Joint_innovation_ML_KF | 3 | 4 | 60 | 8688 | 0.832845 | 0.521267 | 1.85822 | 6.32524 | 0.512546 | 0.559162 | 0.34069 | 0.443248 | 0.374751 | 14.0743 |

## Sequence macro

| model | horizon_s | RMSE_m | MAE_m | coverage90 | coverage95 | mean_area95_m2 | NLL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Data_fitted_Q_KF | 1 | 0.159854 | 0.106175 | 0.918653 | 0.938189 | 0.321769 | -1.38015 |
| Data_fitted_Q_KF | 3 | 0.86642 | 0.554923 | 0.892175 | 0.906713 | 6.82723 | 1.99049 |
| Deterministic_CV | 1 | 0.171242 | 0.113446 | N/A | N/A | N/A | N/A |
| Deterministic_CV | 3 | 0.888899 | 0.5683 | N/A | N/A | N/A | N/A |
| Fixed_noise_KF | 1 | 0.151087 | 0.100488 | 0.976262 | 0.988223 | 0.825487 | -1.01636 |
| Fixed_noise_KF | 3 | 0.851835 | 0.545695 | 0.956125 | 0.966603 | 18.6002 | 2.20803 |
| Joint_innovation_ML_KF | 1 | 0.132189 | 0.088171 | 0.538616 | 0.593024 | 0.0171787 | 5.72269 |
| Joint_innovation_ML_KF | 3 | 0.819135 | 0.525193 | 0.516115 | 0.564105 | 0.447774 | 13.8937 |

## Track macro

| model | horizon_s | RMSE_m | MAE_m | coverage90 | coverage95 | mean_area95_m2 | NLL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Data_fitted_Q_KF | 1 | 0.160469 | 0.123246 | 0.89775 | 0.921041 | 0.314043 | -1.22163 |
| Data_fitted_Q_KF | 3 | 0.85126 | 0.643789 | 0.870546 | 0.890233 | 6.65245 | 2.19681 |
| Deterministic_CV | 1 | 0.171043 | 0.131243 | N/A | N/A | N/A | N/A |
| Deterministic_CV | 3 | 0.870839 | 0.658367 | N/A | N/A | N/A | N/A |
| Fixed_noise_KF | 1 | 0.151718 | 0.116669 | 0.974262 | 0.986389 | 0.825487 | -0.961833 |
| Fixed_noise_KF | 3 | 0.837409 | 0.63319 | 0.951898 | 0.965739 | 18.6002 | 2.27489 |
| Joint_innovation_ML_KF | 1 | 0.133109 | 0.102629 | 0.450258 | 0.5092 | 0.0164695 | 8.2121 |
| Joint_innovation_ML_KF | 3 | 0.806933 | 0.610027 | 0.415617 | 0.46812 | 0.429129 | 17.2597 |

RMSE=sqrt(mean(||recorded-pred||²)); MAE=mean(||recorded-pred||), both Euclidean metres. Coverage uses Mahalanobis² <= chi²(2) quantile; area=π chi² sqrt(det(S)). Deterministic intervals are N/A. All forecasts target recorded trajectories, not independent physical GT. Dense origins and overlapping horizons are correlated.

## Smoothing sensitivity

| sequence_id | horizon_s | causal_window_s | n | RMSE_m | MAE_m | median_m | p90_m | p95_m | max_m | residual_cov_xx_m2 | residual_cov_xy_m2 | residual_cov_yy_m2 | naive_effective_q_trace_proxy_m2_s3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0000_20230322_081506 | 1 | 0.12 | 656 | 0.129949 | 0.0844643 | 0.0549411 | 0.189893 | 0.319168 | 0.587124 | 0.00879578 | 2.02397e-05 | 0.00792802 | 0.0250857 |
| 0000_20230322_081506 | 1 | 0.4 | 656 | 0.159139 | 0.102726 | 0.0639285 | 0.241057 | 0.385631 | 0.722822 | 0.0132611 | 9.18157e-05 | 0.01181 | 0.0376066 |
| 0000_20230322_081506 | 1 | 1 | 656 | 0.214999 | 0.136513 | 0.0817508 | 0.319026 | 0.520199 | 0.951463 | 0.02455 | 0.000529574 | 0.0211584 | 0.0685626 |
| 0000_20230322_081506 | 3 | 0.12 | 656 | 0.825025 | 0.511336 | 0.282906 | 1.40545 | 2.07137 | 3.23613 | 0.376119 | 0.0330966 | 0.296245 | 0.0373536 |
| 0000_20230322_081506 | 3 | 0.4 | 656 | 0.882159 | 0.546327 | 0.299364 | 1.52396 | 2.23877 | 3.43544 | 0.432081 | 0.0409883 | 0.335996 | 0.042671 |
| 0000_20230322_081506 | 3 | 1 | 656 | 0.991794 | 0.611919 | 0.321442 | 1.75982 | 2.54042 | 3.82915 | 0.552462 | 0.0624116 | 0.416561 | 0.0538346 |
| 0001_20230523_105516 | 1 | 0.12 | 2398 | 0.121935 | 0.0889755 | 0.0669964 | 0.188328 | 0.246483 | 0.76189 | 0.0077503 | 0.00286256 | 0.00709569 | 0.022269 |
| 0001_20230523_105516 | 1 | 0.4 | 2398 | 0.147313 | 0.106897 | 0.0794294 | 0.228968 | 0.295648 | 0.910009 | 0.0112855 | 0.00421456 | 0.010381 | 0.0324997 |
| 0001_20230523_105516 | 1 | 1 | 2398 | 0.195319 | 0.140004 | 0.1028 | 0.299303 | 0.39388 | 1.24196 | 0.019766 | 0.00758259 | 0.0183123 | 0.0571174 |
| 0001_20230523_105516 | 3 | 0.12 | 2398 | 0.676656 | 0.471894 | 0.341774 | 0.997119 | 1.26168 | 4.48431 | 0.240688 | 0.0961247 | 0.215501 | 0.0253438 |
| 0001_20230523_105516 | 3 | 0.4 | 2398 | 0.717532 | 0.497537 | 0.356185 | 1.05203 | 1.34955 | 4.8022 | 0.270611 | 0.109656 | 0.242272 | 0.0284935 |
| 0001_20230523_105516 | 3 | 1 | 2398 | 0.795456 | 0.543965 | 0.384412 | 1.14054 | 1.49852 | 5.27265 | 0.332786 | 0.139978 | 0.297256 | 0.0350023 |
| 0002_20230523_111106 | 1 | 0.12 | 2451 | 0.193176 | 0.127029 | 0.0835147 | 0.280207 | 0.413552 | 1.69728 | 0.0209339 | 0.0016201 | 0.0163513 | 0.0559278 |
| 0002_20230523_111106 | 1 | 0.4 | 2451 | 0.234346 | 0.15386 | 0.102879 | 0.343706 | 0.506641 | 2.05508 | 0.0309133 | 0.00224287 | 0.0239551 | 0.0823027 |
| 0002_20230523_111106 | 1 | 1 | 2451 | 0.312873 | 0.204975 | 0.135566 | 0.464195 | 0.678485 | 2.57878 | 0.0557706 | 0.00360765 | 0.0420194 | 0.146685 |
| 0002_20230523_111106 | 3 | 0.12 | 2451 | 1.11094 | 0.735546 | 0.466942 | 1.75048 | 2.54779 | 6.33554 | 0.728677 | 0.0193875 | 0.504254 | 0.0684962 |
| 0002_20230523_111106 | 3 | 0.4 | 2451 | 1.17947 | 0.78182 | 0.489024 | 1.85764 | 2.70924 | 6.41496 | 0.824275 | 0.0203826 | 0.56531 | 0.0771992 |
| 0002_20230523_111106 | 3 | 1 | 2451 | 1.31421 | 0.872617 | 0.530594 | 2.12173 | 3.08151 | 6.36456 | 1.03282 | 0.0184684 | 0.692043 | 0.0958256 |
| 0003_20230523_111514 | 1 | 0.12 | 3183 | 0.118198 | 0.0745706 | 0.0421849 | 0.174915 | 0.274923 | 0.802699 | 0.00673808 | 0.00146828 | 0.0072265 | 0.0209469 |
| 0003_20230523_111514 | 1 | 0.4 | 3183 | 0.144169 | 0.0903018 | 0.0511913 | 0.213312 | 0.333366 | 1.00308 | 0.010022 | 0.00229941 | 0.0107535 | 0.0311632 |
| 0003_20230523_111514 | 1 | 1 | 3183 | 0.195684 | 0.12009 | 0.0667732 | 0.285774 | 0.458068 | 1.34446 | 0.0184723 | 0.00476605 | 0.0198003 | 0.057409 |
| 0003_20230523_111514 | 3 | 0.12 | 3183 | 0.725479 | 0.420427 | 0.215796 | 1.03453 | 1.75711 | 4.77622 | 0.254878 | 0.0799041 | 0.270957 | 0.029213 |
| 0003_20230523_111514 | 3 | 0.4 | 3183 | 0.776436 | 0.447516 | 0.225139 | 1.12087 | 1.88493 | 5.06339 | 0.291453 | 0.0939841 | 0.310835 | 0.0334604 |
| 0003_20230523_111514 | 3 | 1 | 3183 | 0.879132 | 0.499662 | 0.238787 | 1.29092 | 2.19602 | 5.57315 | 0.372414 | 0.127335 | 0.399679 | 0.0428941 |

The naive 3*trace(Cov(residual))/(2*h³) column is only a diagnostic scale. It omits state/observation uncertainty and bias; it is NOT the fitted q or Q_true. Smoothing changes causal velocity and residual dispersion, demonstrating dependence on representation. No centered or future-using smoother was evaluated.

## Control / candidate diagnostics

q_condition_diagnostics.csv keeps track/sequence/prediction support for source_type, past-only sensor switch, stop<=.3m/s, acceleration>.5m/s², deceleration<-.5m/s², turn>45deg/s (both speeds>.2m/s). These are noisy past-window proxies, not behavioral GT, and are not used for conditional model fitting. At overlapping conditions the same forecast can appear in several diagnostic rows.

## Gaussian failures

| sequence_id | track_uid | error_m | mahalanobis2 | covered95 | radius95_m |
| --- | --- | --- | --- | --- | --- |
| 0002_20230523_111106 | 0002_20230523_111106/001 | 6.39444 | 147.146 | 0 | 1.29031 |
| 0002_20230523_111106 | 0002_20230523_111106/016 | 5.20103 | 97.347 | 0 | 1.29031 |
| 0002_20230523_111106 | 0002_20230523_111106/002 | 4.92054 | 87.1303 | 0 | 1.29031 |
| 0003_20230523_111514 | 0003_20230523_111514/007 | 4.91192 | 60.9511 | 0 | 1.54002 |
| 0002_20230523_111106 | 0002_20230523_111106/015 | 4.68905 | 79.125 | 0 | 1.29031 |
| 0001_20230523_105516 | 0001_20230523_105516/002 | 4.65016 | 53.9173 | 0 | 1.55014 |

Failure plots are selected after evaluation for inspection only. Green future trajectories are evaluation references and never inputs to filtering. Observation/initial-state/motion errors remain mixed.

Coverage (서버 원본에서 확인: `../figures/q_coverage.png`)

![Sharpness](../../figures/261026/q_sharpness.png)

Gaussian tails (서버 원본에서 확인: `../figures/q_gaussian_tail.png`)

Smoothing (서버 원본에서 확인: `../figures/q_smoothing_sensitivity.png`)
