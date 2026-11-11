from pathlib import Path
import sys,os,json,hashlib,gzip,random
V=Path(os.environ.get('VIEW2RISK_WORKDIR',Path(__file__).resolve().parents[1]));R=V.parent
UPSTREAM=Path(os.environ['DDMDN_REPO']);MODEL_ROOT=Path(os.environ['DDMDN_MODEL_ROOT'])
sys.path[:0]=[str(V/'deps'),str(V/'vendor/drone-dataset-tools/src'),str(R/'src'),str(UPSTREAM/'framework'),str(UPSTREAM/'framework/ddmdn'),str(UPSTREAM/'framework/datasets')]
os.environ['CUDA_VISIBLE_DEVICES']=''
import numpy as np,torch
from misc import Config_Setup,build_mesh_grid
from ddmdn.model import DDMDN
from types import SimpleNamespace
from uncertainty import gmm_logp,first_exit

def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple,np.ndarray)):return [clean(v) for v in x]
 if isinstance(x,np.generic):return clean(x.item())
 if isinstance(x,float) and not np.isfinite(x):return None
 return x

def save(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(clean(d),ensure_ascii=False,allow_nan=False).encode();tmp=Path(str(p)+'.tmp');tmp.write_bytes(gzip.compress(b) if p.suffix=='.gz' else b);tmp.replace(p)
def read(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(dataset):
 torch.set_num_threads(2);random.seed(31);np.random.seed(31);torch.manual_seed(31)
 args=SimpleNamespace(cfg=f'full/{dataset}_full.json',gpu='',bar=False);setattr(args,'print',False)
 cfg=Config_Setup(args,'test',str(MODEL_ROOT));model=DDMDN(cfg);p=MODEL_ROOT/f'full/{dataset}_full/checkpoints/model_weights_best.pt';ck=torch.load(p,map_location='cpu',weights_only=False);model.load_state_dict(ck['model'],strict=True);model.eval()
 for par in model.parameters():par.requires_grad_(False)
 _,xx,yy=build_mesh_grid(cfg.grid.size_meter,cfg.grid.size_meter,cfg.full_grid_resolution)
 save(V/f'reports/{dataset}_checkpoint.json',dict(status='PASSED',sha256=sha(p),path=str(p),input_positions=cfg.input_horizon,input_dt=cfg.common.input_delta_t,output_times=(np.array(cfg.output_horizons)+1)*cfg.common.input_delta_t,strict_load=True,training=False))
 return cfg,model,ck['annealing_status'],torch.stack([xx,yy],0)

def forward(model,cfg,ann,past,grid,mask,seed=31,gt=None):
 torch.manual_seed(seed)
 if gt is None:gt=torch.zeros((len(past),past.shape[1],cfg.len_forecast_horizon,4))
 with torch.inference_mode():out,ok=model(past,gt,grid,mask,ann['mode_prune_delta'],ann['mode_prune_tau'],ann['top_p_trunc'])
 if not ok:raise ValueError('Official model returned unsuccessful mixture')
 return out
