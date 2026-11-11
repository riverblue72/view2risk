# R_UQ_FINAL_DECISION — View2Risk 최종 판정

## 최종 결정

**기존 최종 웹과 Legacy R+Q를 보존한다. 새로운 모델로 교체하지 않는다.** 보정 XY + 공식 차분/인과적 Heading은 IMPTC에서 의미 있는 부분 개선을 보였지만, inD의 95% Coverage와 점 오차까지 일관되게 개선하지 못했다. 두 데이터셋 전체에서 최종 UQ 개선이 입증됐다고 주장하지 않는다. 이 비교로 추가 모델 탐색을 종료하고 기존 결과의 발표 준비로 전환한다.

서버 별도 작업 경로: `<private-server-path>`. 원래 `final_uq/`, 공식 전체 Test, 체크포인트와 원본 데이터는 변경하지 않았다. 웹 파일을 포함한 release hash를 시작·종료 시 대조했다. 신경망 추가·학습·GPU 잡·신규 데이터셋은 없다.

## 1. 세 가지 방법과 공식 전처리의 적용 한계

1. **Legacy FFBS:** CV4 위치·속도 posterior에서 위치만 꺼내고, 기존 causal adapter로 위치 차분 속도/가속도/Heading을 생성한다. 기존 릴리스의 기준이다.
2. **CA6 직접 상태:** 기존 실험의 고정 q_jerk=0.05m²/s⁵, velocity prior variance=1(m/s)²를 유지한다. 같은 FFBS 상태에서 위치·속도·가속도·Heading을 직접 전달한다.
3. **보정 XY + 공식 전처리:** CA6 FFBS 위치를 사용하되 공식 DD-MDN과 같은 위치 차분 `v=diff(X)/0.1`, `a=diff(v)/0.1`, 첫 값을 복제하는 경계 규칙으로 6개 입력 특징을 생성한다. Heading은 공식 Motion_Classifier의 과거 판단 로직을 사용한다.

**공식 offline Heading에는 정지/애매한 움직임에서 미래 GT를 사용하는 분기가 있다.** 온라인에서 이를 그대로 재현하면 누출이 발생한다. 따라서 실제 미래 GT를 전달하지 않고 마지막 과거 위치의 상수 padding으로 그 미래 분기를 차단한다. Padding은 모델 예측·합성 성능 데이터가 아니며 모델의 미래 입력으로 전달되지 않는다. 이는 “공식 차분 + 인과적 공식 Heading”이며, 미래를 사용하는 학습 전처리와 완전히 동일한 분포라고 주장하지 않는다. 이 잔여 차이는 해소되지 않은 한계다.

각 샘플의 Heading·translation·ego 회전·지도 crop·주변 객체 변환·출력 역변환은 같은 샘플 좌표계를 쓴다. 타깃만 SPD 합성 오차를 받으며 주변 객체와 지도 자체는 정확하다고 가정한다. 0.1초 차분이 잡음을 증폭할 수 있다는 사실은 보정 XY에서도 완전히 없어지지 않는다.

## 2. Train/Validation 선택과 별도 Calibration

| dataset | phase | manifest windows | recordings |
|---|---|---|---|
| IMPTC | train | 79 | 12 |
| IMPTC | validation | 12 | 11 |
| IMPTC | calibration | 16 | 16 |
| inD | train | 11 | 11 |
| inD | validation | 5 | 5 |
| inD | calibration | 5 | 5 |

IMPTC는 기존 날짜별 Train/Validation/Calibration/Test manifest를 유지했다. inD는 공식 Train/Test를 유지하고 기존 Eval 10개 recording 중 앞 5개를 Validation, 나머지 5개를 Calibration으로 고정 분리했다. 현재 실험의 Train/Validation/Calibration/Test recording은 서로 겹치지 않는다. 다만 과거 실험에서 inD Eval과 기존 Test가 이미 여러 번 사용됐으므로, 이를 완전히 새롭고 한 번만 사용한 외부 검증이라고 주장하지 않는다.

