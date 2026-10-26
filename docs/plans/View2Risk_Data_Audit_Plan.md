# View2Risk — 데이터 탐색·품질 분석 및 R/Q 후보 요소 선정 계획

> **현재 단계:** 데이터 미다운로드 → 샘플 확보 → 스키마 조사 → 데이터 품질 분석 → 모델링할 요소 결정  
> **이번 단계에서 하지 않는 것:** Kalman Filter 학습/튜닝, 최종 R·Q 추정, Monte Carlo, G95 계산, 신호 최적화  
> **목적:** '어떤 불확실성을 만들까?'를 막연히 정하는 대신, **실제 공개 데이터로 무엇이 측정·검증 가능한지** 먼저 확인한다.

---

## 0. 지금까지의 결정과 기존 HTML과의 관계

- **핵심 UQ 축은 2개:**
  - **R (measurement/perception uncertainty):** 보행자 위치를 관측할 때 생기는 오차와 그 조건별 변화.
  - **Q (motion/process uncertainty):** 특정 움직임 모델로 미래 상태를 예측할 때 설명되지 않는 실제 상태 변화.
- **B (between-person speed variability):** 사람마다 평균 속도가 다른 현상. 별도 주력 UQ 모듈로 만들기보다, **초기 속도 분포/개인차**로 다룬다.
- **원래 HTML에서 유지할 내용:** R, 사람 간 속도 차이, Q, 거리·가림, 횡단보도 길이, 신호·혼잡 등의 조건 후보.
- **원래 HTML에서 유보할 내용:** 예제에서 계산된 R 위치 RMSE 약 0.19 m, Q의 `q ≈ 0.05`, G95에 대한 기여도는 **예비 계산**이다. 전체 데이터·추정 공식·단위·표본 독립성을 확인하기 전까지 확정값으로 사용하지 않는다.
- **최종 지향점(다음 단계):** 입력 궤적 → 조건부 R/Q → 상태 추정 → 미래 궤적의 예측분포. **완전 횡단 데이터가 충분할 때에만** 횡단 완료 시간 분포와 G95까지 검증한다.

> **핵심 주의:** SPD에서 구할 수 있는 카메라 측/virtual-LiDAR 측 *주석 차이*는 **순수 카메라 모델의 예측 오차가 아니다.** 시각 차이·주석 오차·좌표계 문제 등이 섞인 *paired annotation discrepancy*이며, R의 후보 측정치로 감사(audit)한다. IMPTC 궤적도 센싱 기반이므로 단순 궤적 잔차를 곧바로 순수 Q라고 부르지 않는다.

---

## 1. 어떤 데이터를 받을까? 다운로드 순서

