"""Visible trajectory inspection and geometry-only registration alternatives."""
from pathlib import Path
import os,json,itertools
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/data/whereami/math/full_rq_261026')
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from geometry import load_map,crosswalks,rectangle

xy,color,labels=load_map();defs=crosswalks(xy,labels)
registration=json.loads((ROOT/'reports/registration.json').read_text())
diagram=registration['diagram_centroid_pixels']
world=np.vstack([d['center'] for d in defs]+[[0.,0.]])
A=np.column_stack([world,np.ones(4)])
alternatives=[]
for perm in itertools.permutations(['f1','f2','f3']):
    target=np.array([diagram[k] for k in perm]+[diagram['origin']])
    fit=np.linalg.lstsq(A,target,rcond=None)[0]
    error=np.linalg.norm(A@fit-target,axis=1)
    alternatives.append(dict(component1_signal=perm[0],component2_signal=perm[1],component3_signal=perm[2],
        affine_centroid_RMSE_pixels=float(np.sqrt((error**2).mean())),max_error_pixels=float(error.max()),
        source='official_diagram_manually_selected_centroids_plus_documented_origin',
        independent_survey_accuracy=False))
alts=pd.DataFrame(alternatives).sort_values('affine_centroid_RMSE_pixels')
alts.to_csv(ROOT/'reports/registration_alternatives.csv',index=False,encoding='utf-8-sig')
expected=tuple(d['signal'] for d in defs)
assert tuple(alts.iloc[0][['component1_signal','component2_signal','component3_signal']])==expected

review=pd.read_csv(ROOT/'reports/review.csv')
q=pd.read_parquet(BASE/'data/processed/imptc_pedestrian_tracks.parquet',columns=['track_uid','ts_us','x','y','status'])
for page in range((len(review)+5)//6):
    fig,axes=plt.subplots(2,3,figsize=(15,10))
    for ax,(_,e) in zip(axes.ravel(),review.iloc[page*6:(page+1)*6].iterrows()):
        geom=next(d for d in defs if d['component']==e.component)
        center=geom['center'];extent=15
        local=(abs(xy[:,0]-center[0])<extent)&(abs(xy[:,1]-center[1])<extent)
        ids=np.flatnonzero(local)[::5]
        ax.scatter(xy[ids,0],xy[ids,1],c=color[ids]/255,s=.5,alpha=.22,zorder=1)
        _,box=rectangle(geom);ax.plot(box[:,0],box[:,1],c='black',lw=1.5,zorder=3)
        g=q[q.track_uid==e.track_uid]
        times=g.ts_us.to_numpy()/1e6
        ok=(g.status.to_numpy()==2)
        # Break paths at status/gap boundaries rather than drawing across gaps.
        cont=np.r_[False,(np.diff(times)<=.06)&(np.diff(times)>0)]&ok&np.r_[False,ok[:-1]]
        x=g.x.to_numpy().copy();y=g.y.to_numpy().copy()
        for k in np.flatnonzero(~cont)[1:]:
            x[k]=np.nan;y[k]=np.nan
        ax.plot(x,y,c='white',lw=4,zorder=4);ax.plot(x,y,c='royalblue',lw=2,zorder=5)
        span=g[g.ts_us.between(e.first_map_ts_us,e.last_map_ts_us)]
        ax.plot(span.x,span.y,c='darkorange',lw=3,zorder=7)
        ax.scatter([g.x.iloc[0]],[g.y.iloc[0]],c='green',s=45,marker='^',zorder=9)
        ax.scatter([g.x.iloc[-1]],[g.y.iloc[-1]],c='red',s=45,marker='s',zorder=9)
        for side,c in [('pre','lime'),('post','magenta')]:
            if np.isfinite(e.get(side+'_x_m',np.nan)):
                ax.scatter([e[side+'_x_m']],[e[side+'_y_m']],c=c,edgecolors='black',s=60,zorder=10)
        if len(span)>4:
            i=min(len(span)-1,len(span)//2+2);j=max(0,i-4)
            ax.annotate('',xy=(span.x.iloc[i],span.y.iloc[i]),xytext=(span.x.iloc[j],span.y.iloc[j]),arrowprops=dict(arrowstyle='->',lw=2,color='black'),zorder=11)
        ax.set_xlim(center[0]-extent,center[0]+extent);ax.set_ylim(center[1]-extent,center[1]+extent)
        ax.set_aspect('equal');ax.set_title(f'{e.track_uid}\n{e.signal_group} / {e.classification} / signal={e.entry_signal_code}',fontsize=8)
        ax.set_xlabel('X (m)');ax.set_ylabel('Y (m)')
    for ax in axes.ravel()[len(review.iloc[page*6:(page+1)*6]):]:ax.axis('off')
    fig.suptitle('Recorded trajectory on official map; orange=this event; blue=track\nGreen triangle=start / red square=end / lime=pre landing / magenta=post landing; rule labels, not manual GT',fontsize=10)
    fig.tight_layout();fig.savefig(ROOT/f'figures/review_visible_{page+1:02}.png',dpi=150);plt.close(fig)

# Compare a complete case per crossing and a censored case with provider's
# original topview image. Selection is deterministic and includes failure.
selected=[]
for signal in ['f1','f2','f3']:
    subset=review[(review.signal_group==signal)&(review.classification=='complete_rule')]
    if len(subset):selected.append(subset.iloc[0])
subset=review[review.classification=='partial_censored']
if len(subset):selected.append(subset.iloc[0])
for i,e in enumerate(selected,1):
    directory=Path(e.source_path).parent
    source=directory/'topview.png'
    if not source.exists():source=directory/(directory.name+'_topview.png')
    assert source.exists(), str(source)
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    g=q[q.track_uid==e.track_uid];geom=next(d for d in defs if d['component']==e.component)
    sample=np.random.default_rng(42).choice(len(xy),70000,replace=False)
    axes[0].scatter(xy[sample,0],xy[sample,1],c=color[sample]/255,s=.4,alpha=.2)
    axes[0].plot(g.x,g.y,c='white',lw=5);axes[0].plot(g.x,g.y,c='royalblue',lw=2)
    _,box=rectangle(geom);axes[0].plot(box[:,0],box[:,1],c='black',lw=2)
    axes[0].scatter([g.x.iloc[0]],[g.y.iloc[0]],c='green',marker='^',s=60)
    axes[0].scatter([g.x.iloc[-1]],[g.y.iloc[-1]],c='red',marker='s',s=60)
    axes[0].axis('equal');axes[0].set(xlabel='local X (m)',ylabel='local Y (m)',title='Our common-coordinate trajectory/map')
    axes[1].imshow(plt.imread(source));axes[1].axis('off');axes[1].set_title('Unmodified provider *_topview.png')
    fig.suptitle(f'{e.track_uid}: {e.signal_group}, {e.classification}')
    fig.tight_layout();fig.savefig(ROOT/f'figures/provider_compare_{i:02}.png',dpi=150);plt.close(fig)
proof=dict(passed=True,registration_best=expected,review_cases=len(review),provider_image_comparisons=len(selected),all_provider_images_present=True)
(ROOT/'reports/review_validation.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof),flush=True)
