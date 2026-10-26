from pathlib import Path
import csv,json,hashlib,os
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
os.environ['TMPDIR']=str(ROOT/'tmp')
def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def js(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def csvw(p,rows,fields=None):
    rows=list(rows);fields=fields or list(dict.fromkeys(k for r in rows for k in r));p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else clean(v) for k,v in r.items()})
def stats(a):
    a=np.asarray(a,dtype=float);a=a[np.isfinite(a)]
    if not len(a):return dict(n=0)
    return dict(n=len(a),mean=a.mean(),std=a.std(),median=np.median(a),p05=np.quantile(a,.05),p95=np.quantile(a,.95),min=a.min(),max=a.max())
def table(rows,fields):
    def fmt(x):
        if isinstance(x,float):return f'{x:.4f}'
        return str(x).replace('|','/')
    return '\n'.join(['| '+' | '.join(fields)+' |','| '+' | '.join(['---']*len(fields))+' |',*['| '+' | '.join(fmt(r.get(k,'')) for k in fields)+' |' for r in rows]])
