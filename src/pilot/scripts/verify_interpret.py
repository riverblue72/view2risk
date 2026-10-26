"""Independent matrix-KF/OLS cross-checks, then interpretation of frozen predictions."""
from pathlib import Path
import hashlib
import json
import platform
import sys
import numpy as np
import pandas as pd
import numba

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(df):
    rows=[list(df.columns),['---']*len(df.columns)]+list(df.fillna('N/A').itertuples(index=False,name=None))
    return '\n'.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rows)


def reference_filter(t,xy,r,q):
    """Full 4x4 matrices and Joseph updates, independent of optimized scalar KF."""
    m=np.array([xy[0,0],xy[0,1],0.,0.]);P=np.diag([r,r,4.,4.])
    H=np.array([[1.,0.,0.,0.],[0.,1.,0.,0.]])
    R=np.eye(2)*r;I=np.eye(4)
    means=[m.copy()];covs=[P.copy()]
    for k in range(1,len(t)):
        dt=t[k]-t[k-1];F=np.eye(4);F[:2,2:]=np.eye(2)*dt
        Q=q*np.block([[np.eye(2)*dt**3/3,np.eye(2)*dt**2/2],
                      [np.eye(2)*dt**2/2,np.eye(2)*dt]])
        m=F@m;P=F@P@F.T+Q
        S=H@P@H.T+R;K=np.linalg.solve(S,H@P).T
        m=m+K@(xy[k]-H@m)
        J=I-K@H;P=J@P@J.T+K@R@K.T
        means.append(m.copy());covs.append(P.copy())
    return np.array(means),np.array(covs)


