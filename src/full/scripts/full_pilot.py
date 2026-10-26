"""Full-data extension: site-held-out R proxy, date-grouped causal Q forecasts."""
from pathlib import Path
import os,json,hashlib,time,sys,platform
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl');os.environ['NUMBA_CACHE_DIR']=str(ROOT/'tmp/numba')
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import minimize,minimize_scalar
from scipy.stats import chi2,spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from numba import njit
from reused_math import clean,kf,slope,normstats,gauss_stats,metrics,metric_table,reference_filter,LEVELS

OLD=Path('/data/whereami/math/view2risk_261025')
PUBLIC=Path('/data/whereami/math/Public-V2X-Datasets')
MODELS=['Deterministic_CV','Fixed_noise_KF','Data_fitted_Q_KF','Joint_innovation_ML_KF']
RNG=np.random.default_rng(42)
START=time.time()

def js(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def md(name,parts):(ROOT/'reports'/name).write_text('\n\n'.join(parts)+'\n')
def tab(df):
    f=df.copy()
    for c in f:
        if pd.api.types.is_float_dtype(f[c]):f[c]=f[c].map(lambda v:f'{v:.6g}' if np.isfinite(v) else 'N/A')
    return '\n'.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in [list(f.columns),['---']*len(f.columns),*list(f.fillna('N/A').itertuples(index=False,name=None))])
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def figure(name):plt.tight_layout();plt.savefig(ROOT/'figures'/name,dpi=145);plt.close()
def status(stage,**extra):js('status.json',dict(state=stage,elapsed_s=time.time()-START,**extra));print(stage,json.dumps(clean(extra)),flush=True)

def grouped_bootstrap(frame,group,metric_cols,repetitions=2000):
    stats=frame.groupby(group).agg(n=('error_m','size'),squared=('error_m',lambda a:np.sum(a*a)),absolute=('error_m','sum'),hit90=('covered90','sum'),hit95=('covered95','sum'),area95=('area95_m2','sum'))
    a=stats.to_numpy();idx=np.random.default_rng(42).integers(0,len(a),(repetitions,len(a)));s=a[idx].sum(axis=1)
    values=dict(RMSE_m=np.sqrt(s[:,1]/s[:,0]),MAE_m=s[:,2]/s[:,0],coverage90=s[:,3]/s[:,0],coverage95=s[:,4]/s[:,0],mean_area95_m2=s[:,5]/s[:,0])
    return {key:np.quantile(values[key],[.025,.975]).tolist() for key in metric_cols},len(a)

