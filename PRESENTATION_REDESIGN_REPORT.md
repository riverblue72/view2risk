# View2Risk 과학 그림과 기록 기반 3D 시연

[11장 발표](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-1) · [10장 내장 3D](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-10) · [독립 시연](https://riverblue72.github.io/view2risk/presentation/demo.html) · [전체 평가 기록](https://riverblue72.github.io/view2risk/presentation/results.html)

View2Risk는 보행자 관측의 오차가 미래 위치 예측과 기한별 횡단 완료확률에 어떻게 전파되는지 연구한다. 사전학습 DD-MDN에서 얻은 미래 운동 분포에 대해 View2Risk가 구현한 입력 보정 실험, 출구 통과확률 변환, 실제 기록 대조를 보여준다.

## 별도 UQ 발표본

[UQ 발표](https://riverblue72.github.io/view2risk/presentation/presentation-uq.html#scene-1)에는 별도 주소와 발표자 노트가 있다. 기존 발표 주소는 위의 11장 발표 링크다.

| 장 | 연구 흐름과 근거 |
|---|---|
| 1–2 | 하나의 보행에서 관측 위치, 미래 경로, 최초 Exit 통과시간이 각각 무엇을 의미하는지 설명한다. SPD는 관측오차 대리값, IMPTC는 주 평가, inD는 보조 검증에 사용했다. |
| 3 | SPD Train의 2,465개 위치 주석 쌍으로 편향과 공분산 R을 추정한 절차를 표시한다. 사전학습 DD-MDN의 경로 분기와 별도로 학습한 XGBoost AFT의 잔여시간 분기를 한 도식에 배치했다. |
| 4–5 | 동일한 관측오차 조건에서 IMPTC와 inD의 ADE를 비교한 뒤, IMPTC의 4초 위치 포함률과 영역 면적을 대조한다. 보정 후 ADE의 감소와 95% 영역의 실제 포함률 미달을 구분한다. |
| 6–7 | 최초 Exit 통과를 기한별 사건으로 바꿔 Brier로 평가한다. f2에서 경로 표본 집계와 직접 시간 모형의 저장 CDF를 같은 실제 완료 시각과 대조한다. Exit-aware 개선은 기존 XGBoost M1과 비교한다. |
| 8–11 | 기존 한국 적용, 개선 제안, Babylon.js 내장 시연, 결론을 유지한다. |

입력 오차 근거는 `data/public/demo-evidence.json`의 `r_proxy.train_fit`이다. 궤적·공간·완료 강건성 집계의 원표는 `r_robustness/r_robustness_metrics.csv`다. f2 경로 기반 확률은 `data/public/r/o0008.json`, 직접 시간 확률은 `data/public/exit-aware.json`의 `EA_M1__calibrated`에서 읽는다. XGBoost 성능은 `exit_aware/exit_aware_matched_metrics.csv`의 매칭 Test 결과를 사용한다. 표본 하나의 일치 여부로 확률의 보정 수준을 판정할 수 없고, 보정 뒤 공간 포함률이 낮은 원인은 이번 비교로 식별할 수 없다.

별도 진입점은 `presentation-uq.html`, 전용 슬라이드와 스타일은 `pres/story-uq.js`, `pres/story-uq.css`다. 세 파일을 `presentation/site/`와 `docs/presentation/`에 동일하게 두었다. `V2R_DECK=uq`로 `presentation/tools/uq_browser_check.mjs`를 실행하면 새 발표의 수치, 해상도별 배치, 8–11장 일치 여부와 기존 시뮬레이터의 동작을 검사한다.

배포된 GitHub Pages에서 기존 발표와 새 발표의 8–11장 본문, 발표자 노트, 시연의 초기 화면과 스크립트 주소가 일치했다. Chrome에서 새 발표 11장을 1920×1080, 1440×900, 1366×768 및 전체 화면으로 검사했다. f2의 Entry–Exit 254개 위치, 180개 WebGL 조건 조합의 저장 확률·경로·HDR·실제 위치, WebGL 실패 시의 2D 재생을 확인했다.

## 현재 배포 구성 · 11장

국내 보행신호 적용 장을 포함한 팀 발표를 기준으로 6장에는 DD-MDN의 경로 기반 완료확률과 관측 보정 결과를 두었다. [7장 직접 시간 예측](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-7)은 f2 사례, 출구까지 남은 거리별 학습 시점, 매칭 Test의 네 기한별 Brier를 한 장에 담는다. 8장은 국내 속도·시나리오로 계산한 별도 신호시간, 9장은 개선 제안, 10장은 3D 시연, 11장은 결론이다.

- 사례 곡선은 `data/public/exit-aware.json`의 `o0008 / EA_M1__calibrated`에서 읽은 81개 저장 시각과 누적확률이다. 입력도 같은 행의 거리·종방향 속도·가속도를 쓴다. 실제 잔여시간 2.063초는 같은 사건의 실제 Exit 시각에서 예측 시작 시각을 빼서 구한다.
- 학습 분포는 `pres/evidence.json → audit.support`, 평가값은 `audit.matched`의 IMPTC dd_matched/test 사건별 가중 Brier와 `key_table.mean_brier`에서 읽는다. 기존 M1과 Exit-aware M1을 같은 236시점·120건에서 비교한다.
- 본문과 발표자 노트에서 ADE의 4초 평균, SPD 주석 불일치 RMSE, 공간 포함률 회복의 한계 및 가능한 원인을 구분했다. 아래 10장 구성과 기존 시연 검토는 이전 버전의 개편 이력이다.

## 기본 시연 · f2 한 건의 Entry → Exit 위치 추적

발표 9장과 독립 시연은 동일한 Entry에서 세 조건을 겹쳐 보여준다. 10.0791초 동안 보행자 모델은 공개 IMPTC 기준 위치를 따라간다. 각 색 고리는 같은 시각의 기준·합성·보정 위치를 표시한다. 조건을 개별 선택해도 보행자, 시계와 카메라는 고정된다. 현재 오차(cm)는 각 위치와 기준 위치 사이의 유클리드 거리다. 시점별 DD-MDN과 완료확률은 **저장된 미래 예측 보기**에서 열 수 있다.

- 입력은 [f2 공개 보행 기록](docs/presentation/data/public/cases/public-imptc-01.json)의 실제 시각·좌표, [경계 정답과 SPD Train 추정치](docs/presentation/data/public/demo-evidence.json)의 `GT`와 `r_proxy.train_fit`이다. Entry와 Exit 시각에서 인접 두 기록을 선형 보간했다. 두 경계 사이의 원래 관측 252개와 경계 위치 둘을 포함한다.
- [생성 코드](presentation/tools/build_f2_tracking.py)는 최초 위치를 공통 Entry로 고정한다. 이후 매 시점에 SPD 주석 차이의 편향과 공분산을 사용한 독립 Gaussian 오차를 더한다(NumPy PCG64, 시드 20261126, IID 1×). 이는 전 구간의 위치 추적을 설명하기 위해 별도로 만든 한 가지 합성 관측 실현이다.
- 보정은 [기존 CV4 모형](final/src/observation.py)의 순방향 칼만 갱신을 따른다. 실제 시간 간격, 알려진 Entry 위치, 초기 속도 평균 0과 분산 25, 측정 편향 보정, [기존 f2 설정](docs/presentation/data/public/r/o0008.json)의 R과 q=0.5를 사용했다. 각 시점의 결과는 그때까지 도착한 관측만 사용한다. [전체 추적 좌표](docs/presentation/demo/f2-full-track.json)는 시연 파일로 따로 저장했다. 기존 0.9초 입력의 궤적 예측, Brier, Coverage 및 모델 가중치는 이 파일을 사용하지 않는다.
- 구현은 `pres/full-track.js`, `pres/guided-world.js`, `pres/uq.css`, 발표와 독립 페이지의 진입점에 있다. 정적 사이트 원본과 배포본을 동기화했다. [횡단 중간](presentation/review/scientific-uq/full-track-mid.jpg) · [Exit 도착](presentation/review/scientific-uq/full-track-exit.jpg)

Chrome 검증에서 254개 시점의 세 메시와 보행자 좌표를 시연 파일과 대조했다. 재생·일시정지·Entry 복귀, 개별 선택, 카메라, 이전 예측 시연으로의 왕복, 2D 대체 화면을 확인했다. 1920×1080, 1440×900, 1366×768에서 발표 배치를 검사했고 기존 예측 조합 180개도 재검증했다.

## 발표 구성과 도표

| 장 | 발표 제목 | 주요 근거 |
|---|---|---|
| 1 | 보행자 예측에는 미래 위치뿐 아니라 불확실성도 고려해야 한다. | 횡단 예시와 현재 위치·가능한 미래·출구 도착의 세 질문. |
| 2 | 관측 불확실성과 미래 이동 불확실성을 구분하여 분석한다. | 두 불확실성 개념도, SPD·IMPTC·inD 역할과 여섯 단계 연구 흐름. |
| 3 | 보행자 위치 주석의 차이로부터 관측오차 분포를 추정했다. | A · f2 입력 이력과 SPD 학습 2,465쌍의 공분산 및 95% 측정오차 타원. |
| 4 | 확률적 미래 경로와 직접 시간 예측을 통해 공간·시간 UQ를 구성했다. | B · DD-MDN의 입력 10점과 미래 8시각. 별도 학습 XGBoost AFT를 병렬로 그린 구조도. |
| 5 | 관측오차 보정으로 미래 위치 예측오차를 약 81% 감소시켰다. | C · 동일 시각의 거리 오차와 두 데이터셋의 0~5 m 공통 축 ADE 막대. |
| 6 | 위치 예측 정확도의 회복이 불확실성의 신뢰성까지 보장하지는 않았다. | D · 명목 확률 질량과 경험적 포함률. 산점도에 각 조건의 포함률과 4초 영역 면적을 직접 표기. |
| 7 | 미래 이동분포를 횡단 완료확률로 변환하고 실제 기록으로 평가했다. | E·F · 개념도, f2 한 사례의 H1~H4 이산 확률과 실제 결과, H4 Brier 집계. |
| 8 | 횡단 완료 직전의 학습 데이터를 보완해 시간 예측 성능을 개선했다. | G · 훈련 시점의 거리 분포와 같은 M1의 H1~H4 사건별 가중 Brier 막대. |
| 9 | 관측부터 미래 예측과 횡단 완료까지 하나의 시스템으로 구현했다. | Entry → Exit 합성 위치 추적 후 기존 캐시 시점의 확률 예측과 실제 기록을 비교. |
| 10 | 보행자의 공간·시간 불확실성을 정량화하고 검증하는 시스템을 구축했다. | 두 실험의 비교 기준을 명시한 결과 네 행, 연구 기여와 적용 한계. |

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

### 세 조건 동시 재생

발표 9장과 독립 시연은 Clean·Noisy·Corrected의 Babylon.js 화면 세 개를 나란히 연다. 같은 Entry 좌표, 기록 시계, 사람, 경계와 카메라를 공유한다. 각 카메라는 자기 조건의 입력, 대표·후보 경로와 HDR만 따로 렌더링한다. 세 조건 버튼은 모든 단계에서 선택할 수 있다. 선택은 상세 수치와 강조 표시를 바꾸며, 재생 시각과 단계 전환 전의 조건을 유지한다. ‘선택 조건 확대’로 한 화면에 집중했다가 원래 비교로 복귀할 수 있다.

첫 프레임부터 각 화면에 해당 조건의 저장 입력 궤적을 원래 위치에 표시하고, 버튼 안에는 공통 축척의 확대 그림을 제공한다. f2의 경우 이는 Entry 이후 8.02초 원점에서 사용한 과거 10점이다. 이 시각을 화면에 명시한다. 보행자는 세 화면 모두 실제 Entry에서 출발하며, 3D 미래 예측은 각 조건에 실제로 저장된 시점에 도달하면 표시된다. [Entry에서 세 조건 비교](presentation/review/scientific-uq/three-conditions-entry.jpg) · [같은 시점의 세 미래 분포](presentation/review/scientific-uq/three-conditions-forecast.jpg)

### 저장된 미래 예측 보기 · 전체 횡단과 네 단계

[기본 f2 횡단 중의 공간 분포와 시간별 완료확률](presentation/review/scientific-uq/whole-crossing.jpg)

발표 9장과 독립 3D 시연의 **전체 횡단** 및 네 단계는 해당 보행자의 실제 **Entry 통과 위치**에서 시작한다. 이 위치는 저장된 통과 시각을 사이에 둔 두 기록 좌표를 시간에 따라 선형 보간해 구한다. 첫 프레임은 이 교차점이고, 이후에는 원래 기록 좌표와 시각을 쓴다. 세 사례에서 교차점과 방향별 Entry 선 사이의 거리를 확인했다. 기본 f2의 Entry → Exit는 10.08초이고, Entry부터 마지막 공개 좌표까지의 재생은 13.06초다.

시간축의 0은 Entry다. f2의 ‘관측 오차’ 탭을 직접 누르거나 같은 탭에서 **처음부터**를 누르면 Entry에서 시작해 보행 기록을 따라간다. Entry 후 약 7.12초에 저장된 입력 구간에 진입하고, 8.02초에 세 조건의 비교 원점에 도달한다. **비교 시점으로**를 누르면 이 원점으로 즉시 이동한다. 실제 예측과 관측오차 실험의 시점 및 좌표는 원자료를 따른다. [f2 Noisy의 첫 프레임](presentation/review/scientific-uq/entry-observation.jpg)

f2의 기준 예측은 공개 사례 파일에 1초 간격으로 저장되어 있다. 도달한 최신 시점의 후보 경로·대표 경로·선택 기한의 HDR과 저장 완료확률을 읽는다. 실제 통과 확인 후에는 통과 결과를 보여준다. H4만 저장된 시점은 H1~H3를 미저장으로 표시한다. Noisy와 Corrected의 공개 캐시는 사례마다 한 시점에 있으므로, 그 예측의 유효 구간에서만 겹쳐 본다.

### 조건별 재생

이전 배포 화면의 기본 f2 사례에서 2·3단계 및 정답 공개 전 4단계의 타임라인 최솟값과 최댓값이 모두 8초였고 재생 버튼도 비활성화되어 있었다. 현재 2단계의 **관측 재생**은 선택한 모델 입력의 0.9초 이력을 다시 보여준다. 실제 사람은 기록을 따라 걷고 색 고리는 해당 조건의 저장 입력점을 순서대로 지난다. 3·4단계의 **예측 재생**에서는 보라색 예측 보행자가 0.5초 간격의 저장 대표 위치를 선택한 기한까지 따라간다. 이때 파란 실제 보행자는 예측 시점에 머문다. 4단계에서 정답을 공개하고 **예측·실제 재생**을 누르면 두 움직임을 같은 시간축에서 비교할 수 있다.

재생 중 조건을 바꾸면 같은 시계에서 새 조건으로 이어진다. 정지한 상태에서는 같은 시각끼리 비교한다. 분포의 영역과 네 완료확률은 선택한 예측 시점과 기한을 기준으로 표시한다. 재생 중 보이는 이동 지점은 저장된 자료에서 가져온다.

## 수치와 그림 출처

교차 데이터셋 ADE는 `r_robustness/r_robustness_metrics.csv`의 Test / overall / All / pooled / horizon_s=4 행에서 읽는다. Clean 및 IID 1×의 noisy·filtered_mean 순서로 IMPTC는 0.283 / 3.925 / 0.742 m (유효 215), inD는 0.418 / 4.569 / 0.871 m (유효 99)다. 발표 코드는 같은 공개 집계의 JSON 사본을 사용한다. 다른 합성 오차 설정은 전체 강건성 보고서로 연결했다.

직접 시간 모형은 `pres/evidence.json → audit.matched`에서 dd_matched / test / calibrated M1 두 버전의 `event_weighted_brier`를 사용한다. Original의 H1~H4는 0.10827 / 0.04634 / 0.02714 / 0.04410, Exit-aware는 0.00618 / 0.01021 / 0.02503 / 0.02396이다. 기한별 유효 분모는 236 / 224 / 222 / 217이다. 훈련 표본 구성은 `audit.support`에서 읽는다.

시연 끝의 단일 사례 요약은 `demo/f2-full-track.json`의 254개 시점 각각에서 Noisy 또는 Corrected와 Clean 사이의 유클리드 거리를 구해 평균한다. 21.16 cm에서 8.79 cm로 감소했다(58.4%). 이 값의 대상은 같은 시각의 관측 위치다. 미래 경로 ADE와 완료확률은 각각 별도의 예측 실험에서 평가했다.


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

## 이번 발표 다듬기에서 수정한 파일

- `presentation/site/pres/story.js` — 제목, 근거, 10개 발표자 노트, 결론 표와 부록 링크.
- `pres/scientific-svg.js`, `pres/uq-figures.js` — 병렬 구조도, 원본 집계 선택, ADE·M1 비교 막대, f2 기한별 막대, Coverage·면적 직접 표기.
- `pres/full-track.js` — Exit에서만 표시하는 1건의 평균 관측오차 요약.
- `pres/uq.css`, `presentation.html`, `demo.html` — 발표 배치·자산 버전 및 동일한 `docs/presentation/` 배포본.
- `presentation/tools/uq_browser_check.mjs`, `presentation/review/scientific-uq/`, 본 보고서 — 표시 수치, 해상도, 전체 화면, 재생 검증 및 최신 발표 화면.

## 이전 시연 개편의 변경 파일

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

최종 발표는 1920×1080, 1440×900, 1366×768과 1440×900 전체 화면 모드에서 10장을 각각 렌더링해 본문과 하단 탐색 영역 경계를 확인했다. 표시 수치 검사에는 5장의 두 데이터셋, 6장의 포함률·면적, 7장의 확률과 Brier, 8장의 두 모형 네 기한, 10장의 결과표가 포함된다. 시연에서는 254개 좌표의 동기화와 Exit 요약을 확인했다.

2026-11-26, 사이트 커밋 `fae40db`의 [GitHub Pages 배포](https://github.com/riverblue72/view2risk/actions/runs/45749241390) 완료 후 공개 주소에서 같은 Chrome 검사를 통과했다. 공개 페이지에서 캡처한 10장으로 화면 기록을 갱신했다. 3D 180조합과 2D 180조합이 캐시와 일치했고 JavaScript 예외·실패한 자산 요청은 0건이었다. 보호 자료의 원본 바이트와 정적 사이트 221개 파일의 소스·배포 일치도 확인했다.

### 이전 시연 검증

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
