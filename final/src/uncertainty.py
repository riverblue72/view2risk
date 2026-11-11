import numpy as np
from scipy.special import logsumexp
import contourpy
LEVELS=[.5,.68,.8,.9,.95]

def boundary_value(xy,g,direction):
 z=np.asarray(xy)-g['center'];s=z@np.array(g['axis']);y=z@np.array(g['normal']);end=g['end_B' if direction==1 else 'end_A'];edge=np.interp(y,end['lateral_knots'],end['axial_knots']);return (s-edge)*direction,y

def first_exit(paths,start,times,g,direction):
 p=np.asarray(paths);p=p[None] if p.ndim==2 else p;p=np.concatenate([np.broadcast_to(start,(len(p),1,2)),p],axis=1);tt=np.r_[0,times];b,y=boundary_value(p,g,direction);ans=np.full(len(p),np.nan)
 for i in range(1,p.shape[1]):
  mask=(b[:,i-1]<0)&(b[:,i]>=0)&np.isnan(ans);frac=-b[:,i-1]/np.maximum(b[:,i]-b[:,i-1],1e-12);lat=y[:,i-1]+frac*(y[:,i]-y[:,i-1]);mask&=(lat>=g['lateral_limits'][0])&(lat<=g['lateral_limits'][1]);ans[mask]=tt[i-1]+frac[mask]*(tt[i]-tt[i-1])
 return ans

def gmm_logp(points,means,covs,weights):
 diff=np.asarray(points)[:,None,:]-means;iv=np.linalg.inv(covs);quad=np.einsum('nmi,mij,nmj->nm',diff,iv,diff);logdet=np.linalg.slogdet(covs)[1];return logsumexp(np.log(np.maximum(weights,1e-300))[None]-.5*(2*np.log(2*np.pi)+logdet[None]+quad),axis=1)
