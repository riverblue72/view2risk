"""Validate only presentation source/deployment. No network, inference or training."""
from pathlib import Path
import json, hashlib, shutil, sys, re
root=Path(__file__).resolve().parents[2]
site=root/'presentation/site'; deployed=root/'docs/presentation'
if '--sync' in sys.argv:
    shutil.copytree(site,deployed,dirs_exist_ok=True)
def manifest(p):
    return {str(f.relative_to(p)): hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
a=manifest(site); b=manifest(deployed)
assert a==b, 'Source/deployment mismatch (stale files also fail)'
for rel in a:
    p=site/rel
    assert p.suffix.lower() not in {'.pt','.pth','.ckpt','.safetensors','.npy','.npz','.nii','.gz'}, rel
    if p.suffix in {'.html','.js','.json','.csv','.md'} and not rel.startswith('assets/'):
        text=p.read_text()
        for pattern in [r'/api/',r'/data/whereami/',r'/Users/',r'github_pat_[A-Za-z0-9_]+',r'ghp_[A-Za-z0-9]+',r'-----BEGIN [A-Z ]*PRIVATE KEY']:
            assert not re.search(pattern,text), (rel,pattern)
provenance=json.loads((site/'data/public/provenance.json').read_text())
assert provenance['case_count']==3
for c in provenance['cases']:
    case=json.loads((site/'data/public/cases'/str(c['id']+'.json')).read_text())
    assert case['dataset']=='IMPTC' and case['origin0_s']==0
rindex=json.loads((site/'data/public/r-index.json').read_text())
assert len(rindex)==3
for row in rindex:
    d=json.loads((site/'data/public/r'/row['file']).read_text())
    assert d['dataset']=='IMPTC'
    assert 'clean' in d['results']
    for scenario in ['iid_0.5','iid_1','iid_2','correlated_1','dropout_1']:
        for mode in ['noisy','filtered_mean','rq']:
            assert scenario+'__'+mode in d['results']
print(json.dumps({'status':'PASSED','identical_site_files':len(a),'public_cases':3,'matched_r_origins':3,'private_API_or_checkpoint_files':False},indent=2))
