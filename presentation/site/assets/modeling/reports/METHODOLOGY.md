# View2Risk 최종 방법론

## 모델과 시간 범위

메인 예측기는 [공식 DD-MDN](https://github.com/kav-institute/ddmdn) 하나다. [논문](https://arxiv.org/abs/2602.11214)과 공개 IMPTC Full / inD Full 체크포인트를 사용한다. 두 실제 config 모두 입력 10점 × 0.1초(첫~마지막 span 0.9초), 출력 +0.5~4초 8점이다. 재학습하지 않았다. 1초 Rolling Forecast는 새 실제 관측으로 다시 조건화하는 것이며 최초 시점의 15~20초 예측 검증이 아니다.

`p_Q(X_future | X_past, C)`는 시점별 GMM과 joint anchor trajectory mixture로 표현한다. 20개 discrete hypothesis의 confidence score는 정규화된 경로 확률이 아니다. R+Q 화면에서는 여러 posterior history의 실제 DD-MDN 가설 중 높은 원본 confidence 경로를 표시하며, 그 점수 역시 혼합분포의 경로 확률이 아니다.

## 데이터와 인과적 입력

IMPTC의 기존 GT v1 semantic 경계 및 264개 sequence를 읽으며 원본을 수정하지 않는다. status=2의 실제 보행자 클래스만 사용한다. 추적 단절을 별도 구간으로 나누어 속도 계산이 공백을 가로지르지 않게 한다. 통계의 사람 수는 원본 recording/track ID 기준이다. 전역적으로 동일한 사람인지는 확인할 수 없다.

inD는 승인된 v1.1 원본 33 recording을 [공식 drone-dataset-tools](https://github.com/ika-rwth-aachen/drone-dataset-tools)로 로드한다. 좌표는 공식 DD-MDN inD 전처리와 동일하게 `(xCenter, -yCenter)`로 변환하며 시간은 frame/frameRate이다. 출력과 지도도 같은 좌표계를 사용한다. 차량 bounding box는 공식 함수의 4×2 꼭짓점을 그대로 사용한다. 실제 지도는 공식 배포 semantic mask를 사용한다. [inD 데이터 논문](https://arxiv.org/abs/1911.07602).

입력 보간·방향·주변 객체 이력에는 origin 이후 좌표를 사용하지 않는다. 정지 상태의 방향은 과거 관측만으로 결정한다. 공식 offline 전처리와 인과적 adapter의 차이를 기록하며, 공식 HDF5 전체 Test와 raw online 데모의 수치를 혼합하지 않는다. 미래 GT는 입력 생성 후 오차 평가에만 사용한다.

## PedPy 분석

[PedPy](https://github.com/PedestrianDynamics/PedPy) 1.5.1의 TrajectoryData, compute_individual_speed, compute_classic_density, compute_n_t를 사용한다.

- 속도: 25Hz 자료에서 ±5프레임, 총 0.4초 좌표 차분. 끝부분은 one-sided 계산. 미래를 사용할 수 있는 기술 분석이며 DD-MDN 입력으로 제공하지 않는다.
- 밀도: 구역 안에서 관측된 사람 수/물리 면적, 명/m². 경계 위 점의 포함 여부는 PedPy 정의를 따른다. Voronoi 밀도가 아니다.
- IMPTC 분석 구역: semantic corridor의 convex hull. PedPy의 convex area 조건을 충족하기 위한 분석용 구역이며 완료 GT Entry/Exit를 변경하지 않는다.
- inD 분석 구역: 공식 camera footprint. 분석선은 footprint 중간의 세로선이며 횡단 완료 Exit라고 주장하지 않는다.
- 흐름: PedPy로 찾은 개인별 최초 분석선 통과 수/해당 recording 관측시간, 명/s. 양방향을 합치며 반복 통과 횟수가 아니다. UI 값은 recording 전체 평균이다.
- 정지: 속도 0.2m/s 미만이 1초 이상. 감속: 가속도 −0.3m/s² 미만이 0.4초 이상. 재출발: 정지 구간 종료 후 1초 내 0.3m/s 초과. 방향변화: 1초 진행 방향 변화가 45도 이상인 상태가 0.4초 이상이며 두 변위가 모두 0.3m 이상.

이는 규칙 기반 pseudo-label이며 실제 의도 GT 또는 학습된 정지 head가 아니다. 작은 가속도·방향 변화는 미분 잡음에 민감하다. 속도·밀도별 오차 비교는 사후 기술 분석이다. 통계를 모델에 추가 입력하지 않는다.

## SPD R_proxy와 상태 추정

관측 모델은 `y_t = H x_t + b_R + ε_t`, `ε_t ~ N(0,R)`이다. 기존 SPD Train 2,465쌍에 적합한 bias와 covariance를 그대로 읽는다. 전체 10,109쌍의 기술 통계와 구분한다. 실제 detector error가 아니라 카메라–LiDAR annotation disagreement이다. [V2X-Seq 출처](https://github.com/AIR-THU/DAIR-V2X-Seq).

[FilterPy](https://github.com/rlabbe/filterpy)의 KalmanFilter와 Q_continuous_white_noise를 사용한다. 상태는 `[x,y,vx,vy]`. R의 단위는 m², q_filter=0.5m²/s³는 고정된 공학적 가정이다. q_filter를 DD-MDN의 행동 Q와 동일시하지 않는다. Test로 q_filter를 튜닝하지 않았다. 광범위 위치 prior와 속도 prior에서 관측을 갱신한다. dropout에서는 관측 update를 생략한다. [Kalman 참고 설명서](https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python).

실험은 ①clean, ②Train R Gaussian noisy, ③Kalman mean input, ④R+Q, ⑤마지막 0.4초 dropout의 hold-last와 R+Q, ⑥AR(1)=0.8 상관 오차의 noisy와 R+Q이다. 조건 간 동일 seed와 동일 checkpoint를 쓴다. 잡음은 타깃에만 적용하고 지도·주변 객체는 정확하다고 가정한다. SPD 좌표의 bias/covariance를 IMPTC/inD XY에 그대로 옮기는 축 정렬은 가정이며 물리적으로 검증하지 않았다. 상관 오차 조건에서 white-noise Kalman filter는 일부러 모델 불일치를 가진다.

## 시간 상관을 유지한 R+Q

`p(X_future | Y_past) = ∫ p_DDMDN(X_future | X_past,C) p_R(X_past | Y_past) dX_past`.

현재 origin까지의 필터 결과로 forward-filtering backward-sampling(FFBS)을 수행한다. 마지막 상태를 posterior에서 뽑고, 과거 상태를 `p(x_t | x_(t+1), Y_≤origin)`에서 역순으로 뽑는다. 이에 따라 과거 프레임을 독립적으로 샘플링하지 않는다. origin 이후 관측을 사용한 smoothing이 아니다.

과거 경로 8개를 각각 실제 DD-MDN에 넣어 얻은 GMM을 1/8 가중치로 혼합한다. 지도 crop·회전·ego 좌표는 각 샘플에 맞게 갱신한다. 각 공식 joint anchor mixture에서 미래를 샘플링하여 총 3,200개 경로를 구성한다. 위치 HDR은 시점별 2,500개 MC와 120×120 adaptive grid로 계산한다. 유한 MC·grid 근사이며 MC 수렴성을 확정하지 않았다.

DD-MDN 자체가 annotation noise를 이미 학습했을 수 있으므로 R을 중복 반영할 가능성이 있다. clean/noisy/filtered-mean/R+Q 비교는 그 영향을 보는 진단이지 R·Q의 물리적 분리 증명이 아니다. R+Q가 반드시 오차를 줄이거나 완료확률을 낮춘다고 가정하지 않는다.

## Exit 및 평가

IMPTC joint future samples의 최초 opposite Exit 통과를 찾아 H=1/2/3/4초 내 비율을 계산한다. 0.5초 점 사이를 선형 보간한다. GT v1은 최초 통과시각과 반대편에서 0.12초 이상 관측된 확인 조건을 가진다. 모델 표본에는 그 관측 확인 과정이 없으며 joint anchor 내 시간 공분산도 제한적이다.

실제 GT 통과시각 구간이 horizon 경계와 겹치거나 검열로 확인할 수 없으면 unknown이다. 이미 Exit를 지난 origin도 완료 위험 평가에서 제외한다. 이를 실패(0)로 만들지 않는다. raw Brier와 Reliability는 판정 가능한 부분집합의 complete-case 진단이며 IPCW 모집단 추정이 아니다. 별도 Calibration을 하지 않았으므로 Simulation-only이다. inD의 semantic Exit 검토가 없어 도달 확률을 계산하지 않는다.

위치 비교는 모든 조건에 미래 8점 GT가 있는 동일 window를 사용한다. ADE/FDE, minADE/minFDE, 시점별 GMM NLL, Coverage, 물리 HDR 면적을 계산한다. min 지표는 oracle 선택이다. window/event/recording 수를 구분한다. 공개 inD Test는 recording 단위 분리이며 학습과 장소가 겹칠 수 있어 외부 교차로 일반화로 주장하지 않는다.

개인 예측의 독립성을 가정한 집단 전체 완료확률과 마지막 완료시간을 만들지 않는다. 아직 개인 완료확률이 검증되지 않았으므로 검증된 예상 잔류 인원도 표시하지 않는다.

## 라이선스와 보존

inD 원본 및 복원 가능한 재생 자료는 외부 배포하지 않는다. 웹 서버는 127.0.0.1에만 bind하고 SSH 터널로 승인된 사용자에게 제공한다. 정적 웹 폴더에 inD CSV를 두지 않으며 제한된 private API만 제공한다. 이 서버를 공개 호스팅하면 안 된다. 집계 지표는 좌표 재구성이 불가능한 통계로 분리한다.

기존 N00/N01/N02·22개 GPU 실험·Survival 결과는 원래 별도 프로젝트에 보존되어 최종 메인 모델이나 주요 비교 대상에 포함되지 않는다. v3와 Rerun도 보존했다. 추가 학습·GPU 잡은 없다.

R+Q의 대표 경로 첫 구간 속도는 posterior 평균 현재 위치에서 첫 미래 위치까지의 차분이다. 이후 구간은 해당 경로의 연속 미래 좌표 차분이다. 이는 별도 속도 head나 각 posterior history의 시작점을 보존한 속도 posterior가 아니다. GT 경로의 시작점은 조건과 무관하게 Clean의 실제 현재 위치로 유지한다.


## 최종 품질 점검 보충 — release_qa_20261110

inD semantic 변환은 공식 채널별 비교 후 red-channel을 취하는 방식과 정확히 맞췄다. 실제 blocking RGB (70,70,70)와 코드 사전 (70,70,71)의 차이 때문에 이전 exact RGB 방식은 장애물을 누락했다. 수정 후 기존 99개 origin·8조건을 동일하게 재계산했다. IMPTC는 원래 공식 방식과 일치했다.

0.1초 iid 위치오차 차분에서 Cov(δv)=2R/dt², Cov(δa)=6R/dt⁴. X/Y 위치 SD 0.156835/0.177521m는 속도 SD 2.217981/2.510527m/s, 가속도 SD 38.416562/43.483602m/s²로 증폭된다. 상관오차에서는 이 iid 공식이 그대로 성립하지 않으며 별도 조건으로 유지한다.

KF Q_delta는 상태 [x,y,vx,vy]에서 q * [[dt³/3,0,dt²/2,0],[0,dt³/3,0,dt²/2],[dt²/2,0,dt,0],[0,dt²/2,0,dt]]이다. q=0.5m²/s³와 P0=diag(10⁶,10⁶,25,25)를 바꾸지 않았다. FFBS의 전체 평균과 공분산을 batch Gaussian conditioning과 검증했다. 이 수학 fixture를 실측 성능에 섞지 않았다.

R+Q 입력은 조건부 history별 ego 회전·translation·지도 crop으로 실제 모델에 전달된다. 표시용 평균 history에는 단일 ego rotation이 없으므로 rotation=null로 저장하고, 실제 context는 input_contexts 8개로 남긴다. 이전의 마지막 샘플 rotation 메타데이터 혼합은 수정했으며 IMPTC 예측 수치는 불변이다.

전체 미래 covariance = E_history[Cov(X_future|history)] + Cov_history(E[X_future|history]). 두 실제 사례에서 이 항을 기록했지만 물리적 R/Q의 정확한 원인 비율로 해석하지 않는다. DD-MDN 학습 annotation noise와 추가 R의 중복 여부는 독립 잠재 GT 없이 식별하지 못한다.

공식 inD의 raster scale=12, radius=120px와 recording별 orthoPxToMeter를 따르면 실제 crop 폭은 약 36.576m 또는 23.461m이다. nominal grid 좌표 범위는 20m이다. 이는 공식 checkpoint 전처리의 특성이므로 Test 결과에 맞춰 바꾸지 않았다. 이를 물리적 장면 크기가 정확히 20m라고 주장하지 않는다.

현재 R+Q가 Clean 수준으로 회복되지 않았고, 17개 사례는 일반화 결론을 내리기에 부족하다. 상세 수치는 FINAL_RESULTS.md, 수정 및 종료 판정은 FINAL_RELEASE_CHECK.md를 따른다.


SPD 원본 산출 코드와 [공식 좌표 명세](https://github.com/AIR-THU/DAIR-V2X-Seq/blob/main/dataset/v2x-seq-spd/README.md)를 추가 대조했다. infrastructure camera/virtual-LiDAR의 3d_location은 모두 infrastructure virtual-LiDAR 좌표이며, 기존 코드는 두 주석에 같은 world 변환을 적용한 뒤 XY 차이를 계산한다. 축·단위 처리에는 이 검토에서 오류가 발견되지 않았다. 다만 적합한 R은 시각 보정 전 dx/dy를 사용하므로 센서 timestamp 차이의 영향도 포함할 수 있다. 이를 독립 detector 측정잡음이라고 해석하지 않는다. 이전 R 모델 선택은 Student-t4였지만 이번 고정 통합은 Train Gaussian moments를 사용한 가정이며 그 선택 모델을 재현했다고 주장하지 않는다.

## GitHub Pages 공개판

위 private 서버 구현과 별개로, 공개판은 API 없는 정적 export다. 실제 IMPTC의 짧은 라이선스 허용 구간과 사전 계산 결과만 제공한다. inD는 비복원성 집계 지표만 표시한다. 자세한 배포 범위는 final/DATA_POLICY.md를 따른다.
