# 추가 데이터 품질·공간 검증 및 TFD Example

공식 IMPTC README에서 같은 로컬 좌표계를 사용하는 semantic ground map 링크를 확인해 11MB ZIP을 추가 확보했다. 원본 map ZIP은 assets/에 보존했다. 이 검사는 R/Q 파라미터를 바꾸거나 신호·날씨를 예측 변수에 넣지 않는다.

## IMPTC 지도 연결

| scope | XY_radius_m | denominator_rows | near_known_map_rows | near_fraction | comparable_rows | provided_vs_map_ground_code_agreement | crosswalk_touch_tracks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_status | 0.1 | 1710765 | 1689464 | 0.9875488451073058 | 1686206 | 0.9946685043227221 | 1168 |
| accepted_status2 | 0.1 | 1648100 | 1627944 | 0.9877701595776955 | 1624749 | 0.9946496351128697 | 1166 |
| all_status | 0.25 | 1710765 | 1705787 | 0.9970901906457053 | 1702520 | 0.9947137184878886 | 1168 |
| accepted_status2 | 0.25 | 1648100 | 1643377 | 0.9971342758327771 | 1640173 | 0.9946938524167878 | 1166 |
| all_status | 0.5 | 1710765 | 1707320 | 0.9979862809912524 | 1704053 | 0.9947184741319666 | 1168 |
| accepted_status2 | 0.5 | 1648100 | 1644846 | 0.9980256052424004 | 1641642 | 0.9946986005475006 | 1166 |

지도 vertex 1,000,000개. XY 최근접 지도점의 색상 code와 제공 ground_type을 대조했다. 두 정보가 같은 처리 계통에서 생성됐을 수 있으므로 독립 위치 정확도나 segmentation GT 검증은 아니다. 지도/기록 궤적을 공통 metre 좌표로 표시한 그림은 figures/imptc_semantic_map_tracks.png에 있다.

횡단보도 연결 성분은 0.25m raster의 탐색 후보로만 저장했다. 검증된 양쪽 진입/이탈 영역과 개별 트랙의 f1/f2/f3 배정이 없어 **확정 완전/부분 횡단 수는 N/A**다. ground_type5 또는 지도상 체류만으로 완전 횡단을 세거나 G95를 만들지 않았다.

## 전체 IMPTC 품질 요약

{
  "signal_temporal_missing_fraction": 0.0019897531221412645,
  "weather_temporal_missing_fraction": 0.0018389433966675727,
  "position_speed_gt5": 104,
  "position_speed_gt20": 0,
  "track_mean_speed_mean_mps": 1.016566777324795,
  "between_track_mean_speed_std_mps": 0.46473023811331743,
  "within_track_speed_std_mean_mps": 0.372165940305454
}

imptc_full_condition_support.csv는 조건별 관측/트랙/시퀀스/날짜 지원 규모다. imptc_strict_event_sensitivity.csv는 status2와 유효 인접 간격만 사용하는 정지·가감속·회전 후보표다. 기존 source별 all-status 탐색표와 분모가 다르며 행동 정답이 아니다.

## TFD 선택 비교

{
  "scope": "single-infrastructure trajectory Example only; other views not pooled",
  "trajectory_files": 77,
  "pedestrian_scene_track_groups": 908,
  "pedestrian_observations": 19978,
  "unique_intersection_id_timestamp_rows": 16739,
  "duplicate_key_rows": 6478,
  "conflicting_duplicate_keys": 0,
  "timestamp_unit": "Observed UNIX epoch seconds in CSV; preserved original string and converted Decimal to integer microseconds",
  "coordinate_unit_note": "Provider XY and velocity-vector fields retained; no cross-dataset covariance or physical Q fit was inferred from undocumented CSV units.",
  "dataset_class_counts": {
    "VEHICLE": 200195,
    "BICYCLE": 42079,
    "PEDESTRIAN": 19977
  },
  "independent_person_count_not_established": true,
  "historical_q_005_reproduced": false,
  "reason": "Original HTML q calculation/units/independent-state assumptions not established; no arbitrary match to q=.05"
}

단일 infrastructure view만 사용했다. 겹친 클립/시점이나 센서별 view를 독립 사람/실험으로 합산하지 않았다. IMPTC와 궤적을 섞거나 과거 q≈.05를 임의 재현하지 않았다.
