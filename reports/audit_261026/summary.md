# View2Risk MD 추가 감사 결과 — 261026

**전체 공개 시퀀스로 남은 관측 가능 항목을 추가 실행했다.** 기존 R/Q 모델·예측·결과는 보존했다. 핵심 추가분은 공식 지도 기반 완전/부분 횡단 분류, f1/f2/f3 공간·시간 연결, 공식 SPD K 투영 규약 확인, 조건별 R 분포와 전 행 품질 플래그다.

## 1. 횡단 완료/부분 관측

IMPTC Full01–05의 1,920트랙·1,710,765관측을 그대로 유지했다. 기준 설정의 트랙 분류는 서로 배타적이다.

| primary_class | tracks | sequences | dates |
| --- | --- | --- | --- |
| has_complete_rule | 787 | 246 | 15 |
| no_accepted_map_touch | 754 | 210 | 14 |
| touch_without_complete | 379 | 160 | 14 |

`has_complete_rule`: 최소1회의 완료 규칙을 만족. `touch_without_complete`: 횡단보도 접촉은 있으나 완료 규칙 미충족이며, 부분 관측·landing 부족·되돌아감 등을 포함한다. `no_accepted_map_touch`: 유효 status2 관측에서0.25m 지도 매칭 기준 접촉 없음. 세 트랙 수 합은1,920이다.

완료 이벤트는 **846회 /787트랙**이다. 트랙별 개수와 이벤트 개수는 다르며, 같은 트랙이 여러 횡단보도를 지날 수 있다.

| signal_group | complete_events | track_groups | sequences | dates | length_m | width_m |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | 180 | 179 | 130 | 14 | 10.90769458034634 | 3.943714907652958 |
| f2 | 386 | 385 | 190 | 14 | 15.776911240745935 | 3.890389799991635 |
| f3 | 280 | 278 | 153 | 13 | 9.999451441773502 | 3.74381242406913 |

## 2. 사전에 정한 완료 규칙과 민감도

공식 지면 지도 crosswalk 점을 연결 성분으로 나눈 뒤 PCA 축의0.5~99.5% 경계를 사용했다. 전체 원본의 `status=2`, 유한 좌표, `0<dt<=0.060s` 연속 구간만 완료 여부를 판별한다. 기본 기준은 양 끝 경계 밖0.25m, 폭 여유0.75m, 시작/끝 landing의 sidewalk/curb 지도 매칭0.25m 이내 및0.12초 지속이다. landing 검색은 해당 이벤트 앞뒤3초, 끝단4m 범위다.

반대편 양 끝의 관측이 있고, 진입~이탈 사이95% 이상이 여유 포함 횡단보도 직사각형에 있으며,50% 이상이 crosswalk 지도점이고,5m/s 초과 급점프가 없으면 `complete_rule`이다. 같은 쪽 복귀는 `returned_same_side`, 시작/끝 관측이 잘리면 `partial_censored`, landing 근거 부족은 `partial_missing_landing`이다. 불충족/이상 사례는 삭제하지 않고 분류해 남긴다. 모든 설정과 샘플링 seed는 집계 전 protocol.json에 고정했다.

| config | events | tracks | sequences | dates |
| --- | --- | --- | --- | --- |
| base | 846 | 787 | 246 | 15 |
| strict | 737 | 699 | 235 | 15 |
| wide | 886 | 820 | 247 | 15 |

이 수치는 **공식 지도와 기록 궤적에 적용한 운영 규칙에 따른 분류**다. 독립적인 사람이 표시한 완전 횡단 정답이나 분류 정확도는 아니다. 일부 시각적으로 완전해 보이는 경로도 landing 관측이 짧으면 보수적으로 미완료에 남는다. 포함률·모델 점수·G95를 좋게 만들기 위해 경계를 조정하지 않았다.

## 3. 신호 그룹의 공간·시간 연결

