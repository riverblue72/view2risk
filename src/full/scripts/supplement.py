"""Audit-only geometry/context and optional TFD supplement; no model fitting."""
from pathlib import Path
import os,json,zipfile,hashlib,time
from collections import Counter
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl')
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OLD=Path('/data/whereami/math/view2risk_261025')
PUBLIC=Path('/data/whereami/math/Public-V2X-Datasets')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def js(name,x):(ROOT/'reports'/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if hasattr(v,'item') else v.tolist())+'\n')
def tab(df):
    f=df.copy();rows=[list(f.columns),['---']*len(f.columns),*list(f.fillna('N/A').itertuples(index=False,name=None))]
    return '\n'.join('| '+' | '.join(str(v).replace('|','/') for v in r)+' |' for r in rows)

def geometry(q):
    archive=ROOT/'assets/imptc_ground_plane.zip'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        names=[n for n in z.namelist() if n.endswith('.ply')];assert len(names)==1
        payload=z.read(names[0])
    end=payload.index(b'end_header\n')+len(b'end_header\n');header=payload[:end].decode();assert 'format binary_little_endian' in header
    types={'float':'<f4','double':'<f8','uchar':'u1','char':'i1','int':'<i4','uint':'<u4'}
    fields=[];count=None
    for line in header.splitlines():
        if line.startswith('element vertex '):count=int(line.split()[-1])
        elif line.startswith('property '):
            _,dtype,name=line.split();fields.append((name,types[dtype]))
    array=np.frombuffer(payload,offset=end,count=count,dtype=np.dtype(fields));assert end+array.nbytes==len(payload)
    xy=np.column_stack((array['x'],array['y'])).astype(float)
    colors=np.column_stack([array[x] for x in ['red','green','blue']]).astype(np.uint32)
    packed=(colors[:,0]<<16)|(colors[:,1]<<8)|colors[:,2]
    rgb=[[128,64,128],[244,35,232],[81,0,81],[150,100,100],[157,234,50],[229,165,10],[98,160,234],[128,128,128]]
    codes={r*65536+g*256+b:i for i,(r,g,b) in enumerate(rgb)}
    unique,inverse=np.unique(packed,return_inverse=True);labels=np.array([codes.get(int(x),-1) for x in unique],dtype=np.int8)[inverse]
    finite=np.isfinite(q[['x','y']]).all(axis=1).to_numpy();indices=np.flatnonzero(finite)
    tree=cKDTree(xy);distance,nearest=tree.query(q.loc[finite,['x','y']].to_numpy(),workers=2)
    mapped=np.full(len(q),-1,dtype=np.int8);mapped[indices]=labels[nearest]
    distances=np.full(len(q),np.nan);distances[indices]=distance
    provided=pd.to_numeric(q.ground_type,errors='coerce').to_numpy();comparable=np.isfinite(provided)&(mapped>=0)&finite
    stats=[]
    for threshold in [.1,.25,.5]:
        for scope in ['all_status','accepted_status2']:
            denominator=finite & ((q.status.to_numpy()==2) if scope=='accepted_status2' else True)
            near=denominator&(distances<=threshold)&(mapped>=0);paired=near&comparable
            stats.append(dict(scope=scope,XY_radius_m=threshold,denominator_rows=int(denominator.sum()),near_known_map_rows=int(near.sum()),near_fraction=float(near.sum()/denominator.sum()),
                comparable_rows=int(paired.sum()),provided_vs_map_ground_code_agreement=float((mapped[paired]==provided[paired]).mean()) if paired.any() else None,
                crosswalk_touch_tracks=int(q.loc[near&(mapped==5),'track_uid'].nunique())))
    pd.DataFrame(stats).to_csv(ROOT/'reports/ground_map_consistency.csv',index=False)
    # Candidate raster components expose geometry, but do not label full crossings.
    cross=xy[labels==5];components=[]
    if len(cross):
        origin=cross.min(axis=0);cells=np.floor((cross-origin)/.25).astype(int);image=np.zeros(tuple(cells.max(axis=0)+1),bool);image[cells[:,0],cells[:,1]]=True
        linked=ndimage.binary_closing(image,structure=np.ones((3,3)));numbered,n=ndimage.label(linked,structure=np.ones((3,3)))
        for number in range(1,n+1):
            where=np.argwhere(numbered==number)
            if len(where)<16:continue
            components.append(dict(component=number,raster_cells=len(where),raster_resolution_m=.25,
                min_x_m=float(origin[0]+where[:,0].min()*.25),max_x_m=float(origin[0]+(where[:,0].max()+1)*.25),
                min_y_m=float(origin[1]+where[:,1].min()*.25),max_y_m=float(origin[1]+(where[:,1].max()+1)*.25),candidate_not_validated_entry_exit=True))
    pd.DataFrame(components).to_csv(ROOT/'reports/crosswalk_component_candidates.csv',index=False)
    # Preserve a row-level QC join for future verified crossing definitions.
    mapped_table=q[['sequence_id','track_uid','ts_us','status','ground_type']].copy()
    mapped_table['map_nearest_XY_distance_m']=distances;mapped_table['map_ground_code']=mapped
    mapped_table.to_parquet(ROOT/'data/imptc_ground_map_join.parquet',index=False,compression='zstd')
    fig,ax=plt.subplots(figsize=(10,8));sample=np.random.default_rng(42).choice(len(xy),min(80000,len(xy)),replace=False)
    ax.scatter(xy[sample,0],xy[sample,1],c=colors[sample]/255.,s=.7,rasterized=True,alpha=.6)
    touching=sorted(q.loc[(mapped==5)&(distances<=.25),'track_uid'].unique())
    chosen=np.random.default_rng(42).choice(touching,min(6,len(touching)),replace=False) if touching else []
    for uid in chosen:
        g=q[q.track_uid==uid].sort_values('ts_us');ax.plot(g.x,g.y,lw=1,label=uid)
        ax.annotate('',xy=(g.x.iloc[-1],g.y.iloc[-1]),xytext=(g.x.iloc[max(0,len(g)-10)],g.y.iloc[max(0,len(g)-10)]),arrowprops=dict(arrowstyle='->',color='black'))
    ax.set(xlabel='IMPTC local East X (m)',ylabel='North Y (m)',title='Official semantic point map + recorded tracks\nSame-source ground-code consistency, not independent ground truth');ax.axis('equal');ax.legend(fontsize=5)
    fig.tight_layout();fig.savefig(ROOT/'figures/imptc_semantic_map_tracks.png',dpi=160);plt.close(fig)
    proof=dict(map_archive=str(archive),source_url='https://drive.google.com/file/d/1uPcvJv-etmImUCoVugBAJUJmFrLcd5kR/view',SHA256=sha(archive),zip_crc_passed=True,
        vertices=int(count),unknown_RGB_vertices=int((labels<0).sum()),coordinate_frame='Provider docs explicitly same local metre frame as trajectories',
        XY_nearest_projection=True,results=stats,crosswalk_candidate_components=len(components),
        confirmed_complete_crossings=None,partial_crossings=None,reason='No independently verified entry/opposite-exit definitions or single-track f1/f2/f3 assignment. Raster components alone do not establish complete crossing GT.',
        same_source_consistency_not_independent_accuracy=True,not_used_for_Q_fitting=True)
    js('ground_geometry_audit.json',proof)
    return proof

