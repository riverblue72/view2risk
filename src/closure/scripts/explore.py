from pathlib import Path
import os,json,urllib.request,hashlib
ROOT=Path(__file__).resolve().parents[1]
for d in ['docs','reports','figures','data','tmp']:(ROOT/d).mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from geometry import load_map,crosswalks,rectangle

sources={
 'official_vis.py':'https://raw.githubusercontent.com/AIR-THU/DAIR-V2X/main/tools/visualize/vis_label_in_image.py',
 'official_calib.py':'https://raw.githubusercontent.com/AIR-THU/DAIR-V2X/main/tools/dataset_converter/spd2kitti_tracking/gen_kitti/calib_dair2kitti.py',
 'official_vis_utils.py':'https://raw.githubusercontent.com/AIR-THU/DAIR-V2X/main/tools/visualize/vis_utils.py',
 'official_spd_labels.py':'https://raw.githubusercontent.com/AIR-THU/DAIR-V2X/main/tools/dataset_converter/spd2kitti_tracking/gen_kitti/label_dair2kitti.py',
}
for name,url in sources.items():
    p=ROOT/'docs'/name
    if not p.exists():
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'View2Risk-audit'}),timeout=30).read())
(ROOT/'docs/official_sources.json').write_text(json.dumps({k:dict(url=v,sha256=hashlib.sha256((ROOT/'docs'/k).read_bytes()).hexdigest()) for k,v in sources.items()},indent=2))
xy,color,labels=load_map()
defs=crosswalks(xy,labels)
rows=[]
fig,axes=plt.subplots(1,2,figsize=(16,8))
sample=np.random.default_rng(42).choice(len(xy),min(150000,len(xy)),replace=False)
axes[0].scatter(xy[sample,0],xy[sample,1],c=color[sample]/255,s=.5,alpha=.7)
centers=[]
for d in defs:
    b,box=rectangle(d)
    axes[0].plot(box[:,0],box[:,1],color='black',lw=2)
    axes[0].text(*d['center'],d['signal'],fontsize=20,color='black',weight='bold')
    rows.append(dict(component=d['component'],signal=d['signal'],center_x=d['center'][0],center_y=d['center'][1],
                     length_m=b[1,0]-b[0,0],width_m=b[1,1]-b[0,1],axis_x=d['axis'][0],axis_y=d['axis'][1]))
axes[0].scatter([0],[0],c='red',s=80,zorder=10,label='Documented origin')
axes[0].set(xlabel='local X / east (m)',ylabel='local Y / north (m)',title='Geometry-only mapping to provider signal diagram')
axes[0].axis('equal');axes[0].legend()
im=Image.open('/data/whereami/math/view2risk_261025/repos/imptc/images/traffic_light_signal_groups.jpg')
axes[1].imshow(im);axes[1].axis('off');axes[1].set_title('Official diagram: labels and origin, no behavior fitting')
# Manually selected centroids on the 512x512 official diagram + documented
# origin. Affine residual is a registration diagnostic, not GT precision.
diagram={'f1':[159,169],'f2':[300,193],'f3':[292,350],'origin':[230,137]}
world=np.vstack([d['center'] for d in defs]+[[0.,0.]])
pixels=np.array([diagram[d['signal']] for d in defs]+[diagram['origin']])
A=np.column_stack([world,np.ones(len(world))])
fit=np.linalg.lstsq(A,pixels,rcond=None)[0]
residual=np.linalg.norm(A@fit-pixels,axis=1)
for d in defs:
    _,box=rectangle(d)
    proj=np.column_stack([box,np.ones(len(box))])@fit
    axes[1].plot(proj[:,0],proj[:,1],color='black',ls='--')
fig.tight_layout();fig.savefig(ROOT/'figures/map_signal_registration.png',dpi=160);plt.close(fig)
pd.DataFrame(rows).to_csv(ROOT/'reports/geometry_preview.csv',index=False)
(ROOT/'reports/registration.json').write_text(json.dumps(dict(
    mapping={str(d['component']):d['signal'] for d in defs},
    method='Topology, long f2 crossing, documented coordinate origin; manual provider-diagram centroid registration',
    diagram_centroid_pixels=diagram,affine_world_to_pixel=fit.tolist(),
    centroid_residual_pixels=residual.tolist(),not_surveyed_georeference=True),indent=2))
print(pd.DataFrame(rows).to_string(index=False),flush=True)
print('REGISTRATION',residual.tolist(),flush=True)
for name in sources:
    p=ROOT/'docs'/name
    lines=p.read_text().splitlines()
    print('OFFICIAL_CODE',name,flush=True)
    for i,line in enumerate(lines):
        if any(s in line for s in ['cam_K','cam_D','rotation','reshape','intrinsic','P2']):
            print(i+1,line[:180],flush=True)
