"""Finalize data-audit handoff after frozen full-model evaluation and supplements."""
from pathlib import Path
import json,hashlib,shutil,time
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OLD=Path('/data/whereami/math/view2risk_261025')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if hasattr(v,'item') else v.tolist())+'\n')
def table(df):return '\n'.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in [list(df.columns),['---']*len(df.columns),*list(df.fillna('N/A').itertuples(index=False,name=None))])

def main():
    report=ROOT/'reports';validation=json.loads((report/'validation.json').read_text());assert validation['passed']
    supplemental=json.loads((report/'supplement_validation.json').read_text());assert supplemental['passed']
    inputs=json.loads((ROOT/'input_sha256.json').read_text());assert all(sha(Path(p))==h for p,h in inputs.items())
    code=json.loads((ROOT/'execution_freeze.json').read_text())['code_sha256'];assert all(sha(ROOT/p)==h for p,h in code.items())
    before_models={str(p):sha(p) for p in (ROOT/'models').glob('*.json')}
    q=pd.read_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet');r=pd.read_parquet(ROOT/'data/spd_pair_residuals.parquet')
    eligible=r[r.model_eligible]
    factors=[]
    def add(axis,name,availability,field,frame,groups,decision,unit,limit):
        present=frame[field].notna() if field in frame else np.zeros(len(frame),bool)
        present_frame=frame.loc[present]
        factors.append(dict(component=axis,factor=name,observability=availability,column=field,unit=unit,observations=len(frame),nonmissing=int(present.sum()),
            missing_fraction=float(1-present.mean()),track_groups=present_frame.track_uid.nunique() if 'track_uid' in frame else None,
            sequences=present_frame.sequence_id.nunique() if 'sequence_id' in frame else None,
            independent_group_type=groups,independent_groups=present_frame[groups].nunique() if groups in frame else None,
            decision=decision,identifiability_limit=limit,final_physical_R_Q_identification=False))
    for name,field,availability,unit in [('distance','distance_to_sensor_m','Derived','m'),('occlusion','occluded_state','Direct','source code'),('bbox_size','bbox_area_px','Derived','pixels2'),('truncation','truncated_state','Direct','source code')]:
        add('R',name,availability,field,eligible,'intersection_loc','Keep descriptive candidate; conditional model not selected',unit,'Shared paired annotations, asynchronous time and camera calibration ambiguity; not R_camera')
    add('R','sensor_time_gap','Direct','timestamp_gap_s',eligible,'intersection_loc','Keep timing QC control','seconds','Motion/time/annotation effects not separated')
    for name,field,availability,unit in [('current_speed','speed_reported_mps','Direct; converted once','m/s'),('acceleration_deceleration','accel_proxy','Derived','m/s2 proxy'),('heading_change','heading_rate_deg_s','Derived','degrees/s proxy'),('stop_restart','speed_reported_mps','Derived threshold candidates','m/s'),('nearby_pedestrians','nearby_ped_count','Derived','distinct observed tracks within5m')]:
        add('Q',name,availability,field,q,'recording_date','Keep diagnostic candidate; no conditional model selected',unit,'Recorded sensing/tracking and numerical-derivative noise are mixed with behavior')
    add('Q/R','sensor_source','Direct','source_type',q,'recording_date','Keep stratification control','0 LiDAR /1 fusion /2 camera','Sensor switching can change both measured motion and perception')
    add('Q','pedestrian_signal','Direct group states; track spatial assignment unverified','signal_f1',q,'recording_date','Hold per-track signal model; excluded from current pilot','provider code','f1/f2/f3 temporal coverage is not validated track-specific signal assignment')
    add('Q','weather','Direct','weather_name',q,'recording_date','Audit support only; excluded from current pilot','source category','No weather-wise R/Q performance claim; contexts are date/sequence correlated')
    add('B','between_track_mean_speed','Derived track summaries','speed_reported_mps',q,'recording_date','Initial speed prior candidate only','m/s','Track averages mix people, conditions and stops; cross-sequence person identity unavailable')
    add('Outcome','completed_crossing','Semantic ground geometry available; entry/exit validation missing','ground_type',q,'recording_date','Hold confirmed complete/partial crossing counts (N/A)','provider ground code','Crosswalk touch and raster component membership are not complete-crossing GT')
    pd.DataFrame(factors).to_csv(report/'factor_decision_table.csv',index=False)
    dictionaries=[]
    for label,frame in [('SPD',r),('IMPTC',q)]:
        for column in frame:
            unit='source ID/code/flag or documented metadata'
            if column in ['camera_timestamp','lidar_timestamp','ts_us']:unit='UNIX epoch microseconds int64'
            elif column in ['timestamp_gap','timestamp_gap_s','dt','track_duration_s','signal_age_s','weather_age_s']:unit='seconds'
            elif column in ['x','y','z','dx','dy','dz','distance_to_sensor_m','horizontal_discrepancy_m','spatial_3d_discrepancy_m'] or '_world_' in column or '_label_' in column:unit='metres; provider frame'
            elif column.endswith('mps'):unit='m/s; speed_reported_mps already converted from raw km/h'
            elif column=='accel_proxy':unit='m/s2 measured-speed derivative proxy'
            elif column in ['heading_rad','heading_change']:unit='radians'
            elif column=='heading_rate_deg_s':unit='degrees/s'
            elif column=='bbox_area_px':unit='pixels2'
            elif column=='recording_date':unit='YYYYMMDD from sequence ID'
            dictionaries.append(dict(dataset=label,column=column,dtype=str(frame[column].dtype),unit=unit,missing_count=int(frame[column].isna().sum()),
                meaning='not independent physical ground truth' if column in ['dx','dy','accel_proxy','speed_from_position_mps'] else column))
    pd.DataFrame(dictionaries).to_csv(report/'data_dictionary.csv',index=False)
    inv=pd.read_csv(report/'q_segment_inventory.csv');max_valid=inv.groupby('track_uid').duration_s.max()
    metrics=json.loads((report/'imptc_metrics.json').read_text())
    strict={str(t):int((max_valid>=t).sum()) for t in [1,2,5,10]}
    js(report/'continuity_count_comparison.json',dict(original_audit_incremental_float_seconds=metrics['strict_continuity_counts'],
        pilot_segments_integer_timestamp_difference_seconds=strict,note='Any exact-threshold floating accumulation difference is recorded; model origin eligibility was not altered.'))
    classes={}
    for i in range(1,6):
        source=OLD/'reports/imptc_metrics.json' if i==1 else ROOT/f'parts/imptc_set_{i:02d}/reports/imptc_metrics.json'
        part=json.loads(source.read_text())
        for name,n in part['all_VRU_class_counts'].items():classes[name]=classes.get(name,0)+n
    js(report/'full_population_inventory.json',dict(IMPTC_raw_sequences=270,IMPTC_pedestrian_sequences=q.sequence_id.nunique(),
        sequences_without_pedestrian=270-q.sequence_id.nunique(),all_VRU_classes=classes,total_VRU_tracks=sum(classes.values()),
        SPD_source_frames=11275,SPD_source_sequences=67,SPD_pedestrian_sequences=eligible.sequence_id.nunique(),SPD_paired_track_groups=eligible.track_uid.nunique(),SPD_pairs=len(eligible)))
    ground=supplemental['ground_map'];tfd=supplemental['tfd'];quality=supplemental['quality']
    text=['# Full-data audit and feasibility',
        f'IMPTC: 270 raw sequences, {q.sequence_id.nunique()} with Pedestrian tracks, {q.track_uid.nunique()} track groups, {len(q):,} observations, documented valid status2={(q.status==2).sum():,}. All original Pedestrian rows are retained. The remaining6sequences have no class0 pedestrians, not input failures.',
        table(pd.DataFrame([dict(minimum_seconds=k,valid_tracks=v) for k,v in strict.items()])),
        'Original per-set audit vs integer-timestamp segment counts are both preserved in continuity_count_comparison.json.',
        f'SPD: 67 source sequences /11,275 frames; Pedestrian pairs occur in {eligible.sequence_id.nunique()} sequences /{eligible.intersection_loc.nunique()} sites /{eligible.track_uid.nunique()} track groups /{len(eligible):,} matched rows. No frame/track is treated as a separate independent person.',
        'Conditions and source-wise support are in imptc_full_condition_support.csv / spd_condition_counts.csv; strict behavior sensitivity is in imptc_strict_event_sensitivity.csv.',
        json.dumps(quality,indent=2),
        'Official semantic map acquisition, world-coordinate point join and same-source label agreement are in 04_geometry_context_tfd.md. Confirmed complete/partial crossings and per-track signal spatial assignment remain unverified (N/A); raster touch counts are not full-crossing labels.',
        'TFD Example is kept as a separate single-infrastructure-view audit with clipped/overlapping scene keys explicitly recorded. Its trajectories are never pooled with IMPTC or treated as independent extra people. Historical q≈.05 has no established original calculation/units, so it was not forced to match.',
        'Data definitions/units are in data_dictionary.csv. Candidate decisions, counts and constraints are in factor_decision_table.csv. Physical R/Q identifiability, G95, signal optimization and final conditional model selection remain beyond verified evidence.']
    (report/'data_audit_full.md').write_text('\n\n'.join(text)+'\n')
    appendix='\n## 보충 감사와 공간 검증\n\n'
    appendix+='공식 IMPTC semantic ground map(100만 점)을 추가 확보해 같은 로컬 좌표에서 궤적과 대조했다. 0.25m 이내 지도점이 있는 status2 관측의 ground code 일치율은 **99.47%**다. 같은 데이터 처리에서 생성된 정보일 수 있어 독립 GT 정확도로 해석하지 않는다. 지도와 궤적 중첩 그림 및 자세한 표는 [04_geometry_context_tfd.md](04_geometry_context_tfd.md)에 있다.\n\n'
    appendix+='확정 완전/부분 횡단 수와 개별 트랙 신호 배정은 검증된 진입/이탈 정의가 없어 N/A로 유지했다. TFD Example도 별도 감사했고 IMPTC와 합산하지 않았다.\n\n'
    appendix+='전체 감사 요약은 [data_audit_full.md](data_audit_full.md), 컬럼 사전은 [data_dictionary.csv](data_dictionary.csv), 후보 결정은 [factor_decision_table.csv](factor_decision_table.csv)를 참조한다.\n\n'
    appendix+='R의 기존 Example253쌍은 전체 데이터와의 잔차 차이가0으로 재현됐다. 전체 R RMSE0.298680m, 중앙값0.139037m, p95=0.475109m, 최대7.102860m이므로 큰 꼬리 사례를 함께 봐야 한다. 샘플0.185183m와의 차이를 기존 샘플 손상이나 카메라 모델 성능 변화로 해석하지 않는다.\n'
    with (report/'full_summary.md').open('a') as f:f.write(appendix)
    (ROOT/'README.md').write_text('# View2Risk full-data extension — 261026\n\n먼저 reports/full_summary.md를 확인한다. 기존 샘플 감사와 R/Q 파일럿을 보존한 별도 전체 확장판이다.\n\nSPD6교차로의 주석10,109쌍과 IMPTC Full01–05의1,920보행자 트랙을 감사했다. R은 교차로 holdout, Q는15촬영날짜를묶은5-fold로 고정 검증했다. 시그널/날씨 predictor, G95 및 순수 R/Q 참값 주장은 하지 않는다.\n\n검증: reports/validation.json 및 reports/supplement_validation.json. 새 데이터/예측: data/; 모델: models/; 그림: figures/; 실행: run.sh. 기존 sample/Set01 결과와 원본은 변경하지 않았다.\n')
    from PIL import Image
    for image in (ROOT/'figures').glob('*.png'):
        with Image.open(image) as im:im.verify()
    assert all(sha(Path(p))==h for p,h in before_models.items())
    validation['supplemental_geometry_context_TFD_checks_passed']=True
    validation['model_parameter_files_unchanged_during_supplement']=True
    validation['final_manifest_required']=True
    js(report/'validation.json',validation)
    js(ROOT/'status.json',dict(state='complete',full_audit_and_pilot=True,supplements_complete=True,summary=str(report/'full_summary.md'),finished_utc=time.time()))
    if not (ROOT/'manifest_model_phase.json').exists():shutil.copy2(ROOT/'manifest.json',ROOT/'manifest_model_phase.json')
    files={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink() and not any(x in p.relative_to(ROOT).parts for x in ['tmp','parts','raw']) and p.name!='manifest.json' and p.suffix!='.log'}
    js(ROOT/'manifest.json',files)
    assert all(sha(ROOT/p)==h for p,h in files.items())
    print(json.dumps(dict(passed=True,manifest_files=len(files),summary=str(report/'full_summary.md'),core_models_unchanged=True)),flush=True)

if __name__=='__main__':main()
