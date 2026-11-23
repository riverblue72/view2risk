# Final Presentation Redesign

Status: PASSED — five scenes, Korean explanation, shared architecture and fixed-case link.

## Five-minute speaker script

### 1. Question (40 seconds)

“실제 교차로를 걷는 이 보행자는 앞으로 3초 안에 횡단을 마칠까요? View2Risk는 가능한 미래 위치와 반대편 Exit까지의 완료 확률을 구분해 보여줍니다. 완료하지 못할 확률은 같은 분포의 보완확률입니다. 충돌 확률이나 배치된 신호 제어 시스템을 뜻하지는 않습니다.”

Visual: real recorded crossing, completion/survival notation. Transition: “먼저 무엇을 완료라고 정의했는지 보겠습니다.”

### 2. Data and GT (55 seconds)

“IMPTC의 위치 시계열과 semantic crosswalk label 5를 사용합니다. f1/f2/f3별 20개 transverse bin과 median-3 smoothing으로 저장된 A/B 경계를 만들고, 진행 방향에 따라 반대편 Exit를 정합니다. 첫 통과 뒤 0.12초 이상의 연속 관측으로 확인하는 operational GT입니다. 발의 물리적 통과 시점을 별도로 수작업 주석한 것은 아닙니다. 완료 1,019건, right-censored 170건, unresolved 218건, return 8건은 서로 다른 상태입니다. 미확인 사건을 실패로 바꾸지 않습니다. inD는 위치 예측 평가, SPD는 관측오차 대리분포에 사용했습니다.”

Visual: saved geometry and catalog counts. Transition: “이 데이터에서 두 종류의 예측을 만듭니다.”

### 3. Parallel predictors (65 seconds)

“DD-MDN은 공식 사전학습 모델입니다. 0.1초 간격 과거 10점으로 4초까지의 미래 위치분포를 예측합니다. joint sampled path가 Exit를 통과하는 비율로 완료 확률을 계산합니다. XGBoost Survival AFT는 별도로 학습한 모델로, 거리·종방향 속도·가속도 등을 받아 잔여 완료시간 분포를 예측합니다. DD-MDN 출력을 XGBoost에 넣는 구조가 아닙니다. R은 세 번째 예측 모델이 아니라, SPD 주석 차이에 근거한 합성 관측오차를 기존 예측기에 전파하는 비교 실험입니다. PedPy는 실제 보행 통계 분석에 사용합니다.”

Visual: new architecture. Transition: “같은 보행자와 같은 시점에서 이 차이를 확인하겠습니다.”

### 4. Synchronized comparison (85 seconds)

“Compare Models를 열면 f2의 +8초 관측 시점이 세 패널에 고정됩니다. 남은 거리 약 3.42 m, 종방향 속도 약 1.57 m/s입니다. DD-MDN의 H3 완료 확률은 66.25%, 3,200개 joint samples 중 2,120개 통과에 해당합니다. 아래 CDF는 XGBoost의 시간분포이며 새로운 공간 경로가 아닙니다. H를 바꾸면 세 패널의 같은 horizon을 봅니다. GT를 열면 실제 3초 이내 완료 여부와 한 사례의 제곱오차를 확인할 수 있습니다. R에서 IID 1×를 고르면 같은 과거의 관측만 교란된 결과입니다. Filtered mean과 FFBS의 확률과 영역이 다르며 어느 쪽도 항상 더 낫지는 않습니다.”

Visual: shared case/H, forecast first, GT reveal, R change. Keep origin +8 s throughout. Transition: “한 사례의 차이가 전체 성능을 뜻하지는 않으므로, 저장된 평가 결과를 함께 봅니다.”

### 5. Findings and conclusion (55 seconds)

“위치 예측과 완료 확률의 품질은 서로 다른 목표입니다. 236 origins / 120 events의 재사용된 Test 비교에서 Conditional AFT의 평균 Brier가 더 낮았고, DD-MDN이나 XGBoost가 모든 기준선을 이긴 것은 아닙니다. Exit 근처 Train support를 복원하자 원래 XGBoost M1의 H1 Brier는 약 0.10827에서 0.00618로 개선됐습니다. 그러나 가속도와 crowding의 독립적인 이득은 확립되지 않았습니다. 관측오차는 예측을 악화시킬 수 있고, filtering과 FFBS에는 정확도와 영역 크기의 절충이 있습니다. 기여는 새로운 foundation model이 아니라, 실제 데이터의 공간 예측과 완료 확률을 구별하고 신뢰성을 검증하는 재현 가능한 연결과 시각화입니다.”

Visual: matched evidence and limitations. End with the unchanged DD-MDN Q-only default and optional AFT/R comparisons.

## Likely questions

- Why not distance/speed alone? It is explicitly retained as a strong baseline; model complexity is not assumed superior.
- Why DD-MDN if Conditional AFT has lower Brier? DD-MDN supplies spatial futures; lower time-event Brier does not supply a spatial distribution.
- Does crowding cause uncertainty? No causal effect or independent incremental benefit was established.
- Is R real IMPTC detector error? No; it is transferred SPD annotation-disagreement proxy noise.
- What does Coverage95 mean? Empirical inclusion in a nominal 95% positional region, interpreted together with its area; not 95% completion probability.
- Why four seconds? These official checkpoint outputs end at +4 s. Rolling observations do not validate a 15–20 s forecast from the original origin.

## Interaction and notes

Existing Next/Previous, keyboard arrows, scene progress, fullscreen and presenter-note controls remain. The guided scene links directly to `compare.html`, which initializes the preverified same-origin default. The diagram is reused from Methods. Return navigation is in the common header. Browser tests verified all five scenes, keyboard navigation, visible architecture above the footer, and comparison link.

## Release boundary

This is a local review revision dated 2026-11-23. No commit or push was performed. The public GitHub Pages release is unchanged. Canonical files are in `presentation/site/`; the deployment mirror is `docs/presentation/`. Existing `final/`, `docs/final/`, saved experimental results and model artifacts were not edited. No fitting, inference, calibration or GPU work was run.

The static website replays already saved inference outputs. It does not run DD-MDN or XGBoost in the browser. Only existing allowlisted IMPTC excerpts are used for individual demonstrations; no new individual inD records or private inference packets were exported.
