"""Allowlisted IMPTC-only public presentation export. No training or inference.
Usage: python export_site.py PRIVATE_PROJECT EMPTY_EXPORT_DIRECTORY
"""
from pathlib import Path
import sys,json,gzip,copy,re,hashlib,shutil,math
from collections import Counter
V=Path(sys.argv[1]);O=Path(sys.argv[2]);S=V/'website';assert not O.exists();O.mkdir(parents=True)
def rd(p):
 b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def wr(p,x):
 p=O/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,separators=(',',':')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
REMOVE={'source_path','source_paths','raw_sources','sources','source_hashes','private_paths','input_file','checkpoint_path','model_path','raw_path','source_csv','source_json','finite_first_exit_s'}
def scrub(x,zero=0,aliases=None):
 aliases=aliases or {}
 if isinstance(x,dict):
  out={}
  for k,v in x.items():
   if k in REMOVE or k.startswith('/data/') or k.startswith('/Users/'):continue
   if k in {'sequence','recording','recording_id','track_uid','track_id','date'} and aliases:v=aliases.get(str(v),'public-recording' if k!='date' else 'date-redacted')
   out[k]=scrub(v,zero,aliases)
  return out
 if isinstance(x,list):return [scrub(v,zero,aliases) for v in x]
 if isinstance(x,(float,int)) and not isinstance(x,bool):
  if not math.isfinite(x):return None
  return x-zero if zero and 1.5e9<float(x)<2e9 else x
 if isinstance(x,str):
  if x in aliases:return aliases[x]
  x=re.sub(r'/data/whereami/[^\s\)\]<>"\x27`]+','[private-source]',x)
  x=re.sub(r'/Users/[^\s\)\]<>"\x27`]+','[local-path]',x)
  for a,b in aliases.items():x=x.replace(a,b)
  return x
 return x
ci=rd(V/'condition_uq_20261121/private/viewer_index.json');ev=rd(V/'interactive_demo_20261122/private/evidence.json');ea=rd(V/'exit_aware_20261122/private/viewer.json');ri=rd(V/'r_robustness_20261121/private/index.json')
preset=next(x for x in ea['cases'] if x['uid']=='o0008');selected=[preset['event_id']]
for cw in ['f1','f3']:
 event=next(x['event_id'] for x in ev['cases'] if x['crosswalk']==cw and any(z['event_id']==x['event_id'] for z in ci));selected.append(event)
aliases={event:f'public-imptc-{i+1:02d}' for i,event in enumerate(selected)};zeros={};case_files={};provenance=[]
for event in selected:
 c=next(x for x in ci if x['event_id']==event);src=V/'condition_uq_20261121/private'/c['file'];d=rd(src);assert d['dataset']=='IMPTC';zero=d['origin0_s'];zeros[event]=zero;pid=aliases[event];m={event:pid,str(d['track_uid']):pid+'-target',str(d['sequence']):pid}
 out=scrub(d,zero,m);out['origin0_s']=0;out['date']='date-redacted';out['data_kind']='actual_precomputed_DDMDN_output';out['license']='CC-BY-NC-4.0';out['source']='https://zenodo.org/records/14811016'
 for j,n in enumerate(out.get('neighbors',[])):n['id']=f'neighbor-{j+1}'
 wr(Path('data/public/cases')/(pid+'.json'),out);case_files[event]='data/public/cases/'+pid+'.json'
 provenance.append({'id':pid,'dataset':'IMPTC','source_sha256':sha(src),'forecast_origins':[p['elapsed_s'] for p in out['forecasts']],'license':'CC-BY-NC-4.0'})
# Main catalog includes only the selected licensed IMPTC excerpts.
idx=rd(S/'data/inference.json');idx={k:v for k,v in idx.items() if k!='cases'};idx=scrub(idx);idx['cases']=[]
public_ci=[]
for event in selected:
 c=next(x for x in ci if x['event_id']==event);r=scrub(c,zeros[event],aliases);r['file']=case_files[event];idx['cases'].append({**r,'track_uid':aliases[event]+'-target'});public_ci.append(r)
