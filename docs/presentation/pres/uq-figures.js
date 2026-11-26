'use strict';
// Both pages use the same case join, chart functions and precision.
const UQ = {
  colors: {clean:'#225983',noisy:'#bc591e',filtered_mean:'#007566',future:'#594ca1',gt:'#ac285b'},
  names: {clean:'오차 없음',noisy:'카메라 오차',filtered_mean:'보정 후'},
  horizons: [1,2,3,4],
  async load() {
    const [, evidence] = await Promise.all([V2R.init({aggregate:false}), V2R.json('pres/evidence.json')]);
    this.evidence = evidence;
    return this.caseAt(V2R.ri.find(row => row.uid === 'o0008'));
  },
  async caseAt(row) {
    const s = await V2R.select(row.event_id,row.origin_s);
    if (s.r?.uid !== row.uid || !s.e || !s.geometry) throw Error('기록과 예측의 식별자가 일치하지 않습니다.');
    return s;
  },
  pct(p) {return Number.isFinite(p) ? (100*p).toFixed(2)+'%' : '자료 없음';},
  reduction(oldValue,newValue) {return (100*(1-newValue/oldValue)).toFixed(1)+'%';},
  source(path,label=path) {return '<a href="'+path+'">'+PE(label)+'</a>';},
  caseSource(s) {
    return 'IMPTC '+PE(s.c.crosswalk)+' · '+PE(s.key.event_id)+' · 예측 시작 +'+s.key.origin_s+'초 · '+
      this.source('data/public/r/'+s.r.uid+'.json')+' · '+this.source('data/public/demo-evidence.json','경계·실제 통과 기록');
  }
};

function uqLegend(entries) {
  return '<div class="uq-legend">'+entries.map(([name,color,dash])=>
    '<span><i style="border-color:'+color+';border-top-style:'+(dash?'dashed':'solid')+'"></i>'+name+'</span>').join('')+'</div>';
}

// Preserve the metre aspect ratio. In the crossing map, positive x points toward Exit.
function uqProjection(points,width,height,project=p=>p) {
  const coords=points.map(project);
  const ranges=[0,1].map(k=>[Math.min(...coords.map(p=>p[k])),Math.max(...coords.map(p=>p[k]))]);
  const scale=Math.min((width-90)/Math.max(.1,ranges[0][1]-ranges[0][0]),(height-78)/Math.max(.1,ranges[1][1]-ranges[1][0]));
  const centre=ranges.map(([a,b])=>(a+b)/2);
  const xy=point=>{
    const [x,y]=project(point);
    return [width/2+(x-centre[0])*scale,height/2-(y-centre[1])*scale];
  };
  return {scale,xy,points:path=>path.map(p=>xy(p).map(n=>n.toFixed(2)).join(',')).join(' ')};
}
function uqLine(plot,path,color,width,attrs='') {
  return '<polyline points="'+plot.points(path)+'" fill="none" stroke="'+color+'" stroke-width="'+width+'" stroke-linecap="round" stroke-linejoin="round" '+attrs+'/>';
}
function uqScale(scale,length,height) {
  return '<path d="M22 '+(height-16)+'h'+(length*scale)+'" stroke="#435762" stroke-width="2"/><text x="22" y="'+(height-23)+'">'+length+' m</text>';
}
function uqEllipse(R,centre) {
  const radius=Math.sqrt(-2*Math.log(.05));
  const a=Math.sqrt(R[0][0]), b=R[1][0]/a, c=Math.sqrt(R[1][1]-b*b);
  return Array.from({length:73},(_,i)=>{
    const t=i*Math.PI/36;
    return [centre[0]+radius*a*Math.cos(t),centre[1]+radius*(b*Math.cos(t)+c*Math.sin(t))];
  });
}
function uqHistory(s,scenario) {
  const clean=s.r.results.clean, noisy=s.r.results[scenario+'__noisy'], corrected=s.r.results[scenario+'__filtered_mean'];
  const n=corrected.filter.observed_points;
  const paths=[clean.input.observed_xy,noisy.input.observed_xy.slice(0,n),corrected.input.observed_xy];
  // 95% bivariate Gaussian measurement-error contour, centred on the last available noisy observation.
  const ellipse=uqEllipse(corrected.filter.filter_R,paths[1].at(-1));
  const plot=uqProjection([...paths.flat(),...ellipse],450,240), colors=Object.values(UQ.colors);
  const lines=paths.map((path,i)=>uqLine(plot,path,colors[i],2.4)+path.map(p=>{
    const [x,y]=plot.xy(p);
    return '<circle cx="'+x+'" cy="'+y+'" r="2.8" fill="'+colors[i]+'"/>';
  }).join('')).join('');
  return '<svg class="field history" viewBox="0 0 450 240" role="img" aria-label="같은 과거의 기준, 합성 관측, 칼만 보정 위치와 측정오차 타원"><polygon points="'+plot.points(ellipse)+'" fill="#f8dec8" fill-opacity=".55" stroke="'+colors[1]+'" stroke-dasharray="4 3"/>'+lines+uqScale(plot.scale,.25,240)+'</svg>'+
    uqLegend([['기준',colors[0]],['합성 관측',colors[1]],['Kalman 보정',colors[2]],['95% 측정오차 타원',colors[1],true]]);
}