def quality(q):
    conditions=[]
    for field in ['status','source_type','ground_type','weather_name','signal_f1','signal_f2','signal_f3']:
        for value,g in q.groupby(field,dropna=False):
            conditions.append(dict(field=field,value=str(value),observations=len(g),tracks=g.track_uid.nunique(),sequences=g.sequence_id.nunique(),recording_dates=g.recording_date.nunique()))
    pd.DataFrame(conditions).to_csv(ROOT/'reports/imptc_full_condition_support.csv',index=False)
    uid=q.track_uid.to_numpy();same=np.r_[False,uid[1:]==uid[:-1]]
    valid=(q.status.to_numpy()==2)&q.finite_coordinates.to_numpy()
    dt=q.dt.to_numpy();contiguous=same&valid&np.r_[False,valid[:-1]]&(dt>0)&(dt<=.060)
    episodes=[]
    for kind,limits,field in [('stop',[.2,.3,.5],'speed_reported_mps'),('acceleration',[.3,.5,1.],'accel_proxy'),('deceleration',[.3,.5,1.],'accel_proxy'),('turn',[30.,45.,60.],'heading_rate_deg_s')]:
        values=q[field].to_numpy()
        for limit in limits:
            detected=(values<limit) if kind=='stop' else (values>limit) if kind=='acceleration' else (values<-limit) if kind=='deceleration' else ((abs(values)>limit)&(q.speed_from_position_mps.to_numpy()>.2))
            detected&=valid
            if kind!='stop':detected&=contiguous
            previous=np.r_[False,detected[:-1]]
            beginnings=detected&~(previous&contiguous)
            episodes.append(dict(candidate=kind,threshold=limit,observations=int(detected.sum()),episodes=int(beginnings.sum()),
                restarts=int(((~detected)&previous&contiguous).sum()) if kind=='stop' else None,
                tracks=q.loc[detected,'track_uid'].nunique(),sequences=q.loc[detected,'sequence_id'].nunique(),recording_dates=q.loc[detected,'recording_date'].nunique(),
                status2_and_valid_interval_only=True,not_behavior_ground_truth=True))
    pd.DataFrame(episodes).to_csv(ROOT/'reports/imptc_strict_event_sensitivity.csv',index=False)
    tracks=pd.read_csv(ROOT/'reports/imptc_track_summary.csv')
    missing=dict(signal_temporal_missing_fraction=float((~q.signal_available).mean()),weather_temporal_missing_fraction=float((~q.weather_available).mean()),
        position_speed_gt5=int((q.speed_from_position_mps>5).sum()),position_speed_gt20=int((q.speed_from_position_mps>20).sum()),
        track_mean_speed_mean_mps=float(tracks.mean_speed_reported_mps.mean()),between_track_mean_speed_std_mps=float(tracks.mean_speed_reported_mps.std(ddof=0)),
        within_track_speed_std_mean_mps=float(tracks.within_track_speed_std_mps.mean()))
    js('imptc_full_quality_summary.json',missing);return missing

