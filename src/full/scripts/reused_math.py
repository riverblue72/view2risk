import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import chi2
LEVELS={90:float(chi2.ppf(.90,2)),95:float(chi2.ppf(.95,2))}


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)): return [clean(v) for v in x]
    if isinstance(x, np.ndarray): return clean(x.tolist())
    if isinstance(x, np.generic): return clean(x.item())
    if isinstance(x, float) and not np.isfinite(x): return None
    return x


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


def metrics(g):
    return dict(test_sequences=g.sequence_id.nunique(),test_tracks=g.track_uid.nunique(),predictions=len(g),
        RMSE_m=np.sqrt(np.mean(g.error_m**2)),MAE_m=g.error_m.mean(),p95_error_m=g.error_m.quantile(.95),max_error_m=g.error_m.max(),
        coverage90=g.covered90.mean(),coverage95=g.covered95.mean(),mean_area90_m2=g.area90_m2.mean(),mean_area95_m2=g.area95_m2.mean(),
        mean_radius95_m=g.radius95_m.mean(),NLL=g.NLL.mean())


def metric_table(data,keys):
    return pd.DataFrame([dict(zip(keys,k if isinstance(k,tuple) else (k,)),**metrics(g)) for k,g in data.groupby(keys,dropna=False,sort=True)])


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
