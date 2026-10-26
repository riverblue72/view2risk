"""Observed-schema IMPTC parser and quality diagnostics, no R/Q fitting."""
from collections import Counter,defaultdict
from pathlib import Path
import json,math,os
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from common import ROOT,js,sha,csvw,stats,table

STAGE=os.environ.get('VIEW2RISK_STAGE','main')
REPORT=ROOT/'reports' if STAGE=='main' else ROOT/'reports'/('stage_'+STAGE)
PROCESSED=ROOT/'data/processed' if STAGE=='main' else ROOT/'data/processed'/('stage_'+STAGE)
def items(path,field):
    if not path.exists():return {},{}
    j=json.loads(path.read_text());return j,j.get(field,{})
def asof(ts,data,tolerance):
    keys=sorted(int(k) for k in data);values=[data[str(k)] for k in keys]
    if not keys:return None,None
    index=int(np.searchsorted(keys,int(ts),side='right')-1)
    if index<0:return None,None
    age=(int(ts)-keys[index])/1e6
    return (values[index],age) if 0<=age<=tolerance else (None,age)
def longest_segment(ts,valid):
    best=current=0.;last=None
    for t,v in zip(ts,valid):
        if not v:last=None;current=0.;continue
        if last is not None and 0<(int(t)-int(last))<=60000:current+=(int(t)-int(last))/1e6
        else:current=0.
        best=max(best,current);last=t
    return best