Validation 후보는 Legacy, 고정 CA6 직접 상태, XY 공식 전처리의 q_jerk {0.05,0.5,5}m²/s⁵ × velocity prior variance {1,25}(m/s)²이다. 가속도 prior variance=1(m/s²)², 위치 prior variance=1e6m², SPD Train Gaussian bias/covariance, seed, FFBS 8개, 모델 가중치는 고정했다. 기존 q_acceleration=0.5m²/s³와 새 q_jerk의 숫자를 같은 단위로 비교하지 않는다.

관측 Innovation NLL은 `reports/*_innovation.json`에 Train/Validation별로 기록했다. 후보 선택은 **미래 DD-MDN Validation NLL**을 사용하되 Coverage95≥85%, |Coverage68−68%|≤20%p, 영역≤Legacy의 2배라는 사전 조건을 함께 적용했다. 통과 후보 중 최소 미래 NLL을 선택했고 fallback은 두 데이터셋 모두 없었다. 이 기준은 실험 코드/plan에 Test 전에 기록했다. 완벽한 다목적 최적화를 보장하는 기준은 아니다.

선택 전 공통 GT 가용성 검사에서 IMPTC의 12개 예정 Validation 사례 중 미래가 끊긴 2개를 모든 후보에서 동일 제외했다. 실제 미래 평가 Validation은 IMPTC 10개, inD 5개다. 완전한 전체 Validation 평가가 아닌 고정 소규모 검토다. 최초 None-GT 오류 로그를 보존했고, 후보 성능을 보고 제외한 것은 아니다.

### Validation의 모든 후보 — 동일 코호트

| dataset | method | origins/events | ADE m | FDE m | NLL nats | Coverage68 % | Coverage95 % | Area95 m² |
|---|---|---|---|---|---|---|---|---|
| IMPTC | direct | 10/10 | 1.963 | 3.395 | 2.397 | 66.25 | 90.00 | 25.73 |
| IMPTC | legacy | 10/10 | 3.397 | 5.695 | 2.884 | 97.50 | 100.00 | 118.59 |
| IMPTC | xy_q0.05_p1.0 | 10/10 | 1.965 | 3.465 | 2.330 | 67.50 | 90.00 | 26.09 |
| IMPTC | xy_q0.05_p25.0 | 10/10 | 2.010 | 3.505 | 2.561 | 63.75 | 90.00 | 28.59 |
| IMPTC | xy_q0.5_p1.0 | 10/10 | 2.030 | 3.491 | 2.430 | 70.00 | 90.00 | 31.57 |
| IMPTC | xy_q0.5_p25.0 | 10/10 | 2.280 | 4.012 | 2.610 | 66.25 | 90.00 | 34.57 |
| IMPTC | xy_q5.0_p1.0 | 10/10 | 2.648 | 4.492 | 3.064 | 76.25 | 95.00 | 66.40 |
| IMPTC | xy_q5.0_p25.0 | 10/10 | 3.205 | 5.467 | 3.322 | 70.00 | 92.50 | 70.63 |
| inD | direct | 5/5 | 1.156 | 1.646 | 2.149 | 75.00 | 90.00 | 27.71 |
| inD | legacy | 5/5 | 1.465 | 2.133 | 2.099 | 90.00 | 97.50 | 45.87 |
| inD | xy_q0.05_p1.0 | 5/5 | 0.825 | 1.088 | 2.153 | 70.00 | 90.00 | 26.92 |
| inD | xy_q0.05_p25.0 | 5/5 | 1.514 | 2.451 | 2.273 | 82.50 | 90.00 | 26.61 |
| inD | xy_q0.5_p1.0 | 5/5 | 1.572 | 2.711 | 2.126 | 75.00 | 90.00 | 29.64 |
| inD | xy_q0.5_p25.0 | 5/5 | 1.304 | 2.166 | 2.059 | 80.00 | 90.00 | 29.58 |
| inD | xy_q5.0_p1.0 | 5/5 | 1.434 | 2.365 | 2.063 | 85.00 | 92.50 | 48.26 |
| inD | xy_q5.0_p25.0 | 5/5 | 0.639 | 1.050 | 2.385 | 85.00 | 92.50 | 50.35 |

### 입력 분포 일치만 비교하는 동일 필터 통제

