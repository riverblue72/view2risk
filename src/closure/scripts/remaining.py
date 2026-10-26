"""Close observable audit items; never refit models or overwrite prior results."""
from pathlib import Path
import os,json,hashlib,urllib.request,re,ast,time
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/data/whereami/math/full_rq_261026')
OLD=Path('/data/whereami/math/view2risk_261025')
PUBLIC=Path('/data/whereami/math/Public-V2X-Datasets')
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def csv(df,name):df.to_csv(ROOT/'reports'/name,index=False,encoding='utf-8-sig',na_rep='N/A')
def js(name,obj):(ROOT/'reports'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else x.tolist())+'\n')
def projection(cp,K,D,P,mode):
    if mode=='P_supplied':
        h=P@np.r_[cp,1.];return h[:2]/h[2] if h[2]>0 else np.full(2,np.nan)
    if cp[2]<=0:return np.full(2,np.nan)
    x,y=cp[:2]/cp[2]
    if mode=='K_with_D':
        k1,k2,p1,p2,k3=np.pad(np.asarray(D,float),(0,max(0,5-len(D))))[:5]
        r2=x*x+y*y;rad=1+k1*r2+k2*r2*r2+k3*r2**3
        x,y=x*rad+2*p1*x*y+p2*(r2+2*x*x),y*rad+p1*(r2+2*y*y)+2*p2*x*y
    h=K@np.array([x,y,1.]);return h[:2]/h[2]

