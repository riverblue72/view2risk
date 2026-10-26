"""Actual SPD paired annotation discrepancy; not detector error or final R."""
from collections import Counter,defaultdict
from pathlib import Path
import json
import numpy as np
import pandas as pd
from common import ROOT,js,sha,csvw,stats,table
REPORT=ROOT/'reports';PROCESSED=ROOT/'data/processed'
def loc(a):return np.array([a['3d_location'][k] for k in ['x','y','z']],float)
def matrix(j):return np.array(j['rotation'],float).reshape(3,3),np.array(j['translation'],float).reshape(3)
def main():
    REPORT.mkdir(exist_ok=True);PROCESSED.mkdir(parents=True,exist_ok=True)
    paths=list((ROOT/'data/raw').glob('spd*/**/infrastructure-side/data_info.json'));assert paths
    all_rows=[];frames=[];calibrations=[];examples=[];protected={};classes=Counter()
    for ip in paths:
        root=ip.parent;info=json.loads(ip.read_text());assert isinstance(info,list);protected[str(ip)]=sha(ip)
        for f in info:
            def read(key):
                p=root/f[key];assert p.exists();protected[str(p)]=sha(p);return json.loads(p.read_text())
            ca=read('label_camera_std_path');li=read('label_lidar_std_path');intr=read('calib_camera_intrinsic_path');cl=read('calib_virtuallidar_to_camera_path');wl=read('calib_virtuallidar_to_world_path')
            R,t=matrix(cl);W,u=matrix(wl);K=np.array(intr['cam_K']).reshape(3,3);P=np.array(intr['P']).reshape(3,4)
            assert np.isfinite(R).all() and np.isfinite(W).all() and abs(np.linalg.det(R))>1e-8 and abs(np.linalg.det(W))>1e-8
            wo=float(np.max(abs(W.T@W-np.eye(3))));co=float(np.max(abs(R.T@R-np.eye(3))))
            assert wo<.005;center=-np.linalg.solve(R,t)
            rt=float(np.max(abs(np.linalg.solve(W,W@np.ones(3)+u-u)-1)))
            assert rt<1e-8
            calibrations.append(dict(frame_id=f['frame_id'],world_det=float(np.linalg.det(W)),world_orthogonality_error=wo,camera_det=float(np.linalg.det(R)),camera_orthogonality_error=co,camera_transform_not_rigid=co>.005,world_roundtrip_error=rt))
            ct,lt=int(f['image_timestamp']),int(f['pointcloud_timestamp']);assert 1e15<ct<3e15 and 1e15<lt<3e15
            a=defaultdict(list);b=defaultdict(list)
            for prefix,labels,out in [('camera',ca,a),('lidar',li,b)]:
                for label in labels:
                    classes[prefix+'|'+label['type']]+=1
                    if label['type'].lower()=='pedestrian':out[str(label['track_id'])].append(label)
            if len(examples)<2 and (a or b):examples.append(dict(frame=f,camera_pedestrian=next(iter(a.values()),[])[:1],lidar_pedestrian=next(iter(b.values()),[])[:1],camera_calibration=cl,world_calibration=wl,intrinsic=intr))
            frames.append(dict(sequence_id=f['sequence_id'],frame_id=f['frame_id'],camera_timestamp_us=ct,lidar_timestamp_us=lt,timestamp_gap_s=(ct-lt)/1e6,camera_pedestrians=sum(map(len,a.values())),lidar_pedestrians=sum(map(len,b.values())),camera_duplicate_ids=sum(len(x)>1 for x in a.values()),lidar_duplicate_ids=sum(len(x)>1 for x in b.values()),image_exists=(root/f['image_path']).exists(),pointcloud_exists=(root/f['pointcloud_path']).exists()))
            for tid in sorted(set(a)|set(b)):
                match=len(a[tid])==len(b[tid])==1;aa=a[tid][0] if len(a[tid])==1 else None;bb=b[tid][0] if len(b[tid])==1 else None
                row=dict(sequence_id=str(f['sequence_id']),frame_id=str(f['frame_id']),track_id=tid,track_uid=str(f['sequence_id'])+'/'+tid,camera_timestamp=ct,lidar_timestamp=lt,timestamp_unit='UNIX epoch microseconds',timestamp_gap=(ct-lt)/1e6,timestamp_gap_s=(ct-lt)/1e6,coordinate_frame='world horizontal XY; both source annotations virtual_lidar',matched=match,match_method='same_frame_class_unique_shared_track_id' if match else 'missing_or_duplicate_ID',same_exact_timestamp=ct==lt,occluded_state=aa.get('occluded_state') if aa else None,truncated_state=aa.get('truncated_state') if aa else None,bbox_area_px=None,distance_to_sensor_m=None,paired_annotation_not_detector_error=True,calibration_camera_nonrigid=co>.005,image_path=str(root/f['image_path']),camera_label_path=str(root/f['label_camera_std_path']),lidar_label_path=str(root/f['label_lidar_std_path']))
                flags=[]
                if not match:flags.append('UNMATCHED_OR_DUPLICATE_ID')
                if ct!=lt:flags.append('ASYNCHRONOUS_LABEL_PAIR')
                if co>.005:flags.append('PROVIDED_CAMERA_TRANSFORM_NONRIGID')
                for prefix,label in [('camera',aa),('lidar',bb)]:
                    point=loc(label) if label else np.full(3,np.nan);wp=W@point+u;cp=R@point+t;h=K@cp;hp=P@np.r_[cp,1]
                    for axis,v in zip('xyz',point):row[prefix+'_label_'+axis]=v
                    for axis,v in zip('xyz',wp):row[prefix+'_world_'+axis]=v
                    uv=h[:2]/h[2] if h[2]>0 else np.full(2,np.nan);uvp=hp[:2]/hp[2] if hp[2]>0 else np.full(2,np.nan)
                    for axis,v in zip('uv',uv):row[prefix+'_projected_'+axis]=v
                    for axis,v in zip('uv',uvp):row[prefix+'_P_projected_'+axis]=v
                if aa:
                    box=aa['2d_box'];row['bbox']=box;row['bbox_area_px']=max(0,box['xmax']-box['xmin'])*max(0,box['ymax']-box['ymin']);row['distance_to_sensor_m']=float(np.linalg.norm(loc(aa)-center));row['distance_reference']='camera center from general inverse affine, distance in source virtual_lidar metric'
                if match:
                    delta=W@(loc(aa)-loc(bb));row.update(dx=delta[0],dy=delta[1],dz=delta[2],horizontal_discrepancy_m=float(np.linalg.norm(delta[:2])),spatial_3d_discrepancy_m=float(np.linalg.norm(delta)),same_2d_box=aa['2d_box']==bb['2d_box'])
                    for prefix in ['camera','lidar']:
                        for mode,up,vp in [('K',row[prefix+'_projected_u'],row[prefix+'_projected_v']),('P',row[prefix+'_P_projected_u'],row[prefix+'_P_projected_v'])]:row[prefix+'_'+mode+'_projection_inside_bbox']=bool(box['xmin']<=up<=box['xmax'] and box['ymin']<=vp<=box['ymax'])
                row['quality_flag']=';'.join(flags);all_rows.append(row)
    df=pd.DataFrame(all_rows);df.to_parquet(PROCESSED/'spd_pedestrian_pairs.parquet',index=False,compression='zstd');paired=df[df.matched].copy();assert len(paired)
    csvw(REPORT/'spd_frame_inventory.csv',frames);csvw(REPORT/'spd_calibration_checks.csv',calibrations);js(REPORT/'spd_schema_examples.json',examples)
    tr=[]
    for uid,g in paired.groupby('track_uid'):
        g=g.sort_values('camera_timestamp');r=dict(track_uid=uid,observations=len(g),RMSE_xy_m=float(np.sqrt(np.mean(g.dx**2+g.dy**2))))
        for axis in ['dx','dy']:
            v=g[axis].to_numpy();r[axis+'_lag1_correlation']=float(np.corrcoef(v[:-1],v[1:])[0,1]) if len(v)>2 and np.std(v[:-1])>0 and np.std(v[1:])>0 else None
        tr.append(r)
    csvw(REPORT/'spd_track_summary.csv',tr);conditions=[]
    for field in ['distance_to_sensor_m','bbox_area_px','timestamp_gap_s']:paired[field+'_bin']=pd.qcut(paired[field],4,duplicates='drop').astype(str) if paired[field].nunique()>1 else 'constant_no_variation'
    for field in ['occluded_state','truncated_state','distance_to_sensor_m_bin','bbox_area_px_bin','timestamp_gap_s_bin']:
        for value,g in paired.groupby(field,dropna=False):conditions.append(dict(condition=field,value=str(value),observations=len(g),distinct_track_groups=g.track_uid.nunique(),sequences=g.sequence_id.nunique(),RMSE_xy_m=float(np.sqrt(np.mean(g.dx**2+g.dy**2))),median_discrepancy_m=float(g.horizontal_discrepancy_m.median()),p95_discrepancy_m=float(g.horizontal_discrepancy_m.quantile(.95))))
    csvw(REPORT/'spd_condition_counts.csv',conditions)
    groups=list(paired.groupby('track_uid'));sums=np.array([np.sum(g.dx**2+g.dy**2) for _,g in groups]);ns=np.array([len(g) for _,g in groups]);ids=np.random.default_rng(42).integers(0,len(groups),(2000,len(groups)));boot=np.sqrt(sums[ids].sum(1)/ns[ids].sum(1))
    metrics=dict(availability='existing_local_example_SHA256_verified',frames=len(frames),sequences=paired.sequence_id.nunique(),camera_pedestrian_observations=sum(r['camera_pedestrians'] for r in frames),lidar_pedestrian_observations=sum(r['lidar_pedestrians'] for r in frames),union_ID_rows=len(df),matched_pairs=len(paired),unmatched_or_duplicate_rows=int((~df.matched).sum()),match_rate=len(paired)/len(df),distinct_pedestrian_track_groups=paired.track_uid.nunique(),not_independent_person_or_intersection_count=True,timestamp_gap_s=stats([r['timestamp_gap_s'] for r in frames]),RMSE_world_horizontal_xy_m=float(np.sqrt(np.mean(paired.dx**2+paired.dy**2))),discrepancy_norm_m=stats(paired.horizontal_discrepancy_m),dx_m=stats(paired.dx),dy_m=stats(paired.dy),RMSE_track_cluster_bootstrap95=np.quantile(boot,[.025,.975]),camera_nonrigid_calibration_frames=sum(r['camera_transform_not_rigid'] for r in calibrations),max_camera_orthogonality_error=max(r['camera_orthogonality_error'] for r in calibrations),same_2d_box_pairs=int(paired.same_2d_box.sum()),class_counts=dict(classes),camera_detector_predictions_present=False,final_R_estimated=False)
    for mode in ['K','P']:
        for prefix in ['camera','lidar']:metrics['projection_'+mode+'_'+prefix+'_bbox_fraction']=float(paired[prefix+'_'+mode+'_projection_inside_bbox'].mean())
    js(REPORT/'spd_metrics.json',metrics)
    (REPORT/'spd_schema_report.md').write_text('# SPD observed schema\n\n실제251frame camera/virtuallidar label JSON을 읽었다. track_id는앞자리0있는문자열. timestamp는문자열 UNIX epoch **microseconds**이며 int64차분후1e6으로초변환한다.\n\n공식README는두annotation의3d_location을동일virtual-LiDAR좌표계로명시한다. 실제finite/invertible calibration, world transform의near-rigid성과roundtrip, 제공K/P에의한3D→2Dbox투영을검사했다. 이는독립적인calibration정답검증을뜻하지않는다.\n\n제공camera matrix는정규직교회전이아닌경우가있어 transpose를inverse로쓰지않았다. K/P투영적합률을별도로기록하고데이터를임의보정하지않았다. world수평discrepancy는양쪽에같은제공world변환을적용했다. 실제JSON예제는spd_schema_examples.json.\n\n같은seq/frame/Pedestrian class의양쪽unique track_id만매칭했다. 시각차는그대로보존하고동기오차가아닌paired annotation discrepancy로만계산했다. unmatched/duplicate는제거하지않는다.\n')
    text=['# R-candidate audit: paired annotation discrepancy','',table([dict(metric=k,value=json.dumps(v,default=lambda x:x.tolist(),ensure_ascii=False)) for k,v in metrics.items()],['metric','value']),'',table(conditions,['condition','value','observations','distinct_track_groups','sequences','RMSE_xy_m','median_discrepancy_m','p95_discrepancy_m']),'',
          '조건bin은샘플분위수기반탐색구간이며최종R모델이아니다. 같은track이여러bin에기여하므로track수를합산하지않는다. spd_track_summary.csv는track별lag1자기상관을포함한다. bootstrap2000회는track군집표본이며단일교차로/sequence에조건부인예비CI다.','',
          '카메라모델예측결과가없고2Dbox를공유하는두annotation간차이다. annotation/시각차/calibration특성/시간상관이섞이므로순수카메라모델오차나그하한,정확한R공분산으로해석하지않는다. 최종R추정은미실행.','',
          'GoogleDrive공식Example2개와fullmetadataZIPquota문제로기존로컬공식Example을복사했다. 로컬→서버4,011파일SHA256을검증했다. 공식archiveMD5와전송무결성을구분하며fullSPD확대는공식접근제약으로미실행.','',
          '각track의최대discrepancy사례중8track에대해원본이미지와타깃crop을나란히저장했다(figures/spd_case_*.png). K투영을보여주고P투영및왜곡해석제약을병기한다. 자동cause flag는후보일뿐실제오차원인정답이아니다.']
    (REPORT/'r_quality_report.md').write_text('\n'.join(text)+'\n');visualize(paired)
    for p,h in protected.items():assert sha(p)==h
    js(REPORT/'spd_raw_integrity.json',dict(passed=True,hashes=protected,raw_unchanged=True))
    csvw(REPORT/'spd_data_dictionary.csv',[dict(dataset='SPD',field=c,dtype=str(df[c].dtype),unit='UNIX microseconds' if c in ['camera_timestamp','lidar_timestamp'] else 'seconds' if c in ['timestamp_gap','timestamp_gap_s'] else 'm' if c in ['dx','dy','dz','horizontal_discrepancy_m','spatial_3d_discrepancy_m','distance_to_sensor_m'] or '_label_' in c or '_world_' in c else 'pixels²' if c=='bbox_area_px' else 'source ID/code/flag/pixel',missing_count=int(df[c].isna().sum())) for c in df])
    print(json.dumps(metrics,default=lambda x:x.tolist()),flush=True)