def r_analysis():
    raw=pd.read_parquet(ROOT/'data/processed/spd_pedestrian_pairs.parquet')
    info=json.loads((PUBLIC/'raw/spd_full/V2X-Seq-SPD/infrastructure-side/data_info.json').read_text())
    by={str(r['frame_id']):r for r in info};assert len(by)==len(info)
    raw['intersection_loc']=[by[str(f)]['intersection_loc'] for f in raw.frame_id]
    raw['model_eligible']=raw.matched & np.isfinite(raw[['dx','dy']]).all(axis=1)
    raw.to_parquet(ROOT/'data/spd_pair_residuals.parquet',index=False,compression='zstd')
    r=raw[raw.model_eligible].copy();e=r[['dx','dy']].to_numpy();sites=sorted(r.intersection_loc.unique());assert len(sites)>=2
    summary=normstats(e);mu=e.mean(axis=0);cov=np.cov(e.T,ddof=0)
    # Parameter uncertainty resamples sites, preserving every row and track within each site.
    clusters=[g[['dx','dy']].to_numpy() for _,g in r.groupby('intersection_loc')]
    sufficient=np.array([[len(a),*a.sum(axis=0),*(a.T@a).ravel()] for a in clusters])
    draws=RNG.integers(0,len(clusters),(2000,len(clusters)));s=sufficient[draws].sum(axis=1)
    means=s[:,1:3]/s[:,0,None];cs=s[:,3:].reshape(-1,2,2)/s[:,0,None,None]-means[:,:,None]*means[:,None,:]
    boot_rmse=np.sqrt((s[:,3]+s[:,6])/s[:,0])
    intervals=dict(bias_m=np.quantile(means,[.025,.975],axis=0),R_pair_proxy_m2=np.quantile(cs,[.025,.975],axis=0),RMSE_m=np.quantile(boot_rmse,[.025,.975]))
    output=[];folds=[];pred=[]
    for site in sites:
        train=r[r.intersection_loc!=site];test=r[r.intersection_loc==site]
        et=train[['dx','dy']].to_numpy();ev=test[['dx','dy']].to_numpy();bias=et.mean(0);C=np.cov(et.T,ddof=0)
        # Empirical radial calibration, using development data only; no density NLL claim.
        central=et-bias;radial=np.einsum('ni,ij,nj->n',central,np.linalg.inv(C+np.eye(2)*1e-10),central)
        cuts={level:float(np.quantile(radial,level/100)) for level in LEVELS}
        folds.append(dict(test_intersections=[site],development_intersections=[x for x in sites if x!=site],
            test_sequences=sorted(test.sequence_id.unique()),test_tracks=test.track_uid.nunique(),test_pairs=len(test)))
        for name,matrix,center,thresholds in [('Gaussian_zero_bias',et.T@et/len(et),np.zeros(2),LEVELS),
            ('Gaussian_with_bias',C,bias,LEVELS),('Empirical_radial_proxy',C,bias,cuts)]:
            values=gauss_stats(ev,center,matrix,thresholds)
            if name.startswith('Empirical'):values['NLL']=np.nan
            output.append(dict(model=name,test_intersection=site,test_sequences=test.sequence_id.nunique(),test_tracks=test.track_uid.nunique(),test_pairs=len(test),**values))
            delta=ev-center;d2=np.einsum('ni,ij,nj->n',delta,np.linalg.inv(matrix+np.eye(2)*1e-10),delta)
            pred.append(pd.DataFrame(dict(model=name,intersection_loc=site,sequence_id=test.sequence_id.to_numpy(),track_uid=test.track_uid.to_numpy(),frame_id=test.frame_id.to_numpy(),
                covered90=d2<=thresholds[90],covered95=d2<=thresholds[95],area90_m2=values['area90_m2'],area95_m2=values['area95_m2'],mahalanobis2=d2)))
    table=pd.DataFrame(output);table.to_csv(ROOT/'reports/r_site_holdout_metrics.csv',index=False)
    rp=pd.concat(pred,ignore_index=True);rp.to_parquet(ROOT/'data/r_holdout_predictions.parquet',index=False,compression='zstd')
    agg=table.groupby('model')[['coverage90','coverage95','area95_m2','NLL']].mean().reset_index();agg.to_csv(ROOT/'reports/r_site_macro.csv',index=False)
    micro=rp.groupby('model')[['covered90','covered95','area95_m2']].mean().reset_index();micro.to_csv(ROOT/'reports/r_pair_micro.csv',index=False)
    # Compare overlapping Example exports, without adding Example rows to the full cohort.
    sample=pd.read_parquet(OLD/'data/processed/spd_pedestrian_pairs.parquet')
    common=sample.merge(r,on=['sequence_id','frame_id','track_id'],suffixes=('_sample','_full'))
    if len(common):
        common['residual_delta_m']=np.hypot(common.dx_sample-common.dx_full,common.dy_sample-common.dy_full)
        common[['sequence_id','frame_id','track_id','residual_delta_m']].to_csv(ROOT/'reports/r_sample_full_overlap.csv',index=False)
    timing=[]
    for field in ['timestamp_gap_s','distance_to_sensor_m']:
        timing.append(dict(field=field,spearman_rho=spearmanr(r[field],np.hypot(r.dx,r.dy)).statistic,dependent_rows_no_iid_pvalue=True))
    pd.DataFrame(timing).to_csv(ROOT/'reports/r_covariate_diagnostics.csv',index=False)
    autocorr=[]
    for uid,g in r.groupby('track_uid'):
        g=g.sort_values('camera_timestamp');dt=np.diff(g.camera_timestamp.to_numpy(np.int64))/1e6;keep=(dt>0)&(dt<=.15)
        record=dict(track_uid=uid,intersection_loc=g.intersection_loc.iloc[0],pairs=len(g),valid_lag_pairs=int(keep.sum()))
        for name in ['dx','dy']:
            a=g[name].to_numpy()[:-1][keep];b=g[name].to_numpy()[1:][keep]
            record[name+'_lag1']=np.corrcoef(a,b)[0,1] if len(a)>2 and a.std()>0 and b.std()>0 else np.nan
        autocorr.append(record)
    pd.DataFrame(autocorr).to_csv(ROOT/'reports/r_fixed_time_autocorrelation.csv',index=False)
    parameters=dict(name='R_pair_proxy',frame='supplied world horizontal XY',units='m2',mean_bias_m=mu,covariance_m2=cov,ddof=0,summary=summary,
        site_cluster_bootstrap95=intervals,sites=sites,eligible_pairs=len(r),raw_ID_rows=len(raw),tracks=r.track_uid.nunique(),sequences=r.sequence_id.nunique(),
        excluded_unmatched_or_nonfinite=int((~raw.model_eligible).sum()),pure_camera_R=False,calibration_resolved=False,
        sample_overlap_pairs=len(common),sample_overlap_max_residual_delta_m=float(common.residual_delta_m.max()) if len(common) else None,folds=folds)
    js('models/r_pair_proxy_params.json',parameters)
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for site,g in r.groupby('intersection_loc'):
        axes[0].hist(np.hypot(g.dx,g.dy),bins=50,density=True,histtype='step',label=site)
    axes[0].set(xlabel='Paired annotation norm (m)',ylabel='Density');axes[0].legend(fontsize=6)
    axes[1].scatter(r.distance_to_sensor_m,np.hypot(r.dx,r.dy),s=2,alpha=.25);axes[1].set(xlabel='Camera distance (m)',ylabel='Annotation difference (m)')
    for name,g in table.groupby('model'):axes[2].plot(range(len(g)),g.coverage95,'o-',label=name)
    axes[2].axhline(.95,ls='--',color='k');axes[2].set(xticks=range(len(sites)),xticklabels=sites,ylabel='95% region coverage',ylim=(0,1.03));axes[2].tick_params(axis='x',rotation=45);axes[2].legend(fontsize=6)
    figure('r_full_diagnostics.png')
    md('01_r_full.md',['# R_pair_proxy full-data extension',
        f'{len(r):,} eligible paired observations / {r.track_uid.nunique()} sequence-track groups / {r.sequence_id.nunique()} sequences / {len(sites)} intersections. All raw ID rows, including unmatched/duplicate cases, remain in data/spd_pair_residuals.parquet.',
        'Full-sample descriptive bias/covariance and site-cluster bootstrap are in models/r_pair_proxy_params.json. Only development intersections supply holdout means/covariances/empirical radial thresholds. No camera detector predictions are present.',
        tab(table),'Site macro:',tab(agg),'Pair micro:',tab(micro),
        'Empirical_radial_proxy uses empirical development Mahalanobis quantiles, preserving the Gaussian covariance shape. It is a diagnostic empirical region, not a continuous density model; NLL is N/A. The 2,000-resample parameter bootstrap keeps entire intersections together and is weak with only six sites.',
        'No conditional distance/occlusion model was selected from Test. Existing spd_condition_counts.csv and the new figure are descriptive support checks only. Shared boxes, asynchronous timestamps, annotation dependence and supplied camera-matrix/projection issues remain; this does not identify R_camera.',
        f'Overlap with the previous Example export: {len(common)} pairs; no Example rows were pooled. Any numerical export differences are recorded rather than overwriting old outputs.',
        '![R diagnostics](../figures/r_full_diagnostics.png)'])
    return parameters,folds