def calibration():
    start=time.time();spd=PUBLIC/'raw/spd_full/V2X-Seq-SPD/infrastructure-side'
    info=json.loads((spd/'data_info.json').read_text())
    frames=[];cache={};sourcehash={}
    for f in info:
        paths=[spd/f[k] for k in ['calib_virtuallidar_to_camera_path','calib_camera_intrinsic_path','calib_virtuallidar_to_world_path']]
        payload=[p.read_bytes() for p in paths]
        for p,b in zip(paths,payload):sourcehash[str(p)]=hashlib.sha256(b).hexdigest()
        c,intr,w=[json.loads(b) for b in payload]
        R=np.array(c['rotation'],float);t=np.array(c['translation'],float).ravel()
        W=np.array(w['rotation'],float);u=np.array(w['translation'],float).ravel()
        K=np.array(intr['cam_K']).reshape(3,3);D=np.array(intr.get('cam_D',[]));P=np.array(intr['P']).reshape(3,4)
        U,s,V=np.linalg.svd(R);rigid=U@np.diag([1,1,np.linalg.det(U@V)])@V
        cache[str(f['frame_id'])]=(R,t,K,D,P,W,u,rigid)
        im=Image.open(spd/f['image_path']);size=im.size;im.close()
        frames.append(dict(frame_id=str(f['frame_id']),sequence_id=str(f['sequence_id']),site=f['intersection_loc'],
          camera_id=str(f['camera_id']),camera_orthogonality_max=float(abs(R.T@R-np.eye(3)).max()),
          camera_det=float(np.linalg.det(R)),singular_min=float(s.min()),singular_max=float(s.max()),
          nearest_SO3_delta_fro=float(np.linalg.norm(R-rigid)),world_orthogonality_max=float(abs(W.T@W-np.eye(3)).max()),
          K_fx=float(K[0,0]),P_fx=float(P[0,0]),K_fy=float(K[1,1]),P_fy=float(P[1,1]),
          nonzero_distortion=bool(np.any(D!=0)),image_width=size[0],image_height=size[1],
          intrinsic_width=intr['width'],intrinsic_height=intr['height'],image_intrinsic_size_match=tuple(size)==(intr['width'],intr['height'])))
    frames=pd.DataFrame(frames);csv(frames,'calibration_frames.csv')
    pairs=pd.read_parquet(BASE/'data/processed/spd_pedestrian_pairs.parquet')
    records=[];roundtrip=[];transpose_errors=[]
    for row in pairs.itertuples():
        R,t,K,D,P,W,u,rigid=cache[str(row.frame_id)]
        for origin in ['camera','lidar']:
            point=np.array([getattr(row,origin+'_label_'+c) for c in 'xyz'])
            cp=R@point+t;recovered=np.linalg.solve(R,cp-t)
            roundtrip.append(np.linalg.norm(recovered-point))
            transpose_errors.append(np.linalg.norm(R.T@(cp-t)-point))
            for mode in ['K_official','K_with_D','P_supplied','K_SO3_diagnostic_only']:
                coordinates=projection((rigid@point+t) if mode=='K_SO3_diagnostic_only' else cp,K,D,P,mode)
                box=row.bbox
                inside=bool(box['xmin']<=coordinates[0]<=box['xmax'] and box['ymin']<=coordinates[1]<=box['ymax'])
                old_u=getattr(row,origin+'_projected_u');old_v=getattr(row,origin+'_projected_v')
                if mode=='K_official':np.testing.assert_allclose(coordinates,[old_u,old_v],rtol=1e-12,atol=1e-9,equal_nan=True)
                records.append(dict(frame_id=row.frame_id,sequence_id=row.sequence_id,track_uid=row.track_uid,annotation=origin,
                    projection=mode,u=coordinates[0],v=coordinates[1],inside_shared_bbox=inside))
    projected=pd.DataFrame(records);projected.to_parquet(ROOT/'data/projection_diagnostics.parquet',index=False,compression='zstd')
    summary=projected.groupby(['annotation','projection']).agg(pairs=('inside_shared_bbox','size'),inside_bbox=('inside_shared_bbox','sum'),track_groups=('track_uid','nunique')).reset_index()
    summary['inside_bbox_pct']=100*summary.inside_bbox/summary.pairs
    summary['not_independent_calibration_accuracy']=True
    csv(summary,'projection.csv')
    # Execute only official helper AST in isolation, without its unrelated imports.
    helper=ROOT/'docs/official_vis_utils.py';tree=ast.parse(helper.read_text())
    fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='get_cam_calib_intrinsic')
    env={'np':np,'read_json':lambda p:json.loads(Path(p).read_text())}
    # Actual helper may call read_json or json.load; supply both safely.
    env.update(json=json)
    exec(compile(ast.Module(body=[fun],type_ignores=[]),str(helper),'exec'),env)
    helper_checks=0
    for f in info[::max(1,len(info)//20)]:
        actual=env['get_cam_calib_intrinsic'](str(spd/f['calib_camera_intrinsic_path']))
        expected=np.zeros((3,4));expected[:3,:3]=cache[str(f['frame_id'])][2]
        np.testing.assert_allclose(actual,expected,rtol=0,atol=0);helper_checks+=1
    # Diverse, deterministic original-image diagnostic examples.
    selected=pd.concat([pairs.nlargest(4,'horizontal_discrepancy_m'),pairs.sample(4,random_state=42)]).drop_duplicates(['frame_id','track_uid'])
    ledger=[]
    for i,row in enumerate(selected.itertuples(),1):
        im=Image.open(row.image_path)
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for ax in axes:
            ax.imshow(im);b=row.bbox;ax.add_patch(Rectangle((b['xmin'],b['ymin']),b['xmax']-b['xmin'],b['ymax']-b['ymin'],fill=False,edgecolor='lime',lw=2))
            for origin,marker in [('camera','o'),('lidar','x')]:
                subset=projected[(projected.frame_id==row.frame_id)&(projected.track_uid==row.track_uid)&(projected.annotation==origin)]
                for mode,color in [('K_official','deepskyblue'),('K_with_D','magenta'),('P_supplied','yellow')]:
                    r=subset[subset.projection==mode].iloc[0];ax.scatter([r.u],[r.v],c=color,s=30,marker=marker,label=f'{origin}/{mode}')
            ax.axis('off')
        b=row.bbox;pad=max(50,(b['ymax']-b['ymin'])*2)
        axes[1].set_xlim(max(0,b['xmin']-pad),min(im.width,b['xmax']+pad));axes[1].set_ylim(min(im.height,b['ymax']+pad),max(0,b['ymin']-pad))
        axes[0].set_title('Original image and shared annotation box');axes[1].set_title('Projection diagnostics, no calibration alteration')
        axes[1].legend(fontsize=5)
        fig.suptitle(f'frame {row.frame_id} / {row.track_uid}; paired difference {row.horizontal_discrepancy_m:.3f}m')
        fig.tight_layout();fig.savefig(ROOT/f'figures/calib_{i:02}.png',dpi=140);plt.close(fig);im.close()
        ledger.append(dict(case=i,frame_id=row.frame_id,track_uid=row.track_uid,paired_difference_m=row.horizontal_discrepancy_m,figure=f'calib_{i:02}.png',selection='largest4_plus_seed42_random4'))
    csv(pd.DataFrame(ledger),'calibration_cases.csv')
    proof=dict(passed=True,frames=len(frames),pairs=len(pairs),
      official_K_helper_exact_checks=helper_checks,official_uses_cam_K=True,
      general_inverse_roundtrip_max_m=float(max(roundtrip)),transpose_inverse_error_p95_m=float(np.quantile(transpose_errors,.95)),
      nonrigid_frames=int((frames.camera_orthogonality_max>.005).sum()),
      max_orthogonality_error=float(frames.camera_orthogonality_max.max()),
      image_intrinsic_size_mismatch=int((~frames.image_intrinsic_size_match).sum()),
      K_vs_P_convention_resolved_to_official_K=True,
      camera_matrix_nonrigidity_cause_resolved=False,no_raw_matrix_correction=True,
      bbox_test_is_annotation_consistency_not_independent_accuracy=True,
      elapsed_s=time.time()-start)
    js('calibration_validation.json',proof);js('calibration_sources.json',sourcehash)
    print('CALIBRATION',json.dumps(proof),flush=True)

def condition_audit():
    p=pd.read_parquet(BASE/'data/processed/spd_pedestrian_pairs.parquet')
    frames=pd.read_csv(ROOT/'reports/calibration_frames.csv',dtype={'frame_id':str,'sequence_id':str})
    p=p.merge(frames[['frame_id','site']],on='frame_id',validate='many_to_one')
    rows=[]
    for field in ['distance_to_sensor_m','bbox_area_px','timestamp_gap_s','occluded_state','truncated_state']:
        if field in ['occluded_state','truncated_state']:values=p[field].astype(str)
        else:values=pd.qcut(p[field],4,duplicates='drop').astype(str)
        for value,g in p.groupby(values,dropna=False):
            d=g[['dx','dy']].to_numpy();cov=np.cov(d,rowvar=False,bias=True)
            per=g.assign(error2=g.dx**2+g.dy**2).groupby('track_uid').error2.mean().pow(.5)
            rows.append(dict(field=field,stratum=str(value),observations=len(g),track_groups=g.track_uid.nunique(),
                sequences=g.sequence_id.nunique(),sites=g.site.nunique(),RMSE_m=float(np.sqrt((d*d).sum(axis=1).mean())),
                median_m=float(g.horizontal_discrepancy_m.median()),p95_m=float(g.horizontal_discrepancy_m.quantile(.95)),
                track_macro_RMSE_m=float(per.mean()),bias_x_m=float(d[:,0].mean()),bias_y_m=float(d[:,1].mean()),
                cov_xx_m2=float(cov[0,0]),cov_xy_m2=float(cov[0,1]),cov_yy_m2=float(cov[1,1]),
                descriptive_only=True,track_groups_not_independent_persons=True))
    r=pd.DataFrame(rows);csv(r,'r_conditions.csv')
    fig,axes=plt.subplots(1,3,figsize=(15,4))
    for ax,field in zip(axes,['distance_to_sensor_m','occluded_state','bbox_area_px']):
        sub=r[r.field==field];ax.bar(np.arange(len(sub)),sub.RMSE_m)
        ax.set_xticks(np.arange(len(sub)),sub.stratum,rotation=30,ha='right',fontsize=7)
        ax.set_title(field);ax.set_ylabel('Paired annotation RMSE (m)')
        for i,(_,row) in enumerate(sub.iterrows()):ax.text(i,row.RMSE_m,f'n={row.observations}\nt={row.track_groups}',ha='center',va='bottom',fontsize=6)
    fig.suptitle('Descriptive strata; repeated tracks/sites, no causal or conditional-model claim')
    fig.tight_layout();fig.savefig(ROOT/'figures/r_conditions.png',dpi=160);plt.close(fig)
    # Explicit all-observation flags preserve abnormal data for handoff.
    cols=['sequence_id','track_uid','ts_us','status','source_type','dt','x','y','z','speed_reported_mps','speed_from_position_mps','quality_flags','recording_date']
    q=pd.read_parquet(BASE/'data/processed/imptc_pedestrian_tracks.parquet',columns=cols)
    q['flag_position_speed_gt5']=q.speed_from_position_mps>5
    q['flag_position_speed_gt20']=q.speed_from_position_mps>20
    q['flag_reported_speed_disagreement_gt2']=abs(q.speed_from_position_mps-q.speed_reported_mps)>2
    q['flag_nonpositive_or_gap_dt']=q.dt.le(0)|q.dt.gt(.060)
    q.to_parquet(ROOT/'data/imptc_quality_flags.parquet',index=False,compression='zstd')
    flag_counts=[]
    for c in q.columns:
        if not c.startswith('flag_'):continue
        g=q[q[c]];flag_counts.append(dict(flag=c,observations=len(g),track_groups=g.track_uid.nunique(),sequences=g.sequence_id.nunique(),dates=g.recording_date.nunique(),removed_from_source=False,not_verified_ID_switch=True))
    csv(pd.DataFrame(flag_counts),'quality_flags.csv')
    fig,axes=plt.subplots(1,3,figsize=(15,4))
    tracks=pd.read_csv(BASE/'reports/imptc_track_summary.csv')
    duration=q.groupby('track_uid').ts_us.agg(lambda s:(s.max()-s.min())/1e6)
    axes[0].hist(duration,bins=35);axes[0].set(xlabel='Track duration (s)',ylabel='Track groups')
    speed=q.groupby('track_uid').speed_reported_mps.agg(['mean','std'])
    axes[1].hist(speed['mean'],bins=35);axes[1].set(xlabel='Mean speed per track (m/s)',ylabel='Track groups')
    axes[2].hist(speed['std'],bins=35);axes[2].set(xlabel='Within-track speed std (m/s)',ylabel='Track groups')
    fig.suptitle('B vs within-track variability: all1920 tracks, not identified unique people')
    fig.tight_layout();fig.savefig(ROOT/'figures/q_quality.png',dpi=160);plt.close(fig)
    js('quality_validation.json',dict(passed=True,observations_retained=len(q),tracks=q.track_uid.nunique(),r_strata=len(r),no_rows_deleted=True))
    print('CONDITIONS_AND_FLAGS',len(r),len(q),flush=True)

def tfd_legacy():
    d=pd.read_parquet(BASE/'data/tfd_example_pedestrians.parquet')
    # Same supplied sensor view only. Duplicates between clipped scenes receive
    # one canonical observation key for diagnostic weighting, not new identities.
    keys=['city','intersect_id','id','ts_us']
    d=d.sort_values(['source_file','ts_us']).drop_duplicates(keys).sort_values(keys).copy()
    rows=[];residuals=[]
    for key,g in d.groupby(['city','intersect_id','id'],sort=False):
        g=g.sort_values('ts_us').reset_index(drop=True)
        dt=np.diff(g.ts_us.to_numpy())/1e6;xy=g[['x','y']].to_numpy();vel=g[['v_x','v_y']].to_numpy()
        valid=(dt>0)&(dt<=.151)
        posvel=np.diff(xy,axis=0)/dt[:,None]
        dv=np.diff(vel,axis=0)
        for i in np.flatnonzero(valid):
            residuals.append(dict(city=key[0],intersect_id=key[1],id=key[2],ts_us=int(g.ts_us.iloc[i+1]),dt_s=dt[i],
                position_speed_native_per_s=float(np.linalg.norm(posvel[i])),reported_vector_norm=float(np.linalg.norm(vel[i+1])),
                vector_rmse_assuming_v_native_per_s=float(np.linalg.norm(posvel[i]-vel[i+1])),
                vector_rmse_assuming_v_kmh=float(np.linalg.norm(posvel[i]-vel[i+1]/3.6)),
                q_velocity_increment_proxy_native2_per_s3=float(np.dot(dv[i],dv[i])/(2*dt[i])),
                source_scene_overlap_deduplicated=True))
    res=pd.DataFrame(residuals)
    res.to_parquet(ROOT/'data/tfd_velocity_diagnostics.parquet',index=False,compression='zstd')
    for key,g in res.groupby('intersect_id'):
        rows.append(dict(intersect_id=key,increments=len(g),source_ID_groups=g.id.nunique(),dt_median_s=g.dt_s.median(),
            mean_q_velocity_increment_proxy_native2_per_s3=g.q_velocity_increment_proxy_native2_per_s3.mean(),
            median_q_velocity_increment_proxy_native2_per_s3=g.q_velocity_increment_proxy_native2_per_s3.median(),
            vector_RMSE_assuming_native_per_s=float(np.sqrt((g.vector_rmse_assuming_v_native_per_s**2).mean())),
            vector_RMSE_assuming_kmh=float(np.sqrt((g.vector_rmse_assuming_v_kmh**2).mean())),
            original_q005_reproduction=False,physical_Q_identified=False))
    csv(pd.DataFrame(rows),'tfd_q_diagnostic.csv')
    claims=pd.DataFrame([
      dict(claim='SPD_RMSE_approx_0.19m',status='reproduced_as_paired_annotation_difference',value=.1851830173,unit='m',reason='253 original Example pairs reproduced exactly in full-data overlap; not pure camera detector error'),
      dict(claim='TFD_q_approx_0.05',status='original_formula_and_selection_unavailable',value=np.nan,unit='unknown_original',reason='HTML contains a numeric claim but no estimator, delta-t convention or executable q source; diagnostic native-unit velocity proxy saved separately, not asserted identical'),
      dict(claim='TFD_68_segments_4_complete_crossings',status='original_selection_unavailable',value=np.nan,unit='segment_or_crossing',reason='Local PoC uses another outside-inside-outside definition and reported14 candidates; neither establishes original68/4 selection nor opposite-end completion'),
      dict(claim='G95_contributions',status='outside_current_MD_scope_preliminary_only',value=np.nan,unit='seconds',reason='No reconstruction of unsupported original Shapley/Monte Carlo claims'),
    ]);csv(claims,'preliminary_claims.csv')
    js('tfd_validation.json',dict(passed=True,canonical_unique_observations=len(d),finite_contiguous_increments=len(res),
        source_rows_before_dedup=19978,physical_units_not_independently_confirmed=True,original_q_formula_available=False,
        process_noise_not_separated_from_measurement_noise=True,no_cross_dataset_pooling=True))
    print('TFD_DIAGNOSTIC',len(d),len(res),flush=True)

def main():
    for folder in ['data','reports','figures','docs','tmp']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
    # Frozen originals, including old sample results, must remain unchanged.
    before=json.loads((BASE/'manifest.json').read_text())
    assert all(sha(BASE/k)==h for k,h in before.items())
    calibration();condition_audit();tfd_legacy()
    assert all(sha(BASE/k)==h for k,h in before.items())
    js('remaining_validation.json',dict(passed=True,previous_manifest_files_unchanged=len(before),
       no_model_refit=True,no_prediction_change=True,no_source_data_edit=True))

if __name__=='__main__':main()
