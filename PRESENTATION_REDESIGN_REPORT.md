# View2Risk 발표 및 시연 개편

[발표 1장](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-1) · [7장 내장 3D 시연](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-7) · [독립 시연](https://riverblue72.github.io/view2risk/presentation/demo.html) · [전체 결과와 부록](https://riverblue72.github.io/view2risk/presentation/results.html)

연구 질문은 보행자의 현재 위치와 미래 운동의 불확실성을 횡단 완료확률로 변환했을 때 그 예측이 실제 기록과 얼마나 일치하는가이다. 공식 사전학습 DD-MDN은 미래 운동 분포를 제공한다. View2Risk는 관측오차 실험, 의미 경계와 완료 정답 구성, 경로 분포의 시간별 완료확률 변환, 기록 대조와 시각화를 구현했다.

## 발표 구성

| 장 | 화면에 포함한 자료 |
|---|---|
| 1. 문제 정의 | 실제 f2 경로와 3초 예측영역. 현재 위치, 가능한 미래, 완료 시각이라는 세 질문과 교통 분야의 활용 맥락 |
| 2. 데이터 | SPD 주석 차이, IMPTC 궤적·경계·완료 정답, inD 보조 궤적 평가의 역할. 같은 사례의 과거 관측과 미래 분포를 나란히 표시 |
| 3. UQ 구조 | 기준 관측 직행과 선택적 Kalman 보정, 공식 DD-MDN, 공간 HDR와 시간별 Exit 확률, 공통 정답 평가. Conditional AFT 및 XGBoost AFT의 직접 시간 예측 경로 |
| 4. 관측오차와 보정 | SPD 주석 차이로 추정한 R, 같은 과거의 세 관측, Kalman 보정 전후 ADE와 H4 Brier |
| 5. 미래 운동과 강건성 | 보정 입력의 4초 경로 후보·대표 경로·실제 미래·두 HDR. 동일 집단의 Coverage95와 면적 |
| 6. 횡단 완료와 개선 | 실제 f2 사례의 기한별 완료확률과 정답. 별도의 Exit-aware XGBoost AFT 학습 범위와 동일 M1 전후 비교 |
| 7. 통합 3D 시연 | 기존 Babylon.js 엔진·IMPTC 지도·보행자·카메라를 직접 마운트. 네 단계와 정답 공개를 슬라이드에서 조작 |
| 8. 기여와 한계 | 관측·운동 모델링, 완료 UQ, 실제 기록 검증. 사전학습 모델 의존성, 대리 R, 불완전한 보정, 과도한 FFBS 영역, 정지·재출발 자료 부족, 기준선 비교, Test 재사용, 4초 한계, 오프라인 평가 |

## 통합 3D 시연

기본 사례는 f2의 `public-imptc-01 / o0008`이다. 이 사례는 같은 +8초 시점에 세 입력 조건의 예측과 HDR이 모두 있고, 실제 Exit 통과가 예측 후 2.063초에 일어나 4초 평가 범위 안에서 예측과 비교할 수 있다. 예측 점수 순위는 사례 선정에 사용하지 않았다. 추가 드롭다운의 f1과 f3은 같은 검사를 통과한 공개 사례이며 실제 완료 시각은 각 예측 시점에서 4초 이후다.

| 단계 | 발표자 조작과 화면 |
|---|---|
| 1. 실제 보행 | 재생하면 최대 4초 전부터 관측 좌표와 기록 시각을 따라 걷고, 캐시된 예측 시점에 자동 정지한다. 기록 슬라이더는 그 시점까지만 이동한다. 이동 중의 종방향 속도는 연속된 최근 0.6초 기록에서 계산한다. |
| 2. 관측 오차 | 실제 보행자와 카메라를 고정하고 Clean / Noisy / Kalman 입력을 바꾼다. 합성 오차 조건에서는 마지막 유효 측정점에 저장된 측정 공분산으로 계산한 95% 타원을 그린다. |
| 3. 미래 운동 | 저장된 20개 경로 후보와 최고 confidence 대표 경로를 나타낸다. H=1·2·3·4초에서 해당 시각의 68%·95% HDR 윤곽과 반투명 내부를 지면에 그린다. 경로는 해당 기한까지, 영역은 해당 기한의 한 시각에만 표시한다. |
| 4. 횡단 완료 | 주황색 Exit를 강조하고 joint 분포 표본으로 평가한 네 기한의 누적 완료확률을 표시한다. 정답 공개는 실제 미래 경로·최초 Exit 통과 시각·선택 기한의 완료 여부를 함께 연다. 공개 후 재생은 해당 기한까지만 가능하다. 숨기면 기록 시계와 보행자가 예측 시점으로 돌아간다. |

왼쪽 70%는 기존 3D 횡단 환경, 오른쪽 30%는 조건·시간·거리·속도·확률이다. 재생과 시점 변경은 하단에서 조작한다. 2~4단계의 거리와 속도는 동일한 기준 관측의 **예측 시점** 특징이다. 조건이나 H를 바꿀 때 카메라는 움직이지 않는다. 일부 Noisy 영역이 횡단보도 화면을 벗어날 때 **전체 영역 위에서 보기**를 누르면 해당 잡음과 H의 세 입력 조건에 있는 모든 경로·윤곽과 경계를 같은 축척에 담는다. 카메라 초기화로 횡단보도 시점에 복귀한다.

`app.js`의 기존 `initScene`, 지도 픽셀→월드 변환, 보행자 메시, 경계 라벨과 ArcRotateCamera를 재사용한다. `demo/demo.js`와 `ui/ui.js`의 기존 상세 탐색기는 원래 경로에서 사용할 수 있다. 새로운 슬라이드에서는 해당 라우터의 헤더·자료 패널을 올리지 않는다. 덱이 Babylon 번들과 지도 이미지를 미리 요청하고, 7장을 나갈 때 렌더 루프·메시·엔진을 해제한다.

실제 위치는 공개 사례의 `actual_observations.xy / elapsed_s`에서 읽는다. 3D 사람의 자세는 기록 이동량에 연동한 도식 표현으로, 신체 관절 측정값은 공개 자료에 없다. 공개 파일에는 joint Monte Carlo 궤적 원본 전체가 없다. 지도에는 저장된 후보를 그리며 막대는 별도로 저장된 joint 통과율을 읽는다. 68%·95% 영역은 시점별 위치 분포다. 평가 범위는 최대 4초다.

WebGL 엔진 생성에 실패하면 같은 시점의 2D 기록을 사용한다. 독립 페이지의 접이식 **2D 상세 탐색**에는 직접 시간 예측과 기존 집계 비교가 있다. 공개 자료와 스크린샷의 IMPTC 출처·저자·비상업 라이선스·발췌 조건은 [자료 정책](docs/presentation/DATA_POLICY.md)에 명시돼 있다.

## 수치와 그림 출처

아래 경로는 배포 디렉터리 `docs/presentation/` 기준이다. 화면에서 읽는 집계 사본은 `pres/evidence.json`이다. 원본 CSV의 선택 행과 수치를 대조했다.

| 항목 | 원본과 선택 기준 |
|---|---|
| R과 관측 그림 | `data/public/demo-evidence.json → r_proxy.train_fit`의 SPD Train 주석 2,465쌍. `r_robustness/FINAL_R_ROBUSTNESS_REPORT.md` §3–4의 합성 교란 및 보정 방법. 사례별 `data/public/r/{uid}.json → results[설정].input.observed_xy`, 보정 자료의 `filter.filter_R`, `filter.observed_points` |
| 합성 관측오차·공간 | `r_robustness/r_robustness_metrics.csv`. IMPTC / Test / H4 / overall / All / pooled. clean (λ0), iid (λ1) noisy, filtered_mean. `ade_m`, `brier`, `coverage95`, `hdr95_area_m2`. `pres/evidence.json → r`과 대조 |
| 학습 범위 | `exit_aware/exit_aware_summary.json → training_distance_coverage`의 original, exit_aware 행. `n_train_origins`, `min_distance_m`, `n_train_lt1`. 화면 사본 `pres/evidence.json → audit.support`와 일치 |
| M1 Brier | `exit_aware/exit_aware_matched_metrics.csv`에서 dd_matched / test / M1__calibrated, EA_M1__calibrated의 H1~H4 `event_weighted_brier`. H1 및 네 값의 산술평균이 `pres/evidence.json → key_table`의 `h1`, `mean_brier`와 일치 |
| 사례, 경계와 확률 | `data/public/r-index.json`의 event_id·origin_s·uid로 `data/public/cases/public-imptc-0{1,2,3}.json`과 `data/public/r/{o0008,o0000,o0011}.json`을 결합. 위치 후보·대표 점수·HDR은 `hypotheses_xy`, `hypothesis_confidence_scores`, `regions`. 완료확률은 조건별 `exit.probabilities`. 경계는 `data/inference.json → geometry`, 실제 미래는 forecast의 `future_GT_xy` |
| 실제 완료와 직접 예측 | `data/public/demo-evidence.json → cases[].GT, features`의 통과 시각과 기준 관측 특징. 해당 시점의 `GT_by_horizon`으로 실제 결과 판정. 선택 비교는 `data/public/ui-completion.json`의 Conditional AFT와 `data/public/exit-aware.json`의 EA_M1__calibrated |

| IMPTC 합성 관측오차 | ADE (m) | H4 Brier | Coverage95 | HDR95 (m²) |
|---|---:|---:|---:|---:|
| Clean | 0.283 | 0.03472 | 96.05% | 7.37 |
| Noisy | 3.925 | 0.33527 | 74.12% | 748.20 |
| Kalman 보정 | 0.742 | 0.08594 | 78.51% | 10.27 |

같은 237개 시점, 120개 사건에서 지표별 유효 분모는 ADE 215, Brier 218, 4초 endpoint Coverage 228, HDR 면적 237이다. 관측 보정은 점 예측 정확도를 상당 부분 회복했으나 95% 영역의 실제 포함률은 목표 아래에 남았다.

| XGBoost AFT M1 | 기존 | Exit-aware |
|---|---:|---:|
| 학습 시점 | 1,113 | 2,322 |
| 최소 잔여 거리 | 2.19 m | 0.059 m |
| Exit 1 m 이내 | 0 | 393 |
| H1–H4 평균 Brier | 0.05646 | 0.01635 |
| H1 Brier | 0.10827 | 0.00618 |

동일 Test 236개 시점 / 120건 기준이다. 화면 표의 다섯 자리 값을 사용하면 평균 감소율 약 71.0%, H1 감소율 약 94.3%이다. 반올림 전 평균의 감소율은 71.0522%이다. 이 비교에서는 학습 데이터의 양과 구성도 함께 달라졌다.

기본 단일 사례 `public-imptc-01 / o0008 / +8초`의 기준 잔여 거리는 3.42 m, 종방향 속도는 1.57 m/s이다. Clean 확률은 0%, 2.53%, 66.25%, 66.97%이며 실제 통과는 예측 후 2.063초이다.

## 부록과 보존

[전체 결과](docs/presentation/results.html)에 원래 Results 경로, 상세 Exit-aware 및 R 보고서, 이전 비교 시뮬레이터를 연결했다. 전체 기준선 표, constant-speed와 Conditional AFT, FFBS, 불확정 모델 변형, 가속도·혼잡 분석, 초기 보정과 수식·설정 기록은 기존 자료에서 확인할 수 있다. 공개 데이터 경계는 IMPTC 발췌와 inD 집계로 유지했다. 원본 결과, GT, 체크포인트에 대한 변경이나 새로운 학습·추론은 없었다.

## 변경 파일

정적 구현은 `presentation/site/`와 `docs/presentation/`에 동일하게 반영했다.

| 파일 | 역할 |
|---|---|
| `app.js` | 기존 장면 초기화에 시연용 캔버스·재생 콜백을 연결. 상세 탐색기의 기존 기본 진입점 유지 |
| `presentation.html`, `demo.html` | 같은 3D 구현과 사전 로드, 독립 페이지의 선택적 2D 탐색 |
| `pres/story.js` | 4~6장 재구성, 7장 생성·해제 |
| `pres/guided-world.js` | 기록 기반 자세, 경계, 측정 타원, 미래 후보·대표·GT, 저장된 윤곽을 따라 채운 지면 HDR과 카메라 |
| `pres/guided-replay.js` | 단계별 시계, 사례·관측 조건·H, 정답 공개, 확률과 2D 대체 화면 |
| `pres/uq-replay.js`, `pres/uq-figures.js`, `pres/uq.css` | 공통 수치·타원·표, 독립 페이지 통합, 일관된 색과 반응형 배치 |
| `presentation/tools/uq_browser_check.mjs` | 실제 WebGL 메시, 조작, 레이아웃, 스크린샷과 대체 화면 검증 |
| `presentation/review/guided-3d/`, `PRESENTATION_REDESIGN_REPORT.md` | 검증 화면 12장과 본 보고서 |

## 브라우저 검증

Chrome 158에서 소프트웨어 WebGL(ANGLE/SwiftShader)을 사용했다. 1920×1080, 1440×900, 1366×768에서 7장의 네 단계마다 가로 넘침과 하단 잘림을 검사했다. 사용 가능한 컨트롤의 중앙을 실제로 누를 수 있는지 확인했고, 전체 화면 진입·복귀도 시험했다. 8장과 네 단계의 캡처는 1440×900이다.

- f2 기록 재생·일시정지·원점 자동 정지, 기록 좌표와 사람 위치 일치, 시간 슬라이더와 초기화, 조건 변경 시 원점과 카메라 고정, 전체 영역 상단 시점과 카메라 복귀를 확인했다.
- 3사례 × 5잡음 설정 × 3입력 × 4기한의 **180가지 3D 조합**에서 대표 경로, 68%·95% 윤곽과 GT의 실제 Babylon 튜브 중심을 저장 좌표와 대조했다. 표시된 네 확률과 선택 기한의 실제 결과도 대조했다. GT는 공개 전 숨겨져 있고 숨기기를 누르면 실제 미래 메시와 시각이 제거된다.
- 독립 페이지의 선택적 2D 비교에서도 같은 180조합을 검증했다. WebGL 컨텍스트 생성을 강제로 실패시켜 평면 그림에서도 GT 공개·숨김 규칙이 유지되는지 검사했다. 기존 상세 Babylon 탐색기의 초기화와 지도 렌더링도 확인했다. 검사 중 JavaScript 예외나 누락된 자산은 없었다.
- `python3 presentation/tools/verify_static.py`로 정적 소스와 배포본 218개 파일의 일치 및 공개 자료 범위를 확인했다. 브라우저 검증은 자료 조회·렌더링에 한정되며 실제 장치의 실시간 검출, 외부 날짜 성능 또는 모집단 보정 성능을 평가하지 않는다.

## 캡처

[1장](presentation/review/guided-3d/scene-1.jpg) · [2장](presentation/review/guided-3d/scene-2.jpg) · [3장](presentation/review/guided-3d/scene-3.jpg) · [4장](presentation/review/guided-3d/scene-4.jpg) · [5장](presentation/review/guided-3d/scene-5.jpg) · [6장](presentation/review/guided-3d/scene-6.jpg) · [7장](presentation/review/guided-3d/scene-7.jpg) · [8장](presentation/review/guided-3d/scene-8.jpg)

[1. 실제 보행](presentation/review/guided-3d/stage-1.jpg) · [2. 관측 오차](presentation/review/guided-3d/stage-2.jpg) · [3. 미래 운동](presentation/review/guided-3d/stage-3.jpg) · [4. 완료와 정답](presentation/review/guided-3d/stage-4.jpg)