| dataset | method | origins/events | ADE m | FDE m | NLL nats | Coverage68 % | Coverage95 % | Area95 m² |
|---|---|---|---|---|---|---|---|---|
| IMPTC | direct | 10/10 | 1.963 | 3.395 | 2.397 | 66.25 | 90.00 | 25.73 |
| IMPTC | xy_q0.05_p1.0 | 10/10 | 1.965 | 3.465 | 2.330 | 67.50 | 90.00 | 26.09 |
| inD | direct | 5/5 | 1.156 | 1.646 | 2.149 | 75.00 | 90.00 | 27.71 |
| inD | xy_q0.05_p1.0 | 5/5 | 0.825 | 1.088 | 2.153 | 70.00 | 90.00 | 26.92 |

이 표는 q/prior가 같은 CA6 직접 입력과 공식 XY 차분의 효과를 구분한다. Test에서 선택된 inD XY 후보는 q/prior도 달라졌으므로 그 전체 차이를 전처리 변경 하나의 인과적 효과로 해석하면 안 된다.

### 동결된 후보

| dataset | 선택 | q_jerk m²/s⁵ | velocity prior variance (m/s)² | 동결 시점 |
|---|---|---|---|---|
| IMPTC | xy_q0.05_p1.0 | 0.05 | 1.0 | Calibration/Test 이전 |
| inD | xy_q0.5_p25.0 | 0.5 | 25.0 | Calibration/Test 이전 |

`configs/frozen_candidates.json`의 hash를 보정·Test 전후 확인했다. 이 시점 이후 모델 후보·q·prior를 바꾸지 않았다.

## 3. 확률 Calibration

각 데이터셋의 동결된 후보를 별도 Calibration 분할에서만 적합했다. Gaussian 각 component의 covariance를 `Σ' = s²Σ`로 바꾸는 양의 SD 배율 s 하나를 Calibration 미래 위치 NLL로 선택했다. 범위 [0.25,16]도 Test 전에 고정했다. 평균·정규화된 혼합 가중치·이력 샘플 가중치 1/8은 유지했다. discrete hypothesis의 비정규화 confidence를 확률로 변환하지 않았다.

시점별 2D mixture와 joint 16D anchor mixture에 **같은 s**를 적용했다. joint covariance는 전체 16×16 행렬을 양수배하므로 정상적인 Gaussian mixture와 시간 공분산 구조를 유지한다. 양정치·가중치 합 1을 독립 검사했다. 두 head가 처음부터 별도로 학습된 DD-MDN이므로 두 분포의 marginal이 서로 완전히 같아졌다고 주장하지 않는다. Calibration 목표는 시점별 위치 NLL이며 joint trajectory NLL과 횡단 완료확률은 보정 성능 검증 대상이 아니다.

평균과 discrete 대표 경로를 바꾸지 않으므로 Calibration 전후 ADE/FDE가 동일하다. 해당 불변성을 검사했다. 원래 hypothesis confidence 순서는 표시용으로 유지하며 “보정된 path 발생확률”로 해석하지 않는다.

| dataset | Calibration n | SD multiplier s | fit 전 NLL | fit 후 NLL |
|---|---|---|---|---|
| IMPTC | 16 | 2.084825 | 2.528 | 2.141 |
| inD | 5 | 1.300150 | 1.801 | 1.763 |

### Calibration 적합 데이터 — 독립 성능 증거가 아님

| dataset | method | origins/events | ADE m | FDE m | NLL nats | Coverage68 % | Coverage95 % | Area95 m² |
|---|---|---|---|---|---|---|---|---|
| IMPTC | selected_calibrated | 16/16 | 1.200 | 2.039 | 2.141 | 85.16 | 97.66 | 65.51 |
| IMPTC | selected_raw | 16/16 | 1.200 | 2.039 | 2.528 | 60.94 | 86.72 | 25.61 |
| inD | selected_calibrated | 5/5 | 1.186 | 1.999 | 1.763 | 80.00 | 95.00 | 30.62 |
| inD | selected_raw | 5/5 | 1.186 | 1.999 | 1.801 | 75.00 | 92.50 | 23.47 |

