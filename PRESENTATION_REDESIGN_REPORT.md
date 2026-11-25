# View2Risk 과학 그림과 기록 기반 3D 시연

[10장 발표](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-1) · [9장 내장 3D](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-9) · [독립 시연](https://riverblue72.github.io/view2risk/presentation/demo.html) · [전체 평가 기록](https://riverblue72.github.io/view2risk/presentation/results.html)

View2Risk는 보행자 관측의 오차가 미래 위치 예측과 기한별 횡단 완료확률에 어떻게 전파되는지 연구한다. 사전학습 DD-MDN에서 얻은 미래 운동 분포에 대해 View2Risk가 구현한 입력 보정 실험, 출구 통과확률 변환, 실제 기록 대조를 보여준다.

## 발표 구성과 도표

| 장 | 연구 질문 | 도표와 읽는 법 |
|---|---|---|
| 1 · 문제 정의 | 한 경로로 언제 횡단을 마칠지 설명할 수 있는가? | 개념 횡단보도 위에 현재 위치, 여러 미래, 기한 안의 Exit 통과를 직접 표시했다. |
| 2 · 자료 | 현재 위치와 미래 운동의 불확실성은 어떻게 다른가? | 측정 위치의 산포와 미래 방향의 분기를 나란히 그렸다. SPD는 관측오차 대리값, IMPTC는 움직임과 완료 정답, inD는 보조 위치 평가에 쓴다. |
| 3 · 관측 모형 | 입력 위치가 얼마나 흔들릴 수 있는가? | **A**. 실제 f2의 같은 열 시각에 기준·합성·보정 위치와 측정오차 95% 타원을 겹쳤다. SPD Train 2,465쌍의 X/Y 표준편차는 15.7/17.8 cm, 위치 불일치 RMSE는 23.8 cm다. |
| 4 · 예측 구조 | 0.9초 관측에서 어떻게 4초 위치 분포를 얻는가? | **B**. 과거 10점, 0.5초 간격 미래 8점, 경로 후보·대표 경로·실제 미래·4초 HDR을 표시했다. 별도 구조도가 선택적 Kalman 처리와 공간·시간 평가의 분기를 보여준다. |
| 5 · 위치 오차 | 관측 보정으로 예측이 실제 위치에 가까워지는가? | **C**. 같은 시각의 실제·예측 위치를 화살표로 연결했다. ADE는 8개 거리의 평균, FDE는 마지막 거리이며 둘 다 m 단위다. Noisy 대비 보정 ADE가 81.1% 줄었다. |
| 6 · 공간 불확실성 | 95% 영역이 실제 위치를 얼마나 자주 포함하는가? | **D**. HDR의 68%·95% 예측 질량, 실제 위치의 포함·이탈 개념도, 실제 Coverage와 면적의 산점도. 가로축은 m² 로그 눈금, 가로 점선은 목표 95%다. |
| 7 · 완료확률 | H초 안에 Exit를 지날 확률은 얼마이며 그 오차는 어떻게 재는가? | **E·F**. 6/10은 개념 그림이다. 바로 아래에 f2의 저장된 joint 통과율·실제 통과 시각을 표시한다. Brier는 0·1 정답과 확률 차이의 제곱평균이다. 80% 예측에서 완료하면 한 사례의 제곱오차는 0.04다. 집계 H4 Brier는 Noisy 대비 74.4% 감소했다. |
| 8 · 직접 시간 예측 | 출구 직전의 학습 자료를 보강하면 어떤 변화가 있는가? | **G**. 동일한 개수 축척의 누적 막대에 실제 Train 구간별 개수를 표시했다. 1 m 미만, 1~2 m 미만, 2 m 이상이 기존 0/0/1,113개에서 393/385/1,544개로 바뀌었다. 별도 XGBoost AFT M1 실험이다. |
| 9 · 통합 시연 | 같은 보행자에서 관측만 바꾸면 무엇이 달라지는가? | Babylon.js로 기록 → 관측오차 → 미래 분포 → 완료와 정답의 네 단계를 한 슬라이드 안에서 조작한다. |
| 10 · 기여와 한계 | 어떤 범위에서 결론을 지지하는가? | 관측·운동의 모델링, 완료 UQ, 기록 대조의 기여와 실제 평가 범위를 설명하고 전체 결과로 연결한다. |

위치 도표는 미터 축척을 양 방향에 동일하게 적용한다. 파란색은 기준, 주황은 합성 오차, 청록은 보정, 보라색은 예측, 분홍은 실제 미래, 황색은 Exit다. 선 굵기, 점선, 직접 주석, 밝기가 밀집한 선과 영역을 구분한다. 도식적 수치는 ‘개념 예시’로 표시한다. HDR은 특정 미래 시각에서 밀도가 높은 위치들의 영역이다. Coverage95는 정답 좌표가 해당 영역에 든 비율이고 HDR95 Area는 그 영역의 공간적 크기다. 걷는 통로 전체 및 충돌 사건은 이 평가의 대상 밖이다.

## 기존 조건 전환의 진단과 수정

개편 직전 GitHub Pages의 Chrome 브라우저에서 f2/+8초, IID 1×, H3를 고정하고 세 조건을 선택했다. 당시에도 완료확률과 대표 경로 메시 ID는 바뀌고, 보행자 위치와 카메라는 유지됐다. 기존 드롭다운은 1단계에서 비활성화된 이유가 화면에 없었다. 관측 끝점과 실제 사람을 구별할 표시가 없었고, 보정 화면에서 원래 오차가 있는 이력을 볼 수 없었다. 좁은 횡단부 시점만으로는 큰 Noisy 영역의 범위도 파악하기 어려웠다.

| f2 · H3 · IID 1× | 선택 키 | 완료확률 | HDR95 면적 | 대표 끝점과 실제 간 거리 | 이 기한의 개별 제곱오차 |
|---|---|---:|---:|---:|---:|
| Clean | `clean` | 66.25% | 1.96 m² | 0.24 m | 0.1139 |
| Noisy | `iid_1__noisy` | 74.44% | 818.53 m² | 2.97 m | 0.0653 |
| Corrected | `iid_1__filtered_mean` | 85.75% | 8.57 m² | 0.77 m | 0.0203 |

세그먼트 버튼은 활성 조건을 강조하며 2~4단계에서 조작할 수 있다. 한 번 선택한 저장 결과에서 입력 끝점, 대표·후보 경로, 선택 시각 HDR, 완료확률, 사례별 면적을 함께 읽는다. 원래 사람은 기록 좌표를 유지하고 색 고리가 모델 입력의 끝점을 가리킨다. Corrected는 기준 과거와 반투명 합성 과거 위에 굵은 보정선을 겹친다. 2단계에서는 세 이력의 동시 비교를 선택할 수 있다.

기본 횡단부·상단 비교·전체 영역 보기가 있다. 같은 사례·오차 설정·H에서는 모든 조건의 경로와 윤곽 합집합으로 전체 범위를 결정한다. 조건 버튼은 카메라를 유지한다. 횡단부 화면에는 전체 영역 삽입도, 전체 영역 화면에는 횡단부 확대 삽입도를 제공한다. 정답 공개 전에는 실제 미래와 통과 시각 및 예측오차를 감춘다. 공개 후 선택 기한의 대표 끝점 오차와 개별 완료 제곱오차를 표시한다. 기준 거리·속도, 실제 궤적 및 완료 시각은 조건에 공통이다.

기본 f2는 세 입력 조건의 예측·HDR이 같은 원점에 있고 실제 통과가 2초와 3초 사이에 관측돼 선정했다. 추가 공개 사례 f1, f3은 예측 시점 이후 4초 안에 횡단을 완료하지 않는다. 1단계는 실제 타임스탬프를 재생해 저장 원점에서 멈춘다. 3단계는 선택한 기한까지의 저장 후보와 그 한 시각의 68%·95% 윤곽을 그린다. 4단계는 정답을 공개하거나 다시 감출 수 있다. WebGL 생성 실패 시 같은 기록을 사용한 2D 보기가 작동한다. 독립 페이지에서 직접 AFT 비교와 집계 결과를 추가로 열 수 있다.

## 수치와 그림 출처

아래 경로는 배포 디렉터리 `docs/presentation/` 기준이다. 화면에서 읽는 집계 사본은 `pres/evidence.json`이다. 원본 CSV의 선택 행과 수치를 대조했다.

| 항목 | 원본과 선택 기준 |
|---|---|
| R과 관측 그림 | `data/public/demo-evidence.json → r_proxy.train_fit`의 SPD Train 주석 2,465쌍. `r_robustness/FINAL_R_ROBUSTNESS_REPORT.md` §3–4의 합성 교란 및 보정 방법. 사례별 `data/public/r/{uid}.json → results[설정].input.observed_xy`, 보정 자료의 `filter.filter_R`, `filter.observed_points` |
| 합성 관측오차·공간 | `r_robustness/r_robustness_metrics.csv`. IMPTC / Test / H4 / overall / All / pooled. clean (λ0), iid (λ1) noisy, filtered_mean. `ade_m`, `fde_m`, `brier`, `coverage95`, `hdr95_area_m2`. `pres/evidence.json → r`과 대조 |
| 학습 범위 | `exit_aware/exit_aware_summary.json → training_distance_coverage`의 original, exit_aware 행. `n_train_origins`, `min_distance_m`, `n_train_lt1`, `n_train_lt2`. 화면 사본 `pres/evidence.json → audit.support`와 일치 |
| M1 Brier | `exit_aware/exit_aware_matched_metrics.csv`에서 dd_matched / test / M1__calibrated, EA_M1__calibrated의 H1~H4 `event_weighted_brier`. H1 및 네 값의 산술평균이 `pres/evidence.json → key_table`의 `h1`, `mean_brier`와 일치 |
| 사례, 경계와 확률 | `data/public/r-index.json`의 event_id·origin_s·uid로 `data/public/cases/public-imptc-0{1,2,3}.json`과 `data/public/r/{o0008,o0000,o0011}.json`을 결합. 위치 후보·대표 점수·HDR은 `hypotheses_xy`, `hypothesis_confidence_scores`, `regions`. 완료확률은 조건별 `exit.probabilities`. 경계는 `data/inference.json → geometry`, 실제 미래는 forecast의 `future_GT_xy` |
| 실제 완료와 직접 예측 | `data/public/demo-evidence.json → cases[].GT, features`의 통과 시각과 기준 관측 특징. 해당 시점의 `GT_by_horizon`으로 실제 결과 판정. 선택 비교는 `data/public/ui-completion.json`의 Conditional AFT와 `data/public/exit-aware.json`의 EA_M1__calibrated |

| IMPTC 합성 관측오차 | ADE (m) | H4 Brier | Coverage95 | HDR95 (m²) |
|---|---:|---:|---:|---:|
| Clean | 0.283 | 0.03472 | 96.05% | 7.37 |
| Noisy | 3.925 | 0.33527 | 74.12% | 748.20 |
| Kalman 보정 | 0.742 | 0.08594 | 78.51% | 10.27 |

같은 237개 시점, 120개 사건에서 지표별 유효 분모는 ADE 215, Brier 218, 4초 FDE 및 endpoint Coverage 228, HDR 면적 237이다. 관측 보정은 점 예측 정확도를 상당 부분 회복했으나 95% 영역의 실제 포함률은 목표 아래에 남았다.

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

배포 소스는 `presentation/site/`, GitHub Pages 사본은 `docs/presentation/`이다. 두 위치에 같은 파일을 반영했다.

| 파일 | 이번 개편의 변경 |
|---|---|
| `presentation.html`, `demo.html` | SVG 모듈을 로드하고 발표와 독립 시연의 자산 버전을 맞췄다. |
| `pres/story.js`, `pres/scientific-svg.js` | 10개 장면의 한국어 질문·해설과 발표자 노트, 도표 A–G 및 구조도, 실제 집계표를 구성했다. |
| `pres/guided-world.js`, `pres/guided-replay.js` | 조건별 메시와 입력 끝점, 이력 중첩, 공통 카메라, 사례별 정보, 조작과 정답 공개를 구현했다. 기존 `app.js`의 장면·지도·사람과 재생 구조를 사용한다. |
| `pres/uq-figures.js`, `pres/uq.css` | 공통 집계 행, 축척과 삽입도, 색·단위, 발표 크기별 배치를 정의했다. |
| `presentation/tools/uq_browser_check.mjs` | 공개 JSON과 실제 Babylon 메시의 좌표 비교, 조건 버튼 클릭, 브라우저·레이아웃·캡처 검사를 확장했다. |
| `presentation/review/scientific-uq/`, `presentation/README.md`, 본 보고서 | 전후 화면과 전체 슬라이드·단계 캡처, 발표 진입점 및 검증 기록을 갱신했다. |

## 브라우저 검증

2026-11-26 (KST), 사이트 커밋 `ff2e575` 배포 후 실제 GitHub Pages 주소에서 브라우저 캐시를 끄고 아래 검사를 재실행했다. 3D 180조합과 독립 2D 180조합이 모두 통과했고, JavaScript 예외·누락 자산·요청 실패는 0건이었다. [Pages 배포 기록](https://github.com/riverblue72/view2risk/actions/runs/45665303213)

Chrome의 ANGLE/SwiftShader WebGL로 실제 3D 장면을 구동했다. 1920×1080, 1440×900, 1366×768에서 열 장의 본문과 하단 내비게이션 경계, 시연 네 단계 컨트롤의 위치와 클릭 가능 여부를 검사했다. 전체 화면, 앞뒤 이동·뒤로 가기, 발표자 노트, 기록 재생·정지·초기화 및 카메라 복귀도 확인했다.

- 실제 포인터로 정답 공개 전후에 세 조건을 눌러 선택 키·입력 끝점과 새 메시 ID, 이전 메시 제거, 카메라와 사람 위치 보존을 확인했다.
- **3사례 × 5오차 설정 × 3조건 × 4기한 = 180조합**에서 후보·대표 경로, HDR68·95 윤곽과 실제 경로의 Babylon 튜브 중심 좌표, 네 확률, 선택 기한, 정답 및 사례 면적을 공개 파일과 대조했다. 독립 2D 탐색에서도 같은 180조합의 확률·기한·정답 경로를 대조했다.
- Noisy 전체 보기에서 95% 윤곽의 정점이 캔버스 경계 안에 있는지 확인했다. 원래 Babylon 상세 탐색기와 지도, 전체 평가 기록, WebGL 강제 실패 시 2D 대체 화면의 정답 공개도 검사했다.
- 로컬 정적 소스·배포본 219개 파일의 일치와 공개 범위를 `python3 presentation/tools/verify_static.py`로 검사했다. 화면 검증은 헤드리스 Chrome 결과이며 다른 GPU·브라우저의 성능은 측정하지 않았다.

## 남은 한계

SPD 주석 차이는 IMPTC 검출기의 실측오차에 대한 대리값이다. 사전학습 예측기에 의존하며 별도의 물리적 과정잡음 Q를 식별하지 않았다. 보정 후 Coverage95는 78.51%에 머물렀고 FFBS 영역은 지나치게 넓었다. 정지·재출발 평가가 제한적이며 단순 기준선에 대한 일관된 우위는 관측되지 않았다. 같은 과거 Test를 재사용했으며 검증 범위는 최대 4초의 오프라인 기록이다. 공개 사례 3건으로 모집단 수준의 보정이나 실시간 안전 효과를 검증할 수 없다. 공개 파일에는 joint 표본 경로 전체가 없어 화면에는 저장된 경로 후보를 그리고 기한별 막대는 저장된 joint 표본 통과율을 쓴다. 원본 자료의 공개 조건은 [자료 정책](docs/presentation/DATA_POLICY.md)에 있다.

## 스크린샷

[1장](presentation/review/scientific-uq/scene-1.jpg) · [2장](presentation/review/scientific-uq/scene-2.jpg) · [3장](presentation/review/scientific-uq/scene-3.jpg) · [4장](presentation/review/scientific-uq/scene-4.jpg) · [5장](presentation/review/scientific-uq/scene-5.jpg) · [6장](presentation/review/scientific-uq/scene-6.jpg) · [7장](presentation/review/scientific-uq/scene-7.jpg) · [8장](presentation/review/scientific-uq/scene-8.jpg) · [9장](presentation/review/scientific-uq/scene-9.jpg) · [10장](presentation/review/scientific-uq/scene-10.jpg)

[1단계 실제 기록](presentation/review/scientific-uq/stage-1.jpg) · [2단계 관측 오차](presentation/review/scientific-uq/stage-2.jpg) · [3단계 미래 위치](presentation/review/scientific-uq/stage-3.jpg) · [4단계 완료 정답](presentation/review/scientific-uq/stage-4.jpg)

| 동일 f2 · H3 · 정답 공개 | 개편 전 배포 화면 | 개편 후 |
|---|---|---|
| Clean | [이전 화면](presentation/review/scientific-uq/before-clean.jpg) | [현재 화면](presentation/review/scientific-uq/after-clean.jpg) |
| Noisy | [이전 화면](presentation/review/scientific-uq/before-noisy.jpg) | [현재 화면](presentation/review/scientific-uq/after-noisy.jpg) |
| Corrected | [이전 화면](presentation/review/scientific-uq/before-filtered_mean.jpg) | [현재 화면](presentation/review/scientific-uq/after-filtered_mean.jpg) |

[Noisy H4 전체 영역과 횡단부 확대](presentation/review/scientific-uq/overview-noisy.jpg)