def visualize(df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image
    figs=REPORT/'figures';figs.mkdir(exist_ok=True);fig,ax=plt.subplots(1,3,figsize=(12,3.7))
    ax[0].hist(df.timestamp_gap_s*1000,bins=30);ax[0].set(xlabel='camera-lidar timestamp gap (ms)',ylabel='Paired observations');ax[1].hist(df.horizontal_discrepancy_m,bins=30);ax[1].set(xlabel='Annotation discrepancy norm (m)');ax[2].scatter(df.distance_to_sensor_m,df.horizontal_discrepancy_m,s=9,alpha=.6);ax[2].set(xlabel='Distance to inverse-calib camera center (m)',ylabel='Discrepancy (m)');fig.tight_layout();fig.savefig(figs/'spd_quality.png',dpi=140);plt.close(fig)
    cases=df.loc[df.groupby('track_uid').horizontal_discrepancy_m.idxmax()].sort_values('horizontal_discrepancy_m',ascending=False).head(8);ledger=[]
    for n,(_,r) in enumerate(cases.iterrows(),1):
        im=np.asarray(Image.open(r.image_path).convert('RGB'));box=r.bbox;x0=max(0,int(box['xmin'])-50);x1=min(im.shape[1],int(box['xmax'])+50);y0=max(0,int(box['ymin'])-50);y1=min(im.shape[0],int(box['ymax'])+50)
        fig,axes=plt.subplots(1,2,figsize=(12,4))
        for i,ax in enumerate(axes):
            ax.imshow(im);ax.add_patch(plt.Rectangle((box['xmin'],box['ymin']),box['xmax']-box['xmin'],box['ymax']-box['ymin'],fill=False,color='lime',lw=1))
            for prefix,color in [('camera','orange'),('lidar','cyan')]:ax.scatter(r[prefix+'_projected_u'],r[prefix+'_projected_v'],c=color,label=prefix+' annotation 3D projection (K)',s=35,marker='+')
            if i:ax.set_xlim(x0,x1);ax.set_ylim(y1,y0)
            ax.axis('off');ax.legend(fontsize=6)
        fig.suptitle(f'frame {r.frame_id}, track {r.track_id}; discrepancy={r.horizontal_discrepancy_m:.3f}m; dt={1000*r.timestamp_gap_s:.3f}ms\nPaired annotations, not predictions; supplied K projection, distortion ambiguity retained');fig.tight_layout();fig.savefig(figs/f'spd_case_{n}.png',dpi=140);plt.close(fig)
        ledger.append(dict(sequence_id=r.sequence_id,frame_id=r.frame_id,track_id=r.track_id,discrepancy_m=r.horizontal_discrepancy_m,occluded_state=r.occluded_state,truncated_state=r.truncated_state,timestamp_gap_s=r.timestamp_gap_s,quality_flag=r.quality_flag,cause='candidate_async/annotation/calibration/occlusion; true cause unidentified'))
    csvw(REPORT/'spd_visual_case_ledger.csv',ledger)
if __name__=='__main__':main()
