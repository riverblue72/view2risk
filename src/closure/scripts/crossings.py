"""Full IMPTC spatial/temporal crossing audit, explicitly rule-derived labels."""
from pathlib import Path
import os,json,hashlib,time
ROOT=Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/mpl')
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from geometry import load_map,crosswalks,rectangle

BASE=Path('/data/whereami/math/full_rq_261026')
CONFIGS=[
 dict(name='strict',quantile=.005,map_radius=.1,clearance=.5,lateral_margin=.25,landing_span=.2,retained_fraction=.98),
 dict(name='base',quantile=.005,map_radius=.25,clearance=.25,lateral_margin=.75,landing_span=.12,retained_fraction=.95),
 dict(name='wide',quantile=.005,map_radius=.5,clearance=.1,lateral_margin=1.25,landing_span=.08,retained_fraction=.9),
]
PROTOCOL=dict(configs=CONFIGS,seed=42,max_dt_s=.060,bridge_map_holes_s=.4,
    landing_search_s=3.,landing_max_beyond_end_m=4.,landing_map_codes=[1,3],
    crossing_geometry='PCA of provider crosswalk vertices, 0.5%-99.5% axial bounds',
    max_flagged_step_speed_mps=5.,minimum_crosswalk_map_share=.5,
    signal_join='causal backward previous state, maximum age1.5s; transition-near-entry within1s flagged',
    signal_mapping='official diagram origin/topology + manual centroid registration, not entry-green maximization',
    counts='episodes and distinct sequence-track groups separately; track primary classes mutually exclusive',
    labels='operational map-rule labels, not independent manual GT',
    model_predictions_unchanged=True,G95=False,signal_control=False)

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def js(name,obj):
    (ROOT/'reports'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,
       default=lambda x:x.item() if hasattr(x,'item') else x.tolist())+'\n')
def csv(df,name):
    df.to_csv(ROOT/'reports'/name,index=False,encoding='utf-8-sig',na_rep='N/A')

def freeze():
    p=ROOT/'protocol.json'
    text=json.dumps(PROTOCOL,indent=2,ensure_ascii=False)+'\n'
    if p.exists(): assert p.read_text()==text, 'Protocol cannot change after counts'
    else:p.write_text(text)
    frozen=ROOT/'execution_freeze.json'
    if not frozen.exists():
        files=list((ROOT/'scripts').glob('*.py'))+[p,BASE/'manifest.json',BASE/'data/processed/imptc_pedestrian_tracks.parquet',BASE/'data/imptc_ground_map_join.parquet']
        frozen.write_text(json.dumps(dict(created_utc=time.time(),sha256={str(f):sha(f) for f in files}),indent=2))

def landing(t,s,n,code,dist,a,b,lo,hi,normal_lo,normal_hi,cfg,which):
    if which=='before':
        choices=np.arange(max(0,np.searchsorted(t,t[a]-3)),a)
    else:
        choices=np.arange(b+1,min(len(t),np.searchsorted(t,t[b]+3,side='right')))
    if len(choices)==0:return None
    side=np.where(s<lo-cfg['clearance'],-1,np.where(s>hi+cfg['clearance'],1,0))
    accepted=np.isin(code,[1,3])&(dist<=cfg['map_radius'])
    accepted&=(s>=lo-4)&(s<=hi+4)&(n>=normal_lo-cfg['lateral_margin'])&(n<=normal_hi+cfg['lateral_margin'])
    candidates=[]
    for sg in [-1,1]:
        ix=choices[accepted[choices]&(side[choices]==sg)]
        if len(ix)==0:continue
        runs=np.split(ix,np.flatnonzero(np.diff(ix)>1)+1)
        for run in runs:
            if t[run[-1]]-t[run[0]]+1e-7>=cfg['landing_span']:
                candidates.append((int(run[-1] if which=='before' else run[0]),sg))
    if not candidates:return None
    return (max if which=='before' else min)(candidates,key=lambda z:z[0])

def gate_time(t,s,lower,upper,boundary,direction,which):
    ix=np.arange(lower,upper)
    if len(ix)==0:return None
    good=((s[ix]-boundary)*direction<=0)&((s[ix+1]-boundary)*direction>=0)&((s[ix+1]-s[ix])*direction>1e-8)
    ix=ix[good]
    if not len(ix):return None
    k=ix[0] if which=='first' else ix[-1]
    fraction=(boundary-s[k])/(s[k+1]-s[k])
    return float(t[k]+fraction*(t[k+1]-t[k]))