def tfd_audit():
    root=PUBLIC/'raw/tfd_example/V2X-Seq-TFD-Example/single-infrastructure'
    files=sorted(p for p in root.rglob('*.csv') if 'trajectories' in p.parts)
    rows=[];classes=Counter();provenance={}
    for p in files:
        frame=pd.read_csv(p,dtype={'id':str,'timestamp':str});classes.update(frame.type.astype(str).value_counts().to_dict());provenance[str(p)]=sha(p)
        pedestrian=frame.type.astype(str).str.lower().str.contains('ped') | frame.sub_type.astype(str).str.lower().str.contains('ped')
        part=frame[pedestrian].copy()
        if not len(part):continue
        part['source_file']=str(p);part['scene_id']=p.stem;part['track_uid']=p.stem+'/'+part.id.astype(str)
        part['ts_us']=[int(Decimal(t)*1000000) for t in part.timestamp]
        rows.append(part)
    if not rows:
        proof=dict(scope='single-infrastructure trajectory Example only',files=len(files),pedestrian_rows=0);js('tfd_example_audit.json',proof);return proof
    df=pd.concat(rows,ignore_index=True);df.to_parquet(ROOT/'data/tfd_example_pedestrians.parquet',index=False,compression='zstd')
    summaries=[]
    for uid,g in df.groupby('track_uid'):
        g=g.sort_values('ts_us');dt=np.diff(g.ts_us.to_numpy(np.int64))/1e6
        summaries.append(dict(track_uid=uid,scene_id=g.scene_id.iloc[0],observations=len(g),duration_s=(g.ts_us.iloc[-1]-g.ts_us.iloc[0])/1e6,
            duplicate_timestamps=int((dt==0).sum()),median_dt_s=float(np.median(dt)) if len(dt) else None,
            velocity_vector_zero_fraction=float(((g.v_x==0)&(g.v_y==0)).mean())))
    pd.DataFrame(summaries).to_csv(ROOT/'reports/tfd_example_track_summary.csv',index=False)
    key=['city','intersect_id','id','ts_us'];dup=df.duplicated(key,keep=False)
    unique=df.drop_duplicates(key)
    conflict=df.groupby(key)[['x','y']].nunique().max(axis=1)>1
    proof=dict(scope='single-infrastructure trajectory Example only; other views not pooled',trajectory_files=len(files),pedestrian_scene_track_groups=df.track_uid.nunique(),pedestrian_observations=len(df),
        unique_intersection_id_timestamp_rows=len(unique),duplicate_key_rows=int(dup.sum()),conflicting_duplicate_keys=int(conflict.sum()),
        timestamp_unit='Observed UNIX epoch seconds in CSV; preserved original string and converted Decimal to integer microseconds',
        coordinate_unit_note='Provider XY and velocity-vector fields retained; no cross-dataset covariance or physical Q fit was inferred from undocumented CSV units.',
        dataset_class_counts=dict(classes),independent_person_count_not_established=True,
        historical_q_005_reproduced=False,reason='Original HTML q calculation/units/independent-state assumptions not established; no arbitrary match to q=.05',
        source_files_SHA256=provenance)
    js('tfd_example_audit.json',proof);return proof