[공식 신호 도식](https://github.com/kav-institute/imptc-dataset/blob/main/images/traffic_light_signal_groups.jpg), [좌표 원점 설명](https://github.com/kav-institute/imptc-dataset#coordinate-system), [공식 지면 분류](https://github.com/kav-institute/imptc-dataset/blob/main/data_formats/ground_plane.md)를 대조했다. 긴 횡단보도와 원점의 위치, 양쪽 짧은 횡단보도 topology로 component1=f2, component2=f1, component3=f3를 연결했다. 도식에서 수동 선택한 중심3개+원점으로 아핀 등록 시 중심 RMSE2.02px이며,6개 그룹 순열 중 다음 후보15.41px보다 일관됐다. 이는 연결 근거이며 측량 정밀도 검증은 아니다. `map_signal_registration.png`, `registration_alternatives.csv`에 근거를 남겼다.

신호는 미래를 보지 않는 backward join으로 마지막 기록을 사용하고1.5초보다 오래되면 결측 처리했다. 횡단보도 밖의 관측에는 가장 가까운 신호를 강제 배정하지 않았다. 공간·시간 연결 Parquet은 data/imptc_signal_join.parquet이다.

완료 이벤트의 진입 시점 신호:

| entry_signal_code | signal_transition_within_1s | events | tracks | interpretation |
| --- | --- | --- | --- | --- |
| 4 | False | 781 | 730 | recorded signal at derived entry, not verified violation label |
| 4 | True | 11 | 11 | recorded signal at derived entry, not verified violation label |
| 10 | False | 45 | 44 | recorded signal at derived entry, not verified violation label |
| 10 | True | 9 | 9 | recorded signal at derived entry, not verified violation label |

신호 기록은1Hz이고 진입 시점도 지도 경계 보간값이다. ±1초 내 전환 여부를 별도로 표시했다. **빨간색 기록에서 진입한 이벤트를 검증된 신호 위반 정답으로 취급하지 않는다.** 이번 작업은 연결 감사이며, 신호/날씨를 기존 Q 예측 변수에 추가하거나 모델을 다시 맞추지 않았다.

## 4. SPD calibration 추가 점검

공식 DAIR-V2X [영상 시각화 도우미](https://github.com/AIR-THU/DAIR-V2X/blob/main/tools/visualize/vis_utils.py)의 `get_cam_calib_intrinsic`는 `cam_K`를3×4 형태에 넣는다. 해당 함수만 AST로 읽어21프레임에서 직접 실행하고 우리 K 구성과 정확히 일치함을 확인했다. 모든11,275프레임의 이미지 크기와 intrinsic width/height도 일치했다.

| annotation | projection | pairs | inside_bbox_pct |
| --- | --- | --- | --- |
| camera | K_SO3_diagnostic_only | 10109 | 80.3343555247799 |
| camera | K_official | 10109 | 99.42625383321791 |
| camera | K_with_D | 10109 | 48.92669898110594 |
| camera | P_supplied | 10109 | 16.60896231081215 |
| lidar | K_SO3_diagnostic_only | 10109 | 68.46374517756455 |
| lidar | K_official | 10109 | 93.69868434068653 |
| lidar | K_with_D | 10109 | 50.73696705905628 |
| lidar | P_supplied | 10109 | 17.667425066772182 |

K 방식은 기존 계산과 일치했다. 제공 P, 추가 plumb_bob distortion, 카메라 행렬을 강제로 SO(3)화하는 대안은 진단용으로만 대조했다. 어느 것도 원본이나 기존 투영/모델에 적용하지 않았다. 이 결과는 주석 중심과 공유2Dbox의 일관성이고 독립 calibration 오차율이 아니다.

제공 카메라 변환행렬11,275개 모두 정규직교 회전 조건을 만족하지 않았다. 일반 역행렬 roundtrip 최대 오차는3.14e-14m이나, 전치행렬을 역으로 오용하면 복원 오차 p95=1.308m이다. **K/P 사용 규약은 정리했지만 nonrigidity의 생성 원인은 공개 자료에서 확인하지 못했다.** 공급자 보정 정답 없이 행렬을 임의로 고치지 않았다. R은 계속 paired annotation discrepancy proxy다.

## 5. 조건별 R, Q 품질과 변수 인계

거리·bbox·시각차 사분위와 가림·절단 수준18개 층에 대해 관측·트랙 그룹·시퀀스·교차로 수, 잔차 RMSE/median/p95, track-macro RMSE, 편향/공분산을 추가했다(`r_conditions.csv`). 거리4구간의 RMSE는 약0.167/0.211/0.284/0.452m였다. 이는 여러 장소·트랙이 섞인 기술통계이고 거리의 인과 효과나 조건부 모델 향상 증거는 아니다.

기존 행동 임계값별 지원 수와 예측 진단을 보존했다. 전 관측 품질 플래그를 새 Parquet으로 내보냈다. 위치 차분 속력5m/s 초과104관측/5트랙,20m/s 초과0관측,0초 이하 또는60ms 초과 interval11개다. ID switch 의심을 위한 감사 플래그이지 ID-switch 정답은 아니다. B의 트랙 평균 속력과 트랙 내 표준편차 그림도 분리했다.

인계 결정: R은 거리 조건을 다음 조건부 설계의 우선 후보, 가림은 통제/진단 변수로 유지한다. bbox는 거리와 중복 점검, 절단은 희소 층 때문에 보류한다. Q의 속도·가감속·정지/재출발·방향 변화는 진단 후보로 유지하고 source_type은 통제한다. B는 초기 속도 사전분포 후보이며 별도 UQ 모듈로 만들지 않는다. 신호는 공간/시간 연결까지 확보했지만 현재 예측 모델에서는 제외한다. 채택 여부는 데이터 인계/설계 역할이며 Test를 본 뒤 조건부 모델 우수성을 선정한 것이 아니다. 세부 컬럼/단위는 source_columns.csv와 columns.csv, 결정은 decisions.csv다.

## 6. TFD와 기존 HTML 수치

TFD Example 단일 infrastructure view만 사용했다. 겹친 클립에서 같은 city/intersection/id/timestamp 관측을 한 번만 가중해16,739고유 관측,16,016유효 인접 increment의 속도벡터·위치 차분 일관성을 추가 점검했다. source ID를 실제 독립 사람으로 세지 않았다.

`q_velocity_increment_proxy = mean((Δvx²+Δvy²)/(2Δt))`의 사이트별 진단을 명시적 산식/단위 가정과 함께 저장했다. 이 값은 관측 잡음과 분리한 Q도, 기존 HTML의 q≈.05 재현도 아니다. 기존 HTML에는 q의 추정기·Δt 방식·68구간/4완전 횡단 선정 규칙이 없고, 찾아본 원래 PoC 스크립트에도 해당 q 계산은 없었다. 숫자만 맞춰 재현했다고 주장하지 않았다. `preliminary_claims.csv`에 재현 가능/불가와 근거를 분리했다. 원래 분석 코드를 확보해야 정확한 과거 수치 재현이 가능하다.

## 7. MD 항목별 완료 근거와 실제 남은 제약

`checklist.csv`는 원본 감사 MD의 체크박스37개와 파일럿 보고 필수6개를 각각 결과 파일에 연결한다. 실제 가능한 추가 집계/검사는 수행했고, 원본 데이터 수정·기존 보고서 덮어쓰기 없이 결과를 추가했다. 이전 '전부 완료'를 물리 참값 식별까지 완료했다는 뜻으로 읽으면 안 된다.

- 횡단/신호: 추가 데이터가 없어 못 한다고 남겨두지 않고, 공식 geometry로 운영 규칙과 공간/시간 연결을 만들었다. 독립 수동 GT는 여전히 없다.
- Calibration: 공식 K 규약 확인과 원본 행렬 수치 검사는 완료. 행렬 nonrigidity 원인은 공급자 설명/독립 보정 없이 확정 불가다.
- 과거 q≈.05: 원래 코드·산식이 없어 동일 수치의 정확 재현은 불가. 재현 가능한 대체 진단을 별도로 제공했다.
- G95·신호 최적화·통합 순수 R/Q 주장은 MD 범위 밖이며 실행하지 않았다.

## 8. 파일과 재현

바로 볼 표는 result.csv, crossing_full.csv, crossing_counts.csv, tracks.csv, signal.csv, projection.csv, r_conditions.csv, decisions.csv, checklist.csv다. 원시 행/ID를 가진 신규 Parquet은 data/에 있다.

검증: execution_freeze.json의 사전 프로토콜/소스/입력 해시, 기존 full manifest119항목, 기존 샘플 입력·결과 해시, 이번에 읽은 raw calibration·신호 해시를 다시 대조했다. 양 끝 반대 방향/양의 시간/영역 보존/인과적 신호 연결을 확인하고,22개 층화 사례의 원시 JSON 좌표·status·시각을 독립 재조회했다. 별도의 제공 topview와4사례를 대조하는 그림도 저장했다. 같은 처리 계통의 정보라 독립 GT 정확도를 증명하지는 않는다.

CPU 실행: sbatch run.sh → sbatch run_remaining.sh → sbatch run_review.sh → python scripts/finalize.py. 이 명령은 기존 모델 학습 명령이 아니다. Python/버전·코드/결과 해시는 environment.json 및 manifest.json에 기록했다. 완료 디렉터리는 새 분석으로 덮어쓰지 않는다.