wr(Path('data/inference.json'),idx);wr(Path('data/public/condition-index.json'),public_ci)
# Preserve only exact selected-event records in API replacements.
for src,target in [('interactive_demo_20261122/private/evidence.json','demo-evidence'),('exit_aware_20261122/private/viewer.json','exit-aware'),('website_redesign_20261122/private/completion.json','ui-completion'),('xgb_aft_20261121/private/viewer.json','aft-clearance')]:
 d=rd(V/src);out={k:scrub(v) for k,v in d.items() if k not in {'cases','explorer','sources','raw_sources'}};out['cases']=[scrub(c,zeros[c['event_id']],aliases) for c in d['cases'] if c['event_id'] in selected]
 if 'explorer' in d:out['explorer']=[scrub(c,zeros.get(c.get('event_id'),0),aliases) for c in d['explorer'] if c.get('event_id') in selected or c.get('uid') in {x['uid'] for x in out['cases']}]
 wr(Path('data/public')/(target+'.json'),out)
# One actually evaluated R origin per selected event; preserve same-origin packet, all saved scenarios.
public_ri=[]
for event in selected:
 r=next(x for x in ri if x['event_id']==event and (x['uid']=='o0008' if event==preset['event_id'] else True));src=V/'r_robustness_20261121/private'/r['file'];d=rd(src);assert d['dataset']=='IMPTC';rr=scrub(r,zeros[event],aliases);rr['file']=r['uid']+'.json';public_ri.append(rr);d=scrub(d,zeros[event],aliases);d.pop('file',None);wr(Path('data/public/r')/rr['file'],d)
wr(Path('data/public/r-index.json'),public_ri)
# Static UI and aggregate assets. No original per-origin CSVs or data catalogs copied.
json_allow={'data/results.json','data/exploratory.json','ui/aggregate.json','pres/evidence.json','demo/method_sources.json','condition/condition_uq_summary.json','r_robustness/r_robustness_summary.json','xgb_aft/xgb_aft_summary.json','exit_aware/exit_aware_summary.json'}
api={'/api/demo-evidence':'data/public/demo-evidence.json','/api/exit-aware':'data/public/exit-aware.json','/api/ui-completion':'data/public/ui-completion.json','/api/aft-clearance':'data/public/aft-clearance.json','/api/condition-index':'data/public/condition-index.json','/api/r-index':'data/public/r-index.json','/api/r-origin/':'data/public/r/','/api/condition-case/':'','/api/case/':'data/public/cases/','/api/background/':'assets/ind-unavailable.svg?recording='}
for p in S.rglob('*'):
 if not p.is_file() or p.suffix=='.gz':continue
 rel=str(p.relative_to(S));allowed=False
 if rel in json_allow:
  d=rd(p)
  if rel=='data/results.json':
   d={k:d[k] for k in ['official','position_comparison','exit_evaluation','subgroups','pedpy','limitations','R_proxy','checkpoints'] if k in d}
   for c in d.get('checkpoints',{}).values():c.pop('path',None)
  if rel=='xgb_aft/xgb_aft_summary.json' and isinstance(d.get('eligibility'),dict):
   removed=d['eligibility'].pop('exclusions',[])
   d['eligibility']['excluded_record_count']=len(removed)
   d['eligibility']['excluded_reasons']=dict(Counter(str(x.get('reason','unspecified')) for x in removed))
  wr(Path(rel),scrub(d));continue
 if p.suffix in {'.js','.html','.css'} and (len(p.relative_to(S).parts)==1 or p.relative_to(S).parts[0] in {'pres','ui','demo','assets'}):allowed=True
 if p.suffix=='.png':allowed=True
 if rel.startswith('assets/katex/') and p.suffix in {'.woff','.woff2','.ttf'}:allowed=True
 if p.suffix=='.md':allowed=True
 if p.suffix=='.csv' and ('metrics' in p.name or p.name=='exit_coverage_aggregate.csv'):allowed=True
 if not allowed:continue
 q=O/rel;q.parent.mkdir(parents=True,exist_ok=True)
 if p.suffix in {'.js','.html','.css','.md','.csv'}:
  s=scrub(p.read_text())
  for a,b in api.items():s=s.replace(a,b)
  # Site-root links become deployment-directory-relative, including scripts and iframes.
  s=re.sub(r'(["\x27`])/(?!/)(?=[A-Za-z?#])',r'\1./',s)
  s=s.replace('PRIVATE RESEARCH VIEWER','PUBLIC RESEARCH DEMO').replace('Private IMPTC / licensed inD viewer','Public IMPTC excerpt · inD aggregate-only').replace('Private completion artifact unavailable','Saved public completion artifact unavailable')
  if p.suffix=='.html':s=s.replace('</head>','<script defer src="public-notice.js"></script></head>')
  s=s.replace('AFT_DATA.cases.map(x=>`<option','AFT_DATA.cases.filter(x=>R_INDEX.some(r=>r.uid===x.uid)).map(x=>`<option')
  s=s.replace('source: private data/public/demo-evidence.json → ${ue(e.source_path)}','source: data/public/demo-evidence.json (allowlisted public excerpt)')
  if p.suffix=='.html':s=s.replace('</head>','<link rel="icon" href="data:,"></head>')
  s=s.replace('assets/modeling/data/results.json','data/results.json').replace('assets/modeling/data/exploratory.json','data/exploratory.json')
  s=s.replace('href="data/origins.csv" target="_blank">전체 origin CSV','href="data/public/provenance.json" target="_blank">공개 사례 origin / provenance JSON')
  q.write_text(s)
 else:shutil.copy2(p,q)