def main():
    q=pd.read_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet')
    geo=geometry(q);qual=quality(q);del q
    tfd=tfd_audit()
    text=['# 추가 데이터 품질·공간 검증 및 TFD Example',
        '공식 IMPTC README에서 같은 로컬 좌표계를 사용하는 semantic ground map 링크를 확인해 11MB ZIP을 추가 확보했다. 원본 map ZIP은 assets/에 보존했다. 이 검사는 R/Q 파라미터를 바꾸거나 신호·날씨를 예측 변수에 넣지 않는다.',
        '## IMPTC 지도 연결',tab(pd.DataFrame(geo['results'])),
        f'지도 vertex {geo["vertices"]:,}개. XY 최근접 지도점의 색상 code와 제공 ground_type을 대조했다. 두 정보가 같은 처리 계통에서 생성됐을 수 있으므로 독립 위치 정확도나 segmentation GT 검증은 아니다. 지도/기록 궤적을 공통 metre 좌표로 표시한 그림은 figures/imptc_semantic_map_tracks.png에 있다.',
        '횡단보도 연결 성분은 0.25m raster의 탐색 후보로만 저장했다. 검증된 양쪽 진입/이탈 영역과 개별 트랙의 f1/f2/f3 배정이 없어 **확정 완전/부분 횡단 수는 N/A**다. ground_type5 또는 지도상 체류만으로 완전 횡단을 세거나 G95를 만들지 않았다.',
        '## 전체 IMPTC 품질 요약',json.dumps(qual,ensure_ascii=False,indent=2),
        'imptc_full_condition_support.csv는 조건별 관측/트랙/시퀀스/날짜 지원 규모다. imptc_strict_event_sensitivity.csv는 status2와 유효 인접 간격만 사용하는 정지·가감속·회전 후보표다. 기존 source별 all-status 탐색표와 분모가 다르며 행동 정답이 아니다.',
        '## TFD 선택 비교',json.dumps({k:v for k,v in tfd.items() if k!='source_files_SHA256'},ensure_ascii=False,indent=2),
        '단일 infrastructure view만 사용했다. 겹친 클립/시점이나 센서별 view를 독립 사람/실험으로 합산하지 않았다. IMPTC와 궤적을 섞거나 과거 q≈.05를 임의 재현하지 않았다.']
    (ROOT/'reports/04_geometry_context_tfd.md').write_text('\n\n'.join(text)+'\n')
    js('supplement_validation.json',dict(passed=True,ground_map=geo,tfd=tfd,quality=qual,main_model_parameters_modified=False))
    print(json.dumps(dict(supplement_complete=True,map_vertices=geo['vertices'],TFD_pedestrian_rows=tfd.get('pedestrian_observations',0))),flush=True)

if __name__=='__main__':main()
