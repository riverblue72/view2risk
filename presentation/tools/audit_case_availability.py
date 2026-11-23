#!/usr/bin/env python3
"""Read-only audit of public replay availability; no inference / GT generation."""
import csv, hashlib, json, pathlib, sys, collections
ROOT=pathlib.Path(__file__).resolve().parents[2]
SITE=ROOT/'presentation/site'
OUT=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'presentation/ux-evidence')
OUT.mkdir(parents=True,exist_ok=True)
sources={}
def load(path):
 p=SITE/path;sources[path]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def exact(a,b):return a['event_id']==b['event_id'] and a['origin_s']==b['origin_s']
cat=load('data/inference.json');aft=load('data/public/exit-aware.json');ri=load('data/public/r-index.json');ev=load('data/public/demo-evidence.json');cond=load('data/public/ui-completion.json')
rows=[];all_origins=[]
for entry in cat['cases']:
 assert entry['dataset']=='IMPTC'
 c=load(entry['file']);assert c['event_id']==entry['event_id'] and c['dataset']==entry['dataset']
 for f in c['forecasts']:
  key={'event_id':c['event_id'],'origin_s':f['origin_s']};a=next((x for x in aft['cases'] if exact(x,key)),None);ridx=next((x for x in ri if exact(x,key)),None);r=load('data/public/r/'+ridx['file']) if ridx else None
  if r:
   assert exact(r,key);assert r['future_GT_xy']==f['future_GT_xy']
  clean=f['conditions']['clean'];all_origins.append({**key,'uid':a['uid'] if a else None,'aft_saved':bool(a),'r_saved':bool(r),'features_saved':any(exact(x,key) for x in ev['cases'])})
  for h in range(1,5):
   ex=clean.get('exit',{});p=(ex.get('probabilities') or {}).get(str(h));p=ex.get('model_probability_4s') if p is None and h==4 else p
   y=(ex.get('GT_by_horizon') or {}).get(str(h));y=(a.get('GT',{}).get(str(h)) if a else None) if y is None else y;y=ex.get('GT_within4s') if y is None and h==4 else y
   y=int(y) if y is not None and y in (0,1,True,False) else None
   ap=a['cdf']['EA_M1__calibrated'][a['grid_s'].index(h)] if a else None
   if a and p is not None:assert abs(p-a['cdf']['DDMDN'][a['grid_s'].index(h)])<1e-9
   all_r=bool(r) and all((r['results'].get(k,{}).get('exit',{}).get('probabilities') or {}).get(str(h)) is not None for k in ['clean']+[s+'__'+m for s in ['iid_0.5','iid_1','iid_2'] for m in ['noisy','filtered_mean','rq']])
   eligible=y is not None and not ex.get('already_beyond_exit',False)
   row={'dataset':'IMPTC',**key,'uid':a['uid'] if a else None,'horizon_s':h,'dd_probability':p,'aft_m1_probability':ap,'outcome':y,'outcome_eligible':eligible,'r_complete':all_r,'guided_eligible':eligible and p is not None and ap is not None and all_r,'features_saved':bool(a),'prediction_not_saved':not bool(a),'noise_not_run':not bool(r),'gt_unknown':y is None,'dd_horizon_not_saved':p is None}
   rows.append(row)
with (OUT/'availability_by_origin_horizon.csv').open('w') as fp:
 w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary={'status':'PASSED','public_origins':len(all_origins),'events':len(cat['cases']),'aft_origins':sum(x['aft_saved'] for x in all_origins),'r_origins':sum(x['r_saved'] for x in all_origins),'guided_uids':sorted(set(x['uid'] for x in rows if x['guided_eligible'])),'by_horizon':[{ 'horizon_s':h,'guided':sum(x['guided_eligible'] for x in rows if x['horizon_s']==h),'known_gt':sum(x['outcome'] is not None for x in rows if x['horizon_s']==h),'dd_probability_saved':sum(x['dd_probability'] is not None for x in rows if x['horizon_s']==h)} for h in range(1,5)],'missing_aft_origins':sum(not x['aft_saved'] for x in all_origins),'missing_r_origins':sum(not x['r_saved'] for x in all_origins),'source_hashes':sources}
assert summary['guided_uids']==['o0000','o0008','o0011'];(OUT/'availability_audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='source_hashes'},indent=2))