def build_segments(q):
    segments=[];inventory=[];origins=[];ledger=[]
    for uid,g in q.groupby('track_uid',sort=True):
        g=g.sort_values('source_index').reset_index(drop=True)
        ts=g.ts_us.to_numpy(np.int64);valid=(g.status.to_numpy()==2)&np.isfinite(g[['x','y','z']].to_numpy()).all(1)
        starts=[];current=[]
        for i in range(len(g)):
            adjacent=bool(current) and 0<int(ts[i]-ts[current[-1]])<=60000
            if not valid[i] or (current and not adjacent):
                if current:starts.append(current);current=[]
            if valid[i]:current.append(i)
        if current:starts.append(current)
        before=len(origins)
        for n,indices in enumerate(starts):
            a=g.iloc[indices];raw=a.ts_us.to_numpy(np.int64);t=(raw-raw[0])/1e6;xy=a[['x','y']].to_numpy();sid=uid+f'/seg{n:02d}'
            source=a.source_type.fillna(-1).to_numpy();nearby=a.nearby_ped_count.fillna(-1).to_numpy()
            sequence=str(a.sequence_id.iloc[0]);date=sequence.split('_')[1]
            inventory.append(dict(sequence_id=sequence,recording_date=date,track_uid=uid,segment_id=sid,observations=len(a),duration_s=t[-1],ge1=t[-1]>=1,ge2=t[-1]>=2,ge5=t[-1]>=5,ge10=t[-1]>=10))
            ai=[];aj=[];ah=[];nominal=[];row_ids=[];velocities=[];last=-np.inf
            for i in range(len(a)):
                if t[i]<1-1e-9 or t[i]-last<.2-1e-6:continue
                targets=[]
                for h in [1.,3.]:
                    p=np.searchsorted(t,t[i]+h);c=[j for j in [p-1,p] if i<j<len(a)]
                    j=min(c,key=lambda j:abs(t[j]-t[i]-h)) if c else -1
                    if j<0 or abs(t[j]-t[i]-h)>.0201:break
                    targets.append(j)
                if len(targets)!=2:continue
                v=np.array([slope(t,xy,i,w) for w in [.12,.4,1.]])
                if not np.isfinite(v).all():continue
                past=np.searchsorted(t,t[i]-.4,side='right')-1;pv=slope(t,xy,past,.4)
                speed=np.linalg.norm(v[1]);ps=np.linalg.norm(pv);accel=(speed-ps)/(t[i]-t[past])
                turn=abs(np.degrees(np.arctan2(pv[0]*v[1,1]-pv[1]*v[1,0],pv@v[1]))/(t[i]-t[past])) if min(speed,ps)>.2 else np.nan
                lo=np.searchsorted(t,t[i]-1.)
                for h,j in zip([1.,3.],targets):
                    rid=len(origins);dt=t[j]-t[i];ai.append(i);aj.append(j);ah.append(dt);nominal.append(h);row_ids.append(rid);velocities.append(v)
                    origins.append(dict(origin_row=rid,sequence_id=sequence,recording_date=date,track_uid=uid,segment_id=sid,anchor_id=sid+f'/{raw[i]}',
                        anchor_ts_us=int(raw[i]),future_ts_us=int(raw[j]),horizon_s=h,actual_horizon_s=dt,
                        anchor_x_m=xy[i,0],anchor_y_m=xy[i,1],GT_recorded_x_m=xy[j,0],GT_recorded_y_m=xy[j,1],
                        source_type=int(source[i]),source_switch_past1s=len(np.unique(source[lo:i+1]))>1,
                        speed_mps=speed,accel_proxy_mps2=accel,turn_rate_proxy_deg_s=turn,
                        stop_candidate=speed<=.3,accel_candidate=accel>.5,decel_candidate=accel<-.5,
                        turn_candidate=bool(np.isfinite(turn) and turn>45),nearby_ped_count=int(nearby[i])))
                last=t[i]
            segments.append(dict(sequence_id=sequence,recording_date=date,track_uid=uid,segment_id=sid,t=t,xy=xy,raw_ts=raw,
                i=np.array(ai,dtype=np.int64),j=np.array(aj,dtype=np.int64),h=np.array(ah),horizon=np.array(nominal),
                row_ids=np.array(row_ids,dtype=np.int64),velocities=np.array(velocities)))
        ledger.append(dict(track_uid=uid,sequence_id=g.sequence_id.iloc[0],raw_observations=len(g),valid_observations=int(valid.sum()),valid_segments=len(starts),eligible_forecasts=len(origins)-before))
    inv=pd.DataFrame(inventory);orig=pd.DataFrame(origins)
    assert sum(len(s['t']) for s in segments)==int(((q.status==2)&np.isfinite(q[['x','y','z']]).all(axis=1)).sum())
    inv.to_csv(ROOT/'reports/q_segment_inventory.csv',index=False);pd.DataFrame(ledger).to_csv(ROOT/'reports/q_validity_funnel.csv',index=False)
    orig.to_parquet(ROOT/'data/q_origins.parquet',index=False,compression='zstd')
    return segments,orig,inv

def sequence_score(segments,r,q,innovation=False):
    grouped={}
    for s in segments:
        if len(s['t'])<2:continue
        m,c,nll=kf(s['t'],s['xy'],r,q)
        if innovation:
            valid=s['t']>=1.
            if valid.any():
                key=(s['recording_date'],0);old=grouped.get(key,[0.,0]);old[0]+=float(nll[valid].sum());old[1]+=int(valid.sum());grouped[key]=old
        elif len(s['i']):
            i,j,h=s['i'],s['j'],s['h'];e=s['xy'][j]-m[i,:2]-h[:,None]*m[i,2:]
            v=c[i,0]+2*h*c[i,1]+h*h*c[i,2]+q*h**3/3+r
            values=np.log(2*np.pi*v)+.5*np.sum(e*e,axis=1)/v
            for hh in [1.,3.]:
                mask=s['horizon']==hh;key=(s['recording_date'],hh);old=grouped.get(key,[0.,0]);old[0]+=float(values[mask].sum());old[1]+=int(mask.sum());grouped[key]=old
    return float(np.mean([total/n for total,n in grouped.values() if n]))

