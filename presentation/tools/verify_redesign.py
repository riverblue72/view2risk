"""Read-only artifact consistency checks for the synchronized public demonstration."""
from pathlib import Path
import json,hashlib,subprocess,sys
root=Path(__file__).resolve().parents[2];site=root/'presentation/site';p=site/'data/public'
rd=lambda q:json.loads(q.read_text())
same=lambda a,b:a['event_id']==b['event_id'] and abs(a['origin_s']-b['origin_s'])<1e-6
index=rd(site/'data/inference.json');ea=rd(p/'exit-aware.json')['cases'];cond=rd(p/'ui-completion.json')['cases'];ri=rd(p/'r-index.json');evidence=rd(p/'demo-evidence.json')['cases']
checks=[];origins=0;matched_aft=0;matched_r=0;all_results=0
for row in index['cases']:
 c=rd(site/row['file']);assert c['dataset']=='IMPTC'
 for f in c['forecasts']:
  origins+=1;key={'event_id':c['event_id'],'origin_s':f['origin_s']};r=f['conditions']['clean'];assert r['input']['latest_input_source_ts']<=f['origin_s']+1e-6
  a=next((x for x in ea if same(x,key)),None);q=next((x for x in ri if same(x,key)),None)
  if a:
   matched_aft+=1
   for h in range(1,5):
    assert abs(a['cdf']['DDMDN'][h*20]-r['exit']['probabilities'][str(h)])<1e-9
    labels=[x for x in [a['GT'].get(str(h)),r['exit'].get('GT_by_horizon',{}).get(str(h))] if x is not None];assert len(set(labels))<=1
   for model,curve in a['cdf'].items():assert len(curve)==81 and all(0<=x<=1 for x in curve) and all(y+1e-12>=x for x,y in zip(curve,curve[1:]))
  if q:
   matched_r+=1;packet=rd(p/'r'/q['file']);assert same(packet,key) and packet['future_GT_xy']==f['future_GT_xy']
   for mode,res in packet['results'].items():
    all_results+=1;assert res['input']['latest_input_source_ts']<=key['origin_s']+1e-6
    for h in range(1,5):
     y=res['exit']['GT_by_horizon'].get(str(h));base=r['exit']['GT_by_horizon'].get(str(h));assert y==base
     assert 0<=res['exit']['probabilities'][str(h)]<=1
    assert all(len(res['regions'])==8 for _ in [0])
for x in evidence:
 assert all(t<=x['origin_s']+1e-6 for s in x['samples'] for t in s['support_timestamps'])
# Original artifact bytes, not only numerical summaries, must remain unchanged.
protected=['final','docs/final','presentation/site/data','presentation/site/condition','presentation/site/r_robustness','presentation/site/xgb_aft','presentation/site/exit_aware','presentation/site/pres/evidence.json','presentation/site/pres/PRESENTATION_METRIC_AUDIT.md','presentation/site/demo/method_sources.json','presentation/site/ui/aggregate.json']
changes=subprocess.check_output(['git','diff','HEAD','--name-only','--',*protected],cwd=root,text=True).splitlines();assert not changes,changes
out={'status':'PASSED','public_events':len(index['cases']),'saved_origins':origins,'matched_aft_origins':matched_aft,'matched_r_origins':matched_r,'r_scenario_method_packets':all_results,'conditional_aft_origins':len(cond),'protected_artifact_modifications':changes,'checks':['exact event/origin joins','identical future XY and horizon GT across matched modes','DD completion probabilities agree with saved CDF','CDF values in [0,1] and monotonic','input source timestamps at or before origin','all original saved artifacts unchanged','no inference or fitting executed']}
print(json.dumps(out,indent=2))
if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(out,indent=2))