def main():
    PROCESSED.mkdir(parents=True,exist_ok=True);REPORT.mkdir(exist_ok=True)
    packages=[p for p in (ROOT/'data/raw').glob('imptc*') if (p/'extraction_complete.json').exists()]
    # Full release is the canonical main audit; sample exports are a separate schema/PoC stage.
    # Same sequence/track can have different numerical exports, so never silently pool them.
    if STAGE=='main' and any(p.name=='imptc_set_01' for p in packages):packages=[p for p in packages if p.name=='imptc_set_01']
    paths=sorted(p for package in packages for p in package.glob('**/vrus/*/track.json'))
    assert paths,'No verified IMPTC tracks extracted'
    registry={};duplicates=[];raw_hashes={};examples=[];all_vru_classes=Counter()
    for p in paths:
        seq=p.parents[2].name;tid=p.parent.name;key=(seq,tid);h=sha(p)
        raw_hashes[str(p)]=h
        if key in registry:
            old=registry[key];duplicates.append(dict(sequence_id=seq,track_id=tid,first=str(old),duplicate=str(p),same_content=sha(old)==h))
            assert sha(old)==h,('Conflicting duplicate sequence/track; inspect before combining',key)
            continue
        registry[key]=p
    records=[];tracks=[];contexts=[];master_cache={};context_cache={};source_tracks=Counter()
    for (seq,tid),p in sorted(registry.items()):
        j=json.loads(p.read_text());overview=j['overview'];all_vru_classes[str(overview.get('class_id'))+'|'+str(overview.get('class_name'))]+=1
        if int(overview['class_id'])!=0:continue
        assert str(overview.get('class_name','')).lower() in ['person','pedestrian']
        source_tracks[p.relative_to(ROOT/'data/raw').parts[0]]+=1
        source=p.relative_to(ROOT/'data/raw').parts[0];folder=p.parents[2]
        if seq not in context_cache:
            cj=folder/'context';ss,signal=items(cj/'traffic_light_signals.json','status_data');ww,weather=items(cj/'weather_data.json','weather_data');mm,master=items(cj/'master_timestamp_sync.json','MISSING')
            for path in [cj/'traffic_light_signals.json',cj/'weather_data.json',cj/'master_timestamp_sync.json']:
                if path.exists():raw_hashes[str(path)]=sha(path)
            context_cache[seq]=(signal,weather,ww.get('overview',{}));master_cache[seq]=set(map(int,mm.keys()))
            contexts.append(dict(sequence_id=seq,signal_records=len(signal),weather_records=len(weather),master_records=len(mm),
                                 signal_dt_s=stats(np.diff(sorted(map(int,signal)))/1e6),weather_dt_s=stats(np.diff(sorted(map(int,weather)))/1e6),
                                 master_dt_s=stats(np.diff(sorted(map(int,mm)))/1e6),weather_overview=ww.get('overview',{}),
                                 source_folder=str(folder)))
        signal,weather,w_over=context_cache[seq]
        data=j['track_data'];assert isinstance(data,dict)
        if len(examples)<2:examples.append(dict(path=str(p),overview=overview,first_record=next(iter(data.items()))))
        raw_rows=list(data.items());original_ts=[int(v['ts']) for _,v in raw_rows]
        order_errors=sum(b<a for a,b in zip(original_ts,original_ts[1:]));bucket=[]
        for source_index,(key,v) in enumerate(raw_rows):
            ts=int(v['ts']);assert 1e15<ts<3e15,'Expected actual microsecond epoch timestamp'
            xyz=v.get('coordinates',[]);finite=len(xyz)==3 and all(np.isfinite(float(x)) for x in xyz)
            sig,sig_age=asof(ts,signal,1.2);wea,wea_age=asof(ts,weather,12.)
            row=dict(dataset_source=source,sequence_id=seq,track_id=tid,track_uid=seq+'/'+tid,source_path=str(p),source_row_key=key,source_index=source_index,
                     ts_raw=str(v['ts']),ts_us=ts,t_seconds=ts/1e6,timestamp_unit='UNIX epoch microseconds',coordinate_frame='IMPTC intersection-local XYZ metres, East/North/Up; different from SPD world',x=float(xyz[0]) if finite else np.nan,y=float(xyz[1]) if finite else np.nan,z=float(xyz[2]) if finite else np.nan,
                     speed_reported_mps=float(v['velocity'])/3.6 if v.get('velocity') is not None else np.nan,
                     status=v.get('status'),source_type=v.get('source_type'),ground_type=v.get('ground_type'),class_prob=v.get('class_prob'),
                     finite_coordinates=finite,strict_documented_valid_status2=v.get('status')==2,
                     timestamp_in_master=ts in master_cache[seq],signal_available=sig is not None,signal_age_s=sig_age,
                     weather_available=wea is not None,weather_age_s=wea_age,weather_status=w_over.get('status') if wea else None,
                     weather_name=w_over.get('name') if wea else None,ped_signal=None,ped_signal_spatial_assignment='not_validated',
                     original_track_out_of_order=order_errors>0)
            for field in ['f1','f2','f3']:row['signal_'+field]=sig.get(field) if sig else None
            for field in ['air_temperature','precipitation_intensity','precipitation_amount','visibility','wind_speed']:
                row['weather_'+field]=wea.get(field) if wea else None
            bucket.append(row)
        bucket.sort(key=lambda r:(r['ts_us'],r['source_index']));n=len(bucket);ts=np.array([r['ts_us'] for r in bucket],dtype=np.int64)
        xy=np.array([[r['x'],r['y']] for r in bucket]);speed=np.array([r['speed_reported_mps'] for r in bucket]);valid=np.array([r['strict_documented_valid_status2'] and r['finite_coordinates'] for r in bucket])
        delta=np.r_[np.nan,np.diff(ts)/1e6];dx=np.r_[np.nan,np.diff(xy[:,0])];dy=np.r_[np.nan,np.diff(xy[:,1])]
        with np.errstate(divide='ignore',invalid='ignore'):
            position_speed=np.hypot(dx,dy)/delta;accel=np.r_[np.nan,np.diff(speed)]/delta
        position_speed[~(delta>0)]=np.nan;accel[~(delta>0)]=np.nan
        heading=np.arctan2(dy,dx);turn=np.r_[np.nan,np.angle(np.exp(1j*np.diff(heading)))];turn_rate=np.degrees(turn)/delta
        dup=Counter(ts);long_all=longest_segment(ts,[r['finite_coordinates'] for r in bucket]);long_strict=longest_segment(ts,valid)
        for i,r in enumerate(bucket):
            flags=[]
            if not r['finite_coordinates']:flags.append('NONFINITE_COORDINATES')
            if dup[r['ts_us']]>1:flags.append('DUPLICATE_TIMESTAMP')
            if np.isfinite(delta[i]) and delta[i]>.06:flags.append('GAP_GT_60MS')
            if np.isfinite(position_speed[i]) and position_speed[i]>5:flags.append('POSITION_SPEED_GT5MPS_CANDIDATE')
            if np.isfinite(position_speed[i]) and position_speed[i]>20:flags.append('EXTREME_JUMP_OR_ID_SWITCH_CANDIDATE')
            if r['status']!=2:flags.append('STATUS_NOT_DOCUMENTED_VALID2')
            if i and r['source_type']!=bucket[i-1]['source_type']:flags.append('SENSOR_SOURCE_SWITCH')
            r.update(dt=delta[i],dx=dx[i],dy=dy[i],speed_from_position_mps=position_speed[i],heading_rad=heading[i],heading_change=turn[i],
                     heading_rate_deg_s=turn_rate[i],accel_proxy=accel[i],track_duration_s=(int(ts[-1])-int(ts[0]))/1e6,
                     gap_count=int(np.sum(delta>.06)),quality_flags=';'.join(flags),raw_status_semantics_verified=False)
        tracks.append(dict(sequence_id=seq,track_id=tid,track_uid=seq+'/'+tid,dataset_source=source,observations=n,strict_valid2_observations=int(valid.sum()),
                           duration_s=(int(ts[-1])-int(ts[0]))/1e6,longest_continuous_all_status_s=long_all,longest_continuous_status2_s=long_strict,
                           mean_speed_reported_mps=float(np.nanmean(speed)),within_track_speed_std_mps=float(np.nanstd(speed)),
                           source_class_name=overview.get('class_name'),overview_length=overview.get('lenght',overview.get('length')),
                           actual_length=n,duplicate_timestamp_rows=sum(dup[t]>1 for t in ts),out_of_order_steps=order_errors,gap_count=int(np.sum(delta>.06)),
                           source_types=sorted({str(r['source_type']) for r in bucket}),status_counts=dict(Counter(str(r['status']) for r in bucket)),
                           raw_path=str(p),raw_sha256=raw_hashes[str(p)]))
        records.extend(bucket)
    df=pd.DataFrame(records);assert len(df)>0
    df['concurrent_ped_count']=0;df['nearby_ped_count']=0
    for _,indices in df.groupby(['sequence_id','ts_us'],sort=False).groups.items():
        sub=df.loc[indices];finite=sub['finite_coordinates'];valid_indices=sub.index[finite];points=sub.loc[valid_indices,['x','y']].to_numpy()
        if len(points):
            # One row per track/timestamp is expected; duplicates are flagged above and never independently counted.
            unique=sub.loc[valid_indices].drop_duplicates('track_uid');tree=cKDTree(unique[['x','y']].to_numpy())
            df.loc[valid_indices,'nearby_ped_count']=np.asarray(tree.query_ball_point(points,5.,return_length=True))-1
            df.loc[indices,'concurrent_ped_count']=len(unique)
    df['nearby_count_radius_m']=5.;df['nearby_count_status_policy']='all_observed_finite_statuses_not_confirmed_valid'
    df.to_parquet(PROCESSED/'imptc_pedestrian_tracks.parquet',index=False,compression='zstd')
    csvw(REPORT/'imptc_track_summary.csv',tracks);csvw(REPORT/'imptc_context_summary.csv',contexts);csvw(REPORT/'imptc_duplicates.csv',duplicates,fields=['sequence_id','track_id','first','duplicate','same_content'])
    js(REPORT/'imptc_schema_examples.json',examples)
    frame_fields=[dict(field=k,type=type(v).__name__,example=v) for k,v in examples[0]['first_record'][1].items()]
    js(REPORT/'imptc_observed_schema.json',dict(fields=frame_fields,overview=examples[0]['overview']))
    metrics=dict(analysis_scope=[p.name for p in packages],sample_stage_kept_separate=True,sequences=df.sequence_id.nunique(),pedestrian_tracks=len(tracks),pedestrian_observations=len(df),
                 source_packages=dict(source_tracks),all_VRU_class_counts=dict(all_vru_classes),duplicate_tracks=len(duplicates),
                 status_counts={str(k):int(v) for k,v in df.status.value_counts(dropna=False).items()},
                 source_type_counts={str(k):int(v) for k,v in df.source_type.value_counts(dropna=False).items()},
                 strict_status2_observations=int(df.strict_documented_valid_status2.sum()),finite_coordinates=int(df.finite_coordinates.sum()),
                 duplicate_timestamp_rows=sum(t['duplicate_timestamp_rows'] for t in tracks),out_of_order_steps=sum(t['out_of_order_steps'] for t in tracks),
                 gap_count=sum(t['gap_count'] for t in tracks),dt_s=stats(df.dt),track_duration_s=stats([t['duration_s'] for t in tracks]),
                 speed_reported_mps=stats(df.speed_reported_mps),speed_position_mps=stats(df.speed_from_position_mps),
                 speed_reported_minus_position_mps=stats(df.speed_reported_mps-df.speed_from_position_mps),
                 between_track_mean_speed_mps=stats([t['mean_speed_reported_mps'] for t in tracks]),within_track_speed_std_mps=stats([t['within_track_speed_std_mps'] for t in tracks]),
                 signal_temporal_missing_fraction=float((~df.signal_available).mean()),weather_temporal_missing_fraction=float((~df.weather_available).mean()),
                 master_timestamp_missing_fraction=float((~df.timestamp_in_master).mean()),
                 position_speed_gt5_observations=int((df.speed_from_position_mps>5).sum()),
                 extreme_jump_gt20_observations=int((df.speed_from_position_mps>20).sum()),
                 strict_continuity_counts={str(t):sum(r['longest_continuous_status2_s']>=t for r in tracks) for t in [1,2,5,10]},
                 all_status_continuity_counts={str(t):sum(r['longest_continuous_all_status_s']>=t for r in tracks) for t in [1,2,5,10]},
                 confirmed_complete_crossings=None,partial_crossings=None,crossing_count_reason='No verified crossing polygons and f1-f3 spatial association; ground_type alone is not a completed crossing',
                 model_training=False,final_R_Q_estimated=False)
    js(REPORT/'imptc_metrics.json',metrics)
    condition_stats(df,tracks)
    schema=['# IMPTC observed schema','',f'실제 {len(tracks)} Pedestrian tracks, {metrics["sequences"]} sequences에서 읽었다. 원본 class_id=0을 사용하며 실제 class_name은 person이다.','',
            '원본 ts는 문자열 microsecond UNIX epoch이다. int64로 읽고 차분 후1e6으로 나눠 초 단위를 만든다(25Hz라면 dt=.04s). track_data key는 순번 문자열이므로 내부 ts를 사용했다. overview 길이 필드는 실제로 `lenght`로 표기된다.','',table(frame_fields,['field','type','example']),'',
            '좌표는 공식 문서의 intersection-local XYZ(m). velocity는 scalar km/h이며 /3.6으로m/s 변환. status=2만 문서상 accepted-valid로 표시하고 status1을 임의로 valid로 재해석하지 않았다. 원본 모든 Pedestrian 관측을 보존하고 strict status2 분석 분모를 별도로 계산했다. 실제 상태 수와 문서 불일치 가능성은 quality report 참조.','',
            'context의 key는 실제 timestamp다. 신호 backward-asof≤1.2s, weather≤12s의 사전 명시된 감사 join을 적용하고 age/missing을 남긴다. 공식 문서의 신호약1Hz/weather10s와 실제 간격을 별도 비교한다. f1/f2/f3를 각각 보존하며 spatial association 미검증 상태에서는 단일ped_signal을 만들지 않는다.','',
            '측정 기반/추적 기반 궤적이므로 위치차분·accel_proxy는 참값 가속도나 순수Q가 아니다. 전체 schema와 실제 예제는 imptc_schema_examples.json, Parquet열과단위는 data_dictionary.csv에 있다.']
    (REPORT/'imptc_schema_report.md').write_text('\n'.join(schema)+'\n')
    text=['# IMPTC Q-candidate quality audit','',table([dict(metric=k,value=json.dumps(v,ensure_ascii=False)) for k,v in metrics.items()],['metric','value']),'',
          '모든 class_id0 관측은 Parquet에 남겼다. 유효 status2만의 분모와 모든 status의 geometry/time-only 연속성 분모는 서로 다르다. 같은 seq/track의 샘플·full 중복은 raw SHA256이 같은 경우 한 번만 센다. 독립적인 사람 수를 보장하지 않으므로 track 수를 independent persons라고 부르지 않는다.','',
          '## 임계값 민감도와 조건','',
          '정지 속도 .2/.3/.5m/s, 가감속 |a| .3/.5/1m/s², 방향변화30/45/60deg/s의 sensitivity grid를 계산했다. 이는 탐색 후보이며 최종 행동 정답이나 Q 모델로 확정하지 않는다. dt>60ms는25Hz 기준1.5step gap flag, 위치차분속도>5m/s와>20m/s는 점프/ID-switch 의심 flag만 남기며 제거하지 않는다.','',
          '현재 속력·가감속·정지재출발·방향·crowding은 noisy measured trajectory에서 파생된다. source_type과status,원시field를 유지하여 관측 잡음과 행동 변화가 섞이는 문제를 드러낸다. 인원수는 같은 sequence/ts의 관측된 distinct track, nearby는 XY5m반경이며 accepted-valid라고 가정하지 않는다.','',
          '신호는 f1/f2/f3의 시간 join까지 검증한다. 어떤 보행자가 어느crosswalk 신호에 대응하는지 확정하지 않았다. 지도상 검증된 진입/출구 polygon이 없으면 완전횡단/부분횡단은 N/A로 기록한다. ground_type5 run을 완전횡단으로 세지 않는다. 신호/날씨/행동별 독립 sequence 수는 조건표에 기록한다.','',
          '공식 지도와 원본 topview 그림의 좌표 설명은 시각화에 나란히 제시하며, 검증되지 않은 world→image mapping으로 trajectory를 겹치지 않는다. raw native source checksum은 imptc_raw_integrity.json에서 검증한다.']
    (REPORT/'q_quality_report.md').write_text('\n'.join(text)+'\n')
    dictionary=[]
    for col in df.columns:
        unit='microseconds since UNIX epoch' if col=='ts_us' else 'm' if col in ['x','y','z','dx','dy','nearby_count_radius_m'] else 'm/s' if 'mps' in col else 'm/s² proxy' if col=='accel_proxy' else 'seconds' if col in ['dt','track_duration_s','signal_age_s','weather_age_s','t_seconds'] else 'radians' if col in ['heading_rad','heading_change'] else 'degrees/s' if col=='heading_rate_deg_s' else 'source code/count/flag/ID, see field'
        dictionary.append(dict(dataset='IMPTC',field=col,dtype=str(df[col].dtype),unit=unit,missing_count=int(df[col].isna().sum()),meaning='spatial signal assignment unavailable' if col=='ped_signal' else col))
    csvw(REPORT/'imptc_data_dictionary.csv',dictionary)
    visualize(df,tracks)
    for p,h in raw_hashes.items():assert sha(p)==h
    js(REPORT/'imptc_raw_integrity.json',dict(passed=True,raw_files=len(raw_hashes),hashes=raw_hashes,all_pedestrian_observations_preserved=True))
    print(json.dumps(metrics),flush=True)

