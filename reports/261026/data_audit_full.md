# Full-data audit and feasibility

IMPTC: 270 raw sequences, 264 with Pedestrian tracks, 1920 track groups, 1,710,765 observations, documented valid status2=1,648,100. All original Pedestrian rows are retained. The remaining6sequences have no class0 pedestrians, not input failures.

| minimum_seconds | valid_tracks |
| --- | --- |
| 1 | 1920 |
| 2 | 1920 |
| 5 | 1887 |
| 10 | 1687 |

Original per-set audit vs integer-timestamp segment counts are both preserved in continuity_count_comparison.json.

SPD: 67 source sequences /11,275 frames; Pedestrian pairs occur in 34 sequences /6 sites /233 track groups /10,109 matched rows. No frame/track is treated as a separate independent person.

Conditions and source-wise support are in imptc_full_condition_support.csv / spd_condition_counts.csv; strict behavior sensitivity is in imptc_strict_event_sensitivity.csv.

{
  "signal_temporal_missing_fraction": 0.0019897531221412645,
  "weather_temporal_missing_fraction": 0.0018389433966675727,
  "position_speed_gt5": 104,
  "position_speed_gt20": 0,
  "track_mean_speed_mean_mps": 1.016566777324795,
  "between_track_mean_speed_std_mps": 0.46473023811331743,
  "within_track_speed_std_mean_mps": 0.372165940305454
}

Official semantic map acquisition, world-coordinate point join and same-source label agreement are in 04_geometry_context_tfd.md. Confirmed complete/partial crossings and per-track signal spatial assignment remain unverified (N/A); raster touch counts are not full-crossing labels.

TFD Example is kept as a separate single-infrastructure-view audit with clipped/overlapping scene keys explicitly recorded. Its trajectories are never pooled with IMPTC or treated as independent extra people. Historical q≈.05 has no established original calculation/units, so it was not forced to match.

Data definitions/units are in data_dictionary.csv. Candidate decisions, counts and constraints are in factor_decision_table.csv. Physical R/Q identifiability, G95, signal optimization and final conditional model selection remain beyond verified evidence.