def fit_q(segments,orig):
    dates=sorted(set(s['recording_date'] for s in segments));order=np.random.default_rng(42).permutation(dates)
    date_fold={str(d):int(i%5) for i,d in enumerate(order)}
    assert len(dates)>=5
    js('data/q_fold_plan.json',dict(seed=42,date_to_fold=date_fold,created_before_parameter_fitting=True,
        folds=[dict(fold=f,test_recording_dates=sorted(d for d in dates if date_fold[d]==f),development_recording_dates=sorted(d for d in dates if date_fold[d]!=f)) for f in range(5)]))
    splits=[];fit={};trials=[]
    for fold in range(5):
        test_dates=sorted(d for d in dates if date_fold[d]==fold);development=sorted(set(dates)-set(test_dates))
        train=[s for s in segments if s['recording_date'] in development]
        test_seq=sorted(orig[orig.recording_date.isin(test_dates)].sequence_id.unique())
        splits.append(dict(fold=fold,test_recording_dates=test_dates,development_recording_dates=development,test_sequences=test_seq,
            note='All sequences/tracks from a date stay together; all parameters use development dates only.'))
        grid=[]
        for sd in [.01,.05,.2]:
            for q in [.01,.1,1.]:
                score=sequence_score(train,sd**2,q);grid.append((score,sd**2,q));trials.append(dict(fold=fold,stage='fixed_grid',r_m2=sd**2,q_m2_s3=q,development_NLL=score))
        best=min(grid);r=best[1];qs=np.logspace(-6,2,17);scores=[sequence_score(train,r,q) for q in qs];idx=int(np.argmin(scores))
        opt=minimize_scalar(lambda lq:sequence_score(train,r,np.exp(lq)),bounds=(np.log(qs[max(0,idx-1)]),np.log(qs[min(16,idx+1)])),method='bounded',options={'xatol':.002,'maxiter':35})
        learned=min((float(opt.fun),float(np.exp(opt.x))),(scores[idx],float(qs[idx])))
        for q,score in zip(qs,scores):trials.append(dict(fold=fold,stage='fitted_q_grid',r_m2=r,q_m2_s3=q,development_NLL=score))
        joint=[]
        for r0,q0 in [(r,best[2]),(.001,.001),(.01,.1)]:
            result=minimize(lambda x:sequence_score(train,np.exp(x[0]),np.exp(x[1]),True),np.log([r0,q0]),method='L-BFGS-B',
                bounds=[(np.log(1e-8),np.log(4)),(np.log(1e-6),np.log(100))],options={'maxiter':60,'ftol':1e-9})
            joint.append(dict(objective=float(result.fun),r_m2=float(np.exp(result.x[0])),q_m2_s3=float(np.exp(result.x[1])),success=bool(result.success),message=str(result.message)))
        jb=min(joint,key=lambda x:x['objective'])
        fit[fold]=dict(Fixed_noise_KF=dict(r_m2=r,q_m2_s3=best[2],development_NLL=best[0]),
            Data_fitted_Q_KF=dict(r_m2=r,q_m2_s3=learned[1],development_NLL=learned[0],optimizer_success=bool(opt.success)),
            Joint_innovation_ML_KF=dict(**jb,starts=joint),development_recording_dates=development,test_recording_dates=test_dates)
        js(f'models/q_fold_{fold}.json',fit[fold]);pd.DataFrame(trials).to_csv(ROOT/'reports/q_tuning_records.csv',index=False)
        status('fitting_Q',completed_folds=fold+1,total_folds=5,fold_parameters=fit[fold])
    js('models/q_effective_params.json',dict(name='Q_effective',state_order=['x','y','vx','vy'],R_unit='m2',q_unit='m2/s3',
        Q_dt='q * [[dt^3/3 I,dt^2/2 I],[dt^2/2 I,dt I]]',initial_P='diag(r,r,4,4)',
        future_position_cov='H F P_filtered F.T H.T + q*h^3/3 I + r I',pure_Q_true=False,SPD_R_used=False,folds=fit))
    return fit,date_fold,splits

def predict_q(segments,orig,fit,date_fold):
    outputs=[];sensitivity=[]
    for s in segments:
        if not len(s['i']):continue
        i,j,h=s['i'],s['j'],s['h'];target=s['xy'][j];fold=date_fold[s['recording_date']]
        for index,window in enumerate([.12,.4,1.]):
            error=target-s['xy'][i]-h[:,None]*s['velocities'][:,index,:]
            sensitivity.append(pd.DataFrame(dict(origin_row=s['row_ids'],causal_window_s=window,residual_x_m=error[:,0],residual_y_m=error[:,1],error_m=np.linalg.norm(error,axis=1))))
        for name in MODELS:
            if name=='Deterministic_CV':pred=s['xy'][i]+h[:,None]*s['velocities'][:,1,:];v=np.full(len(i),np.nan)
            else:
                p=fit[fold][name];m,c,_=kf(s['t'],s['xy'],p['r_m2'],p['q_m2_s3'])
                pred=m[i,:2]+h[:,None]*m[i,2:];v=c[i,0]+2*h*c[i,1]+h*h*c[i,2]+p['q_m2_s3']*h**3/3+p['r_m2']
            e=target-pred;e2=np.sum(e*e,axis=1)
            with np.errstate(invalid='ignore',divide='ignore'):nll=np.log(2*np.pi*v)+e2/(2*v);d2=e2/v
            row=dict(origin_row=s['row_ids'],outer_fold=fold,model=name,predicted_x_m=pred[:,0],predicted_y_m=pred[:,1],residual_x_m=e[:,0],residual_y_m=e[:,1],error_m=np.sqrt(e2),position_variance_m2=v,NLL=nll,mahalanobis2=d2)
            for level,cut in LEVELS.items():
                row[f'covered{level}']=np.where(np.isfinite(v),(d2<=cut).astype(float),np.nan)
                row[f'area{level}_m2']=np.pi*cut*v;row[f'radius{level}_m']=np.sqrt(cut*v)
            outputs.append(pd.DataFrame(row))
    pred=pd.concat(outputs,ignore_index=True);sens=pd.concat(sensitivity,ignore_index=True)
    pred.to_parquet(ROOT/'data/q_predictions_compact.parquet',index=False,compression='zstd')
    sens.to_parquet(ROOT/'data/q_smoothing_residuals.parquet',index=False,compression='zstd')
    data=pred.merge(orig,on='origin_row',validate='many_to_one');sens=sens.merge(orig[['origin_row','sequence_id','recording_date','track_uid','horizon_s']],on='origin_row',validate='many_to_one')
    # Explicit joined per-sample predictions include all IDs, timestamps and frozen condition metadata.
    data.to_parquet(ROOT/'data/imptc_cv_residuals.parquet',index=False,compression='zstd')
    return data,sens