function uqMap(s,result,mode,h,truth,replay=false) {
  const g=s.geometry, dir=s.c.direction, boundaries=['end_A','end_B'].map(end=>V2R.boundary(g,end));
  const [entry,exit]=dir===1?boundaries:boundaries.slice().reverse();
  const project=p=>[g.axis,g.normal].map(axis=>dir*((p[0]-g.center[0])*axis[0]+(p[1]-g.center[1])*axis[1]));
  const index=result.future_times_s.indexOf(h);
  if(index<0) throw Error('저장되지 않은 예측 시간입니다.');
  const past=result.input.observed_xy, paths=result.hypotheses_xy.map(p=>[past.at(-1),...p.slice(0,index+1)]);
  const region=result.regions[index], colors=UQ.colors;
  const gt=[s.r.results.clean.input.observed_xy.at(-1),...s.r.future_GT_xy.slice(0,index+1)].filter(p=>p?.every(Number.isFinite));
  const plot=uqProjection([...entry,...exit,...past,...paths.flat(),...Object.values(region).flat(2),...gt],640,290,project);
  const best=result.hypothesis_confidence_scores.indexOf(Math.max(...result.hypothesis_confidence_scores));
  let svg='<svg class="field forecast" viewBox="0 0 640 290" role="img" aria-label="횡단축을 따라 본 과거, 예측 경로와 +'+h+'초 위치 영역" data-h="'+h+'" data-mode="'+mode+'">';
  svg+='<polygon fill="#e6eeef" points="'+plot.points([...entry,...exit.slice().reverse()])+'"/>';
  for(const [label,boundary] of [['Entry',entry],['Exit',exit]]) {
    const [x,y]=plot.xy(boundary.reduce((a,b)=>plot.xy(a)[1]<plot.xy(b)[1]?a:b));
    svg+=uqLine(plot,boundary,label==='Exit'?'#b87508':'#506975',2,label==='Entry'?'stroke-dasharray="4 3"':'')+
      '<text text-anchor="middle" x="'+x+'" y="'+(y-8)+'">'+label+'</text>';
  }
  for(const level of ['0.95','0.68']) for(const polygon of region[level]) {
    svg+='<polygon data-level="'+level+'" points="'+plot.points(polygon)+'" fill="'+colors.future+'" fill-opacity="'+(level==='0.95'?'.07':'.16')+'" stroke="'+colors.future+'" stroke-width="1.2" '+(level==='0.95'?'stroke-dasharray="5 3"':'')+'/>';
  }
  paths.forEach(path=>{svg+=uqLine(plot,path,colors.future,1.1,'stroke-opacity=".34"');});
  svg+=uqLine(plot,paths[best],colors.future,3,'data-path="representative"');
  svg+=uqLine(plot,past,colors[mode],3.8);
  const [x,y]=plot.xy(past.at(-1));
  svg+='<circle cx="'+x+'" cy="'+y+'" r="4.5" fill="'+colors[mode]+'" stroke="white" stroke-width="1.5"/>';
  if(truth) svg+=uqLine(plot,gt,colors.gt,3,'data-path="truth" stroke-dasharray="7 3"');
  if(replay)svg+=uqReplayDot(colors.future)+(truth?uqRecordedCursor(plot,s):'');
  return svg+uqScale(plot.scale,1,290)+'</svg>'+uqLegend([[UQ.names[mode]+' 과거',colors[mode]],['예측 후보 · 굵은 선은 대표 경로',colors.future],['68% 실선 / 95% 점선 HDR',colors.future,true],...(truth?[['실제 미래',colors.gt,true]]:[])]);
}
function uqBars(result,h) {
  return '<div class="prob-chart" role="group" aria-label="시간별 누적 완료확률">'+UQ.horizons.map(t=>{
    const p=result.exit.probabilities?.[t]??(t===4?result.exit.model_probability_4s:null);
    if(!Number.isFinite(p))return '<div class="prob-row"><span>'+t+'초</span><div class="bar-track"></div><strong>미저장</strong></div>';
    return '<div class="prob-row '+(t===h?'chosen':'')+'" data-t="'+t+'" data-probability="'+p+'"><span>'+t+'초</span><div class="bar-track"><i style="width:'+(100*p)+'%"></i></div><strong>'+UQ.pct(p)+'</strong></div>';
  }).join('')+'</div>';
}
function uqRobustRows(dataset="IMPTC",records=UQ.evidence.r) {
  return Object.keys(UQ.names).map(mode=>records.find(r=>r.dataset===dataset&&r.split==='test'&&r.horizon_s===4&&r.condition==='overall'&&r.group==='All'&&r.location==='pooled'&&r.mode===mode&&(mode==='clean'?r.noise_type==='clean':r.noise_type==='iid'&&r.noise_scale===1)));
}
function uqRobustness(part="both") {
  const rows=uqRobustRows();
  const [,n,k]=rows;
  const accuracy='<article><h2>위치 오차와 완료확률 오차</h2>'+pTable(['입력 조건','ADE (m)','H4 Brier'],rows.map(r=>[UQ.names[r.mode],PN(r.ade_m),PN(r.brier,5)]))+
    '<p class="annotation">Noisy 대비 보정 후 <b>ADE '+UQ.reduction(n.ade_m,k.ade_m)+'</b>, <b>H4 Brier '+UQ.reduction(n.brier,k.brier)+'</b> 감소</p></article>';
  const spatial='<article><h2>4초 후 위치의 95% 예측영역</h2>'+pTable(['입력 조건','Coverage95','HDR95 (m²)'],rows.map(r=>[UQ.names[r.mode],UQ.pct(r.coverage95),PN(r.hdr95_area_m2,2)]))+
    '<p class="annotation">영역은 다시 좁아졌지만 실제 위치를 포함한 비율은 <b>'+UQ.pct(k.coverage95)+'</b>에 머물렀습니다.</p></article>';
  if(part==='accuracy')return accuracy;
  if(part==='spatial')return spatial;
  return '<div class="pair">'+accuracy+spatial+'</div>'+
    '<p class="caption">IMPTC Test · 같은 237개 예측 시점 / 120건의 횡단 · IID 1×. ADE는 4초간 대표 경로의 평균 위치 오차(n=215), Brier는 완료확률과 실제 0·1 결과의 제곱오차(n=218)입니다. Coverage는 4초 위치 포함률(n=228), HDR 면적은 95% 최고밀도영역의 넓이(n=237)입니다. '+UQ.source('r_robustness/r_robustness_metrics.csv')+'</p>';
}
function uqTraining() {
  const [old,next]=['original','exit_aware'].map(v=>UQ.evidence.audit.support.find(row=>row.version===v));
  return pTable(['학습 자료','기존','Exit-aware'],[
    ['예측 시작 시점 수',old.n_train_origins.toLocaleString('en-US'),next.n_train_origins.toLocaleString('en-US')],
    ['최소 잔여 거리',PN(old.min_distance_m,2)+' m',PN(next.min_distance_m,3)+' m'],
    ['Exit 1 m 이내 시점',old.n_train_lt1,next.n_train_lt1]
  ]);
}
function uqM1() {
  const [old,next]=['M1__calibrated','EA_M1__calibrated'].map(model=>UQ.evidence.key_table.find(r=>r.model===model));
  return pTable(['평가 지표','기존 M1','Exit-aware M1','감소율'],[['H1–H4 평균','mean_brier'],['H1','h1']].map(([label,k])=>[label,PN(old[k],5),PN(next[k],5),'<b>'+UQ.reduction(Number(PN(old[k],5)),Number(PN(next[k],5)))+'</b>']))+
    '<p class="caption">IMPTC Test · 동일한 236개 시점 / 120건의 횡단 · 보정된 XGBoost AFT M1. 사건별 가중 Brier가 낮을수록 좋으며, 평균은 1~4초 점수의 산술평균입니다. 감소율은 표에 표시한 값 기준입니다. '+UQ.source('exit_aware/exit_aware_matched_metrics.csv')+'</p>';
}

