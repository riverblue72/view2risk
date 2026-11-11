import numpy as np
import pandas as pd
import pedpy
def stats(a):
 a=np.asarray(a);a=a[np.isfinite(a)];return dict(n=len(a),mean=float(a.mean()) if len(a) else None,median=float(np.median(a)) if len(a) else None,p10=float(np.quantile(a,.1)) if len(a) else None,p90=float(np.quantile(a,.9)) if len(a) else None)
def runs(mask):
 x=np.r_[False,mask,False].astype(int);return list(zip(np.flatnonzero(np.diff(x)==1),np.flatnonzero(np.diff(x)==-1)))
def analyze(dataset,recording,location,rows,areas,lines,duration,origin=0):
 df=pd.DataFrame(rows,columns=['id','frame','x','y']);df=df.drop_duplicates(['id','frame']);tr=pedpy.TrajectoryData(data=df,frame_rate=25);sp=pedpy.compute_individual_speed(traj_data=tr,frame_step=5,speed_calculation=pedpy.SpeedCalculation.BORDER_SINGLE_SIDED);merged=tr.data.merge(sp[['id','frame','speed']],on=['id','frame']);trackstats=[];beh=[]
 for tid,q in merged.groupby('id'):
  q=q.sort_values('frame');speed=q.speed.to_numpy();fr=q.frame.to_numpy();continuous=np.r_[True,np.diff(fr)==1];acc=np.r_[0,np.diff(speed)*25];stop=(speed<.2)&continuous;stops=[(a,b) for a,b in runs(stop) if b-a>=25];slows=[(a,b) for a,b in runs((acc<-.3)&continuous) if b-a>=10];xy=q[['x','y']].to_numpy();d=xy[25:]-xy[:-25];ang=np.arctan2(d[:,1],d[:,0]);turn=np.abs(np.arctan2(np.sin(ang[25:]-ang[:-25]),np.cos(ang[25:]-ang[:-25]))) if len(ang)>25 else np.array([]);turns=sum(b-a>=10 for a,b in runs((turn>np.pi/4)&(np.linalg.norm(d[25:],axis=1)>.3)&(np.linalg.norm(d[:-25],axis=1)>.3)));restart=sum(b<len(speed) and (speed[b:min(b+25,len(speed))]>.3).any() for a,b in stops)
  trackstats.append(dict(dataset=dataset,recording=recording,location=location,id=str(tid),**stats(speed)));beh.append(dict(dataset=dataset,recording=recording,location=location,id=str(tid),stops=len(stops),slowdowns=len(slows),restarts=restart,turns=turns))
 trackstats=[]
 for tid,q in merged.assign(original_id=merged.id.astype(str).str.split(':').str[0]).groupby('original_id'):
  trackstats.append(dict(dataset=dataset,recording=recording,location=location,id=str(tid),**stats(q.speed)))
 zone=[];series=[]
 for name,polygon in areas.items():
  area=pedpy.MeasurementArea(polygon);den=pedpy.compute_classic_density(traj_data=tr,measurement_area=area);line=pedpy.MeasurementLine(lines[name]);nt,cross=pedpy.compute_n_t(traj_data=tr,measurement_line=line);flow=len(cross)/duration if duration>0 else None
  inside=np.asarray([polygon.covers(p) for p in merged.point]);z=merged[inside];density=den.set_index('frame')['density'];z=z.assign(density=z.frame.map(density));bins=[]
  for lo,hi in [(0,.02),(.02,.05),(.05,.1),(.1,.3),(.3,100)]:
   subset=z[(z.density>=lo)&(z.density<hi)];bins.append(dict(lo=lo,hi=hi,n=len(subset),speed_mps=float(subset.speed.mean()) if len(subset) else None))
  zone.append(dict(dataset=dataset,recording=recording,location=location,zone=name,area_m2=polygon.area,duration_s=duration,speed=stats(z.speed),density_person_m2=stats(density),first_crossing_events=len(cross),flow_person_s=flow,line_length_m=line.length,speed_by_density=bins,track_count=z.id.nunique()))
  for frame,val in density.iloc[::25].items():series.append(dict(dataset=dataset,recording=recording,zone=name,time_s=origin+int(frame)/25,density_person_m2=float(val),count=int(round(val*polygon.area)),flow_recording_mean_person_s=flow))
 return trackstats,beh,zone,series