def signals_for_sequence(source):
    p=Path(source).parents[2]/'context/traffic_light_signals.json'
    raw=json.loads(p.read_text())['status_data']
    ts=np.array(sorted(map(int,raw)),np.int64)
    states=np.array([[raw[str(int(t))][f'f{i}'] for i in range(1,4)] for t in ts])
    return ts,states,p

def signal_at(ts,states,event_ts,group):
    if event_ts is None or not np.isfinite(event_ts):return dict(code=np.nan,age_s=np.nan,near_transition=False)
    i=np.searchsorted(ts,int(round(event_ts*1e6)),side='right')-1
    age=(event_ts*1e6-ts[i])/1e6 if i>=0 else np.inf
    if i<0 or age>1.5:return dict(code=np.nan,age_s=age,near_transition=False)
    k=int(group[-1])-1
    transitions=ts[1:][states[1:,k]!=states[:-1,k]]/1e6
    near=bool(np.any(abs(transitions-event_ts)<=1.))
    return dict(code=int(states[i,k]),age_s=float(age),near_transition=near)

def classify(g,geom,cfg,cross_component):
    xy=g[['x','y']].to_numpy();t=g.ts_us.to_numpy()/1e6
    local=(xy-geom['center'])@np.column_stack([geom['axis'],geom['normal']]);s,n=local.T
    bounds,_=rectangle(geom,cfg['quantile']);lo,hi=bounds[:,0];normal_lo,normal_hi=bounds[:,1]
    code=g.map_ground_code.to_numpy();dist=g.map_nearest_XY_distance_m.to_numpy()
    hit=(cross_component==geom['component'])&(code==5)&(dist<=cfg['map_radius'])
    ix=np.flatnonzero(hit)
    if not len(ix):return []
    episodes=np.split(ix,np.flatnonzero(np.diff(t[ix])>.4)+1)
    output=[]
    for ep in episodes:
        a,b=int(ep[0]),int(ep[-1])
        pre=landing(t,s,n,code,dist,a,b,lo,hi,normal_lo,normal_hi,cfg,'before')
        post=landing(t,s,n,code,dist,a,b,lo,hi,normal_lo,normal_hi,cfg,'after')
        row=dict(component=geom['component'],signal_group=geom['signal'],
                 first_map_ts_us=int(g.ts_us.iloc[a]),last_map_ts_us=int(g.ts_us.iloc[b]),
                 map_observations=len(ep),pre_landing_index=pre[0] if pre else -1,
                 post_landing_index=post[0] if post else -1,
                 start_side=pre[1] if pre else 0,end_side=post[1] if post else 0,
                 entry_ts_s=np.nan,exit_ts_s=np.nan,duration_s=np.nan,
                 retained_polygon_fraction=np.nan,crosswalk_map_fraction=np.nan,
                 flagged_jump=False,classification='unresolved_gate',
                 observed_source='same_source_recorded_tracks_and_semantic_map')
        if pre and post and pre[1]==post[1]:row['classification']='returned_same_side'
        elif not pre or not post:
            left_censored=pre is None and t[a]-t[0]<.5
            right_censored=post is None and t[-1]-t[b]<.5
            row['classification']='partial_censored' if left_censored or right_censored else 'partial_missing_landing'
        else:
            direction=post[1]
            entry_bound=lo if pre[1]<0 else hi;exit_bound=hi if post[1]>0 else lo
            entry=gate_time(t,s,pre[0],b,entry_bound,direction,'first')
            exit=gate_time(t,s,a,post[0],exit_bound,direction,'last')
            if entry is not None and exit is not None and exit>entry:
                between=(t>=entry)&(t<=exit)
                inside=(s>=lo-cfg['lateral_margin'])&(s<=hi+cfg['lateral_margin'])&(n>=normal_lo-cfg['lateral_margin'])&(n<=normal_hi+cfg['lateral_margin'])
                retained=float(inside[between].mean()) if between.any() else 0
                map_share=float(hit[between].mean()) if between.any() else 0
                step=np.linalg.norm(np.diff(xy,axis=0),axis=1)/np.diff(t)
                jump=bool(np.any(step[pre[0]:post[0]]>5.))
                row.update(entry_ts_s=entry,exit_ts_s=exit,duration_s=exit-entry,
                    retained_polygon_fraction=retained,crosswalk_map_fraction=map_share,flagged_jump=jump)
                if jump:row['classification']='uncertain_position_jump'
                elif retained<cfg['retained_fraction'] or map_share<.5:row['classification']='partial_side_path'
                else:row['classification']='complete_rule'
        if pre:
            row.update(pre_x_m=float(xy[pre[0],0]),pre_y_m=float(xy[pre[0],1]),pre_ts_us=int(g.ts_us.iloc[pre[0]]))
        if post:
            row.update(post_x_m=float(xy[post[0],0]),post_y_m=float(xy[post[0],1]),post_ts_us=int(g.ts_us.iloc[post[0]]))
        if not np.isfinite(row['entry_ts_s']):
            row['signal_query_ts_s']=t[a]
            row['signal_query_basis']='first_observed_crosswalk_point_not_confirmed_entry'
        else:
            row['signal_query_ts_s']=row['entry_ts_s']
            row['signal_query_basis']='interpolated_geometry_entry'
        output.append(row)
    return output

