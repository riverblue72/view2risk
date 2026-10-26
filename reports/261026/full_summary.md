# View2Risk 전체 데이터 확장 결과 — 261026

**기존 데이터 감사 MD의 미확보 전체 자료를 반영하고, 샘플 R/Q 파일럿과 같은 모델을 별도 전체 확장판으로 실행했다.** 기존 sample_audit 및 pilot_rq_261025는 수정하지 않았다.

R: SPD 인프라 11,275프레임, 34개 paired-data 시퀀스, 6개 교차로, 233개 시퀀스-트랙 그룹, 유효 주석쌍 10,109개. Q: Full01–05의 보행자 1,920트랙, 264시퀀스, 15촬영 날짜, 1,710,765관측. Samples는 합산하지 않았다.

## R_pair_proxy

수평 주석 차이 RMSE **0.298680 m**, 중앙값 0.139037 m, p95 0.475109 m. 평균 편향과 공분산(m², ddof0):

```text
mean = [-0.01143208  0.00467011]
R_pair_proxy =
[[ 0.03732695 -0.00430091]
 [-0.00430091  0.05173044]]
```

교차로를 하나씩 제외하는 검증으로 같은 장소의 인접 클립이 개발/평가 양쪽에 섞이지 않게 했다. 이것은 순수 R_camera나 검출기 정확도가 아니다. 제공 calibration·투영의 미해결 사항은 유지했다. 전체 source QC와 사례 그림은 spd_* 표와 figures/spd_case_*.png에 있다.

## Q_effective 및 recorded-trajectory 검증

기록 날짜를 통째로 묶은5-fold 홀드아웃이다. 모델 방정식·고정 잡음 후보·학습 q 범위·1초/3초 horizon·유효 구간·과거 속도 창·행동 후보 임계값은 샘플판과 같다. 모델별 예측 시작점은 공통이며 실제 평가 대상은 1,906트랙 / 264시퀀스 / 15날짜다.

| model | horizon_s | test_recording_dates | test_sequences | test_tracks | predictions | RMSE_m | MAE_m | coverage90 | coverage95 | mean_area95_m2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data_fitted_Q_KF | 1 | 15 | 264 | 1906 | 265578 | 0.164676 | 0.105324 | 0.923401 | 0.940959 | 0.331172 |
| Data_fitted_Q_KF | 3 | 15 | 264 | 1906 | 265578 | 0.914123 | 0.577593 | 0.883115 | 0.904288 | 7.03841 |
| Deterministic_CV | 1 | 15 | 264 | 1906 | 265578 | 0.176965 | 0.113012 | N/A | N/A | N/A |
| Deterministic_CV | 3 | 15 | 264 | 1906 | 265578 | 0.938623 | 0.592674 | N/A | N/A | N/A |
| Fixed_noise_KF | 1 | 15 | 264 | 1906 | 265578 | 0.156409 | 0.100131 | 0.977999 | 0.986433 | 0.825487 |
| Fixed_noise_KF | 3 | 15 | 264 | 1906 | 265578 | 0.899963 | 0.568676 | 0.954902 | 0.969022 | 18.6002 |
| Joint_innovation_ML_KF | 1 | 15 | 264 | 1906 | 265578 | 0.136755 | 0.0877205 | 0.577066 | 0.626829 | 0.0192069 |
| Joint_innovation_ML_KF | 3 | 15 | 264 | 1906 | 265578 | 0.865232 | 0.546707 | 0.530364 | 0.577111 | 0.501102 |

coverage는0~1 비율, 면적m²다. Deterministic CV의 확률영역은 N/A. 원시 예측 전체는 data/imptc_cv_residuals.parquet. 날짜·시퀀스·트랙 macro 및 날짜 bootstrap95%CI는 reports/q_* 표에 따로 저장했다. 미래 관측 R을 포함한 영역을 기록된 궤적에 비교했으며 독립 물리 참값 검증이 아니다.

정지·가감속·회전·센서 전환 진단, 평활화0.12/0.4/1초 민감도, Gaussian 꼬리와 큰 오차8사례를 제공한다. 외부 Test에 맞춰 영역을 재보정하거나 모델 설정을 바꾸지 않았다.

## 판단과 남은 작업

전체 자료에서도 R/Q 추정 파이프라인은 실행 가능하다. 추가된 자료는 표본·조건 지원을 늘리지만, R의 독립 기준 라벨과 Q의 실측 참값 부족을 해결하지 않는다. 예측영역 포함률과 크기를 함께 확인해야 하며 좋은 점 RMSE가 적절한 불확실성을 뜻하지 않는다. 최종 조건부 모델 선정·실제 R/Q 통합 주장·신호 제어·G95는 보류한다.

## 재현성과 위치

protocol_full_261026.md 및 protocol.json은 full 확장 전에 고정했다. data/splits.json, models/, reports/kernel_reuse.json, input_sha256.json, environment.json, manifest.json에 분할·파라미터·재사용 코드·입력/결과 hash와 버전을 기록했다. 실행은 `sbatch run.sh`이며 완료된 결과 위 재실행은 차단한다. GPU는 사용하지 않았다.

**검증 통과.** 상세: 01_r_full.md, 02_q_full.md, 03_validation.md, limitations.md.

## 고정된 평가 결과 해석

- 1초 Q-fitted: RMSE 0.1647 m, 목표95% 영역의 실제 포함률 94.10% (목표 대비 -0.90%p), 평균 면적 0.3312 m². Joint innovation-ML 포함률은 62.68%다.
- 3초 Q-fitted: RMSE 0.9141 m, 목표95% 영역의 실제 포함률 90.43% (목표 대비 -4.57%p), 평균 면적 7.0384 m². Joint innovation-ML 포함률은 57.71%다.

위 포함률 차이는 현재 가정의 보정 상태를 보여주는 수치이며, 결과를 보고 추정 범위/평가 기준을 변경하지 않았다.

## 보충 감사와 공간 검증

공식 IMPTC semantic ground map(100만 점)을 추가 확보해 같은 로컬 좌표에서 궤적과 대조했다. 0.25m 이내 지도점이 있는 status2 관측의 ground code 일치율은 **99.47%**다. 같은 데이터 처리에서 생성된 정보일 수 있어 독립 GT 정확도로 해석하지 않는다. 지도와 궤적 중첩 그림 및 자세한 표는 [04_geometry_context_tfd.md](04_geometry_context_tfd.md)에 있다.

확정 완전/부분 횡단 수와 개별 트랙 신호 배정은 검증된 진입/이탈 정의가 없어 N/A로 유지했다. TFD Example도 별도 감사했고 IMPTC와 합산하지 않았다.

전체 감사 요약은 [data_audit_full.md](data_audit_full.md), 컬럼 사전은 [data_dictionary.csv](../../results/261026/details/data_dictionary.csv), 후보 결정은 [factor_decision_table.csv](../../results/261026/details/factor_decision_table.csv)를 참조한다.

R의 기존 Example253쌍은 전체 데이터와의 잔차 차이가0으로 재현됐다. 전체 R RMSE0.298680m, 중앙값0.139037m, p95=0.475109m, 최대7.102860m이므로 큰 꼬리 사례를 함께 봐야 한다. 샘플0.185183m와의 차이를 기존 샘플 손상이나 카메라 모델 성능 변화로 해석하지 않는다.