def condition_stats(df,tracks):
    tables=[]
    for field in ['status','source_type','ground_type','weather_name','signal_f1','signal_f2','signal_f3']:
        for value,g in df.groupby(field,dropna=False):
            tables.append(dict(condition=field,value=str(value),observations=len(g),tracks=g.track_uid.nunique(),sequences=g.sequence_id.nunique(),
                               median_speed_mps=float(g.speed_reported_mps.median()),strict_status2=int(g.strict_documented_valid_status2.sum())))
    csvw(REPORT/'imptc_condition_counts.csv',tables)
    events=[]
    for kind,thresholds,field in [('stop',[.2,.3,.5],'speed_reported_mps'),('acceleration',[.3,.5,1.],'accel_proxy'),('deceleration',[.3,.5,1.],'accel_proxy'),('turn',[30.,45.,60.],'heading_rate_deg_s')]:
        for threshold in thresholds:
            mask=(df[field]<threshold) if kind=='stop' else (df[field]>threshold) if kind=='acceleration' else (df[field]<-threshold) if kind=='deceleration' else ((df[field].abs()>threshold)&(df.speed_from_position_mps>.2))
            obs=int(mask.sum());episodes=0;restarts=0;ids=set();seqs=set()
            for uid,g in df.groupby('track_uid',sort=False):
                m=mask.loc[g.index].to_numpy();dt=g.dt.to_numpy();contiguous=(dt>0)&(dt<=.06);starts=m & (np.r_[True,~m[:-1]]|(~contiguous))
                episodes+=int(starts.sum());restarts+=int(np.sum((~m[1:])&m[:-1]&(dt[1:]<=.06))) if kind=='stop' else 0
                if m.any():ids.add(uid);seqs.add(g.sequence_id.iloc[0])
            events.append(dict(candidate=kind,threshold=threshold,observations=obs,episodes=episodes,restarts=restarts,tracks=len(ids),sequences=len(seqs),exploratory_not_final_labels=True))
    csvw(REPORT/'imptc_event_sensitivity.csv',events)

