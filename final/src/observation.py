from core import *
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_continuous_white_noise
CFG=read(V/'configs/r_proxy.json');COV=np.asarray(CFG['train_fit']['covariance_m2']);BIAS=np.asarray(CFG['train_fit']['bias_m'])
def perturb(x,seed,kind='iid'):
 rng=np.random.default_rng(seed);e=rng.multivariate_normal([0,0],COV,len(x))
 if kind=='correlated':
  for k in range(1,len(e)):e[k]=.8*e[k-1]+np.sqrt(1-.8**2)*e[k]
 y=x+BIAS+e
 if kind=='dropout':y[-4:]=np.nan # last 0.4s missing
 return y

def posterior_histories(y,seed=31,n=8,q=.5):
 k=KalmanFilter(dim_x=4,dim_z=2);k.F=np.array([[1,0,.1,0],[0,1,0,.1],[0,0,1,0],[0,0,0,1.]])
 k.H=np.array([[1,0,0,0],[0,1,0,0.]]);k.R=COV.copy();k.Q=Q_continuous_white_noise(dim=2,dt=.1,spectral_density=q,block_size=2,order_by_dim=False);k.x=np.zeros(4);k.P=np.diag([1e6,1e6,25,25]);xf=[];pf=[];xp=[];pp=[]
 for i,z in enumerate(y):
  if i:k.predict()
  xp.append(k.x.copy());pp.append(k.P.copy())
  k.update(z-BIAS if np.isfinite(z).all() else None);xf.append(k.x.copy());pf.append(k.P.copy())
 xf=np.array(xf);pf=np.array(pf);xp=np.array(xp);pp=np.array(pp)
 def psd(a):a=(a+a.T)/2;w,u=np.linalg.eigh(a);return (u*np.maximum(w,1e-10))@u.T
 rng=np.random.default_rng(seed);paths=np.empty((n,len(y),4));paths[:,-1]=rng.multivariate_normal(xf[-1],psd(pf[-1]),n);mean=xf.copy()
 for t in range(len(y)-2,-1,-1):
  J=pf[t]@k.F.T@np.linalg.inv(pp[t+1]);cov=psd(pf[t]-J@pp[t+1]@J.T);paths[:,t]=xf[t]+(paths[:,t+1]-xp[t+1])@J.T+rng.multivariate_normal(np.zeros(4),cov,n);mean[t]=xf[t]+J@(mean[t+1]-xp[t+1])
 return mean[:,:2],paths[:,:,:2],dict(filtered_state=xf[-1].tolist(),filtered_covariance=pf[-1].tolist(),observed_points=int(np.isfinite(y).all(1).sum()),filter_q_m2_s3=q,history_sampling='FFBS joint posterior over past states; no framewise independent draws',filter_R=COV.tolist())
