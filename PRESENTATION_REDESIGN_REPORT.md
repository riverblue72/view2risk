# View2Risk 발표 및 시연 개편

[발표 1장](https://riverblue72.github.io/view2risk/presentation/presentation.html#scene-1) · [독립 시연](https://riverblue72.github.io/view2risk/presentation/demo.html) · [전체 결과와 부록](https://riverblue72.github.io/view2risk/presentation/results.html)

연구 질문은 보행자의 현재 위치와 미래 운동의 불확실성을 횡단 완료확률로 변환했을 때 그 예측이 실제 기록과 얼마나 일치하는가이다. 공식 사전학습 DD-MDN은 미래 운동 분포를 제공한다. View2Risk는 관측오차 실험, 의미 경계와 완료 정답 구성, 경로 분포의 시간별 완료확률 변환, 기록 대조와 시각화를 구현했다.

## 발표 구성

| 장 | 화면에 포함한 자료 |
|---|---|
| 1. 문제 정의 | 실제 f2 경로와 3초 예측영역. 현재 위치, 가능한 미래, 완료 시각이라는 세 질문과 교통 분야의 활용 맥락 |
| 2. 데이터 | SPD 주석 차이, IMPTC 궤적·경계·완료 정답, inD 보조 궤적 평가의 역할. 같은 사례의 과거 관측과 미래 분포를 나란히 표시 |
| 3. UQ 구조 | 기준 관측 직행과 선택적 Kalman 보정, 공식 DD-MDN, 공간 HDR와 시간별 Exit 확률, 공통 정답 평가. Conditional AFT 및 XGBoost AFT의 직접 시간 예측 경로 |
| 4. 합성 관측오차 | 같은 평가 집단의 위치·완료 오차 표와 4초 공간영역 표. Noisy 대비 보정 후 ADE 81.1%, Brier 74.4% 감소 및 보정 후 78.51% 포함률 |
| 5. 횡단 완료 | 실제 Entry·Exit, 과거, 경로 후보, 대표 경로, endpoint HDR, 실제 미래와 완료 시각. 1~4초 확률을 이산 막대로 표시 |
| 6. 시간 예측 개선 | 기존 및 Exit-aware 학습 자료의 거리 범위와 수량, 보정된 XGBoost AFT M1의 동일 Test 전후 비교 |
| 7. 대화형 시연 | 독립 시연과 동일한 컴포넌트를 슬라이드에 직접 삽입 |
| 8. 기여와 한계 | 관측·운동 모델링, 완료 UQ, 실제 기록 검증. 사전학습 모델 의존성, 대리 R, 불완전한 보정, 과도한 FFBS 영역, 정지·재출발 자료 부족, 기준선 비교, Test 재사용, 4초 한계, 오프라인 평가 |

## 시연 동작

- **A · 관측**은 같은 과거의 기준점, 합성 관측점과 보정 이력을 겹쳐 그린다. 마지막 유효 합성 관측에 저장된 측정 공분산 `filter_R`로 계산한 2차원 Gaussian 95% 타원을 표시한다. 관측 누락 설정에서는 실제로 남은 여섯 측정만 점으로 표시한다.
- **B–C · 미래 경로와 완료확률**은 단일 상태로 사례·잡음·입력 조건·H를 공유한다. 경계, 과거와 미래는 거리 비율을 보존하는 횡단축 좌표로 그리며 미터 축척을 표시한다. 저장된 20개 후보와 원래 confidence가 가장 높은 대표 경로를 그린다. 68% 및 95% 영역은 선택 시각의 저장된 HDR 윤곽이다. 이산 후보의 개수를 세어 막대의 확률을 만드는 방식과 구별되도록 막대에는 별도로 저장된 joint 분포 표본의 통과율을 사용했다.
- **실제 정답 공개**는 공간의 실제 미래와 시간별 실제 결과를 함께 켜고 끈다. 최초 진입과 사례 교체 시에는 정답이 감춰진다. 조건 전환은 같은 실제 미래를 유지한다. 잔여 거리와 종방향 속도는 기준 관측의 특징이다. 직접 시간 예측은 접을 수 있는 별도 표에 원래 입력 기준으로 표시한다.
- **D · 집계 검증**은 합성 관측오차, 공간영역, Exit-aware M1 결과만 표시한다. 사례 선택은 이 집계에 영향을 주지 않는다.
- 공개 시연은 IMPTC의 허용된 세 기록과 각 기록의 정확한 예측 시작 시점을 사용한다. 설정은 독립 오차 0.5×·1×·2×, 시간 상관 1×, 관측 누락 1×이다. 실제 기록에서 4초 뒤에 일어난 완료는 관측 사실로 표시하며 예측 막대는 4초에서 끝난다.

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

정적 소스 `presentation/site/`와 Pages 배포본 `docs/presentation/`에 같은 파일을 적용했다.

| 파일 | 변경 |
|---|---|
| `presentation.html`, `pres/story.js` | 8장 구성, 해시 내비게이션, 키보드, 노트, 실제 그림과 표, 내장 시연 |
| `demo.html`, `pres/uq-replay.js` | 단독·내장 공통 상태와 네 가지 시연 보기 |
| `pres/uq-figures.js`, `pres/uq.css` | 저장된 경로·HDR·타원·막대·집계표 렌더링, 반응형 서식 |
| `pres/compare-data.js` | 기존 정확한 사례 결합을 재사용하며 새 화면에서 쓰지 않는 대형 집계 로드를 생략 |
| `results.html` | 시연과 전체 역사적 결과 링크 |

그 밖의 변경은 `presentation/README.md`, `presentation/tools/uq_browser_check.mjs`, 이 보고서이다. 기존 상세 비교의 `pres/simulation.js`와 Results의 `pres/findings.js`는 해당 페이지에서 계속 사용한다.

## 검증

- Chrome 158, 데스크톱 1366×768 및 모바일 폭 390×844에서 8장 순회, 수치·사례 표시, 가로 넘침, 내장 시연 정답 공개를 검사했다.
- 이전·다음, 번호 이동, 좌우 방향키, 브라우저 뒤로 가기, 노트 및 Escape, 전체 화면 진입·해제를 검사했다.
- 단독 시연에서 3사례 × 5설정 × 3조건 × 4시간의 180개 조합을 순회했다. 위치의 선택 시간, 원본 확률, 두 HDR, 대표 경로, 실제 완료 결과를 대조했다. 화면에 그려진 GT의 모든 꼭짓점을 원래 사례의 실제 XY와 비교했다. GT 표시·숨김, 관측 타원, 직접 추정 비교, 집계 전환과 부록도 검사했다.
- `python3 presentation/tools/verify_static.py`로 정적 소스와 배포 사본 216개 파일의 해시 일치 및 공개 파일 검사를 통과했다. 세 사례 각각에서 모든 사용 조건의 시작 시각, GT 레이블, 실제 미래 XY, 최대 4초 지원 범위를 원본 파일과 확인했다.
- 검증 범위는 저장된 기록의 표시와 브라우저 조작이다. 실제 센서 전이, 새로운 날짜에서의 보정, 정지·재출발 성능과 현장 안전 효과는 이 개편에서 평가하지 않았다.

첫 게시 시도에서 GitHub Actions 빌드는 성공했고 Pages 배포 API가 HTTP 502를 반환했다. 해당 실행의 [배포 로그](https://github.com/riverblue72/view2risk/actions/runs/45649969535)에 서버 응답이 기록돼 있다. 발표 HTML은 새 자산에 버전 식별자를 사용해 이전 스크립트 캐시와 구분한다.

최종 화면 커밋 `8d8a720`의 [Pages 빌드·배포](https://github.com/riverblue72/view2risk/actions/runs/45650374293)가 성공했다. 공개 URL에서도 같은 Chrome 검증을 실행해 데스크톱·모바일 8장, 탐색·노트·전체 화면, 시연 180조합의 공간·확률·GT 일치, 집계와 부록을 확인했다. 검증 중 JavaScript 예외와 HTTP 오류 응답은 0건이었다.
