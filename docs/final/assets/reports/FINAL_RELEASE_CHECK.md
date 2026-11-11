# View2Risk — FINAL_RELEASE_CHECK

Run ID: `release_qa_20261110` · 기존 final_uq 유지 · 새 학습/데이터/GPU/기능 확장 없음.

## PASSED

- 원본 데이터·checkpoint·기존 실험 보존. 변경 전 코드·결과·사례 snapshot 존재.
- R source hash/공분산 단위/PSD/bias, Q_delta 상태 순서, FFBS joint conditioning 검사 통과.
- 153개 origin의 동일 seed 입력 재생성. 두 고정 사례의 4조건 모델 출력 재현.
- inD blocking 팔레트 호환성 수정 및 기존 99 origin × 8조건 재검사 완료.
- R+Q 평균 표시 입력과 8개 조건부 context 구분. 예측값과 분리한 메타데이터 정정.
- 공식 IMPTC 전체 Test·IMPTC 위치 지표·PedPy·Exit 지표 변경 없음.
- 기술 검사 47/47 통과. 하이퍼파라미터·체크포인트·seed·GT·표본 선택 변경 없음.
- 기존 origin CSV 누락 링크를 실제 153개 시점으로 정정.
- Results 순서: Model Overview → Pedestrian Dynamics → UQ Results → R Impact → Crossing Completion → Methodology.
- 모든 6개 결과 그래프에 데이터셋, 표본, 조건, horizon/단위 표기. Coverage와 면적을 함께 제시.
- 브라우저: 58개 검사 통과.

## LIMITATION

- R+Q는 Clean 수준을 회복하지 못했다. 높은 Coverage에는 넓은 영역이 동반된다.
- 17개 고정 사례는 탐색 진단이다. 전체 데이터셋·새 교차로 일반화 증거가 아니다.
- SPD annotation disagreement를 실제 detector noise로 해석하지 않는다. 시각 보정 전 잔차이므로 timestamp 차이도 포함할 수 있다. 데이터셋 간 좌표축 전이는 가정이다. 기존 Student-t4 선택 모델과 이번 Gaussian moments 가정은 구분한다.
- 0.1초 차분이 입력 속도·가속도와 heading 잡음을 증폭한다. 이를 줄이기 위한 새 설정 탐색은 하지 않았다.
- q_filter와 초기 prior는 고정 가정이며 최적성을 검증하지 않았다. 8개 과거 MC와 HDR grid의 수렴성을 확정하지 않았다.
- DD-MDN 기존 annotation noise와 추가 R의 중복을 물리적으로 분리할 수 없다.
- 공식 inD context raster의 physical scale/nominal grid 차이는 checkpoint 호환성을 위해 유지했다.
- 1~4초 완료확률은 raw complete-case 진단이다. Calibration 미실행, Simulation-only. 위치 Coverage와 완료확률 Calibration은 별개다.
- inD density의 넓은 영상 구역과 IMPTC corridor는 밀도 해석이 다르다. 행동은 pseudo-label이다.

## BLOCKED

- inD semantic Exit GT 검토가 없어 inD 완료확률은 계산하지 않는다.
- 검증된 장기(15·20초) 완료확률·집단 전체 완료확률은 제공하지 않는다. 별도 근거 없이 확장하지 않는다.

## 발견·정정 이력

1. inD `(70,70,70)` blocking 색이 exact RGB 어댑터에서 누락됨 → 공식 채널 매핑으로 수정, 같은 모든 inD 조건 재계산.
2. 평균 posterior 표시 이력에 마지막 샘플 회전이 붙음 → display rotation=null, 8개 원본 context 별도 기록. IMPTC 예측 수치 불변.
3. origin CSV 링크 누락 → 현재 153개 origin 파일로 연결.
4. IMPTC exact RGB 검사 초기 실패는 원본 팔레트와 사전의 1채널 차이를 드러낸 검사였다. IMPTC 기존 공식 red-channel 변환은 올바르게 blocking을 유지했다. 모델 수정 없이 공식 호환성 검사로 기준을 명확히 했으며 초기 진단도 보존했다.

수정 전후 결과는 모두 공개된 내부 보고서에 포함하며, 좋아진 조건만 선택하지 않는다. 재학습·Test 튜닝에 따른 개선이라고 주장하지 않는다.

## 종료 판정

기능·수치·그림·수식·출처·한계 표기 정합 검사 통과. 위 LIMITATION/BLOCKED를 유지한 최종 연구용 릴리스로 종료한다.

이후 범위는 기존 결과의 발표 준비이며 추가 AI 모델 개발·기능 확장은 없다.