// Camera and inset extents are shared by every condition for a given case/scenario/H.
function uqComparisonExtent(st) {
  const s=st.data, edges=['end_A','end_B'].map(end=>V2R.boundary(s.geometry,end));
  const all=edges.flat(), histories=[];
  for(const key of ['clean',st.scenario+'__noisy',st.scenario+'__filtered_mean']){
    const r=s.r.results[key],i=r.future_times_s.indexOf(st.h);
    histories.push(...r.input.observed_xy);
    all.push(...r.regions[i]['0.95'].flat(),...r.regions[i]['0.68'].flat(),...r.hypotheses_xy.flatMap(path=>path.slice(0,i+1)));
  }
  return {all:all.concat(histories),histories,edges};
}
function uqRecordedCursor(plot,s){
  return '<polyline data-recorded-path="" points="'+plot.points(s.c.actual_observations.xy)+'" visibility="hidden"/>'+
    '<circle data-actual-cursor="" r="5" fill="'+UQ.colors.gt+'" stroke="white" stroke-width="2"/>';
}
function uqReplayDot(color) {
  return '<circle data-replay-cursor="" r="6" fill="'+color+'" stroke="white" stroke-width="2"/>';
}
function uqReplayInset(st) {
  const s=st.data,r=st.result, obs=st.stage===2,extent=uqComparisonExtent(st);
  const noisy=s.r.results[st.scenario+'__noisy'],corrected=s.r.results[st.scenario+'__filtered_mean'];
  const local=st.view==='full';
  const ellipse=uqEllipse(corrected.filter.filter_R,noisy.input.observed_xy[corrected.filter.observed_points-1]);
  const points=obs?extent.histories.concat(ellipse):local?extent.edges.flat():extent.all;
  const project=obs?p=>p:crossingAxes(s);
  const p=uqProjection(points,350,200,project);
  const xy=r.input.observed_xy;
  let b='';
  if(!obs){
    const idx=r.future_times_s.indexOf(st.h);
    for(const [i,path] of extent.edges.entries())b+=uqLine(p,path,(i===1)===(s.c.direction===1)?'#b87508':'#527381',2.7);
    for(const level of ['0.95','0.68'])b+=polygon(p,r.regions[idx][level],level);
    const best=r.hypothesis_confidence_scores.indexOf(Math.max(...r.hypothesis_confidence_scores));
    r.hypotheses_xy.forEach((path,i)=>{b+=uqLine(p,[xy.at(-1),...path.slice(0,idx+1)],UQ.colors.future,i===best?3:1,i===best?'data-replay-path=""':'opacity=".42"');});
    if(st.truth)b+=uqLine(p,[s.clean.input.observed_xy.at(-1),...s.r.future_GT_xy.slice(0,idx+1)],UQ.colors.gt,2.8,'stroke-dasharray="4 2"');
  }
  const allThree=obs&&st.compare;
  if(st.mode!=='clean'||allThree)b+=uqLine(p,s.clean.input.observed_xy,UQ.colors.clean,2.2);
  if(st.mode==='filtered_mean'||allThree)b+=uqLine(p,noisy.input.observed_xy,UQ.colors.noisy,2.2,'stroke-dasharray="4 3" opacity=".65"');
  if(allThree&&st.mode!=='filtered_mean')b+=uqLine(p,corrected.input.observed_xy,UQ.colors.filtered_mean,3.2);
  if(obs&&(st.mode!=='clean'||allThree))b+=uqLine(p,ellipse,UQ.colors.noisy,1.5,'stroke-dasharray="4 3"');
  b+=uqLine(p,xy,UQ.colors[st.mode],3.2,obs?'data-replay-path=""':'')+dot(p.xy(xy.at(-1)),5,UQ.colors[st.mode]);
  if(st.truth)b+=uqRecordedCursor(p,s);
  b+=uqReplayDot(obs?UQ.colors[st.mode]:UQ.colors.future);
  const metres=obs?.25:local?1:5;
  b+=uqScale(p.scale,metres,200);
  const caption=obs?'관측 위치 확대':local?'횡단부 확대':'전체 예측영역';
  return '<div class="inset-title">'+caption+' · 공통 축척</div>'+svgFrame(caption,b,350,200);
}
