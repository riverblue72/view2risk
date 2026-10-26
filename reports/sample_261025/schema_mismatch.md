# Actual input schema and verified mapping

**Mapping correction:** the input has `speed_reported_mps` already in m/s; it must NOT be divided by 3.6 again. Raw km/h conversion was done by the existing parser. Q uses causal XY slope components, not the scalar speed as vx/vy.

Q Parquet does not carry timestamp_unit/coordinate_frame metadata columns; units and frame are mapped from the existing sample schema report. No input columns were added or changed. R uses stored world-horizontal coordinates, not camera projection or an assumed orthogonal camera transform.

## SPD

| column | dtype |
| --- | --- |
| sequence_id | object |
| frame_id | object |
| track_id | object |
| track_uid | object |
| camera_timestamp | int64 |
| lidar_timestamp | int64 |
| timestamp_unit | object |
| timestamp_gap | float64 |
| timestamp_gap_s | float64 |
| coordinate_frame | object |
| matched | bool |
| match_method | object |
| same_exact_timestamp | bool |
| occluded_state | int64 |
| truncated_state | int64 |
| bbox_area_px | float64 |
| distance_to_sensor_m | float64 |
| paired_annotation_not_detector_error | bool |
| calibration_camera_nonrigid | bool |
| image_path | object |
| camera_label_path | object |
| lidar_label_path | object |
| camera_label_x | float64 |
| camera_label_y | float64 |
| camera_label_z | float64 |
| camera_world_x | float64 |
| camera_world_y | float64 |
| camera_world_z | float64 |
| camera_projected_u | float64 |
| camera_projected_v | float64 |
| camera_P_projected_u | float64 |
| camera_P_projected_v | float64 |
| lidar_label_x | float64 |
| lidar_label_y | float64 |
| lidar_label_z | float64 |
| lidar_world_x | float64 |
| lidar_world_y | float64 |
| lidar_world_z | float64 |
| lidar_projected_u | float64 |
| lidar_projected_v | float64 |
| lidar_P_projected_u | float64 |
| lidar_P_projected_v | float64 |
| bbox | object |
| distance_reference | object |
| dx | float64 |
| dy | float64 |
| dz | float64 |
| horizontal_discrepancy_m | float64 |
| spatial_3d_discrepancy_m | float64 |
| same_2d_box | bool |
| camera_K_projection_inside_bbox | bool |
| camera_P_projection_inside_bbox | bool |
| lidar_K_projection_inside_bbox | bool |
| lidar_P_projection_inside_bbox | bool |
| quality_flag | object |

{
  "ids": "sequence_id, frame_id, track_id, track_uid",
  "positions": "camera_world_x/y, lidar_world_x/y; dx/dy",
  "timestamps": "camera_timestamp, lidar_timestamp: int64 UNIX microseconds",
  "conditions": "timestamp_gap_s, distance_to_sensor_m, occluded_state",
  "calibration": "calibration_camera_nonrigid, coordinate_frame"
}

## IMPTC

| column | dtype |
| --- | --- |
| dataset_source | object |
| sequence_id | object |
| track_id | object |
| track_uid | object |
| source_path | object |
| source_row_key | object |
| source_index | int64 |
| ts_raw | object |
| ts_us | int64 |
| t_seconds | float64 |
| x | float64 |
| y | float64 |
| z | float64 |
| speed_reported_mps | float64 |
| status | int64 |
| source_type | int64 |
| ground_type | float64 |
| class_prob | float64 |
| finite_coordinates | bool |
| strict_documented_valid_status2 | bool |
| timestamp_in_master | bool |
| signal_available | bool |
| signal_age_s | float64 |
| weather_available | bool |
| weather_age_s | float64 |
| weather_status | float64 |
| weather_name | object |
| ped_signal | object |
| ped_signal_spatial_assignment | object |
| original_track_out_of_order | bool |
| signal_f1 | float64 |
| signal_f2 | float64 |
| signal_f3 | float64 |
| weather_air_temperature | float64 |
| weather_precipitation_intensity | float64 |
| weather_precipitation_amount | float64 |
| weather_visibility | float64 |
| weather_wind_speed | float64 |
| dt | float64 |
| dx | float64 |
| dy | float64 |
| speed_from_position_mps | float64 |
| heading_rad | float64 |
| heading_change | float64 |
| heading_rate_deg_s | float64 |
| accel_proxy | float64 |
| track_duration_s | float64 |
| gap_count | int64 |
| quality_flags | object |
| raw_status_semantics_verified | bool |
| concurrent_ped_count | int64 |
| nearby_ped_count | int64 |
| nearby_count_radius_m | float64 |
| nearby_count_status_policy | object |

{
  "ids": "sequence_id, track_id, track_uid",
  "positions": "x, y: metres, intersection-local",
  "timestamps": "ts_us: int64 UNIX microseconds",
  "speed": "speed_reported_mps: already converted m/s",
  "validity": "status == 2 and finite x/y/z; segments break at dt<=0 or dt>0.060 seconds",
  "controls": "source_type, status; no signals/weather used"
}
