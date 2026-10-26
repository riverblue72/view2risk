"""Evidence-based candidate decisions and reproducible handoff, no final R/Q fitting."""
from pathlib import Path
from collections import Counter
import json,subprocess
import numpy as np
import pandas as pd
from common import ROOT,js,sha,csvw,stats,table

def main():
    rp=ROOT/'reports';r=json.loads((rp/'spd_metrics.json').read_text());q=json.loads((rp/'imptc_metrics.json').read_text());sample=json.loads((rp/'stage_samples/imptc_metrics.json').read_text())
    overlap=json.loads((rp/'imptc_overlap_exports.json').read_text())
    rdf=pd.read_parquet(ROOT/'data/processed/spd_pedestrian_pairs.parquet');qdf=pd.read_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet')
    added=[]
    for field,value in [('timestamp_unit','UNIX epoch microseconds'),('coordinate_frame','IMPTC intersection-local XYZ metres, East/North/Up; different from SPD world')]:
        if field not in qdf:qdf[field]=value;added.append(field)
    if added:qdf.to_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet',index=False,compression='zstd')
    inv=[]
    for package in ['spd_example','imptc_samples','imptc_set_01']:
        folder=ROOT/'data/raw'/package;mark=json.loads((folder/'extraction_complete.json').read_text())
        if 'archive' in mark:
            item=mark['archive'];inv.append(dict(dataset=package,source=item['url'],archive_path=item['path'],archive_bytes=item['bytes'],raw_bytes=mark['uncompressed_bytes'],members=mark['members'],official_MD5_verified=item['verified_official_md5'],MD5=item['md5'],SHA256=item['sha256'],status='downloaded_verified_extracted'))
        else:inv.append(dict(dataset=package,source=mark['local_source'],archive_path='original archive not available; reused extracted official example',archive_bytes=None,raw_bytes=mark['bytes'],members=mark['files_verified'],official_MD5_verified=False,MD5=None,SHA256='per-file local-to-server manifest,4011 files',status='imported_local_SHA256_verified'))
    csvw(rp/'dataset_inventory.csv',inv)
    factor=[]
    def add(component,name,availability,tracks,sequences,decision,quality,identifiability,fields):
        factor.append(dict(component=component,factor=name,observability=availability,distinct_track_groups=tracks,sequences=sequences,decision=decision,
                           quality_evidence=quality,identifiability=identifiability,columns=fields,final_model_selection=False))
    for name,fields in [('distance','distance_to_sensor_m'),('occlusion','occluded_state'),('bbox_size','bbox_area_px'),('truncation','truncated_state')]:
        add('R',name,'Direct' if name in ['occlusion','truncation'] else 'Derived',r['distinct_pedestrian_track_groups'],r['sequences'],'Hold_conditional_R_keep_fields',
            'Actual fields verified, but only9track groups/1sequence; see spd_condition_counts.csv','Paired annotations, common boxes, async timing and supplied nonrigid camera transform confound pure perception error',fields)
    add('R','sensor_time_gap','Direct',r['distinct_pedestrian_track_groups'],r['sequences'],'Keep_QC_covariate','Integer microsecond timestamps verified; raw signed gap retained','Cannot identify camera error independently of annotation/motion/calibration','camera_timestamp,lidar_timestamp,timestamp_gap_s')
    for name,fields in [('current_speed','speed_reported_mps,speed_from_position_mps'),('acceleration_deceleration','accel_proxy'),('stop_restart','speed_reported_mps,dt'),('heading_change','heading_change,heading_rate_deg_s'),('nearby_pedestrians','nearby_ped_count,concurrent_ped_count')]:
        add('Q',name,'Derived' if name!='current_speed' else 'Direct+Derived',q['pedestrian_tracks'],q['sequences'],'Keep_diagnostic_candidate',
            'Counts/sequence support in imptc_condition_counts.csv and imptc_event_sensitivity.csv; not final event labels',
            'Sensing/tracking/derivative noise included; not pure process noise; nearby5m uses observed finite tracks',fields)
    add('Q/R','sensor_source','Direct',q['pedestrian_tracks'],q['sequences'],'Keep_stratification_control',json.dumps(q['source_type_counts']),
        'Source switching affects measured movement as well as perception; avoid double counting/leakage','source_type,status,quality_flags')
    add('Q','pedestrian_signal','Direct_group_states; single-track spatial assignment Unavailable',q['pedestrian_tracks'],q['sequences'],'Hold_spatial_join',
        f'Temporal missing fraction={q["signal_temporal_missing_fraction"]:.6f}; f1/f2/f3 retained','Which crossing/signal applies to each track is not validated','signal_f1,signal_f2,signal_f3,signal_age_s,ped_signal')
    weather=pd.read_csv(rp/'imptc_condition_counts.csv');ww=weather[(weather.condition=='weather_name')&weather.value.notna()]
    diverse=len(ww[ww.value.notna()])>=2 and int(ww.sequences.min())>=3 if len(ww) else False
    add('Q','weather','Direct',q['pedestrian_tracks'],q['sequences'],'Keep_diagnostic_candidate' if diverse else 'Hold_condition_support',
        f'{len(ww)} observed categories; see condition track/sequence denominators','Weather is sequence-level context; repeated frames are not independent weather observations','weather_name,weather_status,weather_age_s')
    add('B','between_person_speed','Derived_track_mean_proxy',q['pedestrian_tracks'],q['sequences'],'Keep_initial_speed_prior_candidate_only',
        'Between-track mean speed separated from within-track variation; same-person identities across sequences unknown',
        'Track means mix person/environment/stop behavior; not stable person-specific speed truth','track_uid,speed_reported_mps,track_duration_s')
    add('Outcome','completed_crossing_time','Unavailable_until_verified_regions',q['pedestrian_tracks'],q['sequences'],'Exclude_current_round_future_geometry_required',
        'ground_type alone is insufficient; completed/partial count N/A','No validated entry/opposite-exit polygons or per-track signal assignment','N/A')
    csvw(rp/'factor_decision_table.csv',factor)
    dictionary=[]
    for p in [rp/'spd_data_dictionary.csv',rp/'imptc_data_dictionary.csv']:dictionary.extend(pd.read_csv(p).fillna('').to_dict('records'))
    dictionary.extend(dict(dataset='IMPTC',field=f,dtype='string',unit='frame/unit metadata',missing_count=0,meaning=str(qdf[f].iloc[0])) for f in added)
    csvw(rp/'data_dictionary.csv',dictionary)
    funnel=[dict(dataset='SPD',stage='infrastructure_frames',n=r['frames'],unit='frames'),dict(dataset='SPD',stage='camera_pedestrians',n=r['camera_pedestrian_observations'],unit='observations'),dict(dataset='SPD',stage='unique_ID_matched_pairs',n=r['matched_pairs'],unit='pairs'),
            dict(dataset='SPD',stage='distinct_track_groups',n=r['distinct_pedestrian_track_groups'],unit='track groups in1sequence'),
            dict(dataset='IMPTC Set01',stage='all_pedestrian_rows_preserved',n=q['pedestrian_observations'],unit='observations'),dict(dataset='IMPTC Set01',stage='finite_coordinates',n=q['finite_coordinates'],unit='observations'),dict(dataset='IMPTC Set01',stage='documented_valid_status2',n=q['strict_status2_observations'],unit='observations')]
    for sec,n in q['strict_continuity_counts'].items():funnel.append(dict(dataset='IMPTC Set01',stage='strict_valid_continuous_ge'+sec+'seconds',n=n,unit='tracks'))
    csvw(rp/'data_funnel.csv',funnel)
    # Recompute fixed-time lag1 only on plausible consecutive frame intervals, never bridge long gaps.
    trs=[]
    frame=pd.read_csv(rp/'spd_frame_inventory.csv',dtype={'sequence_id':str,'frame_id':str});nominal=np.median(np.diff(np.sort(frame.camera_timestamp_us.unique())))/1e6
    for uid,g in rdf.groupby('track_uid'):
        g=g.sort_values('camera_timestamp');dt=np.diff(g.camera_timestamp.to_numpy())/1e6;keep=(dt>0)&(dt<=1.5*nominal);row=dict(track_uid=uid,lag1_time_window_max_s=1.5*nominal,consecutive_pairs=int(keep.sum()),gapped_pairs_ignored=int((~keep).sum()))
        for col in ['dx','dy']:
            a=g[col].to_numpy()[:-1][keep];b=g[col].to_numpy()[1:][keep];row[col+'_lag1']=float(np.corrcoef(a,b)[0,1]) if len(a)>2 and a.std()>0 and b.std()>0 else None
        trs.append(row)
    csvw(rp/'spd_fixed_time_autocorrelation.csv',trs)
    citations=[dict(name='SPD official repo',url='https://github.com/AIR-THU/DAIR-V2X-Seq',git_commit=subprocess.check_output(['git','-C',str(ROOT/'repos/spd'),'rev-parse','HEAD'],text=True).strip()),
               dict(name='IMPTC official repo',url='https://github.com/kav-institute/imptc-dataset',git_commit=subprocess.check_output(['git','-C',str(ROOT/'repos/imptc'),'rev-parse','HEAD'],text=True).strip()),
               dict(name='IMPTC data record',url='https://zenodo.org/records/14811016',license='CC-BY-NC-4.0 per downloaded Zenodo record; repository code Apache-2.0')]
    js(rp/'source_provenance.json',dict(sources=citations,source_plan_sha256=sha(ROOT/'plan.md'),SPD_dataset_license='Not independently established by the example README; source research use and no redistribution; code-license is not assumed dataset-license',
       historical_HTML='preliminary only: R~0.19m reproduced as annotation-discrepancy diagnostic, q~0.05/G95/contributions not estimated in this audit'))
    summary=['# View2Risk data audit — 261025','',
             '범위: 공개 데이터 확보·실제스키마·품질·R/Q조건후보 선정. 모델학습, Kalman튜닝, 최종R/Q행렬, MonteCarlo/G95/신호최적화는 수행하지 않았다.','',
             '## 확보한 데이터','',table(inv,['dataset','status','archive_bytes','raw_bytes','members','official_MD5_verified']),'',
             'SPD는공식다운로드링크들이quota에걸려기존로컬프로젝트의공식Example을서버로복사하고4,011파일SHA256을대조했다. 원본로컬파일은수정하지않았다. SPD full확대는공식접근제약으로미실행이며conditional R결론은유보한다. IMPTC Samples와FullSet01은Zenodo공식MD5검증후해제했다.','',
             '## R 후보 — SPD','',
             f'{r["frames"]}frames / {r["distinct_pedestrian_track_groups"]}distinct track groups / {r["sequences"]}sequence. camera/lidarPedestrian각{r["camera_pedestrian_observations"]}관측, unique-ID매칭{r["matched_pairs"]}/{r["union_ID_rows"]}, 실패/중복{r["unmatched_or_duplicate_rows"]}. world-horizontal annotation discrepancy RMSE **{r["RMSE_world_horizontal_xy_m"]:.6f}m**, p95 {r["discrepancy_norm_m"]["p95"]:.6f}m. 원래HTML≈0.19m는이정의의진단으로재현됐다. **카메라검출기예측오차나최종R은아니다.**','',
             f'camera source3Dpoint의K투영bbox포함률{100*r["projection_K_camera_bbox_fraction"]:.2f}%, lidar{100*r["projection_K_lidar_bbox_fraction"]:.2f}%. 제공P투영은각각{100*r["projection_P_camera_bbox_fraction"]:.2f}%/{100*r["projection_P_lidar_bbox_fraction"]:.2f}%였다. 제공camera변환은{r["camera_nonrigid_calibration_frames"]}frames에서정규직교회전조건을만족하지않았다(max|RᵀR−I|={r["max_camera_orthogonality_error"]:.6f}). 임의보정없이일반inverse를사용하고calibration해석제약을남겼다. 양쪽label은2Dbox를공유하고시각차도있으므로오차원을분리식별할수없다.','',
             '## Q 후보 — IMPTC','',
             f'Samples: {sample["sequences"]}sequences / {sample["pedestrian_tracks"]}Pedestrian tracks / {sample["pedestrian_observations"]}observations. **본감사는FullSet01만:** {q["sequences"]}sequences / {q["pedestrian_tracks"]}tracks / {q["pedestrian_observations"]}observations, documented-valid status2={q["strict_status2_observations"]}.','',
             f'Samples/Full에겹치는VRU{overlap["overlapping_VRU_tracks"]}tracks(그중Pedestrian{overlap["overlapping_pedestrian_tracks"]})가있고,{overlap["differing_semantic_exports"]}개는JSON내용도달랐다. 같은시간대의3D좌표차이최대{overlap["max_xyz_difference_m"]:.6f}m. 재수출/전처리차이의원인은확정하지않았다. 본표본은FullSet01을canonical로쓰고Samples는별도stage_samples로보존하여혼합/중복가산하지않았다.','',
             '유효status2연속관측트랙수:',table([dict(min_seconds=k,tracks=v) for k,v in q['strict_continuity_counts'].items()],['min_seconds','tracks']),'',
             f'시각간격중앙값{q["dt_s"]["median"]:.6f}s, gap>{.06}s={q["gap_count"]}, 중복시각row={q["duplicate_timestamp_rows"]}, 역순step={q["out_of_order_steps"]}. 보고속력은scalar km/h→m/s로변환했고위치차분속력과비교했다. 두값의높은일치는동일tracking처리로부터나올수있어독립센서참값검증으로간주하지않는다.','',
             f'신호temporaljoin결측{100*q["signal_temporal_missing_fraction"]:.4f}%, weather결측{100*q["weather_temporal_missing_fraction"]:.4f}%. f1/f2/f3를각각보존하지만개별보행자의crosswalk·신호공간배정은미검증이다. 완전/부분횡단수는 **N/A**이며ground_type만으로확정하지않았다.','',
             '## 조건 후보 결정','',table(factor,['component','factor','observability','distinct_track_groups','sequences','decision']),'',
             'Keep는다음단계held-out검증에남길진단후보를뜻하고최종모델채택이아니다. R측필드는보존하되1sequence/9track만으로조건부R을정식추정하지않는다. Q의가속도/정지/회전은측정·추적잡음을포함한proxy이며sensitivity grid로그수만집계했다. B는track평균속도분포를초기속도사전분포후보로남기고별도핵심UQ모듈로추정하지않는다.','',
             'SPD와IMPTC는서로다른국가/교차로/센싱파이프라인이다. 이번표를합쳐동일장면의R/Q가독립적으로식별됐다고주장하지않는다. 장소간transfer와측정오차분리는다음단계검증과제다.','',
             '## 인계 파일','',
             '- data/processed/spd_pedestrian_pairs.parquet: 원시ID·시간·양쪽좌표·조건·매칭/품질flag.\n- data/processed/imptc_pedestrian_tracks.parquet: FullSet01모든Pedestrian관측, 상태·좌표·속력·파생진단·context.\n- reports/data_dictionary.csv: 필드뜻·단위·결측.\n- reports/factor_decision_table.csv: 후보/보류/제외근거.\n- reports/spd_schema_report.md, imptc_schema_report.md, r_quality_report.md, q_quality_report.md: 세부감사.\n- reports/figures/: SPD8사례와분포그림, IMPTC6궤적/원본topview및분포그림.\n- reports/data_funnel.csv: 원본관측과strict진단분모. 원본행은정제테이블에서조용히삭제하지않았다.\n- reports/imptc_overlap_exports.csv: 겹치는export차이; reports/stage_samples/: 독립샘플감사.\n- validation.json: 독립출력검증통과여부.','',
             '원래HTML의q≈.05/G95/기여도수치는preliminary로남기고이번작업에서계산하지않았다. 선택TFD재분석도이번감사에서는미실행이다.','',
             '공식출처: [SPD](https://github.com/AIR-THU/DAIR-V2X-Seq), [IMPTC](https://github.com/kav-institute/imptc-dataset), [Zenodo](https://zenodo.org/records/14811016).']
    (rp/'data_audit_summary.md').write_text('\n'.join(summary)+'\n')
    (ROOT/'README.md').write_text('# View2Risk data audit (261025)\n\n서버 `/data/whereami/math/view2risk_261025/`에서관리한다. 먼저 reports/data_audit_summary.md와 validation.json을확인한다.\n\n원본 data/raw와 downloads는보존하며정제결과는data/processed, 코드는scripts, 보고서는reports에둔다. SPD는기존로컬공식Example을SHA256검증하여가져왔고, IMPTCSamples/Set01은Zenodo공식MD5로검증했다. Samples와Full겹치는export를혼합하지않고main은Set01만사용한다.\n\n실행: scripts/01_inspect_spd.py(SPD), scripts/02_inspect_imptc.py(IMPTC), scripts/finalize.py, scripts/verify.py. 기존파일유지를위해새버전폴더에서재실행할것. source URL·commit·checksum·license는reports/source_provenance.json과dataset_inventory.csv.\n\n이번범위는R/Q조건후보와데이터품질감사다. 모델학습/Kalman튜닝/최종R,Q/MonteCarlo/G95/신호최적화는하지않았다. R은paired annotation discrepancy이고순수카메라모델오차가아니다. Q파생량도측정/추적잡음을포함한proxy다.\n\nSPD full확대는공식Drivequota로미실행. 완전횡단/보행자별신호spatialjoin은미검증이므로N/A. 선택TFD재분석미실행.\n')
    print(json.dumps(dict(finalized=True,R_pairs=r['matched_pairs'],R_track_groups=r['distinct_pedestrian_track_groups'],Q_tracks=q['pedestrian_tracks'],Q_observations=q['pedestrian_observations'],Q_sequences=q['sequences'])),flush=True)
if __name__=='__main__':main()
