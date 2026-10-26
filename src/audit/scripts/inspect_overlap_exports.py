from pathlib import Path
import json
import numpy as np
from common import ROOT,js,sha,csvw
def main():
    def index(package):return {(p.parents[2].name,p.parent.name):p for p in package.glob('**/vrus/*/track.json')}
    a=index(ROOT/'data/raw/imptc_samples');b=index(ROOT/'data/raw/imptc_set_01');rows=[]
    for key in sorted(set(a)&set(b)):
        x,y=[json.loads(p.read_text()) for p in [a[key],b[key]]]
        xx={str(v['ts']):v for v in x['track_data'].values()};yy={str(v['ts']):v for v in y['track_data'].values()};common=set(xx)&set(yy)
        rows.append(dict(sequence_id=key[0],track_id=key[1],class_id=x['overview']['class_id'],same_raw_SHA256=sha(a[key])==sha(b[key]),same_semantic_JSON=x==y,
                         sample_observations=len(xx),full_observations=len(yy),overlap_timestamps=len(common),sample_only_timestamps=len(set(xx)-set(yy)),full_only_timestamps=len(set(yy)-set(xx)),
                         max_xyz_euclidean_difference_m=max((float(np.linalg.norm(np.array(xx[t]['coordinates'])-yy[t]['coordinates'])) for t in common),default=None),
                         max_velocity_difference_kmh=max((abs(xx[t]['velocity']-yy[t]['velocity']) for t in common),default=None),
                         status_disagreements=sum(xx[t]['status']!=yy[t]['status'] for t in common),
                         selected_for_main='full_set_01',reason='Canonical full release; sample stage preserved separately; not independent duplicate tracks'))
    csvw(ROOT/'reports/imptc_overlap_exports.csv',rows)
    js(ROOT/'reports/imptc_overlap_exports.json',dict(overlapping_VRU_tracks=len(rows),overlapping_pedestrian_tracks=sum(r['class_id']==0 for r in rows),
         differing_semantic_exports=sum(not r['same_semantic_JSON'] for r in rows),
         max_xyz_difference_m=max(r['max_xyz_euclidean_difference_m'] for r in rows),main_scope='Full Set01 only',sample_scope='Samples only, separate stage',rows=rows))
    print('OVERLAP',len(rows),sum(r['class_id']==0 for r in rows))
if __name__=='__main__':main()