| 순서 | 데이터 | 당장 받는 범위 | 주목적 | 다운로드·문서 |
|---|---|---|---|---|
| 1 | **V2X-Seq SPD** | **SPD Example**부터 | R에 필요한 paired annotation 존재 여부, 매칭·timestamp 점검 | [공식 저장소](https://github.com/AIR-THU/DAIR-V2X-Seq) · [SPD 스키마](https://github.com/AIR-THU/DAIR-V2X-Seq/blob/main/dataset/v2x-seq-spd/README.md) · [예제 다운로드(공식 링크)](https://drive.google.com/file/d/1gjOmGEBMcipvDzu2zOrO9ex_OscUZMYY/view) |
| 2 | **IMPTC** | **Samples (약 0.3 GB)**부터 | Q 후보에 필요한 연속 보행 궤적·상태 및 신호/환경 필드 점검 | [공식 저장소](https://github.com/kav-institute/imptc-dataset) · [Zenodo 파일 다운로드](https://zenodo.org/records/14811016) · [VRU track 스키마](https://github.com/kav-institute/imptc-dataset/blob/main/data_formats/vru_tracks.md) |
| 3 | V2X-Seq SPD | 샘플 확인 후 필요한 **전체 SPD** | 유효 보행자 pair 수를 늘려 조건별 분석 가능한지 확인 | [공식 전체 데이터 안내](https://github.com/AIR-THU/DAIR-V2X#dataset-download) |
| 4 | IMPTC | 샘플 확인 후 **Full Sequence Set 01–05** 중 한 세트부터, 이후 필요 시 전체 | 연속 궤적·보행 상태·조건별 표본 수 확대 | [Zenodo 파일 목록](https://zenodo.org/records/14811016) |
| 선택 | **V2X-Seq TFD** | 기존 조원이 사용한 TFD Example 먼저 | 기존 HTML의 Q/속도 분석 재현 및 IMPTC와 비교 | [TFD 스키마](https://github.com/AIR-THU/DAIR-V2X-Seq/blob/main/dataset/v2x-seq-tfd/README.md) · [예제](https://drive.google.com/file/d/1-Ri92z6rkH14vAOFOx5xhfzvFxBptgAA/view) |

**다운로드 원칙**

1. **모델 학습용 repository와 데이터 원본은 다르다.** `git clone`만으로 대용량 데이터가 다운로드되지 않는 경우가 많다. 위 공식 데이터 링크에서 압축 파일을 따로 받아야 한다.
2. Google Drive에서 예제 ZIP을 먼저 브라우저로 받은 뒤 압축 해제한다. 전체 데이터는 샘플 파서가 동작하는 것을 확인한 후 받는다.
3. IMPTC는 Zenodo의 `imptc_samples.tar.gz`부터 받는다. Full Sequence 데이터는 `imptc_set_01.tar.gz` ~ `imptc_set_05.tar.gz`로 나뉜다. **VRU Trajectory Dataset(약 3 GB)**과 Full Sequence Dataset(약 20 GB)은 용도가 다르다. 횡단보도·신호·날씨 context가 필요하면 **Full Sequence**를 우선 선택한다.
4. 다운로드 뒤 압축 파일 크기, 파일 목록, 공식 제공 checksum(MD5)이 있다면 체크한다. 라이선스·재배포 조건도 확인한다.
5. **MacBook Air M2에서 시작 가능.** 이번 단계는 JSON/CSV 파싱·통계·시각화이므로 GPU가 필요 없다. 큰 파일은 시퀀스별로 읽으며, 원본 영상·PCD 전체를 RAM에 한꺼번에 올리지 않는다.

### 권장 작업 폴더

```text
View2Risk/
├── data/
│   ├── downloads/               # 다운로드한 원본 압축 파일
│   ├── raw/
│   │   ├── spd_example/         # 실제 압축 해제된 구조에 맞게 정리
│   │   ├── imptc_samples/
│   │   └── spd_full/            # 샘플 검증 후 선택
│   └── processed/               # 정제한 중간 테이블; 원본과 구분
├── scripts/
│   ├── 01_inspect_spd.py
│   ├── 02_inspect_imptc.py
│   ├── 03_audit_r_candidates.py
│   └── 04_audit_q_candidates.py
├── reports/
│   ├── dataset_inventory.csv
│   ├── spd_schema_report.md
│   ├── imptc_schema_report.md
│   ├── r_quality_report.md
│   ├── q_quality_report.md
│   ├── factor_decision_table.csv
│   └── data_audit_summary.md
└── README.md
```

### 첫 실행에 쓸 명령 예시 (Mac / 터미널)

```bash
mkdir -p View2Risk/{data/downloads,data/raw,data/processed,scripts,reports}
cd View2Risk
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas pyarrow scipy matplotlib

# 다운로드한 압축 파일을 data/downloads/에 넣은 뒤 파일 구조 확인
ls -lh data/downloads/
# IMPTC 예시: 먼저 압축 내부 목록만 확인
tar -tzf data/downloads/imptc_samples.tar.gz | head -40
# 폴더가 실제로 어떻게 구성됐는지 확인한 뒤 적절한 위치에 압축 해제
mkdir -p data/raw/imptc_samples
tar -xzf data/downloads/imptc_samples.tar.gz -C data/raw/imptc_samples/
find data/raw/imptc_samples -name 'track.json' | head
```

- SPD 압축 파일 이름이나 압축 내부 최상위 폴더는 다운로드 파일을 보고 확인한 뒤 압축 해제한다.
- JSON 필드의 실제 타입/중첩 형태는 샘플 파일을 열어 확인한다. 스키마 문서의 예시만 보고 파서를 확정하지 않는다.
- `data/raw/` 파일은 **수정하지 않는다.** 모든 결측 처리·변환·필터링 결과는 `data/processed/`에 기록한다.

---

## 2. 1차 조사: 폴더 구조와 스키마 확인 (모델링 전)

### 2-1. SPD의 실제 파일 구조

공식 Infrastructure-side 문서 기준:

```text
infrastructure-side/
├── data_info.json
├── label/
│   ├── camera/{frame_id}.json
│   └── virtuallidar/{frame_id}.json
├── calib/
│   ├── camera_intrinsic/{frame_id}.json
│   ├── virtuallidar_to_camera/{frame_id}.json
│   └── virtuallidar_to_world/{frame_id}.json
├── image/{frame_id}.jpg
└── velodyne/{frame_id}.pcd
```

**우선 확인할 필드**

| 출처 | 우선 탐색 필드 | 확인할 점 |
|---|---|---|
| `data_info.json` | `sequence_id`, `frame_id`, `image_timestamp`, `pointcloud_timestamp` | 시각 단위와 센서 간 동기화 |
| `data_info.json` | `label_camera_std_path`, `label_lidar_std_path` | 해당 프레임의 실제 라벨 경로 존재 여부 |
| `label/camera`, `label/virtuallidar` | `type`, `track_id`, `3d_location`, `2d_box` | Pedestrian 라벨 유무, 두 측의 객체 대응 가능성 |
| 라벨 | `occluded_state`, `truncated_state` | 가림/화면 경계 상태별 관측 빈도 |
| `calib/*` | 변환 행렬/회전/이동 | 두 위치가 정말 같은 좌표계인지 검증 |

**첫 번째 출력:** `spd_schema_report.md` — 실제 JSON 예시 1~2개, 데이터 타입, 좌표계·시간 단위, 누락 필드를 기록한다.

### 2-2. IMPTC의 실제 파일 구조

공식 Full Sequence 문서 기준:

```text
<sequence_id>/
├── context/
│   ├── master_timestamp_sync.json
│   ├── traffic_light_signals.json
│   └── weather_data.json
├── vrus/
│   └── <track_id>/track.json
├── vru_trackinfo.csv
└── sequence_overview_map.jpg  # 그 외 시각화 파일도 제공
```

`track.json`에는 `overview`와 `track_data`가 있으며, 추적 객체가 Pedestrian인지 `overview.class_id` / `class_name`으로 확인한다.

| 필드 | 뜻 | 감사 시 체크할 것 |
|---|---|---|
| `ts` | 시간 | 증가 순서, 중복 시각, 단위(실제 파일 값 확인) |
| `coordinates` | 3차원 위치(m) | 결측·순간 점프·좌표 범위 |
| `velocity` | 속력(km/h) | m/s 변환, 위치 차분 속력과 일치 여부 |
| `status` | 트랙 상태 | `2`(유효) 이외 관측의 비율 |
| `source_type` | `0`=LiDAR, `1`=LiDAR+Camera, `2`=Camera | 센서 출처별 결측·변동 여부 |
| `ground_type` | 지면 분류 | 횡단 중이라고 자동 단정하지 말 것 |
| `context/*` | 신호·날씨·타임스탬프 | 궤적과 조인 가능 여부, 빈 값 비율 |

IMPTC 문서에는 보행자 신호 그룹 `f1`–`f3`가 명시되어 있다. **이 신호와 실제 보행 궤적/횡단보도 위치가 연결되는지** 확인하는 것은 별도 작업이다.

**두 번째 출력:** `imptc_schema_report.md` — Pedestrian 실제 필드와 단위, 시퀀스 ID/트랙 ID 범위, 신호·환경 데이터의 시간 해상도를 기록한다.

---

## 3. R 후보 요소 탐색 — V2X-Seq SPD

### 3-1. R을 계산하기 **전에** 수집할 테이블

가칭: `data/processed/spd_pedestrian_pairs.parquet`

| 컬럼 | 출처/계산 | 필수 여부 |
|---|---|---|
| `sequence_id`, `frame_id`, `track_id` | 공식 메타데이터·라벨 | 필수 |
| `camera_timestamp`, `lidar_timestamp` | `data_info.json` | 필수 |
| `camera_label_x/y/z` | Camera-side 3D label | 필수 |
| `lidar_label_x/y/z` | Virtual-LiDAR-side 3D label | 필수 |
| `coordinate_frame`, `matched`, `match_method` | 매칭·좌표계 점검 | 필수 |
| `occluded_state`, `truncated_state` | 라벨 | 후보 |
| `bbox_area_px` | 2D bbox 너비 × 높이 | 후보 |
| `distance_to_sensor_m` | 센서 위치/좌표계를 확인한 뒤 계산 | 후보 |
| `timestamp_gap` | 두 시각의 차이 | 후보 |

**동일 객체·동일 좌표계·동일 시각 조건을 검증하기 전에는 두 위치를 단순히 빼지 않는다.** 공식 주석이 동일한 virtual-LiDAR 좌표를 사용하더라도, 관측 시각이 다르면 움직이는 보행자의 위치 차이가 남는다.

### 3-2. 실제 품질 점검

- [ ] 데이터셋 전체/샘플의 **보행자 트랙 수**, 프레임 수, 객체 관측 수 집계
- [ ] Camera–LiDAR 동일 객체 매칭 **성공·실패·중복 비율** 집계
- [ ] `camera_timestamp - lidar_timestamp` 분포(중앙값, p95, 최댓값) 확인
- [ ] 좌표계가 실제로 동일한지 라벨과 calibration으로 검증
- [ ] 오차 벡터 `e=(dx,dy)`의 평균·표준편차·RMSE·p95 분포를 **진단용**으로 계산
- [ ] 관측 오차의 시간적 자기상관과 객체별 군집 효과 확인
- [ ] 거리·가림·bbox 크기별 **독립 트랙 수 및 관측 수**를 각각 기록
- [ ] 오류 사례 5~10건 원본 이미지/라벨을 나란히 시각화해 원인 분류

> 단위가 있는 진단 통계를 내더라도 현재 단계에서는 **'R을 정확히 식별했다'고 주장하지 않는다.** 
> 특히 관측 수가 많아도 실제 독립 보행자 트랙이 매우 적으면 조건별 통계가 불안정하다.

### 3-3. 조사할 R 조건 후보 (아직 확정하지 않음)

| 후보 | 필요한 원본 | 선택 여부를 결정할 근거 |
|---|---|---|
| **가림 정도** | `occluded_state` | 각 가림 수준의 독립 트랙 수 + 오차 분포 차이 |
| **보행자 거리** | sensor pose + 3D 위치 | 근거리/원거리 조건별 표본 수 + 유의미한 오차 변화 |
| **센서 시간차** | camera/lidar timestamp | 시각차에 따른 위치 차이가 큰지 |
| 화면 속 객체 크기 | `2d_box` | 작은 객체일수록 차이가 커지는지 |
| 절단(화면 경계) | `truncated_state` | 경계 상태의 표본 수/오차 편향 |

**R 단계의 목표:** 최종 수학 모델을 정하는 게 아니라, `어떤 조건이 R의 분포를 설명할 가능성이 있는지`를 데이터로 판정한다.

---

## 4. Q 후보 요소 탐색 — IMPTC

### 4-1. IMPTC에서 우선 뽑을 테이블

가칭: `data/processed/imptc_pedestrian_tracks.parquet`

| 컬럼 | 출처/계산 | 필수 여부 |
|---|---|---|
| `sequence_id`, `track_id`, `ts` | 원본 `track.json` | 필수 |
| `x`, `y`, `z` | `coordinates` | 필수 |
| `speed_reported_mps` | `velocity / 3.6` | 필수 |
| `status`, `source_type`, `ground_type` | 원본 | 필수 |
| `dt`, `dx`, `dy` | 인접 시각 차이 | 진단 |
| `speed_from_position_mps` | 위치 차분/`dt` | 진단 |
| `heading_change`, `accel_proxy` | 위치·속도 변화 | 후보 |
| `track_duration_s`, `gap_count` | 트랙별 집계 | 품질 |
| `ped_signal`, `weather`, `nearby_ped_count` | context 매칭 후 | 선택 |

**중요:** `velocity`는 속도 벡터가 아니라 **속력(km/h)**이다. 방향성 있는 횡단 속도는 좌표 변화 및 횡단 진행 방향을 이용해야 한다. `accel_proxy`는 위치/속력의 관측 잡음을 포함하므로 실제 가속도 참값이라고 단정하지 않는다.

### 4-2. 실제 품질 점검

- [ ] 전체 Pedestrian 트랙 및 총 유효 관측 수, 시퀀스 수 집계
- [ ] 1/2/5/10초 이상 **연속 관측** 트랙 수, 추적 길이 히스토그램
- [ ] 타임스탬프 `dt` 분포, 중복 시각, 비정상적 간격, 중간 gap 확인
- [ ] `status`·`source_type`별 표본 수 및 유효성 확인
- [ ] 원본 제공 속력과 위치 차분 속력의 차이 확인
- [ ] 급격한 위치 점프·비정상적 속력·ID 스위치 의심 사례를 **삭제하지 말고 플래그** 처리
- [ ] 보행자별 평균 속력 분포(B 후보)와 트랙 내 속력 변동을 **분리**해 요약
- [ ] 정지·감속·가속·방향 전환 후보 구간의 개수를 집계(판정 임계값은 탐색 후 결정)
- [ ] 영상/지도와 몇 개의 궤적을 겹쳐 좌표·방향 검증
- [ ] 보행자 신호·날씨·동시 보행자 수가 시간적으로 매칭 가능한지 검증
- [ ] 횡단보도 안을 **완전히 통과한 궤적 수**와 일부만 관측된 궤적 수를 구분

### 4-3. 조사할 Q 조건 후보 (아직 확정하지 않음)

| 후보 | 필요한 원본 | 왜 확인하나 |
|---|---|---|
| **현재 속력** | `velocity`, 위치 | 정지 직전/저속/보통 속도에서 예측 잔차의 차이 |
| **가속·감속** | 연속 위치·속력 | 일정 속도 가정에서 벗어나는 구간의 빈도 |
| **정지·재출발** | 연속 궤적 | Gaussian Q 하나로 표현하기 어려운 행동 가능성 |
| 방향 변화 | `coordinates` | 직선 횡단과 회전 보행의 차이 |
| 주변 인원수 | 같은 시각의 다른 track | 혼잡도에 따라 움직임 변동이 달라지는지 |
| 보행 신호 상태 | `traffic_light_signals.json` | 신호 조건별 보행 패턴이 다른지 |
| 날씨 | `weather_data.json` | 조건별 표본이 충분할 때만 분포 차이 확인 |
| 센서 출처 | `source_type` | 움직임 변화처럼 보이는 것이 관측 방식 차이인지 점검 |

> **이번 단계의 'Q 후보 잔차'는 진단값**이다. 다음 단계에서 먼저 CV(등속도) 같은 움직임 모델을 확정하고 측정오차 영향을 검토해야 정식 Q 공분산 추정이 가능하다. 정지·재출발 자체를 Q 숫자 하나에 억지로 넣을 필요는 없다.

---

## 5. 데이터 품질 기준과 변수 선정 규칙

임의로 '조건 변수 5개는 꼭 학습한다'라고 정하지 않는다. 각 후보에 대해 다음을 표로 작성한다.

| 판정 항목 | 질문 | 결과 표시 |
|---|---|---|
| **관측 가능성** | 공식 필드가 직접 있는가, 계산할 수 있는가, 아니면 없음인가? | Direct / Derived / Unavailable |
| **데이터 양** | 독립 **보행자·시퀀스 수**가 얼마나 있는가? | 실제 개수 기입 |
| **데이터 품질** | 누락·오염·센서 불일치가 어느 정도인가? | 결측률 / 문제 사례 |
| **조건 다양성** | 각 범주에 유효한 사례가 충분한가? | 조건별 표본 수 |
| **식별 가능성** | 실제 R 또는 Q의 변화를 보는 건가, 서로 다른 오차가 섞였는가? | 확인 / 제약 있음 / 불가 |
| **실제 유용성** | 조건을 추가하면 향후 검증에 활용할 근거가 있는가? | 채택 / 보류 / 제외 |

**결정 규칙**

1. 필드가 없거나 식별이 불가능하면 **제외**(필요 시 미래 데이터 후보로만 기록).
2. 필드는 있지만 특정 조건의 독립 트랙이 너무 적으면 **보류**.
3. 관측 가능하고 품질이 양호하면 **후보 유지**. 실제 모델에 포함할지는 다음 단계에서 held-out 검증으로 결정.
4. R과 Q 조건 변수 간 중복 또는 누출(leakage) 여부를 기록한다. 예: noisy position에서 계산한 가속도를 '실제 움직임 상태 정답'으로 취급하지 않는다.
5. 같은 데이터셋에서 겹치는 시퀀스/잘린 클립/중복 궤적을 독립 표본처럼 세지 않는다. 다음 모델 단계에서 **보행자·시퀀스 단위** 분할을 할 수 있게 ID를 보존한다.

### 최소한의 그래프/테이블

- SPD: 시각차 히스토그램, camera/virtual-LiDAR 짝짓기 성공률, 위치차 분포, 가림/거리별 **독립 트랙 수**
- IMPTC: 보행자 트랙 길이, 유효 프레임·gap 비율, 속력 분포, 정지/가감속 구간 수, context 결측률
- 양쪽: 오류 사례 궤적 시각화, 원본 vs 정제 후 잔존 표본 수(funnel)

---

## 6. 실제 작업 순서와 담당자 인계 기준

### Step A — 다운로드·재현성

- [ ] 공식 링크에서 SPD Example 및 IMPTC Samples 확보
- [ ] 파일 크기/압축 상태/README·라이선스 확인
- [ ] 폴더 구조·파일 개수·버전·다운로드 날짜 기록
- [ ] 조원 HTML의 숫자는 `preliminary`로 별도 표시

**산출물:** `dataset_inventory.csv`, `README.md`의 데이터 출처 섹션

### Step B — 스키마 조사 및 원시 파서

- [ ] SPD `data_info`·라벨·calib의 키와 좌표계 파악
- [ ] IMPTC `track_data`·context의 키/시간 단위 파악
- [ ] 샘플에서 **위치·시간·ID를 잃지 않고** CSV/Parquet으로 변환
- [ ] 실제 구조가 문서 예제와 다르면 차이를 기록

**산출물:** `spd_schema_report.md`, `imptc_schema_report.md`, 두 파서 스크립트

### Step C — 데이터 품질 감사

- [ ] R용 유효 matched pair 개수·오차 관련 품질 문제 정리
- [ ] Q용 유효 연속 Pedestrian 궤적 개수·끊김/급점프 정리
- [ ] 가림·거리, 가감속·정지 등 **조건 후보별 표본 수** 집계
- [ ] 횡단보도 영역 및 완전 횡단 추출이 실제 가능한지 확인
- [ ] 샘플로 충분하지 않으면 전체 데이터 일부/전체로 확대

**산출물:** `r_quality_report.md`, `q_quality_report.md`, 조건별 통계·그래프

### Step D — 요소 결정 회의

- [ ] R에서 채택할 조건(예: 거리·가림) 결정
- [ ] Q에서 채택할 조건(예: 속도·가감속·정지) 결정
- [ ] B는 개인별 속도 사전분포로 남길지 확인
- [ ] 필수 정보가 없으면 대체 데이터/범위 축소 결정
- [ ] **수학팀에 넘길 컬럼 목록과 단위** 최종 확정

**산출물:** `factor_decision_table.csv`, `data_audit_summary.md`

### 수학팀에 넘기는 것 (현 단계 종료 기준)

**넘길 것:**

- 원시를 보존한 `spd_pedestrian_pairs.parquet` 및 `imptc_pedestrian_tracks.parquet`
- 데이터 사전: 각 필드 뜻·단위·좌표계·결측 의미
- 독립 트랙 수, 매칭 성공률, 연속 궤적 수, 시간 간격, 조건별 표본 수
- 대표적인 실패 사례와 `quality_flag`
- *R/Q로 추정 가능한 것과 지금 불가능한 것*을 분리한 결정표

**아직 넘기지 않을 것:** 검증되지 않은 최종 `R` 행렬, `Q` 행렬, G95 수치 또는 R/Q가 독립적으로 정확히 식별됐다는 주장.

---

## 7. 다음 단계(이번 MD의 범위 밖)

품질 감사 결과로 실제 채택 조건이 정해진 후에 진행한다.

1. R: 위치 차이의 편향·공분산 및 조건부 분포 **정식 추정**. 기준 라벨·센서 시간차의 한계 명시.
2. Q: 움직임 모델(CV/CA 등) 확정 후 관측 잡음과 분리해 과정 잡음 추정.
3. Kalman/Particle Filter 또는 다른 상태공간 모델에 R/Q 연결.
4. **Held-out** 궤적으로 위치·속도 90/95% 예측구간의 포함률과 크기 검증.
5. 완전 횡단 궤적이 충분할 경우에만 횡단 시간 분포/G95 검증.

---

## 8. 첫 회의에서 바로 확인할 질문

1. 조원이 기존에 사용한 **SPD/TFD 예제 파일과 분석 코드가 남아 있는가?** 남아 있다면 먼저 회수하고 수치를 재현한다.
2. SPD 샘플에 **독립적인 보행자 라벨 pair**가 몇 트랙·몇 프레임 존재하는가?
3. IMPTC 샘플에는 **유효하게 연속 관측된 Pedestrian**이 몇 트랙 있는가?
4. IMPTC의 context(횡단보도, 신호, 날씨)가 실제 보행자 트랙에 **시간·공간적으로 조인 가능한가?**
5. 이 단계에서 품질이 부족한 요소는 과감히 제외해도 되는가? → **그렇다. 요소 개수를 늘리는 것보다 식별 가능성이 우선이다.**

**지금의 성공 기준은 좋은 R/Q 수치를 내는 것이 아니라, 어떤 불확실성과 조건을 데이터로 실제 추정할 수 있는지 근거를 갖고 결정하는 것이다.**

---

### 공식 참고 문서

- V2X-Seq 메인: https://github.com/AIR-THU/DAIR-V2X-Seq
- V2X-Seq SPD 구조: https://github.com/AIR-THU/DAIR-V2X-Seq/blob/main/dataset/v2x-seq-spd/README.md
- V2X-Seq TFD 구조(선택): https://github.com/AIR-THU/DAIR-V2X-Seq/blob/main/dataset/v2x-seq-tfd/README.md
- DAIR-V2X 전체 데이터 안내: https://github.com/AIR-THU/DAIR-V2X#dataset-download
- IMPTC 공식 저장소: https://github.com/kav-institute/imptc-dataset
- IMPTC VRU 필드 설명: https://github.com/kav-institute/imptc-dataset/blob/main/data_formats/vru_tracks.md
- IMPTC 다운로드/파일 체크섬: https://zenodo.org/records/14811016

> 작성 기준: 2026-10-25. 원본 데이터 파일을 직접 다운로드하여 실행한 결과가 아니라, **공식 스키마와 조원 HTML의 예비 분석을 바탕으로 정리한 실험 준비 계획**이다. 실제 표본 수/품질은 다운로드 후 측정해야 한다.