Calibration 데이터에서 좋아진 수치는 적합 결과일 뿐이다. 특히 inD 5개 recording의 5개 사례는 매우 작고 모든 상황을 대표하지 않는다. Calibration 이후 Test로 s를 다시 조정하지 않았다.

## 4. 마지막 고정 Test 비교

기존 IMPTC 54 origin/6 events/3 recordings와 inD 99 origin/11 tracks/11 recordings, 합계 153개 origin을 동일 seed·동일 가중치로 비교했다. IID SPD Train R_proxy를 타깃 과거 위치에 적용했다. 출력은 +0.5~4초 8점이다. ADE/Coverage/NLL/면적은 horizon 평균, FDE는 +4초다. 반복 origin은 독립적인 사람이 아니고 Test는 역사적으로 재사용된 탐색 자료다.

| dataset | method | origins/events | ADE m | FDE m | NLL nats | Coverage68 % | Coverage95 % | Area95 m² |
|---|---|---|---|---|---|---|---|---|
| IMPTC | direct | 54/6 | 1.855 | 3.294 | 3.378 | 51.16 | 79.63 | 31.16 |
| IMPTC | legacy | 54/6 | 3.087 | 5.328 | 3.410 | 89.35 | 100.00 | 149.56 |
| IMPTC | selected_calibrated | 54/6 | 1.683 | 2.961 | 2.733 | 80.79 | 95.83 | 83.91 |
| IMPTC | selected_raw | 54/6 | 1.683 | 2.961 | 3.268 | 52.31 | 81.02 | 31.30 |
| inD | direct | 99/11 | 1.805 | 3.074 | 2.671 | 64.39 | 86.36 | 29.19 |
| inD | legacy | 99/11 | 1.968 | 3.341 | 2.610 | 80.05 | 95.71 | 48.36 |
| inD | selected_calibrated | 99/11 | 2.026 | 3.501 | 2.524 | 74.24 | 90.78 | 41.46 |
| inD | selected_raw | 99/11 | 2.026 | 3.501 | 2.646 | 66.67 | 88.76 | 31.37 |

### 해석

- IMPTC: XY 후보 자체가 CA6 직접 상태보다 점 오차·NLL을 일부 개선했다. Calibration으로 95% Coverage가 81.02%→95.83%, NLL이 3.268→2.733으로 바뀌었다. Legacy보다 ADE/NLL/면적과 목표 Coverage 거리가 개선됐다. 하지만 68% Coverage는 여전히 80.79%로 과포함이며 6개 이벤트의 부분 개선이지 새 데이터 일반화 입증이 아니다.
- inD: Calibration 후 NLL 2.524는 Legacy 2.610보다 낮고 면적 41.46m²도 Legacy 48.36m²보다 작다. 그러나 Coverage95=90.78%는 Legacy 95.71%보다 목표에서 멀고 ADE/FDE도 악화됐다. Calibration 배율을 Test에 맞춰 늘리지 않았다.
- 단일 covariance 배율은 서로 다른 horizon·정지 상태·이동 속도·데이터셋 조건의 miscalibration을 동시에 해결하지 못할 수 있다. 작은 Calibration 코호트와 분포 이동, 기존 noise의 중복, mixture 평균/가중치의 구조적 오류도 남는다.
- 대표 경로는 원본 confidence 기반 가설이다. posterior 혼합의 최적 점추정치는 아니며, NLL 최적 후보가 ADE 최적 후보일 필요도 없다. 이 규칙을 Test에 맞춰 바꾸지 않았다.

## 5. 정지·재출발 평활화 확인

선택을 동결한 뒤 Train/Validation의 현재 관측까지의 속도 규칙으로 정지/재출발을 감사했다. “정지”는 최근 속도가 0.2m/s 미만, “재출발”은 이력 초기 저속 후 최근 0.4m/s 초과 조건이다. 최대 3개 window/track/kind 및 30개/group으로 제한해 단일 정지 track이 지배하는 문제를 줄였다. 사람의 의도 GT가 아닌 pseudo-label이며 재튜닝에 사용하지 않았다.