def visualize(df,tracks):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    figures=REPORT/'figures';figures.mkdir(exist_ok=True)
    fig,axes=plt.subplots(2,3,figsize=(13,7))
    axes[0,0].hist([t['duration_s'] for t in tracks],bins=25);axes[0,0].set(xlabel='Track duration (s)',ylabel='Pedestrian tracks')
    axes[0,1].hist(df.dt.dropna(),bins=40);axes[0,1].set(xlabel='dt (s)',ylabel='Intervals')
    axes[0,2].hist(df.speed_reported_mps.dropna(),bins=50);axes[0,2].set(xlabel='Reported speed (m/s)',ylabel='Observations')
    axes[1,0].hist([t['mean_speed_reported_mps'] for t in tracks],bins=25);axes[1,0].set(xlabel='Mean speed per track (m/s)',ylabel='Tracks')
    axes[1,1].hist((df.speed_reported_mps-df.speed_from_position_mps).dropna(),bins=50);axes[1,1].set(xlabel='Reported minus position speed (m/s)')
    counts=df.status.value_counts();axes[1,2].bar(counts.index.astype(str),counts);axes[1,2].set(xlabel='Raw status code',ylabel='Observations')
    fig.tight_layout();fig.savefig(figures/'imptc_quality.png',dpi=140);plt.close(fig)
    for n,t in enumerate(sorted(tracks,key=lambda t:(-t['gap_count'],-t['duration_s']))[:6]):
        g=df[df.track_uid==t['track_uid']];fig,ax=plt.subplots(1,2,figsize=(11,4));ax[0].plot(g.x,g.y,'.-',ms=2);ax[0].scatter(g.x.iloc[0],g.y.iloc[0],c='green',label='start');ax[0].scatter(g.x.iloc[-1],g.y.iloc[-1],c='red',label='end');ax[0].set(xlabel='local X east (m)',ylabel='local Y north (m)',title=t['track_uid']);ax[0].axis('equal');ax[0].legend()
        folder=Path(t['raw_path']).parent;images=list(folder.glob('*topview.png'))
        if images:ax[1].imshow(mpimg.imread(images[0]));ax[1].set_title('Original supplied topview; no unverified pixel overlay');ax[1].axis('off')
        else:ax[1].plot(g.ts_us/1e6-g.ts_us.iloc[0]/1e6,g.speed_reported_mps);ax[1].set(xlabel='time (s)',ylabel='speed m/s')
        fig.tight_layout();fig.savefig(figures/f'imptc_case_{n+1}.png',dpi=140);plt.close(fig)
if __name__=='__main__':main()