def q_reports(data,sens,inv,fit,date_fold,segments):
    overall=metric_table(data,['model','horizon_s']);overall['test_recording_dates']=[data[(data.model==r.model)&(data.horizon_s==r.horizon_s)].recording_date.nunique() for _,r in overall.iterrows()]
    overall.to_csv(ROOT/'reports/q_overall_metrics.csv',index=False)
    seq=metric_table(data,['sequence_id','model','horizon_s']);seq.to_csv(ROOT/'reports/q_sequence_metrics.csv',index=False)
    tracks=metric_table(data,['track_uid','model','horizon_s']);tracks.to_csv(ROOT/'reports/q_track_metrics.csv',index=False)
    dates=metric_table(data,['recording_date','model','horizon_s']);dates.to_csv(ROOT/'reports/q_date_metrics.csv',index=False)
    for name,frame in [('sequence',seq),('track',tracks),('date',dates)]:
        frame.groupby(['model','horizon_s'])[['RMSE_m','MAE_m','coverage90','coverage95','mean_area95_m2','NLL']].mean().reset_index().to_csv(ROOT/f'reports/q_{name}_macro.csv',index=False)
    ci=[]
    for (model,h),g in data.groupby(['model','horizon_s']):
        cols=['RMSE_m','MAE_m']+(['coverage90','coverage95','mean_area95_m2'] if model!='Deterministic_CV' else [])
        bounds,n=grouped_bootstrap(g,'recording_date',cols)
        for metric,bound in bounds.items():ci.append(dict(model=model,horizon_s=h,metric=metric,CI95_low=bound[0],CI95_high=bound[1],recording_date_clusters=n,conditional_on_fixed_OOF_predictions=True))
    pd.DataFrame(ci).to_csv(ROOT/'reports/q_date_cluster_bootstrap.csv',index=False)
    smoothing=[]
    for (date,h,w),g in sens.groupby(['recording_date','horizon_s','causal_window_s']):
        e=g[['residual_x_m','residual_y_m']].to_numpy();C=np.cov(e.T,ddof=0)
        smoothing.append(dict(recording_date=date,horizon_s=h,causal_window_s=w,predictions=len(g),tracks=g.track_uid.nunique(),RMSE_m=np.sqrt(np.mean(g.error_m**2)),cov_xx_m2=C[0,0],cov_xy_m2=C[0,1],cov_yy_m2=C[1,1],naive_q_scale=3*np.trace(C)/(2*h**3)))
    sf=pd.DataFrame(smoothing);sf.to_csv(ROOT/'reports/q_smoothing_sensitivity.csv',index=False)
    conditions=[]
    for condition in ['source_type','source_switch_past1s','stop_candidate','accel_candidate','decel_candidate','turn_candidate']:
        for (model,h,value),g in data.groupby(['model','horizon_s',condition]):
            conditions.append(dict(condition=condition,value=str(value),model=model,horizon_s=h,recording_dates=g.recording_date.nunique(),**metrics(g)))
    pd.DataFrame(conditions).to_csv(ROOT/'reports/q_condition_diagnostics.csv',index=False)
    # All plots describe frozen out-of-fold predictions; they never feed back into fitting.
    fig,axes=plt.subplots(1,2,figsize=(13,4))
    for h,ax in zip([1.,3.],axes):
        for model in MODELS[1:]:
            g=dates[(dates.horizon_s==h)&(dates.model==model)]
            ax.plot(range(len(g)),g.coverage95,'o-',label=model)
        ax.axhline(.95,color='k',ls='--');ax.set(xlabel='Held-out recording date index',ylabel='95% recorded-position coverage',ylim=(0,1.02),title=f'{h:g}s')
    axes[0].legend(fontsize=6);figure('q_coverage_by_date.png')
    fig,axes=plt.subplots(1,2,figsize=(13,4))
    for h,ax in zip([1.,3.],axes):
        for model in MODELS[1:]:
            g=dates[(dates.horizon_s==h)&(dates.model==model)];ax.scatter(g.mean_area95_m2,g.coverage95,label=model)
        ax.axhline(.95,color='k',ls='--');ax.set(xlabel='Mean 95% prediction area (m2)',ylabel='Coverage',title=f'{h:g}s')
    axes[0].legend(fontsize=6);figure('q_sharpness.png')
    fig,axes=plt.subplots(1,2,figsize=(13,4))
    for h,ax in zip([1.,3.],axes):
        quantiles=np.linspace(.01,.99,99)
        for model in MODELS[1:]:
            g=data[(data.horizon_s==h)&(data.model==model)]
            ax.plot(chi2.ppf(quantiles,2),np.quantile(g.mahalanobis2,quantiles),label=model)
        ax.plot([0,10],[0,10],'k--');ax.set(xlabel='Chi-square(2) quantile',ylabel='Observed Mahalanobis2 quantile',title=f'{h:g}s tail')
    axes[0].legend(fontsize=6);figure('q_gaussian_tails.png')
    cases=data[(data.model=='Data_fitted_Q_KF')&(data.horizon_s==3.)].sort_values('error_m',ascending=False).drop_duplicates('track_uid').head(8)
    cases.to_csv(ROOT/'reports/q_failure_cases.csv',index=False);by={s['segment_id']:s for s in segments}
    for number,(_,r) in enumerate(cases.iterrows(),1):
        s=by[r.segment_id];i=np.searchsorted(s['raw_ts'],r.anchor_ts_us);j=np.searchsorted(s['raw_ts'],r.future_ts_us);lo=np.searchsorted(s['t'],s['t'][i]-1.)
        fig,ax=plt.subplots(figsize=(6,5));ax.plot(s['xy'][lo:i+1,0],s['xy'][lo:i+1,1],'k-',label='Past input')
        ax.plot(s['xy'][i:j+1,0],s['xy'][i:j+1,1],color='green',label='Future recorded (evaluation only)')
        choices=data[(data.anchor_id==r.anchor_id)&(data.horizon_s==3.)]
        for _,x in choices.iterrows():
            art=ax.scatter(x.predicted_x_m,x.predicted_y_m,marker='x',label=x.model)
            if np.isfinite(x.radius95_m):ax.add_patch(Ellipse((x.predicted_x_m,x.predicted_y_m),2*x.radius95_m,2*x.radius95_m,fill=False,color=art.get_facecolor()[0],alpha=.6))
        ax.axis('equal');ax.set(xlabel='Intersection-local X (m)',ylabel='Y (m)',title=f'{r.track_uid}\n3s Q-fitted error={r.error_m:.2f}m');ax.legend(fontsize=6);figure(f'q_failure_{number:02d}.png')
    md('02_q_full.md',['# Q_effective full-data extension',
        'Canonical Full01–05, never pooled with Samples. Status2 finite XYZ segments break at non-increasing time or >60ms. One-second past-only warmup, 0.2s origin stride, paired 1/3s future availability within20.1ms, actual timestamp separation. No future smoothing.',
        'Five recording-date grouped outer folds. All sequences/tracks from a recording date stay in one fold. Fixed noise grid is chosen on development dates; scalar q is forecast-NLL fitted on development dates with selected R fixed. The optional joint R/q baseline is IMPTC-only innovation ML, not EM and not physical identifiability. No Test-driven interval calibration.',
        'State [x,y,vx,vy], continuous white acceleration spectral density q (m2/s3), Q(dt)=q[[dt3/3 I,dt2/2 I],[dt2/2 I,dt I]]. Isotropic R=rI (m2), P0=diag(r,r,4,4), velocity0. Forecast covariance includes filtered state uncertainty, future q and future R because the target is the recorded trajectory.',
        'Forecast micro:',tab(overall),'Date-level test metrics:',tab(dates),
        'Track, sequence and date macro metrics and date-cluster bootstrap CIs are saved separately. Overlapping forecasts are dependent; no iid-frame CI is used. Deterministic CV intervals are N/A.',
        'Sensitivity uses the same origins for past OLS windows0.12/0.4/1.0s. q_smoothing_sensitivity.csv is diagnostic; its naive q scale is not fitted Q_true. Stop/acceleration/deceleration/turn use the same frozen proxy thresholds and no conditional models. source_type/status are retained controls. No signal, weather, age or violation predictor enters fitting.',
        'Tiny/ending valid segments may not provide both horizons. Their raw rows and exclusion reasons remain in q_validity_funnel.csv. Full end-to-end tracking/GT localization is not claimed. Independent person identity across sequences is unavailable.',
        'The same dataset and some dates were already inspected during the sample pilot/Set01 audit. These are holdouts for the new fits, not a claim of pristine never-inspected external Test.',
        '![Coverage](../figures/q_coverage_by_date.png)','![Sharpness](../figures/q_sharpness.png)','![Tails](../figures/q_gaussian_tails.png)'])
    return overall,dates