def main():
    prior=json.loads((ROOT/'manifest.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in prior.items()),'Original pilot artifact changed before independent verification.'
    d=pd.read_parquet(ROOT/'data/imptc_cv_residuals.parquet')
    q=pd.read_parquet(BASE/'data/processed/stage_samples/imptc_pedestrian_tracks.parquet')
    r=pd.read_parquet(BASE/'data/processed/spd_pedestrian_pairs.parquet')
    params=json.loads((ROOT/'models/q_effective_params.json').read_text())['folds']
    # Reconstruct valid segments without importing any pilot implementation.
    raw_segments={}
    for uid,g in q.groupby('track_uid'):
        g=g.sort_values('source_index');groups=[];current=[];previous=None
        for idx,row in g.iterrows():
            good=int(row.status)==2 and np.isfinite([row.x,row.y,row.z]).all()
            if not good or (previous is not None and not 0<int(row.ts_us)-previous<=60000):
                if current:groups.append(g.loc[current]);current=[]
            if good:current.append(idx);previous=int(row.ts_us)
            else:previous=None
        if current:groups.append(g.loc[current])
        for number,seg in enumerate(groups):raw_segments[uid+f'/seg{number:02d}']=seg.reset_index(drop=True)
    rng=np.random.default_rng(20261025)
    det=d[d.model=='Deterministic_CV']
    spots=det.iloc[rng.choice(len(det),64,replace=False)]
    max_ols_error=0.
    for _,row in spots.iterrows():
        g=raw_segments[row.segment_id];us=g.ts_us.to_numpy(np.int64)
        i=int(np.where(us==row.anchor_ts_us)[0][0]);j=int(np.where(us==row.future_ts_us)[0][0])
        t=(us-us[0])/1e6;past=(t>=t[i]-.4-1e-9)&(t<=t[i])
        X=np.column_stack((t[past]-t[i],np.ones(past.sum())))
        v=np.linalg.lstsq(X,g.loc[past,['x','y']].to_numpy(),rcond=None)[0][0]
        pred=g.loc[i,['x','y']].to_numpy(dtype=float)+(t[j]-t[i])*v
        diff=float(np.max(np.abs(pred-[row.predicted_x_m,row.predicted_y_m])))
        max_ols_error=max(max_ols_error,diff)
        assert diff<1e-9
        assert np.allclose(g.loc[j,['x','y']].to_numpy(dtype=float),[row.GT_recorded_x_m,row.GT_recorded_y_m],atol=1e-12)
    max_kf_mean_error=0.;max_kf_cov_error=0.;checked=0
    # 4 sequences x 3 stochastic models x 2 horizons, each at an actual held-out origin.
    for sequence in sorted(q.sequence_id.unique()):
        for model in ['Fixed_noise_KF','Data_fitted_Q_KF','Joint_innovation_ML_KF']:
            candidates=d[(d.sequence_id==sequence)&(d.model==model)&(d.horizon_s==3.)]
            row=candidates.iloc[len(candidates)//2];g=raw_segments[row.segment_id]
            us=g.ts_us.to_numpy(np.int64);t=(us-us[0])/1e6;xy=g[['x','y']].to_numpy()
            i=int(np.where(us==row.anchor_ts_us)[0][0]);pr=params[sequence][model]
            means,covs=reference_filter(t[:i+1],xy[:i+1],pr['r_m2'],pr['q_m2_s3'])
            for _,rr in d[(d.anchor_id==row.anchor_id)&(d.model==model)].iterrows():
                h=rr.actual_horizon_s;F=np.eye(4);F[:2,2:]=np.eye(2)*h
                pred=(F@means[-1])[:2]
                S=(F@covs[-1]@F.T)[:2,:2]+np.eye(2)*(pr['q_m2_s3']*h**3/3+pr['r_m2'])
                me=float(np.max(np.abs(pred-[rr.predicted_x_m,rr.predicted_y_m])))
                ce=float(np.max(np.abs(S-np.eye(2)*rr.position_variance_m2)))
                max_kf_mean_error=max(max_kf_mean_error,me);max_kf_cov_error=max(max_kf_cov_error,ce)
                assert me<1e-8 and ce<1e-9;checked+=1
    # Entire output: independent chi-square(df=2) quantile via closed form.
    probabilistic=d[d.model!='Deterministic_CV']
    error2=(probabilistic.GT_recorded_x_m-probabilistic.predicted_x_m)**2+(probabilistic.GT_recorded_y_m-probabilistic.predicted_y_m)**2
    assert np.allclose(error2,probabilistic.error_m**2,atol=1e-12)
    for level in [90,95]:
        cut=-2*np.log1p(-level/100)
        coverage=(error2<=cut*probabilistic.position_variance_m2).astype(float)
        assert np.array_equal(coverage,probabilistic[f'covered{level}'])
        assert np.allclose(np.pi*cut*probabilistic.position_variance_m2,probabilistic[f'area{level}_m2'],rtol=1e-12)
    all_metrics=pd.read_csv(ROOT/'reports/q_overall_metrics.csv')
    for _,row in all_metrics.iterrows():
        g=d[(d.model==row.model)&(d.horizon_s==row.horizon_s)]
        assert abs(np.sqrt(np.mean(g.error_m**2))-row.RMSE_m)<1e-12
        assert abs(g.error_m.mean()-row.MAE_m)<1e-12
    residual=r[['camera_world_x','camera_world_y']].to_numpy()-r[['lidar_world_x','lidar_world_y']].to_numpy()
    rp=json.loads((ROOT/'models/r_pair_proxy_params.json').read_text())
    assert np.allclose(residual.mean(axis=0),rp['bias_m'],atol=1e-12)
    assert np.allclose(np.cov(residual.T,ddof=0),rp['R_pair_proxy_m2'],atol=1e-12)
    for test,fit in params.items():assert test not in fit['development_sequences']
    inputs=json.loads((ROOT/'data/input_sha256.json').read_text())
    assert all(sha(BASE/p)==h for p,h in inputs.items())
    results=dict(passed=True,OLS_spots=64,full_matrix_KF_forecasts_checked=checked,
        max_OLS_position_difference_m=max_ols_error,max_KF_position_difference_m=max_kf_mean_error,
        max_KF_covariance_difference_m2=max_kf_cov_error,
        all_probabilistic_coverage_and_area_independently_recomputed=True,
        all_overall_point_metrics_independently_recomputed=True,
        R_mean_covariance_independently_recomputed=True,
        frozen_predictions_params_original_inputs_unchanged=True)
    (ROOT/'reports/independent_validation.json').write_text(json.dumps(results,indent=2)+'\n')
    # Interpret frozen test results; no fitting or evaluation criteria change here.
    learned=all_metrics[all_metrics.model=='Data_fitted_Q_KF'].sort_values('horizon_s')
    fixed=all_metrics[all_metrics.model=='Fixed_noise_KF'].sort_values('horizon_s')
    joint=all_metrics[all_metrics.model=='Joint_innovation_ML_KF'].sort_values('horizon_s')
    detm=all_metrics[all_metrics.model=='Deterministic_CV'].sort_values('horizon_s')
    seq=pd.read_csv(ROOT/'reports/q_sequence_metrics.csv')
    seqfit=seq[seq.model=='Data_fitted_Q_KF'][['sequence_id','horizon_s','test_tracks','predictions','RMSE_m','coverage90','coverage95','mean_area95_m2']]
    excluded=sorted(set(q.track_uid)-set(d.track_uid))
    inv=pd.read_csv(ROOT/'reports/q_segment_inventory.csv');excluded_inv=inv[inv.track_uid.isin(excluded)]
    sdf=pd.read_csv(ROOT/'reports/q_smoothing_sensitivity.csv')
    smoothing=sdf.groupby(['horizon_s','causal_window_s'])[['RMSE_m','residual_cov_xx_m2','residual_cov_yy_m2','naive_effective_q_trace_proxy_m2_s3']].mean().reset_index()
    rtrack=pd.read_csv(ROOT/'reports/r_track_summary.csv');rpred=pd.read_parquet(ROOT/'data/r_holdout_predictions.parquet')
    rmacro=rpred.groupby(['model','track_uid'])[['covered90','covered95','area95_m2']].mean().groupby('model').mean().reset_index()
    rmicro=rpred.groupby('model')[['covered90','covered95','area95_m2']].mean().reset_index()
    ar=[]
    for h in [1.,3.]:
        a=learned[learned.horizon_s==h].iloc[0];b=fixed[fixed.horizon_s==h].iloc[0];c=joint[joint.horizon_s==h].iloc[0];dc=detm[detm.horizon_s==h].iloc[0]
        ar.append(f'- **{h:g}초:** deterministic CV RMSE {dc.RMSE_m:.4f} m → Q-fitted KF {a.RMSE_m:.4f} m. 목표 95% 영역의 실제 포함률 **{100*a.coverage95:.2f}%**, 목표와 차이 {100*(a.coverage95-.95):+.2f}%p, 평균 면적 **{a.mean_area95_m2:.4f} m²**. Fixed-noise는 {100*b.coverage95:.2f}% / {b.mean_area95_m2:.4f} m²로 더 넓은 영역이다. Joint innovation-ML은 점 RMSE {c.RMSE_m:.4f} m이지만 포함률 {100*c.coverage95:.2f}% / 면적 {c.mean_area95_m2:.4f} m²로 과신한다.')
    pieces=['## 실제 수치에 따른 해석 및 독립 재검증',
        '파일럿 계산은 성립하지만 **95% 예측영역이 실제로 95%를 포함하도록 보정됐다고 보기는 어렵다.** 아래는 고정한 홀드아웃 예측을 해석한 결과이며 Test를 보고 설정을 변경하지 않았다.',
        '\n'.join(ar),
        'Q-fitted 모델은 fixed-noise보다 영역이 작지만 특히 3초에서 포함률이 낮다. 이 표만으로 어느 모델이 최종적으로 우수하다고 선정하지 않는다. Joint innovation-ML의 점 예측 개선은 확률분포의 적절성을 뜻하지 않는다. 단기 likelihood에 맞춘 값으로 장기 예측 불확실성이 과소평가될 수 있음을 보여준다.',
        'Joint innovation-ML의 관측 분산 R은 모든 fold에서 설정한 하한 1e-8 m²에 도달했다. 이는 평활화된 기록 궤적과 현재 모델에서 나온 최적화 경계 결과이며 실제 센서 오차가 거의 0이라는 증거가 아니다. 이식 가능한 R/Q의 고유 식별로 해석하지 않는다.',
        '### Q-fitted 모델의 시퀀스별 결과',table(seqfit),
        '### 평가 분모',
        f'유효 연속 구간은 총 87개다. 61트랙 중 **60트랙**에서 1초 과거 + 3초 미래를 동시에 확보했다. 8,688개 공통 시작점 × 2 horizons × 4 models = 69,504개 예측이다. 제외 트랙 {", ".join(excluded)}은 status=2 구간이 아래처럼 짧게 나뉘어 3초 미래를 확보할 수 없다. 해당 트랙의 존재와 유효 관측은 보존했고, 1초/3초 공통 평가에서만 제외했다.',table(excluded_inv),
        '### 평활화/관측 표현에 대한 민감도',table(smoothing),
        '이 표는 시퀀스별 값의 macro 평균이다. 과거 속도 추정 창에 따라 잔차 공분산과 단순 q scale이 달라진다. 동일 관측에서 추정한 값이므로 측정 잡음, 기록 전처리와 움직임을 분리한 실험은 아니다. 실제 모델 q는 models/q_effective_params.json의 개발 세트 추정치이며 위 단순 scale과 구분한다.',
        '### R의 실질 표본 크기와 LOTO 해석',
        f'9트랙 중 가장 긴 2트랙이 **{int(rtrack.pairs.nlargest(2).sum())}/253 = {100*rtrack.pairs.nlargest(2).sum()/253:.2f}%**의 pair를 차지한다. 나머지 중에는 1–2쌍뿐인 트랙이 있어 트랙-macro 포함률도 변동이 크다. bias와 공분산은 한 시퀀스의 paired annotation 설명치다. 추가 R 데이터에서는 독립적인 시퀀스·교차로 및 모델 예측 대 기준 라벨을 우선 확보할 필요가 있다.',
        'R LOTO pair-micro:',table(rmicro),'R LOTO track-macro:',table(rmacro),
        '### 독립 수치 검증',
        f'별도 구현한 4×4 행렬 Kalman filter와 Joseph 공분산 갱신으로 실제 홀드아웃 예측 {checked}개를 대조했다. 위치 최대 차이 {max_kf_mean_error:.3g} m, 공분산 최대 차이 {max_kf_cov_error:.3g} m². 과거 OLS 속도는 독립 최소제곱으로 64개를 대조했다. 전체 확률 예측의 포함 여부·면적과 전체 RMSE/MAE도 별도로 재계산해 통과했다. 기존 입력과 고정된 파라미터·예측 파일의 hash도 일치한다.',
        '이 재검증은 계산의 일관성 확인이다. 실측 GT에 대한 모델 타당성이나 일반화 확인을 대신하지 않는다.']
    interpretation='\n\n'.join(pieces)+'\n'
    target=ROOT/'reports/04_interpretation.md'
    assert not target.exists(),'Do not duplicate completed interpretation.'
    target.write_text('# 해석 및 독립 재검증\n\n'+interpretation)
    with (ROOT/'reports/pilot_summary.md').open('a') as stream:stream.write('\n'+interpretation)
    with (ROOT/'reports/03_validation.md').open('a') as stream:stream.write('\n## Independent implementation verification\n\n'+json.dumps(results,indent=2)+'\n')
    env=json.loads((ROOT/'environment.json').read_text());env['numba']=numba.__version__
    env['commands']=['sbatch pilot_rq_261025/run.sh',
        '/data/whereami/envs/lesionlocator/bin/python pilot_rq_261025/scripts/verify_interpret.py']
    (ROOT/'environment.json').write_text(json.dumps(env,ensure_ascii=False,indent=2)+'\n')
    # Final inventory is regenerated after interpretation; exclude transient log/cache files.
    artifact={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(ROOT).parts and p.name not in ['manifest.json','run.log']}
    (ROOT/'manifest.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(results),flush=True)


if __name__=='__main__':main()