def main():
    freeze();started=time.time()
    q=pd.read_parquet(BASE/'data/processed/imptc_pedestrian_tracks.parquet')
    m=pd.read_parquet(BASE/'data/imptc_ground_map_join.parquet')
    for k in ['sequence_id','track_uid','ts_us']:
        assert q[k].equals(m[k]), k
    q['map_ground_code']=m.map_ground_code.to_numpy();q['map_nearest_XY_distance_m']=m.map_nearest_XY_distance_m.to_numpy()
    xy,color,labels=load_map();definitions=crosswalks(xy,labels)
    all_cross=np.row_stack([d['cloud'] for d in definitions])
    comp=np.concatenate([np.repeat(d['component'],len(d['cloud'])) for d in definitions])
    nearest=cKDTree(all_cross).query(q[['x','y']].to_numpy(),workers=2)[1]
    q['nearest_crosswalk_component']=comp[nearest]
    accepted=(q.status==2)&q.finite_coordinates
    q['valid_segment']=((~accepted)|(~accepted.shift(fill_value=False))|q.track_uid.ne(q.track_uid.shift())|q.dt.gt(.060)|q.dt.le(0)).cumsum()
    events=[];signals={};sources={};tracks=[]
    for uid,g in q.groupby('track_uid',sort=False):
        valid=g[accepted.loc[g.index]]
        if g.sequence_id.iloc[0] not in signals:
            ts,states,path=signals_for_sequence(g.source_path.iloc[0]);signals[g.sequence_id.iloc[0]]=(ts,states);sources[str(path)]=sha(path)
        ts,states=signals[g.sequence_id.iloc[0]]
        for segid,segment in valid.groupby('valid_segment',sort=False):
            segment=segment.reset_index(drop=True)
            if len(segment)<2:continue
            for geom in definitions:
                for cfg in CONFIGS:
                    found=classify(segment,geom,cfg,segment.nearest_crosswalk_component.to_numpy())
                    for event in found:
                        state=signal_at(ts,states,event['signal_query_ts_s'],geom['signal'])
                        event.update(config=cfg['name'],track_uid=uid,sequence_id=g.sequence_id.iloc[0],track_id=g.track_id.iloc[0],
                          recording_date=g.recording_date.iloc[0],valid_segment=int(segid),source_path=g.source_path.iloc[0],
                          entry_signal_code=state['code'],signal_age_s=state['age_s'],signal_transition_within_1s=state['near_transition'])
                        events.append(event)
        tracks.append(dict(track_uid=uid,sequence_id=g.sequence_id.iloc[0],recording_date=g.recording_date.iloc[0],
            total_observations=len(g),accepted_observations=len(valid),
            map_crosswalk_touch_status2=bool(((valid.map_ground_code==5)&(valid.map_nearest_XY_distance_m<=.25)).any())))
    events=pd.DataFrame(events)
    events.insert(0,'event_id',[f'{r.config}:{r.track_uid}:{r.component}:{r.first_map_ts_us}' for r in events.itertuples()])
    assert not events.event_id.duplicated().any()
    base=events[events.config=='base'].copy()
    csv(base,'crossings.csv');csv(events,'crossing_sensitivity_events.csv')
    events.to_parquet(ROOT/'data/crossing_events.parquet',index=False,compression='zstd')
    counts=[]
    for key,g in events.groupby(['config','signal_group','classification'],dropna=False):
        counts.append(dict(zip(['config','signal_group','classification'],key),episodes=len(g),tracks=g.track_uid.nunique(),sequences=g.sequence_id.nunique(),dates=g.recording_date.nunique()))
    csv(pd.DataFrame(counts),'crossing_counts.csv')
    tracks=pd.DataFrame(tracks)
    pertrack=base.groupby('track_uid').classification.agg(list)
    tracks['complete_events']=tracks.track_uid.map(base[base.classification=='complete_rule'].groupby('track_uid').size()).fillna(0).astype(int)
    tracks['all_crosswalk_events']=tracks.track_uid.map(base.groupby('track_uid').size()).fillna(0).astype(int)
    tracks['primary_class']=np.where(tracks.complete_events>0,'has_complete_rule',np.where(tracks.all_crosswalk_events>0,'touch_without_complete','no_accepted_map_touch'))
    csv(tracks,'tracks.csv')
    assert len(tracks)==1920
    summary=tracks.groupby('primary_class').agg(tracks=('track_uid','nunique'),sequences=('sequence_id','nunique'),dates=('recording_date','nunique')).reset_index()
    csv(summary,'track_counts.csv')
    signal_counts=[]
    for key,g in base.groupby(['signal_group','classification','entry_signal_code','signal_transition_within_1s'],dropna=False):
        signal_counts.append(dict(zip(['signal_group','classification','entry_signal_code','transition_within_1s'],key),episodes=len(g),tracks=g.track_uid.nunique(),sequences=g.sequence_id.nunique()))
    csv(pd.DataFrame(signal_counts),'signal.csv')
    # Export an actual all-observation spatial+causal signal join; leave outside
    # crosswalk observations unassigned rather than forcing the nearest group.
    joined=q[['sequence_id','track_uid','ts_us','status','map_ground_code','map_nearest_XY_distance_m','nearest_crosswalk_component']].copy()
    inside=(joined.map_ground_code==5)&(joined.map_nearest_XY_distance_m<=.25)
    lookup={d['component']:d['signal'] for d in definitions}
    joined['signal_group']=joined.nearest_crosswalk_component.map(lookup).where(inside)
    joined['signal_code']=np.nan;joined['signal_age_s']=np.nan
    for seq,ix in joined.groupby('sequence_id').groups.items():
        ts,states=signals[seq];times=joined.loc[ix,'ts_us'].to_numpy();prior=np.searchsorted(ts,times,side='right')-1
        ages=(times-ts[np.maximum(prior,0)])/1e6
        for group in ['f1','f2','f3']:
            take=(joined.loc[ix,'signal_group'].to_numpy()==group)&(prior>=0)&(ages<=1.5)
            selected=np.asarray(ix)[take]
            joined.loc[selected,'signal_code']=states[prior[take],int(group[-1])-1]
            joined.loc[selected,'signal_age_s']=ages[take]
    joined.to_parquet(ROOT/'data/imptc_signal_join.parquet',index=False,compression='zstd')
    mapping=[]
    for d in definitions:
        bounds,box=rectangle(d)
        mapping.append(dict(signal_group=d['signal'],component=d['component'],center_x_m=d['center'][0],center_y_m=d['center'][1],
           length_m=bounds[1,0]-bounds[0,0],width_m=bounds[1,1]-bounds[0,1],axis_x=d['axis'][0],axis_y=d['axis'][1],
           geometry_origin='official_semantic_map',signal_mapping='official_diagram_topology_and_origin',independent_GT=False))
    csv(pd.DataFrame(mapping),'geometry.csv')
    # Stratified inspection cases chosen deterministically, not only successes.
    chosen=[]
    for key,g in base.groupby(['signal_group','classification']):
        chosen.extend(g.sample(n=min(2,len(g)),random_state=42).event_id.tolist())
    review=base[base.event_id.isin(chosen)].copy().reset_index(drop=True)
    for page in range((len(review)+5)//6):
        fig,axes=plt.subplots(2,3,figsize=(15,10))
        for ax,(_,event) in zip(axes.ravel(),review.iloc[page*6:(page+1)*6].iterrows()):
            g=q[q.track_uid==event.track_uid]
            geom=next(d for d in definitions if d['component']==event.component)
            center=geom['center'];extent=18
            local=(abs(xy[:,0]-center[0])<extent)&(abs(xy[:,1]-center[1])<extent)
            ids=np.flatnonzero(local)[::4]
            ax.scatter(xy[ids,0],xy[ids,1],c=color[ids]/255,s=.5,alpha=.5)
            _,box=rectangle(geom);ax.plot(box[:,0],box[:,1],c='black')
            # Keep entire segment context; mark this event's observation span.
            ax.plot(g.x,g.y,c='royalblue',lw=1,alpha=.6)
            e=g[g.ts_us.between(event.first_map_ts_us,event.last_map_ts_us)]
            ax.plot(e.x,e.y,c='orange',lw=2)
            ax.scatter([g.x.iloc[0]],[g.y.iloc[0]],c='green',s=25,marker='^')
            ax.scatter([g.x.iloc[-1]],[g.y.iloc[-1]],c='red',s=25,marker='s')
            if np.isfinite(event.get('pre_x_m',np.nan)):
                ax.scatter([event.pre_x_m],[event.pre_y_m],c='lime',edgecolors='black',s=60)
            if np.isfinite(event.get('post_x_m',np.nan)):
                ax.scatter([event.post_x_m],[event.post_y_m],c='magenta',edgecolors='black',s=60)
            ax.set_xlim(center[0]-extent,center[0]+extent);ax.set_ylim(center[1]-extent,center[1]+extent)
            ax.set_aspect('equal');ax.set_title(f'{event.track_uid}\n{event.signal_group}: {event.classification}; signal={event.entry_signal_code}',fontsize=8)
            ax.set_xlabel('X (m)');ax.set_ylabel('Y (m)')
        for ax in axes.ravel()[len(review.iloc[page*6:(page+1)*6]):]:ax.axis('off')
        fig.suptitle('Rule-derived crossing inspection: green=start, red=end, lime/pre, magenta/post landing\nNot independent crossing GT; all classes sampled, seed42',fontsize=11)
        fig.tight_layout();fig.savefig(ROOT/f'figures/crossing_review_{page+1:02}.png',dpi=140);plt.close(fig)
    review['review_status']='generated_for_inspection_not_independent_manual_GT'
    csv(review,'review.csv')
    # Independent source JSON checks for all review cases: actual timestamps,
    # coordinates, valid status and causal traffic-light match.
    for _,event in review.iterrows():
        raw=json.loads(Path(event.source_path).read_text())['track_data']
        src={int(x.get('ts',key)):x for key,x in raw.items()}
        for tskey in ['first_map_ts_us','last_map_ts_us']:
            val=src[int(event[tskey])];assert val['status']==2
            row=q[(q.track_uid==event.track_uid)&(q.ts_us==int(event[tskey]))].iloc[0]
            np.testing.assert_allclose([row.x,row.y,row.z],val['coordinates'],rtol=0,atol=0)
        ts,states=signals[event.sequence_id]
        expected=signal_at(ts,states,event.signal_query_ts_s,event.signal_group)
        assert np.isclose(expected['code'],event.entry_signal_code,equal_nan=True)
    full=base[base.classification=='complete_rule']
    assert (full.start_side==-full.end_side).all()
    assert (full.duration_s>0).all()
    assert (full.retained_polygon_fraction>=.95).all()
    assert not full.flagged_jump.any()
    assert not (joined.signal_code.notna()&joined.signal_group.isna()).any()
    assert (joined.loc[joined.signal_code.notna(),'signal_age_s'].between(0,1.5)).all()
    proof=dict(passed=True,all_original_rows_retained=len(q),tracks=len(tracks),
        mutually_exclusive_primary_counts=summary.set_index('primary_class').tracks.to_dict(),
        base_events=len(base),base_complete_events=len(full),base_complete_tracks=full.track_uid.nunique(),
        sensitivity_complete_events=events[events.classification=='complete_rule'].groupby('config').size().to_dict(),
        actual_raw_JSON_review_cases=len(review),causal_signal_join_verified=True,
        independent_manual_GT=False,spatial_assignment_method='provider_diagram_geometry_origin_registration',
        no_model_refit=True,G95_computed=False,elapsed_s=time.time()-started,
        source_signal_SHA256=sources)
    js('crossing_validation.json',proof)
    print(json.dumps({k:v for k,v in proof.items() if k!='source_signal_SHA256'},default=int),flush=True)

if __name__=='__main__':main()