def validate(rparams,data,orig,segments,folds,date_fold):
    assert len(data)==4*len(orig) and not data[['origin_row','model']].duplicated().any()
    assert np.isfinite(data[['predicted_x_m','predicted_y_m','error_m']].to_numpy()).all()
    p=data[data.model!='Deterministic_CV'];e2=(p.GT_recorded_x_m-p.predicted_x_m)**2+(p.GT_recorded_y_m-p.predicted_y_m)**2
    assert (p.position_variance_m2>0).all()
    for level in [90,95]:
        cut=-2*np.log1p(-level/100)
        assert np.array_equal((e2<=cut*p.position_variance_m2).astype(float),p[f'covered{level}'])
        assert np.allclose(np.pi*cut*p.position_variance_m2,p[f'area{level}_m2'],rtol=1e-12)
    for f in folds:assert not(set(f['test_recording_dates'])&set(f['development_recording_dates']))
    qfit=json.loads((ROOT/'models/q_effective_params.json').read_text())['folds'];by={s['segment_id']:s for s in segments}
    mean_diff=cov_diff=ols_diff=0.;checks=0
    for fold in range(5):
        for model in MODELS[1:]:
            eligible=data[(data.outer_fold==fold)&(data.model==model)&(data.horizon_s==3.)]
            row=eligible.iloc[len(eligible)//2];s=by[row.segment_id];i=np.searchsorted(s['raw_ts'],row.anchor_ts_us)
            pr=qfit[str(fold)][model];m,c=reference_filter(s['t'][:i+1],s['xy'][:i+1],pr['r_m2'],pr['q_m2_s3'])
            h=row.actual_horizon_s;F=np.eye(4);F[:2,2:]=np.eye(2)*h
            pred=(F@m[-1])[:2];C=(F@c[-1]@F.T)[:2,:2]+np.eye(2)*(pr['q_m2_s3']*h**3/3+pr['r_m2'])
            mean_diff=max(mean_diff,float(np.max(abs(pred-[row.predicted_x_m,row.predicted_y_m]))))
            cov_diff=max(cov_diff,float(np.max(abs(C-np.eye(2)*row.position_variance_m2))));checks+=1
    assert mean_diff<1e-8 and cov_diff<1e-9
    det=data[data.model=='Deterministic_CV'];sample=det.sample(min(80,len(det)),random_state=42)
    for _,row in sample.iterrows():
        s=by[row.segment_id];i=np.searchsorted(s['raw_ts'],row.anchor_ts_us);mask=(s['t']>=s['t'][i]-.4-1e-9)&(s['t']<=s['t'][i])
        X=np.column_stack((s['t'][mask]-s['t'][i],np.ones(mask.sum())));v=np.linalg.lstsq(X,s['xy'][mask],rcond=None)[0][0]
        pred=s['xy'][i]+row.actual_horizon_s*v;ols_diff=max(ols_diff,float(np.max(abs(pred-[row.predicted_x_m,row.predicted_y_m]))))
    assert ols_diff<1e-8
    # Test forward-only filtering by changing future observations after an origin.
    s=next(s for s in segments if len(s['t'])>100);xy=s['xy'].copy();changed=xy.copy();changed[80:]+=1000
    a,b,_=kf(s['t'],xy,.01,.1);aa,bb,_=kf(s['t'],changed,.01,.1)
    assert np.array_equal(a[:80],aa[:80]) and np.array_equal(b[:80],bb[:80])
    original=json.loads((ROOT/'input_sha256.json').read_text());assert all(sha(Path(p))==h for p,h in original.items())
    execution=json.loads((ROOT/'execution_freeze.json').read_text());assert all(sha(ROOT/p)==h for p,h in execution['code_sha256'].items())
    from PIL import Image
    figs=list((ROOT/'figures').glob('*.png'))
    for path in figs:
        with Image.open(path) as image:image.verify()
    result=dict(passed=True,original_sample_and_pilot_inputs_results_unchanged=True,date_disjoint_folds=True,
        all_models_common_origins=True,independent_matrix_KF_checks=checks,max_mean_difference_m=mean_diff,max_covariance_difference_m2=cov_diff,
        independent_past_OLS_checks=len(sample),max_OLS_difference_m=ols_diff,all_coverage_area_recomputed=True,
        future_perturbation_causality_test=True,figures_verified=len(figs),
        Q_forecasts=len(data),Q_origins=len(orig)//2,Q_evaluable_tracks=data.track_uid.nunique(),Q_evaluable_sequences=data.sequence_id.nunique(),Q_dates=data.recording_date.nunique(),
        R_sites=len(rparams['sites']),R_eligible_pairs=rparams['eligible_pairs'])
    js('reports/validation.json',result);return result

def finish(rparams,overall,dates,validation,orig,inv):
    q=json.loads((ROOT/'reports/imptc_metrics.json').read_text());rp=json.loads((ROOT/'reports/spd_metrics.json').read_text())
    factors=[]
    for axis,names,decision in [('R',['distance','occlusion','bbox_size','truncation'],'descriptive candidate; no conditional model selected'),
        ('Q',['speed','acceleration_deceleration','stop_restart','heading_change','nearby_observed_tracks'],'keep diagnostic candidate; noisy measurement-derived proxy'),
        ('Q/R',['source_type','status'],'keep observation-process stratification control'),
        ('B',['between_track_mean_speed'],'initial speed prior candidate only'),('Outcome',['completed_crossing','pedestrian_signal_spatial_mapping'],'N/A; verified regions/track-signal association unavailable')]:
        for name in names:factors.append(dict(axis=axis,factor=name,decision=decision,not_final_physical_identification=True))
    pd.DataFrame(factors).to_csv(ROOT/'reports/factor_decision_table.csv',index=False)
    md('03_validation.md',['# Full-data verification',json.dumps(clean(validation),ensure_ascii=False,indent=2),
        'Independent full-matrix Joseph-update Kalman and least-squares checks compare actual held-out forecasts. Original input/result hashes were checked again. Date/site grouping prevents within-group leakage in this extension. These numerical checks do not establish physical GT or prove unique R/Q identifiability.',
        'The full protocol differs from sample4-sequence LOSO in population and stricter group granularity. The original sample results remain frozen. Q date bootstrap conditions on the fixed OOF predictions; it does not include model-refit/selection uncertainty. R bootstrap has only six site clusters.'])
    md('limitations.md',['# Limitations',
        'R_pair_proxy is camera/virtual-LiDAR annotation disagreement, affected by shared labels, asynchrony and calibration interpretation. No independent detector-vs-GT data. Six held-out sites are not broad external validation.',
        'Q_effective targets recorded trajectories from an existing sensing/tracking pipeline, not physical GT. Isotropic Gaussian CV is an assumption; filtering/initial-state/observation/processing effects remain mixed. Innovation-ML boundary solutions do not imply zero physical measurement noise.',
        'Only eligible common1s/3s origins are evaluated. Very short/ending segments and invalid status rows remain in audit tables but lack forecast targets. Dense origins are correlated. Date grouping is conservative; actual identities across dates are unavailable.',
        'Signals/weather/age/violations are not fitted. Complete-crossing/G95 requires independently verified geometry/entry-exit definition and is not computed. SPD and IMPTC are not pooled and SPD R is never forced into IMPTC.',
        'Sample pilot and Set01 were inspected previously; the full extension is exploratory with fixed new-fit holdouts, not an untouched benchmark. No hyperparameters were revised after outer-fold scores.'])
    cols=['model','horizon_s','test_recording_dates','test_sequences','test_tracks','predictions','RMSE_m','MAE_m','coverage90','coverage95','mean_area95_m2']
    md('full_summary.md',['# View2Risk 전체 데이터 확장 결과 — 261026',
        '**기존 데이터 감사 MD의 미확보 전체 자료를 반영하고, 샘플 R/Q 파일럿과 같은 모델을 별도 전체 확장판으로 실행했다.** 기존 sample_audit 및 pilot_rq_261025는 수정하지 않았다.',
        f'R: SPD 인프라 {rp["frames"]:,}프레임, {rparams["sequences"]}개 paired-data 시퀀스, {len(rparams["sites"])}개 교차로, {rparams["tracks"]}개 시퀀스-트랙 그룹, 유효 주석쌍 {rparams["eligible_pairs"]:,}개. Q: Full01–05의 보행자 {q["pedestrian_tracks"]:,}트랙, {q["sequences"]}시퀀스, {q["recording_dates"]}촬영 날짜, {q["observations"]:,}관측. Samples는 합산하지 않았다.',
        '## R_pair_proxy',
        f'수평 주석 차이 RMSE **{rparams["summary"]["RMSE_m"]:.6f} m**, 중앙값 {rparams["summary"]["median_m"]:.6f} m, p95 {rparams["summary"]["p95_m"]:.6f} m. 평균 편향과 공분산(m², ddof0):',
        '```text\nmean = '+np.array2string(np.array(rparams['mean_bias_m']),precision=8)+'\nR_pair_proxy =\n'+np.array2string(np.array(rparams['covariance_m2']),precision=8)+'\n```',
        '교차로를 하나씩 제외하는 검증으로 같은 장소의 인접 클립이 개발/평가 양쪽에 섞이지 않게 했다. 이것은 순수 R_camera나 검출기 정확도가 아니다. 제공 calibration·투영의 미해결 사항은 유지했다. 전체 source QC와 사례 그림은 spd_* 표와 figures/spd_case_*.png에 있다.',
        '## Q_effective 및 recorded-trajectory 검증',
        f'기록 날짜를 통째로 묶은5-fold 홀드아웃이다. 모델 방정식·고정 잡음 후보·학습 q 범위·1초/3초 horizon·유효 구간·과거 속도 창·행동 후보 임계값은 샘플판과 같다. 모델별 예측 시작점은 공통이며 실제 평가 대상은 {validation["Q_evaluable_tracks"]:,}트랙 / {validation["Q_evaluable_sequences"]}시퀀스 / {validation["Q_dates"]}날짜다.',
        tab(overall[cols]),
        'coverage는0~1 비율, 면적m²다. Deterministic CV의 확률영역은 N/A. 원시 예측 전체는 data/imptc_cv_residuals.parquet. 날짜·시퀀스·트랙 macro 및 날짜 bootstrap95%CI는 reports/q_* 표에 따로 저장했다. 미래 관측 R을 포함한 영역을 기록된 궤적에 비교했으며 독립 물리 참값 검증이 아니다.',
        '정지·가감속·회전·센서 전환 진단, 평활화0.12/0.4/1초 민감도, Gaussian 꼬리와 큰 오차8사례를 제공한다. 외부 Test에 맞춰 영역을 재보정하거나 모델 설정을 바꾸지 않았다.',
        '## 판단과 남은 작업',
        '전체 자료에서도 R/Q 추정 파이프라인은 실행 가능하다. 추가된 자료는 표본·조건 지원을 늘리지만, R의 독립 기준 라벨과 Q의 실측 참값 부족을 해결하지 않는다. 예측영역 포함률과 크기를 함께 확인해야 하며 좋은 점 RMSE가 적절한 불확실성을 뜻하지 않는다. 최종 조건부 모델 선정·실제 R/Q 통합 주장·신호 제어·G95는 보류한다.',
        '## 재현성과 위치',
        'protocol_full_261026.md 및 protocol.json은 full 확장 전에 고정했다. data/splits.json, models/, reports/kernel_reuse.json, input_sha256.json, environment.json, manifest.json에 분할·파라미터·재사용 코드·입력/결과 hash와 버전을 기록했다. 실행은 `sbatch run.sh`이며 완료된 결과 위 재실행은 차단한다. GPU는 사용하지 않았다.',
        '**검증 통과.** 상세: 01_r_full.md, 02_q_full.md, 03_validation.md, limitations.md.'])
    # Add a direct data-dependent interpretation; no new fitting is performed.
    learned=overall[overall.model=='Data_fitted_Q_KF'].sort_values('horizon_s')
    joint=overall[overall.model=='Joint_innovation_ML_KF'].sort_values('horizon_s')
    text=[]
    for _,r in learned.iterrows():
        j=joint[joint.horizon_s==r.horizon_s].iloc[0]
        text.append(f'- {r.horizon_s:g}초 Q-fitted: RMSE {r.RMSE_m:.4f} m, 목표95% 영역의 실제 포함률 {100*r.coverage95:.2f}% (목표 대비 {100*(r.coverage95-.95):+.2f}%p), 평균 면적 {r.mean_area95_m2:.4f} m². Joint innovation-ML 포함률은 {100*j.coverage95:.2f}%다.')
    with (ROOT/'reports/full_summary.md').open('a') as f:f.write('\n## 고정된 평가 결과 해석\n\n'+'\n'.join(text)+'\n\n위 포함률 차이는 현재 가정의 보정 상태를 보여주는 수치이며, 결과를 보고 추정 범위/평가 기준을 변경하지 않았다.\n')

def main():
    assert not (ROOT/'reports/full_summary.md').exists(),'Preserve completed full experiment.'
    status('fitting_R')
    rparams,rfolds=r_analysis()
    q=pd.read_parquet(ROOT/'data/processed/imptc_pedestrian_tracks.parquet')
    status('building_Q_origins',observations=len(q))
    segments,orig,inv=build_segments(q);del q
    status('fitting_Q',origins=len(orig)//2,segments=len(segments))
    fit,date_fold,qfolds=fit_q(segments,orig)
    js('data/splits.json',dict(R_site_holdout=rfolds,Q_date_grouped_folds=qfolds,date_to_fold=date_fold))
    status('predicting_Q')
    data,sens=predict_q(segments,orig,fit,date_fold)
    status('summarizing_Q',predictions=len(data))
    overall,dates=q_reports(data,sens,inv,fit,date_fold,segments)
    validation=validate(rparams,data,orig,segments,qfolds,date_fold)
    finish(rparams,overall,dates,validation,orig,inv)
    js('environment.json',dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,platform=platform.platform(),seed=42,GPU_used=False,elapsed_s=time.time()-START))
    js('manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in ['tmp','parts']) and p.name not in ['manifest.json','run.log'] and not p.is_symlink()})
    status('complete',validation=validation,summary=str(ROOT/'reports/full_summary.md'))

if __name__=='__main__':
    try:main()
    except BaseException as exc:status('failed',error_type=type(exc).__name__,error=str(exc));raise