# Condition loader sometimes prepends an API prefix; catalog paths are already static.
# Model selection remains Q-only. Public inD replay is absent by construction.
notice="""document.addEventListener('DOMContentLoaded',()=>{const n=document.createElement('div');n.id='public-data-note';n.style.cssText='padding:7px 16px;background:#e7eff5;color:#24455d;font:13px sans-serif;line-height:1.5';n.innerHTML='Public research demo · 실제 저장 DD-MDN 출력 · IMPTC 예시 3개 · <a href="DATA_POLICY.md">CC BY-NC 4.0 / 출처</a> · inD는 집계 결과만 공개';if(!document.body.classList.contains('p-deck')&&!new URLSearchParams(location.search).has('present'))document.body.append(n);setInterval(()=>{const op=document.querySelector('#dataset option[value="inD"]');if(op){op.disabled=true;op.textContent='inD — aggregate-only (license)';}},1000);});"""
(O/'public-notice.js').write_text(notice)
(O/'assets/ind-unavailable.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200"><text x="20" y="80">inD replay is not distributed. Aggregate results only.</text></svg>')
wr(Path('data/public/provenance.json'),{'cases':provenance,'r_origins':[x['uid'] for x in public_ri],'case_count':len(selected),'original_recording_ids':'replaced with public IDs','timestamps':'relative to each recorded case origin0; physical coordinates unchanged','license':'CC-BY-NC-4.0','source':'https://zenodo.org/records/14811016','excludes':['inD per-origin data and maps','private APIs','model checkpoints','credentials'],'attribution':'Hetzel, Reichert, Reitberger, Doll and Sick — IMPTC v1.0 DOI10.5281/zenodo.14811016'})
(O/'DATA_POLICY.md').write_text('''# Public presentation data policy

The small IMPTC-derived excerpts and stored DD-MDN outputs are shared for noncommercial research under CC BY-NC 4.0. Source: https://zenodo.org/records/14811016 . Authors: Manuel Hetzel, Hannes Reichert, Günther Reitberger, Konrad Doll and Bernhard Sick. License: https://creativecommons.org/licenses/by-nc/4.0/ . Changes: three excerpts selected, original IDs replaced, acquisition timestamps made relative; world coordinates and stored probabilities retained. Attribution and license must accompany reuse. This is data minimization, not an anonymity guarantee.

No inD trajectories, camera backgrounds, reconstructable per-origin data, model checkpoints or private API endpoints are distributed. inD appears only in aggregate statistics. Dataset-derived files are not relicensed as repository code. No model is trained or executed by this static site. Noise trajectories are saved synthetic perturbation experiments of real IMPTC observations, not sensor measurements. Completion calibration remains independently unvalidated.
''')
# Privacy assertions on structured per-origin payloads.
for p in (O/'data/public').rglob('*.json'):
 s=p.read_text();assert '/data/whereami' not in s and '/Users/' not in s and 'base:' not in s,p
 d=json.loads(s)
 if isinstance(d,dict) and 'dataset' in d:assert d['dataset']=='IMPTC',p
print(json.dumps({'files':sum(p.is_file() for p in O.rglob('*')),'bytes':sum(p.stat().st_size for p in O.rglob('*') if p.is_file()),'events':len(selected),'r_packets':len(public_ri)},indent=2))
