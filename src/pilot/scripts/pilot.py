"""Sample-only R proxy and causal CV/Kalman pilot. No original file is mutated."""
from pathlib import Path
import hashlib
import json
import os
import platform
import sys
import time
import warnings

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent
for directory in ['data', 'models', 'reports', 'figures', 'tmp']:
    (ROOT / directory).mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'tmp/mpl'))
os.environ.setdefault('NUMBA_CACHE_DIR', str(ROOT / 'tmp/numba'))
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import chi2, spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from numba import njit

SEED = 42
RNG = np.random.default_rng(SEED)
LEVELS = {90: float(chi2.ppf(.90, 2)), 95: float(chi2.ppf(.95, 2))}
MODELS = ['Deterministic_CV', 'Fixed_noise_KF', 'Data_fitted_Q_KF', 'Joint_innovation_ML_KF']
HORIZONS = [1., 3.]
WINDOWS = [.12, .4, 1.]


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)): return [clean(v) for v in x]
    if isinstance(x, np.ndarray): return clean(x.tolist())
    if isinstance(x, np.generic): return clean(x.item())
    if isinstance(x, float) and not np.isfinite(x): return None
    return x


def js(path, value):
    (ROOT / path).write_text(json.dumps(clean(value), ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def md(path, pieces):
    (ROOT / 'reports' / path).write_text('\n\n'.join(pieces) + '\n')


def tab(frame):
    if not len(frame): return '(none)'
    f = frame.copy()
    for c in f:
        if pd.api.types.is_float_dtype(f[c]): f[c] = f[c].map(lambda v: f'{v:.6g}' if np.isfinite(v) else 'N/A')
    rows = [list(f.columns), ['---'] * len(f.columns)] + list(f.fillna('N/A').itertuples(index=False, name=None))
    return '\n'.join('| ' + ' | '.join(str(x).replace('|', '/') for x in row) + ' |' for row in rows)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def savefig(name):
    plt.tight_layout()
    plt.savefig(ROOT / 'figures' / name, dpi=150)
    plt.close()


def normstats(e):
    n = np.linalg.norm(e, axis=1)
    return dict(n=len(e), bias_m=e.mean(axis=0), covariance_m2=np.cov(e.T, ddof=0),
                RMSE_m=np.sqrt(np.mean(n*n)), MAE_m=n.mean(), median_m=np.median(n),
                p90_m=np.quantile(n, .9), p95_m=np.quantile(n, .95), max_m=n.max())


def gauss_stats(e, mu, cov, thresholds=LEVELS):
    c = cov + np.eye(2) * 1e-10
    d = e - mu
    d2 = np.einsum('ni,ij,nj->n', d, np.linalg.inv(c), d)
    result = dict(NLL=np.mean(np.log(2*np.pi) + .5*np.linalg.slogdet(c)[1] + .5*d2))
    for level, cut in thresholds.items():
        result[f'coverage{level}'] = np.mean(d2 <= cut)
        result[f'area{level}_m2'] = np.pi * cut * np.sqrt(np.linalg.det(c))
    return result


def schema(r, q):
    mapping = {
        'SPD': dict(ids='sequence_id, frame_id, track_id, track_uid', positions='camera_world_x/y, lidar_world_x/y; dx/dy',
                    timestamps='camera_timestamp, lidar_timestamp: int64 UNIX microseconds',
                    conditions='timestamp_gap_s, distance_to_sensor_m, occluded_state',
                    calibration='calibration_camera_nonrigid, coordinate_frame'),
        'IMPTC': dict(ids='sequence_id, track_id, track_uid', positions='x, y: metres, intersection-local',
                      timestamps='ts_us: int64 UNIX microseconds', speed='speed_reported_mps: already converted m/s',
                      validity='status == 2 and finite x/y/z; segments break at dt<=0 or dt>0.060 seconds',
                      controls='source_type, status; no signals/weather used'),
    }
    pieces = ['# Actual input schema and verified mapping',
              '**Mapping correction:** the input has `speed_reported_mps` already in m/s; it must NOT be divided by 3.6 again. Raw km/h conversion was done by the existing parser. Q uses causal XY slope components, not the scalar speed as vx/vy.',
              'Q Parquet does not carry timestamp_unit/coordinate_frame metadata columns; units and frame are mapped from the existing sample schema report. No input columns were added or changed. R uses stored world-horizontal coordinates, not camera projection or an assumed orthogonal camera transform.']
    for name, frame in [('SPD', r), ('IMPTC', q)]:
        pieces += ['## ' + name, tab(pd.DataFrame({'column': frame.columns, 'dtype': [str(x) for x in frame.dtypes]})),
                   json.dumps(mapping[name], ensure_ascii=False, indent=2)]
    md('schema_mismatch.md', pieces)
    js('data/schema_mapping.json', mapping)
    assert set(['dx', 'dy', 'camera_world_x', 'lidar_world_x', 'track_uid']).issubset(r)
    assert set(['x', 'y', 'ts_us', 'status', 'speed_reported_mps', 'track_uid']).issubset(q)
    assert pd.api.types.is_integer_dtype(q.ts_us)


def r_pilot(r):
    e = r[['camera_world_x', 'camera_world_y']].to_numpy() - r[['lidar_world_x', 'lidar_world_y']].to_numpy()
    assert np.allclose(e, r[['dx', 'dy']], atol=2e-11)
    stats = normstats(e)
    old = json.loads((BASE / 'reports/spd_metrics.json').read_text())
    differences = dict(RMSE_m=float(stats['RMSE_m']-old['RMSE_world_horizontal_xy_m']),
                       median_m=float(stats['median_m']-old['discrepancy_norm_m']['median']))
    assert max(abs(x) for x in differences.values()) < 1e-9
    data = r.copy()
    data['residual_x_m'], data['residual_y_m'] = e.T
    data.to_parquet(ROOT / 'data/spd_pair_residuals.parquet', index=False)
    tracks = sorted(r.track_uid.unique())
    clusters = [e[r.track_uid.to_numpy() == t] for t in tracks]
    boot = []
    for _ in range(2000):
        sample = np.concatenate([clusters[i] for i in RNG.integers(0, len(clusters), len(clusters))])
        cov = np.cov(sample.T, ddof=0)
        boot.append([*sample.mean(axis=0), cov[0,0], cov[0,1], cov[1,1], np.sqrt(np.mean(np.sum(sample**2, axis=1)))])
    ci = dict(zip(['bias_x_m','bias_y_m','R_xx_m2','R_xy_m2','R_yy_m2','RMSE_m'], np.quantile(boot, [.025,.975], axis=0).T))
    summary, predictions, folds, holdout = [], [], [], []
    nominal = np.median(np.diff(np.sort(r.camera_timestamp.unique()))) / 1e6
    for track, g in r.groupby('track_uid', sort=True):
        eg = g[['dx','dy']].to_numpy()
        row = dict(track_uid=track, sequence_id=g.sequence_id.iloc[0], pairs=len(g), **normstats(eg))
        row.pop('bias_m'); row.pop('covariance_m2')
        gs = g.sort_values('camera_timestamp'); dt = np.diff(gs.camera_timestamp.to_numpy()) / 1e6
        keep = (dt>0)&(dt<=1.5*nominal)
        row['lag1_valid_pairs'] = int(keep.sum())
        for axis in ['dx','dy']:
            a,b = gs[axis].to_numpy()[:-1][keep],gs[axis].to_numpy()[1:][keep]
            row[axis+'_lag1'] = np.corrcoef(a,b)[0,1] if len(a)>2 and a.std()>0 and b.std()>0 else np.nan
        summary.append(row)
        train = r[r.track_uid != track]; et = train[['dx','dy']].to_numpy()
        mu = et.mean(axis=0); cov = np.cov(et.T, ddof=0)
        # Draw complete training-track clusters before sampling one predictive residual.
        trainclusters = [a[['dx','dy']].to_numpy() for _,a in train.groupby('track_uid')]
        particles = []
        for _ in range(5000):
            pool = np.concatenate([trainclusters[i] for i in RNG.integers(0,len(trainclusters),len(trainclusters))])
            particles.append(pool[RNG.integers(len(pool))])
        particles = np.array(particles); em = particles.mean(axis=0); ec = np.cov(particles.T, ddof=0)+np.eye(2)*1e-10
        ed = particles-em
        radius2 = np.einsum('ni,ij,nj->n', ed,np.linalg.inv(ec),ed)
        empirical_cuts = {k: float(np.quantile(radius2,k/100)) for k in LEVELS}
        folds.append(dict(test_tracks=[track], development_tracks=sorted(train.track_uid.unique())))
        for model, mean, c, cuts in [('Gaussian_zero_bias',np.zeros(2),et.T@et/len(et),LEVELS),
                                     ('Gaussian_with_bias',mu,cov,LEVELS),
                                     ('Empirical_track_bootstrap',em,ec,empirical_cuts)]:
            metrics = gauss_stats(eg,mean,c,cuts)
            if model.startswith('Empirical'): metrics['NLL'] = np.nan
            for _, rr in g.iterrows():
                ev = np.array([rr.dx,rr.dy])-mean
                d2 = ev@np.linalg.solve(c+np.eye(2)*1e-10,ev)
                predictions.append(dict(model=model,track_uid=track,frame_id=rr.frame_id,d2=d2,
                    covered90=d2<=cuts[90],covered95=d2<=cuts[95],area90_m2=metrics['area90_m2'],area95_m2=metrics['area95_m2']))
            rowm = dict(model=model,test_track=track,test_pairs=len(g),**metrics)
            rowm['mean_x_m'],rowm['mean_y_m'] = mean
            holdout.append(rowm)
    trackdf=pd.DataFrame(summary); trackdf.to_csv(ROOT/'reports/r_track_summary.csv',index=False)
    hd=pd.DataFrame(holdout); hd.to_csv(ROOT/'reports/r_holdout_metrics.csv',index=False)
    pd.DataFrame(predictions).to_parquet(ROOT/'data/r_holdout_predictions.parquet',index=False)
    correlations = []
    for field in ['timestamp_gap_s','distance_to_sensor_m']:
        correlations.append(dict(field=field,spearman_rho=float(spearmanr(r[field],np.linalg.norm(e,axis=1)).statistic)))
    correlations.append(dict(field='abs_timestamp_gap_s',spearman_rho=float(spearmanr(abs(r.timestamp_gap_s),np.linalg.norm(e,axis=1)).statistic)))
    pd.DataFrame(correlations).to_csv(ROOT/'reports/r_covariate_diagnostics.csv',index=False)
    params=dict(name='R_pair_proxy',frame='SPD world horizontal XY',unit='m2',covariance_ddof=0,
                bias_m=stats['bias_m'],R_pair_proxy_m2=stats['covariance_m2'],distribution=stats,
                cluster_bootstrap95=ci,tracks=9,sequences=1,pairs=253,reproduction_difference=differences,
                pure_camera_R=False,calibration_resolved=False,holdout_folds=folds)
    js('models/r_pair_proxy_params.json',params)
    fig,ax=plt.subplots(1,3,figsize=(14,4))
    for uid,g in r.groupby('track_uid'): ax[0].scatter(g.dx,g.dy,s=12,label=uid.split('/')[-1])
    ax[0].set(xlabel='dx (m)',ylabel='dy (m)',title='Paired annotation residuals');ax[0].axis('equal')
    ax[0].legend(fontsize=6,ncol=3)
    ax[1].hist(np.linalg.norm(e,axis=1),bins=22,density=True,alpha=.6,label='Observed')
    sim=RNG.multivariate_normal(stats['bias_m'],stats['covariance_m2'],50000)
    ax[1].hist(np.linalg.norm(sim,axis=1),bins=50,density=True,histtype='step',label='Biased Gaussian')
    ax[1].set(xlabel='Residual norm (m)',title='Magnitude and tail');ax[1].legend()
    ax[2].scatter(r.timestamp_gap_s*1000,np.linalg.norm(e,axis=1),s=10)
    ax[2].set(xlabel='Camera - LiDAR time gap (ms)',ylabel='Residual norm (m)',title='Timing diagnostic')
    savefig('r_distribution.png')
    fig,ax=plt.subplots(1,3,figsize=(14,4))
    ax[0].scatter(r.distance_to_sensor_m,np.linalg.norm(e,axis=1),s=12)
    ax[0].set(xlabel='Camera distance in source frame (m)',ylabel='Residual norm (m)')
    oc=sorted(r.occluded_state.unique());ax[1].boxplot([np.linalg.norm(e[r.occluded_state==v],axis=1) for v in oc],tick_labels=[str(v) for v in oc])
    ax[1].set(xlabel='Occlusion code',ylabel='Residual norm (m)')
    for uid,g in r.groupby('track_uid'):
        g=g.sort_values('camera_timestamp');ax[2].plot((g.camera_timestamp-g.camera_timestamp.iloc[0])/1e6,g.horizontal_discrepancy_m,lw=.7,label=uid)
    ax[2].set(xlabel='Time within track (s)',ylabel='Residual norm (m)',title='Serial dependence')
    savefig('r_conditions_time.png')
    agg=hd.groupby('model')[['coverage90','coverage95','area90_m2','area95_m2','NLL']].mean().reset_index()
    md('01_r_pilot.md',['# SPD R_pair_proxy pilot','Track-level leave-one-out: 8 development tracks, 1 held-out track; no frame shuffle.',
       'Residual e = camera world XY - virtual-LiDAR world XY; no camera transform inversion or orthogonalization in this pilot.',
       'Full-sample descriptive estimates (not an external evaluation):',tab(pd.DataFrame([{'metric':k,'value':str(clean(v))} for k,v in stats.items()])),
       'Covariance uses maximum-likelihood ddof=0 after subtraction of the fitted bias; uncentered zero-bias Gaussian uses E[eeᵀ].',
       'LOTO metrics, macro over 9 test tracks:',tab(agg),
       'Empirical model: resample complete development tracks, then draw a predictive residual from their pooled rows (5,000 particles/fold). Ellipse axes use particle covariance; 90/95 radial thresholds are empirical training-particle quantiles. No continuous empirical NLL is asserted. It is a demonstration, not robust density validation.',
       'Cluster bootstrap: 2,000 whole-track resamples, conditional on this single sequence. Full-sample parameter confidence intervals are in models/r_pair_proxy_params.json.',
       tab(trackdf),tab(pd.DataFrame(correlations)),
       'Correlations are descriptive; dependent rows invalidate naive independent-frame significance. Timing differences are not compensated. Camera transform nonorthogonality and K/P projection disagreement remain unresolved. Shared 2D boxes and paired annotation dependencies prevent pure R_camera identification.',
       '![Distribution](../figures/r_distribution.png)','![Conditions](../figures/r_conditions_time.png)'])
    return params,folds


@njit(cache=True)
def kf(t, xy, r, q):
    """Two independent axes with identical 2x2 CV covariance; forward-only."""
    n=len(t);state=np.zeros((n,4));cov=np.zeros((n,3));nll=np.zeros(n)
    state[0,0]=xy[0,0];state[0,1]=xy[0,1]
    pp=r;pv=0.;vv=4.
    cov[0,0]=pp;cov[0,1]=pv;cov[0,2]=vv
    for i in range(1,n):
        dt=t[i]-t[i-1]
        p0=state[i-1,0]+dt*state[i-1,2];p1=state[i-1,1]+dt*state[i-1,3]
        pr=pp+2*dt*pv+dt*dt*vv+q*dt**3/3
        pc=pv+dt*vv+q*dt*dt/2;vr=vv+q*dt
        s=pr+r;ex=xy[i,0]-p0;ey=xy[i,1]-p1
        kp=pr/s;kv=pc/s
        state[i,0]=p0+kp*ex;state[i,1]=p1+kp*ey
        state[i,2]=state[i-1,2]+kv*ex;state[i,3]=state[i-1,3]+kv*ey
        pp=pr*r/s;pv=pc*r/s;vv=vr-pc*pc/s
        cov[i,0]=pp;cov[i,1]=pv;cov[i,2]=vv
        nll[i]=np.log(2*np.pi*s)+.5*(ex*ex+ey*ey)/s
    return state,cov,nll


def slope(t, xy, index, window):
    start=np.searchsorted(t,t[index]-window-1e-9)
    x=t[start:index+1]-t[index];y=xy[start:index+1]
    if len(x)<3:return np.array([np.nan,np.nan])
    xc=x-x.mean();return (xc[:,None]*(y-y.mean(axis=0))).sum(axis=0)/(xc@xc)


def segments_and_anchors(q):
    segments=[];inventory=[];excluded=[]
    for uid,g in q.groupby('track_uid',sort=True):
        # Keep original order and explicitly break non-increasing time; never sort bad rows away.
        g=g.sort_values('source_index').reset_index(drop=True)
        ts=g.ts_us.to_numpy(np.int64);valid=(g.status.to_numpy()==2)&np.isfinite(g[['x','y','z']].to_numpy()).all(axis=1)
        run=[];runs=[]
        for i in range(len(g)):
            adjacent=bool(run) and 0<int(ts[i]-ts[run[-1]])<=60000
            if not valid[i] or (run and not adjacent):
                if run:runs.append(run);run=[]
            if valid[i]:run.append(i)
        if run:runs.append(run)
        for number,indices in enumerate(runs):
            a=g.iloc[indices].reset_index(drop=True);raw=a.ts_us.to_numpy(np.int64)
            t=(raw-raw[0])/1e6;xy=a[['x','y']].to_numpy();sid=uid+f'/seg{number:02d}'
            inventory.append(dict(sequence_id=a.sequence_id.iloc[0],track_uid=uid,segment_id=sid,observations=len(a),duration_s=t[-1],ge1=t[-1]>=1,ge2=t[-1]>=2,ge5=t[-1]>=5,ge10=t[-1]>=10))
            anchors=[];last=-np.inf
            for i in range(len(a)):
                if t[i]<1.-1e-9 or t[i]-last<.2-1e-6:continue
                # Require both horizons for all models and all smoothing diagnostics.
                futures=[]
                for h in HORIZONS:
                    loc=np.searchsorted(t,t[i]+h)
                    choices=[j for j in [loc-1,loc] if i<j<len(a)]
                    j=min(choices,key=lambda j:abs(t[j]-t[i]-h)) if choices else -1
                    if j<0 or abs(t[j]-t[i]-h)>.0201:break
                    futures.append(j)
                if len(futures)!=2:continue
                velocities=np.array([slope(t,xy,i,w) for w in WINDOWS])
                if not np.isfinite(velocities).all():continue
                past=np.searchsorted(t,t[i]-.4,side='right')-1
                pv=slope(t,xy,past,.4)
                speed=np.linalg.norm(velocities[1]);pspeed=np.linalg.norm(pv)
                accel=(speed-pspeed)/(t[i]-t[past]) if pspeed>=0 else np.nan
                cross=pv[0]*velocities[1,1]-pv[1]*velocities[1,0]
                dot=pv@velocities[1]
                turn=abs(np.degrees(np.arctan2(cross,dot))/(t[i]-t[past])) if min(speed,pspeed)>.2 else np.nan
                start=np.searchsorted(t,t[i]-1)
                control=dict(source_type=int(a.source_type.iloc[i]),source_switch_past1s=bool(a.source_type.iloc[start:i+1].nunique()>1),
                    speed_mps=speed,accel_proxy_mps2=accel,turn_rate_proxy_deg_s=turn,
                    stop_candidate=speed<=.3,accel_candidate=accel>.5,decel_candidate=accel<-.5,
                    turn_candidate=bool(np.isfinite(turn) and turn>45),nearby_ped_count=int(a.nearby_ped_count.iloc[i]))
                for h,j in zip(HORIZONS,futures):
                    anchors.append(dict(i=i,j=j,horizon_s=h,actual_horizon_s=float(t[j]-t[i]),velocities=velocities,**control))
                last=t[i]
            segments.append(dict(sequence_id=str(a.sequence_id.iloc[0]),track_uid=uid,segment_id=sid,t=t,xy=xy,raw_ts=raw,frame=a,anchors=anchors))
        excluded.append(dict(track_uid=uid,raw_rows=len(g),status2_finite_rows=int(valid.sum()),excluded_rows=int((~valid).sum()),valid_segments=len(runs)))
    inv=pd.DataFrame(inventory);inv.to_csv(ROOT/'reports/q_segment_inventory.csv',index=False)
    pd.DataFrame(excluded).to_csv(ROOT/'reports/q_validity_funnel.csv',index=False)
    assert sum(len(s['t']) for s in segments)==int(((q.status==2)&np.isfinite(q[['x','y','z']]).all(axis=1)).sum())
    assert inv.groupby('track_uid').ge10.any().sum()==49
    return segments,inv


def sequence_score(segments,r,q,objective='forecast'):
    rows=[]
    for seg in segments:
        if len(seg['t'])<2:continue
        state,cov,nll=kf(seg['t'],seg['xy'],r,q)
        if objective=='innovation':
            keep=seg['t']>=1.
            if keep.any():rows.append((seg['sequence_id'],0.,float(nll[keep].sum()),int(keep.sum())))
        else:
            sums={h:[0.,0] for h in HORIZONS}
            for a in seg['anchors']:
                i,j,h=a['i'],a['j'],a['actual_horizon_s']
                pred=state[i,:2]+h*state[i,2:];err=seg['xy'][j]-pred
                pp,pv,vv=cov[i];variance=pp+2*h*pv+h*h*vv+q*h**3/3+r
                nllv=np.log(2*np.pi*variance)+.5*(err@err)/variance
                sums[a['horizon_s']][0]+=nllv;sums[a['horizon_s']][1]+=1
            for h,(total,n) in sums.items():
                if n:rows.append((seg['sequence_id'],h,total,n))
    df=pd.DataFrame(rows,columns=['sequence','horizon','total','n'])
    agg=df.groupby(['sequence','horizon'])[['total','n']].sum()
    return float((agg.total/agg.n).mean())


def fit_models(segments,sequences):
    fits={};trials=[];folds=[]
    for test in sequences:
        train=[s for s in segments if s['sequence_id']!=test]
        development=[x for x in sequences if x!=test]
        folds.append(dict(test_sequences=[test],development_sequences=development,
            inner_validation_folds=[dict(validation_sequences=[v],fitting_sequences=[x for x in development if x!=v]) for v in development],
            note='Fixed grid has no fitted parameters: each candidate is scored on each inner validation sequence, then sequence/horizon-macro averaged. Learned parameters refit using only three outer-development sequences.'))
        grid=[]
        for sd in [.01,.05,.2]:
            for qval in [.01,.1,1.]:
                score=sequence_score(train,sd**2,qval)
                grid.append((score,sd**2,qval));trials.append(dict(test_sequence=test,stage='fixed_grid_development_only',r_m2=sd**2,q_m2_s3=qval,score=score))
        best=min(grid);r=best[1]
        qgrid=np.logspace(-6,2,17)
        scores=[sequence_score(train,r,v) for v in qgrid];idx=int(np.argmin(scores))
        lo=np.log(qgrid[max(0,idx-1)]);hi=np.log(qgrid[min(len(qgrid)-1,idx+1)])
        opt=minimize_scalar(lambda lq:sequence_score(train,r,np.exp(lq)),bounds=(lo,hi),method='bounded',options={'xatol':.002,'maxiter':35})
        candidates=[(float(opt.fun),float(np.exp(opt.x))),(scores[idx],float(qgrid[idx]))]
        learned=min(candidates)
        for v,score in zip(qgrid,scores):trials.append(dict(test_sequence=test,stage='q_grid_training_only',r_m2=r,q_m2_s3=v,score=score))
        # Optional trajectory-only joint R/Q fit by Kalman innovation maximum likelihood.
        joint=[]
        for r0,q0 in [(r,best[2]),(.001,.001),(.01,.1)]:
            result=minimize(lambda x:sequence_score(train,np.exp(x[0]),np.exp(x[1]),'innovation'),
                np.log([r0,q0]),method='L-BFGS-B',bounds=[(np.log(1e-8),np.log(4)),(np.log(1e-6),np.log(100))],
                options={'maxiter':60,'ftol':1e-9})
            joint.append(dict(objective=float(result.fun),r_m2=float(np.exp(result.x[0])),q_m2_s3=float(np.exp(result.x[1])),success=bool(result.success),message=str(result.message)))
        jb=min(joint,key=lambda x:x['objective'])
        fits[test]=dict(development_sequences=development,
            Fixed_noise_KF=dict(r_m2=r,q_m2_s3=best[2],selection_score=best[0],method='predeclared 3x3 grid; development sequence/horizon macro forecast NLL'),
            Data_fitted_Q_KF=dict(r_m2=r,q_m2_s3=learned[1],selection_score=learned[0],optimizer_success=bool(opt.success),method='r held at development-selected fixed model; q fitted by 1s/3s development forecast NLL; coarse grid then bounded log optimization'),
            Joint_innovation_ML_KF=dict(**jb,starts=joint,method='joint effective R/Q Kalman innovation maximum likelihood; same IMPTC development sequences only; not EM, not uniquely identified'))
        print('FIT',test,json.dumps(clean(fits[test])),flush=True)
    pd.DataFrame(trials).to_csv(ROOT/'reports/q_tuning_records.csv',index=False)
    js('models/q_effective_params.json',dict(state_order=['x','y','vx','vy'],r_units='m2 per axis',
        q_units='m2/s3 acceleration-white-noise spectral density per axis',
        F='[[I,dt I],[0,I]]',Q_dt='q * [[dt^3/3 I, dt^2/2 I],[dt^2/2 I,dt I]]',
        future_recorded_position_covariance='H F P_filtered F.T H.T + q*h^3/3 I + r I',
        initial_state='position=first valid measurement; velocity=0',initial_P='diag(r,r,4,4)',
        warmup_s=1,origin_stride_s=.2,paired_horizons=True,folds=fits,pure_Q_true=False,
        SPD_R_used_for_IMPTC=False))
    return fits,folds


def predict(segments,fits):
    rows=[];sensitivity=[]
    for seg in segments:
        params=fits[seg['sequence_id']]
        filters={name:kf(seg['t'],seg['xy'],params[name]['r_m2'],params[name]['q_m2_s3']) for name in MODELS[1:]}
        for a in seg['anchors']:
            i,j,h=a['i'],a['j'],a['actual_horizon_s']
            identity=dict(sequence_id=seg['sequence_id'],track_uid=seg['track_uid'],segment_id=seg['segment_id'],
                anchor_id=seg['segment_id']+f'/{int(seg["raw_ts"][i])}',anchor_ts_us=int(seg['raw_ts'][i]),
                future_ts_us=int(seg['raw_ts'][j]),horizon_s=a['horizon_s'],actual_horizon_s=h,
                anchor_x_m=seg['xy'][i,0],anchor_y_m=seg['xy'][i,1],GT_recorded_x_m=seg['xy'][j,0],GT_recorded_y_m=seg['xy'][j,1],
                **{k:v for k,v in a.items() if k not in ['i','j','velocities','horizon_s','actual_horizon_s']})
            for window,v in zip(WINDOWS,a['velocities']):
                pred=seg['xy'][i]+h*v;err=seg['xy'][j]-pred
                sensitivity.append(dict(**identity,causal_window_s=window,residual_x_m=err[0],residual_y_m=err[1],error_m=float(np.linalg.norm(err))))
            for name in MODELS:
                if name=='Deterministic_CV':
                    pred=seg['xy'][i]+h*a['velocities'][1];variance=np.nan
                else:
                    state,cov,_=filters[name];pr=params[name];pp,pv,vv=cov[i]
                    pred=state[i,:2]+h*state[i,2:]
                    variance=pp+2*h*pv+h*h*vv+pr['q_m2_s3']*h**3/3+pr['r_m2']
                err=seg['xy'][j]-pred;error2=float(err@err)
                row=dict(**identity,model=name,predicted_x_m=pred[0],predicted_y_m=pred[1],residual_x_m=err[0],residual_y_m=err[1],error_m=np.sqrt(error2),position_variance_m2=variance,
                    NLL=np.log(2*np.pi*variance)+error2/(2*variance) if np.isfinite(variance) else np.nan,
                    mahalanobis2=error2/variance if np.isfinite(variance) else np.nan)
                for level,cut in LEVELS.items():
                    row[f'covered{level}']=float(error2<=cut*variance) if np.isfinite(variance) else np.nan
                    row[f'area{level}_m2']=np.pi*cut*variance
                    row[f'radius{level}_m']=np.sqrt(cut*variance)
                rows.append(row)
    data=pd.DataFrame(rows);sens=pd.DataFrame(sensitivity)
    data.to_parquet(ROOT/'data/imptc_cv_residuals.parquet',index=False)
    sens.to_parquet(ROOT/'data/imptc_smoothing_residuals.parquet',index=False)
    return data,sens


def metrics(g):
    return dict(test_sequences=g.sequence_id.nunique(),test_tracks=g.track_uid.nunique(),predictions=len(g),
        RMSE_m=np.sqrt(np.mean(g.error_m**2)),MAE_m=g.error_m.mean(),p95_error_m=g.error_m.quantile(.95),max_error_m=g.error_m.max(),
        coverage90=g.covered90.mean(),coverage95=g.covered95.mean(),mean_area90_m2=g.area90_m2.mean(),mean_area95_m2=g.area95_m2.mean(),
        mean_radius95_m=g.radius95_m.mean(),NLL=g.NLL.mean())


def metric_table(data,keys):
    return pd.DataFrame([dict(zip(keys,k if isinstance(k,tuple) else (k,)),**metrics(g)) for k,g in data.groupby(keys,dropna=False,sort=True)])


def q_reports(data,sens,inv,fits,segments):
    perseq=metric_table(data,['sequence_id','model','horizon_s'])
    pertrack=metric_table(data,['sequence_id','track_uid','model','horizon_s'])
    overall=metric_table(data,['model','horizon_s'])
    perseq.to_csv(ROOT/'reports/q_sequence_metrics.csv',index=False)
    pertrack.to_csv(ROOT/'reports/q_track_metrics.csv',index=False)
    overall.to_csv(ROOT/'reports/q_overall_metrics.csv',index=False)
    sm=perseq.groupby(['model','horizon_s'])[['RMSE_m','MAE_m','coverage90','coverage95','mean_area95_m2','NLL']].mean().reset_index()
    sm.to_csv(ROOT/'reports/q_sequence_macro_metrics.csv',index=False)
    tm=pertrack.groupby(['model','horizon_s'])[['RMSE_m','MAE_m','coverage90','coverage95','mean_area95_m2','NLL']].mean().reset_index()
    tm.to_csv(ROOT/'reports/q_track_macro_metrics.csv',index=False)
    sensitivity=[]
    for (seq,h,w),g in sens.groupby(['sequence_id','horizon_s','causal_window_s']):
        e=g[['residual_x_m','residual_y_m']].to_numpy();s=normstats(e);c=s.pop('covariance_m2');s.pop('bias_m')
        sensitivity.append(dict(sequence_id=seq,horizon_s=h,causal_window_s=w,**s,
            residual_cov_xx_m2=c[0,0],residual_cov_xy_m2=c[0,1],residual_cov_yy_m2=c[1,1],
            naive_effective_q_trace_proxy_m2_s3=3*np.trace(c)/(2*h**3)))
    sf=pd.DataFrame(sensitivity);sf.to_csv(ROOT/'reports/q_smoothing_sensitivity.csv',index=False)
    cond=[]
    for condition in ['source_type','source_switch_past1s','stop_candidate','accel_candidate','decel_candidate','turn_candidate']:
        for (model,h,value),g in data.groupby(['model','horizon_s',condition]):
            cond.append(dict(condition=condition,value=value,model=model,horizon_s=h,**metrics(g)))
    pd.DataFrame(cond).to_csv(ROOT/'reports/q_condition_diagnostics.csv',index=False)
    # Sequence cluster bootstrap is descriptive with only four independent sequence groups.
    bs=[];rng=np.random.default_rng(SEED+1)
    for (model,h),g in data.groupby(['model','horizon_s']):
        groups=[a for _,a in g.groupby('sequence_id')];values=[]
        for _ in range(1000):
            sampled=[groups[i] for i in rng.integers(0,len(groups),len(groups))]
            n=sum(len(x) for x in sampled)
            values.append([np.sqrt(sum(np.sum(x.error_m**2) for x in sampled)/n),
                sum(np.nansum(x.covered95) for x in sampled)/n if model!='Deterministic_CV' else np.nan])
        for j,name in enumerate(['RMSE_m','coverage95']):
            a=np.array(values)[:,j]
            bs.append(dict(model=model,horizon_s=h,metric=name,low95=float(np.quantile(a,.025)) if np.isfinite(a).any() else np.nan,
                high95=float(np.quantile(a,.975)) if np.isfinite(a).any() else np.nan,clusters=4,note='conditional resampling of 4 OOF sequence outputs; no model refit; unstable CI'))
    pd.DataFrame(bs).to_csv(ROOT/'reports/q_sequence_cluster_bootstrap.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for h,ax in zip(HORIZONS,axes):
        for name in MODELS[1:]:
            g=perseq[(perseq.model==name)&(perseq.horizon_s==h)]
            ax.plot(range(len(g)),g.coverage95,'o-',label=name)
        ax.axhline(.95,color='k',ls='--');ax.set(xticks=range(4),xticklabels=['Seq0','Seq1','Seq2','Seq3'],ylim=(0,1.03),ylabel='Recorded-position coverage 95%',title=f'{h:g}s, outer held-out sequences')
    axes[0].legend(fontsize=7);savefig('q_coverage.png')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for h,ax in zip(HORIZONS,axes):
        for name in MODELS[1:]:
            g=perseq[(perseq.model==name)&(perseq.horizon_s==h)]
            ax.scatter(g.mean_area95_m2,g.coverage95,label=name)
        ax.axhline(.95,color='k',ls='--');ax.set(xlabel='Mean 95% area (m2)',ylabel='Coverage 95%',title=f'{h:g}s sharpness')
    axes[0].legend(fontsize=7);savefig('q_sharpness.png')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for h,ax in zip(HORIZONS,axes):
        for name in MODELS[1:]:
            d=data[(data.model==name)&(data.horizon_s==h)].mahalanobis2.to_numpy()
            levels=np.linspace(.01,.99,99)
            ax.plot(chi2.ppf(levels,2),np.quantile(d,levels),label=name)
        ax.plot([0,10],[0,10],'k--');ax.set(xlabel='Chi-square(2) quantile',ylabel='Empirical squared Mahalanobis quantile',title=f'{h:g}s Gaussian tail diagnostic')
    axes[0].legend(fontsize=7);savefig('q_gaussian_tail.png')
    fig,ax=plt.subplots(figsize=(8,4))
    for (seq,h),g in sf.groupby(['sequence_id','horizon_s']):
        g=g.sort_values('causal_window_s');ax.plot(g.causal_window_s,g.RMSE_m,'o-',label=seq.split('_')[0]+f' {h:g}s')
    ax.set(xlabel='Past-only OLS velocity window (s)',ylabel='Deterministic CV RMSE (m)',title='Observation / smoothing sensitivity');ax.legend(fontsize=7,ncol=2)
    savefig('q_smoothing_sensitivity.png')
    # Select failure illustrations after evaluation; never feed this selection back into fitting.
    fitted=data[(data.model=='Data_fitted_Q_KF')&(data.horizon_s==3.)]
    cases=fitted.sort_values('error_m',ascending=False).drop_duplicates('track_uid').head(6)
    cases.to_csv(ROOT/'reports/q_failure_cases.csv',index=False)
    segment_map={s['segment_id']:s for s in segments}
    for number,(_,case) in enumerate(cases.iterrows(),1):
        seg=segment_map[case.segment_id];i=int(np.searchsorted(seg['raw_ts'],case.anchor_ts_us));j=int(np.searchsorted(seg['raw_ts'],case.future_ts_us))
        lo=np.searchsorted(seg['t'],seg['t'][i]-1.)
        fig,ax=plt.subplots(figsize=(6,5))
        ax.plot(seg['xy'][lo:i+1,0],seg['xy'][lo:i+1,1],'k-',label='Past observed (input)')
        ax.plot(seg['xy'][i:j+1,0],seg['xy'][i:j+1,1],color='green',label='Future recorded (evaluation only)')
        ax.scatter(*seg['xy'][i],c='black',marker='o',s=40)
        comparison=data[(data.anchor_id==case.anchor_id)&(data.horizon_s==3.)]
        for _,rr in comparison.iterrows():
            artist=ax.scatter(rr.predicted_x_m,rr.predicted_y_m,marker='x',s=45,label=rr.model)
            if np.isfinite(rr.radius95_m):
                color=artist.get_facecolor()[0];ax.add_patch(Ellipse((rr.predicted_x_m,rr.predicted_y_m),2*rr.radius95_m,2*rr.radius95_m,fill=False,color=color,alpha=.5))
        ax.set(xlabel='Intersection-local East X (m)',ylabel='North Y (m)',title=f'{case.track_uid}\n3s fitted-Q error={case.error_m:.2f}m; 95% hit={bool(case.covered95)}')
        ax.axis('equal');ax.legend(fontsize=6);savefig(f'q_failure_{number:02d}.png')
    used=data[data.model=='Deterministic_CV']
    residual_summary=[]
    for (seq,h),g in used.groupby(['sequence_id','horizon_s']):
        residual_summary.append(dict(sequence_id=seq,horizon_s=h,**normstats(g[['residual_x_m','residual_y_m']].to_numpy())))
    js('reports/q_cv_residual_distribution.json',residual_summary)
    md('02_q_pilot.md',['# IMPTC Q_effective / motion-model-residual pilot',
        'Only IMPTC Samples. Status=2 finite XYZ segments, original source order, break at dt<=0 or dt>60ms. No SPD parameters, signal, weather, age, or violation labels enter fitting.',
        'Common paired 1s/3s origins: at least 1s valid past, 0.2s stride, nearest actual future observation within 20.1ms. Both horizons must exist in the same continuous segment; actual timestamp separation is used. End-of-track origins with no 3s future are excluded for every model and both horizons. This restriction is recorded and limits short/ending-track evaluation.',
        tab(inv.groupby('sequence_id').agg(valid_segments=('segment_id','size'),tracks=('track_uid','nunique'),status2_rows=('observations','sum')).reset_index()),
        f'Evaluable tracks: {used.track_uid.nunique()}; unique origins: {used.anchor_id.nunique()}; predictions per horizon: {len(used)//2}.',
        'Deterministic CV: current measured position + actual horizon × causal OLS XY velocity from past 0.4s. No future smoothing. Sensitivity windows 0.12/0.4/1.0s use identical origins.',
        'State [x,y,vx,vy]. F(dt)=[[I,dt I],[0,I]]. Continuous white-acceleration Q(dt)=q[[dt³/3 I,dt²/2 I],[dt²/2 I,dt I]]. q units m²/s³, R=r I units m². Forecast recorded-position variance includes filtered-state uncertainty, integrated future q, and future r. Initial velocity=0, P=diag(r,r,4,4), with 1s warmup. Isotropy and Gaussian white noise are modeling assumptions.',
        'Outer LOSO: 4 tests, each with 3 development sequences. Fixed noise uses a predeclared grid (observation SD .01/.05/.2m; q .01/.1/1m²/s³), scored only on development sequences using sequence/horizon-macro forecast NLL. Since candidates have no learned parameters, scoring each development sequence is equivalent to the specified inner validation folds. Data-fitted Q fixes R to that selected grid value and estimates q from the same 3 development sequences using 1s/3s forecast NLL. The optional joint baseline estimates effective R and q by Kalman innovation ML with three initializations, using only IMPTC development trajectories; this is not EM and not a uniquely identified physical R/Q.',
        'No held-out sequence is used in parameter selection, interval calibration, threshold choice, or convergence decisions. No model is selected as a final winner from these tests.',
        '## Outer-test metrics by sequence',tab(perseq),
        '## Overall prediction micro',tab(overall),
        '## Sequence macro',tab(sm),'## Track macro',tab(tm),
        'RMSE=sqrt(mean(||recorded-pred||²)); MAE=mean(||recorded-pred||), both Euclidean metres. Coverage uses Mahalanobis² <= chi²(2) quantile; area=π chi² sqrt(det(S)). Deterministic intervals are N/A. All forecasts target recorded trajectories, not independent physical GT. Dense origins and overlapping horizons are correlated.',
        '## Smoothing sensitivity',tab(sf),
        'The naive 3*trace(Cov(residual))/(2*h³) column is only a diagnostic scale. It omits state/observation uncertainty and bias; it is NOT the fitted q or Q_true. Smoothing changes causal velocity and residual dispersion, demonstrating dependence on representation. No centered or future-using smoother was evaluated.',
        '## Control / candidate diagnostics',
        'q_condition_diagnostics.csv keeps track/sequence/prediction support for source_type, past-only sensor switch, stop<=.3m/s, acceleration>.5m/s², deceleration<-.5m/s², turn>45deg/s (both speeds>.2m/s). These are noisy past-window proxies, not behavioral GT, and are not used for conditional model fitting. At overlapping conditions the same forecast can appear in several diagnostic rows.',
        '## Gaussian failures',tab(cases[['sequence_id','track_uid','error_m','mahalanobis2','covered95','radius95_m']]),
        'Failure plots are selected after evaluation for inspection only. Green future trajectories are evaluation references and never inputs to filtering. Observation/initial-state/motion errors remain mixed.',
        '![Coverage](../figures/q_coverage.png)','![Sharpness](../figures/q_sharpness.png)',
        '![Gaussian tails](../figures/q_gaussian_tail.png)','![Smoothing](../figures/q_smoothing_sensitivity.png)'])
    return overall,perseq,sm


def validate(r,q,segments,data,fits,inputs):
    # Synthetic numerical checks and causality checks catch errors with practical consequences.
    t=np.arange(151,dtype=float)*.04;xy=np.column_stack((2+1.5*t,-3-.2*t))
    v=slope(t,xy,50,.4);assert np.allclose(v,[1.5,-.2],atol=1e-10)
    state,cov,nll=kf(t,xy,.01,.1)
    changed=xy.copy();changed[80:]+=1000
    st2,cv2,_=kf(t,changed,.01,.1)
    assert np.array_equal(state[:80],st2[:80]) and np.array_equal(cov[:80],cv2[:80])
    assert np.all(cov[:,0]>0) and np.all(cov[:,2]>0) and np.all(cov[:,0]*cov[:,2]-cov[:,1]**2>=-1e-10)
    for sid,g in data.groupby(['anchor_id','horizon_s']):
        assert set(g.model)==set(MODELS) and len(g)==len(MODELS)
    assert data.position_variance_m2.dropna().gt(0).all()
    assert np.isfinite(data[['predicted_x_m','predicted_y_m','error_m']].to_numpy()).all()
    assert set(data.sequence_id)==set(fits)
    for test,fit in fits.items():assert test not in fit['development_sequences'] and len(fit['development_sequences'])==3
    for seg in segments:
        assert np.all(seg['frame'].status.to_numpy()==2)
        assert np.isfinite(seg['frame'][['x','y','z']].to_numpy()).all()
        assert len(seg['t'])<2 or np.all((np.diff(seg['t'])>0)&(np.diff(seg['t'])<=.060000001))
        for a in seg['anchors']:
            assert seg['t'][a['i']]>=1-1e-9
            assert a['j']>a['i']
            assert abs(a['actual_horizon_s']-a['horizon_s'])<=.0201
    from PIL import Image
    images=list((ROOT/'figures').glob('*.png'))
    for p in images:
        with Image.open(p) as im:im.verify()
    assert all(sha(BASE/p)==h for p,h in inputs.items()), 'An existing input changed.'
    checks=dict(passed=True,SPD_pairs=len(r),SPD_tracks=r.track_uid.nunique(),IMPTC_sample_rows=len(q),
        IMPTC_valid_rows=sum(len(s['t']) for s in segments),valid_segments=len(segments),
        evaluable_tracks=data.track_uid.nunique(),test_sequences=data.sequence_id.nunique(),
        common_origins=data.anchor_id.nunique(),predictions=len(data),all_models_same_origins=True,
        no_outer_test_in_fitting=True,filter_future_perturbation_causality_test=True,
        exact_constant_velocity_slope_test=True,positive_covariances=True,input_hashes_unchanged=True,
        no_SPD_R_in_IMPTC=True,excluded_conditions_not_used=True,figures_verified=len(images),
        parameter_boundary_diagnostics={test:{name:dict(q_near_lower=fit[name]['q_m2_s3']<=1.1e-6,r_near_lower=fit[name]['r_m2']<=1.1e-8)
            for name in MODELS[1:]} for test,fit in fits.items()})
    js('reports/validation.json',checks)
    return checks


def main():
    start=time.monotonic()
    assert not (ROOT/'reports/pilot_summary.md').exists(), 'Keep completed pilot immutable.'
    selected=['plan.md','reports/sample_audit_261025.md','reports/spd_metrics.json','reports/spd_schema_report.md',
        'reports/r_quality_report.md','reports/spd_condition_counts.csv','reports/sample_audit_261025.validation.json',
        'reports/data_audit_summary.md','data/processed/spd_pedestrian_pairs.parquet',
        'data/processed/stage_samples/imptc_pedestrian_tracks.parquet']
    selected += [str(p.relative_to(BASE)) for p in (BASE/'reports/stage_samples').glob('*') if p.is_file()]
    inputs={p:sha(BASE/p) for p in selected};js('data/input_sha256.json',inputs)
    r=pd.read_parquet(BASE/'data/processed/spd_pedestrian_pairs.parquet')
    q=pd.read_parquet(BASE/'data/processed/stage_samples/imptc_pedestrian_tracks.parquet')
    schema(r,q)
    js('config.json',dict(seed=SEED,horizons_s=HORIZONS,velocity_windows_s=WINDOWS,origin_stride_s=.2,
        warmup_s=1,max_gap_s=.060,future_tolerance_s=.0201,both_horizons_required=True,
        forecast_target='recorded future position, includes effective R',primary_fit_score='development sequence/horizon macro Gaussian NLL',
        outer_split='leave-one-sequence-out',R_split='leave-one-track-out',interval_quantiles=LEVELS,
        fixed_grid_sd_m=[.01,.05,.2],fixed_grid_q_m2_s3=[.01,.1,1],q_bounds=[1e-6,100],joint_r_bounds=[1e-8,4],
        excluded=['signal','weather effects','age','signal violation','G95','SPD_R_as_IMPTC_R']))
    rp,rfolds=r_pilot(r)
    print('R_DONE',rp['distribution']['RMSE_m'],flush=True)
    segments,inv=segments_and_anchors(q)
    sequences=sorted(q.sequence_id.unique());assert len(sequences)==4
    print('SEGMENTS',len(segments),'ANCHORS',sum(len(s['anchors']) for s in segments),flush=True)
    fits,qfolds=fit_models(segments,sequences)
    js('data/splits.json',dict(R_leave_one_track_out=rfolds,Q_leave_one_sequence_out=qfolds))
    data,sens=predict(segments,fits)
    overall,perseq,sm=q_reports(data,sens,inv,fits,segments)
    checks=validate(r,q,segments,data,fits,inputs)
    md('03_validation.md',['# Validation and reproducibility checks',json.dumps(clean(checks),ensure_ascii=False,indent=2),
        'Input hashes compare both Parquet tables and existing reports before/after the run; no audit re-run or download was performed. This is not an external validation of physical R/Q.',
        'LOSO forecasts, by sequence:',tab(perseq),
        'q_sequence_cluster_bootstrap.csv resamples the four existing out-of-fold sequence outputs without refitting; intervals are conditional and unstable. Track-macro and sequence-macro metrics are reported separately from correlated forecast-micro metrics. No naive frame-binomial CI is used.',
        'Data-fitted Q optimizer runs and joint-ML convergence/messages/starting solutions are retained in models/q_effective_params.json. Boundary hits signal weak identifiability or smoothing assumptions, not a sensor-noise truth.',
        'References: [Bayesian Filtering and Smoothing, authors\' textbook](https://users.aalto.fi/~ssarkka/pub/bfs_book_2023_online.pdf); [SciPy chi-square quantiles](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html). Equations are implemented directly, with no external code copied.'])
    md('limitations.md',['# Pilot limitations',
        'SPD: one sequence, 9 track groups, 253 paired annotations; shared boxes, asynchronous observations, and unresolved camera calibration/projection. R_pair_proxy describes pair disagreement, never pure camera prediction error.',
        'IMPTC: 4 sequences and 61 tracks, all from provided sensing/tracking data. Q_effective mixes motion-model mismatch, observation/processing effects, initialization and assumed white Gaussian structure. Scalar km/h-derived speed is not independent velocity GT. Future recorded-position forecasts are proxy validation only.',
        'LOSO prevents sequence leakage, but 4 sequences do not support stable nested selection or broad generalization. Development criteria and bounds are fixed before evaluating outer tests. Test folds are not reused for tuning. Sequence and track identities are retained; real-person cross-sequence identity is unavailable.',
        'Fixed-grid R selection and forecast-fitted q are operational predictive parameters. Optional joint innovation-ML R/Q can be confounded, hit bounds, or favor one-step smoothness while under-covering at 1/3s. Joint ML is not EM and not proof of identifiability.',
        'Isotropic linear CV, zero initial velocity and a finite warmup are assumptions. Overlapping horizons and 0.2s origins remain autocorrelated. Paired-horizon eligibility excludes origins near track ends and very short segments. No performance is claimed for excluded frames.',
        'Smoothing sensitivity uses only past data. Noise injection, external sensor fusion, signal-control optimization, G95, weather/age/violation models are not run. SPD and IMPTC rows/people are not pooled. Additional raw downloads are not required or performed by the pilot.'])
    bias=rp['bias_m'];cov=rp['R_pair_proxy_m2']
    concise=overall[['model','horizon_s','test_sequences','test_tracks','predictions','RMSE_m','MAE_m','coverage90','coverage95','mean_area95_m2']]
    md('pilot_summary.md',['# View2Risk R/Q 파일럿 결과 — 261025',
        '**판정: (A) 샘플 기반 추정·검증 파이프라인은 실행 가능하다. (B) R 확장·검증에는 추가 주석/독립 기준 라벨이 우선 필요하다. (D) 독립 실측 GT가 없어 SPD–IMPTC 통합 R/Q 검증 주장은 보류한다.** Q는 현재 샘플로 기술 검증이 가능하나 추가 시퀀스가 있어야 설정 선택·일반화를 더 안정적으로 검증할 수 있다. 아래 포함률을 보고 실제 보정 품질을 함께 판단해야 하며, 실행 성공을 정확한 불확실성 추정 성공으로 간주하지 않는다.',
        '## 데이터와 분할',
        f'SPD: 1시퀀스·9트랙·253쌍, 트랙별 LOTO. IMPTC Samples: 4시퀀스·61트랙·56,374관측, 유효 status=2 54,314개, 유효 구간 {len(inv)}개, 10초 이상 유효 구간이 있는 트랙 49개. 평가 가능한 트랙 {data.track_uid.nunique()}개, 공통 예측 시작점 {data.anchor_id.nunique():,}개. 각 시작점에서 1초와 3초를 모두 평가했다. IMPTC는 outer LOSO로 3개 시퀀스에서 설정을 정하고 나머지 1개에서 평가했다.',
        '기존 감사/원본은 읽기 전용으로 재사용했다. 전체 데이터 다운로드나 감사 재실행 없이 새 폴더 pilot_rq_261025/에 저장했다.',
        '## R 결과',
        f'기존 RMSE **{rp["distribution"]["RMSE_m"]:.6f} m**, 중앙값 **{rp["distribution"]["median_m"]:.6f} m**를 재현했다. 편향 mean(e)=[{bias[0]:.6f}, {bias[1]:.6f}] m.',
        'R_pair_proxy (m², bias 제거, ddof=0):\n\n```text\n'+np.array2string(np.array(cov),precision=8)+'\n```',
        f'위치 차이 norm p90={rp["distribution"]["p90_m"]:.6f} m, p95={rp["distribution"]["p95_m"]:.6f} m. 편향 없는 Gaussian / 편향 포함 Gaussian / 트랙 bootstrap 경험분포를 LOTO 비교했다. 시간 자기상관·트랙별 편차·시각차 및 거리/가림 진단은 01_r_pilot.md에 있다. 제공 camera 행렬과 투영의 미해결 문제를 보존했으며 이 행렬을 교정하거나 SPD 값을 IMPTC R로 이식하지 않았다.',
        '## Q 및 recorded-trajectory 검증',
        '연속 백색 가속도 CV 모델을 사용한다. q 단위는 m²/s³이며 Q(dt)=q[[dt³/3 I,dt²/2 I],[dt²/2 I,dt I]]다. Data_fitted_Q_KF는 개발 시퀀스의 1초/3초 예측 NLL로 q를 추정한다. 필터 상태 공분산과 미래 관측 R을 포함한 영역을 **기록된 미래 궤적**과 비교했다. 추가 Joint_innovation_ML_KF는 IMPTC 자체 궤적으로 R/q를 함께 추정한 진단 모델이며, 물리적 참값 식별을 뜻하지 않는다.',
        '전체 outer-test 예측 micro. coverage는 0~1 비율, 면적은 m²이며 결정론적 CV의 영역 지표는 N/A:',tab(concise),
        '시퀀스마다 예측 수가 다르므로 아래 sequence macro도 함께 본다:',tab(sm),
        '시퀀스별 원표: [q_sequence_metrics.csv](q_sequence_metrics.csv). 트랙별 원표: [q_track_metrics.csv](q_track_metrics.csv). 모든 모델은 동일 시작점과 두 horizon을 사용했다. 90/95% 포함률과 면적을 함께 보고 과도하게 넓은 영역을 통한 포함률 상승을 구분한다.',
        '관측/평활화 민감도: 인과적 속도 추정 창 0.12/0.4/1.0초를 같은 시작점에 적용했다. q_smoothing_sensitivity.csv에 잔차 공분산·RMSE를 저장했다. 잔차 공분산을 그대로 Q_true라 부르지 않는다. 속도/가감속/정지/방향 변화는 과거 관측에서 계산한 후보이며 조건별 별도 모델을 학습하지 않았다. 신호·날씨 효과·연령·신호 위반은 제외했다.',
        '## 실패와 한계',
        'Gaussian tail QQ, 시퀀스별 포함률과 면적, 서로 다른 트랙의 큰 3초 오차 6사례를 저장했다. 실패 그림의 초록색 미래 궤적은 평가 기준이며 모델 입력이 아니다. 경계값에 붙은 R/q와 optimizer 상태는 q_effective_params.json 및 validation.json에 기록했다. 추적 데이터의 평활화와 측정 잡음이 잔차에 섞여 있어 순수 Q_true나 R_camera를 검증했다고 주장할 수 없다.',
        '## 결과와 재현성',
        '- 상세 R: [01_r_pilot.md](01_r_pilot.md)\n- 상세 Q: [02_q_pilot.md](02_q_pilot.md)\n- 검증: [03_validation.md](03_validation.md), [validation.json](validation.json)\n- 한계: [limitations.md](limitations.md)\n- 입력 매핑: [schema_mismatch.md](schema_mismatch.md)\n- 잔차·분할: ../data/\n- 파라미터: ../models/\n- 그림: ../figures/',
        '실행: 프로젝트 부모 폴더에서 `sbatch pilot_rq_261025/run.sh` 또는 CPU 환경에서 `bash pilot_rq_261025/run.sh`. 정확한 설정은 config.json, 코드/입력/생성 파일 hash는 manifest.json 및 data/input_sha256.json, 라이브러리 버전과 실행 명령은 environment.json에 저장했다. random seed=42. 이미 완료된 폴더에는 재실행해 덮어쓰지 않도록 차단했다.',
        f'수치·공통 평가 표본·인과성·기존 입력 불변성 검증: **{"통과" if checks["passed"] else "실패"}**. 신호 제어/G95/새 원본 다운로드는 수행하지 않았다.'])
    js('environment.json',dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,
        platform=platform.platform(),executable=sys.executable,seed=SEED,elapsed_seconds=time.monotonic()-start,
        command='bash pilot_rq_261025/run.sh (Slurm CPU batch)',plan_sha256=sha(ROOT/'plan.md')))
    (ROOT/'README.md').write_text('# View2Risk R/Q pilot\n\n먼저 reports/pilot_summary.md를 확인한다. 기존 SPD Example와 IMPTC Samples 정제표만 사용한 파일럿이다. 원본/기존 결과는 변경하지 않는다. 모델 파라미터와 평가 출력은 이 폴더 안에만 저장한다.\n')
    js('manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(ROOT).parts and p.name not in ['manifest.json','run.log']})
    print('COMPLETE',json.dumps(clean(checks)),flush=True)


if __name__=='__main__':
    main()