| phase | dataset | 상태 | windows/tracks | XY speed MAE m/s | Legacy speed MAE m/s | 정지 시 가짜 움직임 비율 | 재출발 과소추정 비율 |
|---|---|---|---|---|---|---|---|
| train | IMPTC | restart | 28/25 | 0.183 | 0.205 | 0.000 | 0.143 |
| train | IMPTC | stopped | 30/11 | 0.198 | 0.177 | 0.300 | 0.000 |
| train | inD | restart | 1/1 | 0.296 | 0.128 | 0.000 | 0.000 |
| train | inD | stopped | 9/3 | 0.359 | 0.253 | 0.889 | 0.000 |
| validation | IMPTC | restart | 6/5 | 0.143 | 0.118 | 0.000 | 0.000 |
| validation | IMPTC | stopped | 22/8 | 0.271 | 0.227 | 0.636 | 0.000 |
| validation | inD | restart | 1/1 | 0.089 | 0.185 | 0.000 | 0.000 |
| validation | inD | stopped | 3/1 | 0.369 | 0.223 | 0.667 | 0.000 |

정지 속도 편향과 가짜 움직임은 완전히 해결되지 않았다. inD 재출발은 Train/Validation 각각 1개 track뿐이라 과도한 평활화를 충분히 검증했다고 할 수 없다.

## 6. 검증 및 보존

- 미래 좌표를 변경해도 공식 인과적 adapter의 모델 입력/지도 tensor가 동일함을 검사했다.
- 실제 conditional history마다 ego 역변환과 공식 차분 6개 특징을 검사했다.
- 원래 offline Heading이 미래에 의존할 수 있음을 별도 fixture로 재현했다. 첫 fixture는 미래 첫점이 원점이라 영벡터 heading을 만들었고 검사가 실패했다. 미래 첫점을 비영점으로 고친 뒤 차이가 재현됐다. 초기 실패 로그도 보존했으며 모델 파라미터 변경은 없다.
- Calibration이 가중치/평균과 ADE/FDE를 유지하고 step covariance에 s²를 적용하며 joint 16D mixture가 정규화·양정치를 유지함을 검사했다.
- Train/Validation/Calibration과 Test의 recording/sequence 분리, 동결 config hash, 기존 최종 릴리스 hash를 확인했다.
- 원본/weights/최종 웹·공식 전체 Test는 그대로이며 GPU 잡·신경망 학습은 없다.
- 사전 plan: `configs/final_plan.json`; 후보: `configs/frozen_candidates.json`; 보정: `configs/frozen_calibration.json`; 전체 행: `outputs/windows.csv`; 집계: `outputs/summary.json`; 검사: `reports/checks.json`; 완료: `reports/completion.json`.
- inD 원본·복원 가능한 궤적/조건부 분포는 서버 private 디렉터리에만 보존하고 공개 배포하지 않는다. 공개용 산출물은 집계 표/그림으로 한정한다.

## 7. 최종 프로젝트 정리 및 탐색 종료

**채택:** 기존 최종 프로젝트(공식 DD-MDN + PedPy + SPD proxy/FilterPy)와 Simulation-only 제한을 유지한다. Legacy를 기준으로 발표하고, 이번 연구를 “입력 분포 일치와 Calibration의 효과 및 한계”로 별도 제시한다.

**연구 결과:** IMPTC에서는 부분적인 위치 UQ 개선. inD까지 포함한 일관된 우월성은 미입증. 새 후보를 최종 웹의 기본 모델로 교체하지 않는다. 보정된 위치 Coverage를 완료확률 Calibration의 증거로 사용하지 않는다. inD Exit는 계속 미확정이다.

**중단:** 이 판정으로 추가 q/prior/모델/보정 탐색을 종료한다. Test를 보고 더 좋은 조합을 찾지 않는다. 이후 작업은 현재 결과의 발표자료 정리다.

## 출처

- DD-MDN: https://github.com/kav-institute/ddmdn · 논문: https://arxiv.org/abs/2602.11214
- FilterPy: https://github.com/rlabbe/filterpy
- inD Tools: https://github.com/ika-rwth-aachen/drone-dataset-tools
- PedPy: https://github.com/PedestrianDynamics/PedPy
- SPD: https://github.com/AIR-THU/DAIR-V2X-Seq
