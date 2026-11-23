# View2Risk — Final Website & Simulation Presentation

## 정책

기본 Predictor는 공식 DD-MDN Clean Q-only이다. Noisy Q-only와 Legacy R+Q는 Observation Robustness를 켰을 때만 선택할 수 있다. IMPTC Full/inD Full checkpoint를 유지하며 추가 학습·새 UQ·새 추론은 수행하지 않았다. CA6/corrected XY/Calibration은 Results의 Exploratory Comparison에만 표시한다. 기본 모델을 교체하지 않는다.

## 화면과 시간

- 입력: 최근 10점 × 0.1초, 첫~마지막 실제 시각 차이는 0.9초.
- 출력: +0.5~4초 8점, 기본 Rolling 갱신은 1초. 4는 길이 4m가 아니다.
- 전체 기록 GT는 비공개 원본에서 읽은 표시용 자료다. 모델 예측으로 연결하거나 완성하지 않는다. 원래 저장된 추론 결과는 그대로 보존한다.
- 17개 사례/153개 cached origins(각 사례 +0~+8초). 각 캐시의 +4초 유효 범위가 끝나면 새 예측을 지어내지 않고 GT-only 재생임을 표시한다. 전체 GT에는 추적 단절도 유지한다.
- 모델의 20개 discrete hypothesis confidence는 정규화된 발생확률이 아니다. GMM/anchor weights와 구분한다.

## Geometry

IMPTC GT v1의 semantic Entry/Exit를 사용한다. 현재 track XY를 횡단축 s와 측면축 l로 투영하고 동일 l에서 piecewise-linear Exit까지의 축방향 거리를 구한다. 반대 방향과 이미 Exit 통과한 위치를 처리하며, lateral_limits 밖은 계산을 보류한다. semantic 경계 간 축방향 길이는 지도 추정값이다. 실측 전체 횡단보도 길이가 검증됐다고 주장하지 않는다.

inD semantic Exit는 미검증이므로 crossing panel과 확률을 표시하지 않는다. IMPTC H=1/2/3/4초 Exit 추정은 계속 Simulation-only이다. 최근 위치 Calibration 실험을 Exit probability calibration으로 해석하지 않는다.

## 설명과 실제 수치

How It Works는 공식 DD-MDN(LSTM/CNN/Attention/Diffusion/dual MDN)과 View2Risk가 추가한 경계/rolling/SPD/FilterPy/PedPy/UQ 평가/3D 시각화를 구분한다. 논문 데이터셋 ETH/UCY/SDD/IMPTC/inD와 실제 사용한 Full checkpoint를 구분한다.

KaTeX로 시점별/16D joint mixture, R, FFBS 적분, first passage, ADE/FDE/NLL/Coverage/HDR 면적을 표시한다. bias/covariance는 실제 저장 JSON에서 읽는다. R 원본의 m², q_filter의 m²/s³를 구분한다. 모델은 XY이며 높이는 캐릭터 표현이다.

공식 IMPTC 전체 Test 120,871 windows(ADE 0.391471m, FDE 0.870994m, Coverage68 66.73%, Coverage95 93.97%)와 17개 고정 사례의 SPD 합성 관측오차 비교를 분리한다. 그래프는 원본 JSON의 실제 값으로만 구성한다. Coverage와 95% HDR area를 함께 읽는다. PedPy의 속도/밀도/흐름/행동은 실제 데이터의 기술 통계이며 상태는 pseudo-label이다. IMPTC corridor와 inD image rectangle은 면적 정의가 다르다.

## 보존·라이선스

수식 자산 폴더를 반영하는 과정에서 기존 Babylon 자산 참조가 누락되어 3D 로딩이 실패했다. 백업의 Babylon/지도 파일을 정확히 복원하고 새 버전 URL로 404 캐시를 회피했다. 이후 실제 3D 출력·재생·모드 전환을 포함한 검사를 다시 통과했다.

기존 website/serve.py는 `reports/presentation_20261111/before/`에 백업했다. 원본 src/configs/outputs/private cases는 시작/종료 hash가 같다. 표시용 확장 사례는 `private/presentation_cases/`에 별도 저장했다. 원래 캐시의 forecasts를 변경하지 않았다.

서버는 127.0.0.1:18773에만 bind한다. inD 원본·지도·복원 가능한 궤적은 승인된 SSH 터널에서만 표시한다. 외부 웹 배포나 GitHub push는 하지 않았다. GitHub 소개용 문서는 집계와 설명만 포함하며 private API 자료를 동봉하지 않는다.

## 브라우저 검증

26개 검사 통과. 기본값/선택적 R/시간 범위/거리 계산/GT 재생/실제 metric/수식/지도/재생·일시정지/inD 확률 미표시/런타임 오류를 검사했다.

## 공식 출처

- DD-MDN: https://github.com/kav-institute/ddmdn
- Paper: https://arxiv.org/abs/2602.11214
- PedPy: https://github.com/PedestrianDynamics/PedPy
- FilterPy: https://github.com/rlabbe/filterpy
- inD Tools: https://github.com/ika-rwth-aachen/drone-dataset-tools
- V2X-Seq: https://github.com/AIR-THU/DAIR-V2X-Seq
- KaTeX: https://katex.org/ (MIT, local 0.16.11 assets)
