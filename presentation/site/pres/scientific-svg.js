'use strict';
// Diagram geometry is illustrative only in the explicitly labelled concept panels.
// Measured plots project saved world coordinates with one isotropic metre scale.
const SC=UQ.colors;
function svgFrame(title,body,w=640,h=300){
  return '<svg class="science-svg" viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+PE(title)+'"><title>'+PE(title)+'</title>'+body+'</svg>';
}
function ink(x,y,text,color='#263e48',anchor='start',size=17){
  return '<text x="'+x+'" y="'+y+'" fill="'+color+'" text-anchor="'+anchor+'" font-size="'+size+'">'+PE(text)+'</text>';
}
function segment(x,y,u,v,color,width=1.6,dash=''){
  return '<line x1="'+x+'" y1="'+y+'" x2="'+u+'" y2="'+v+'" stroke="'+color+'" stroke-width="'+width+'" stroke-dasharray="'+dash+'"/>';
}
function dot([x,y],r,color){
  return '<circle cx="'+x+'" cy="'+y+'" r="'+r+'" fill="'+color+'" stroke="white" stroke-width="1"/>';
}
function callout(label,point,x,y,color,anchor='start'){
  return segment(x,y+4,...point,color,1.15)+dot(point,2.4,color)+ink(x,y,label,color,anchor);
}
function projectFigure(points,transform,w=640,h=310) {
  const p=uqProjection(points,w-70,h-76,transform);
  const xy=v=>{const [x,y]=p.xy(v);return [x+40,y+35];};
  return {scale:p.scale,xy,points:path=>path.map(v=>xy(v).join(',')).join(' ')};
}
function crossingAxes(s){
  const [a,b]=[s.geometry.axis,s.geometry.normal],o=s.clean.input.observed_xy.at(-1),dir=s.c.direction;
  return p=>[a,b].map(axis=>dir*((p[0]-o[0])*axis[0]+(p[1]-o[1])*axis[1]));
}
function ruler(plot,len,xaxis='횡단 방향',yaxis='측방향'){
  const y=280;
  return segment(37,y,37+plot.scale*len,y,'#395563',2.6)+ink(37,y-7,len+' m','#395563','start',15)+
    ink(622,295,xaxis+' → (m)','#506575','end',15)+ink(18,21,'↑ '+yaxis+' (m)','#506575','start',15);
}
function polygon(plot,paths,level){
  const d=paths.map(poly=>'M'+poly.map(p=>plot.xy(p).join(',')).join('L')+'Z').join('');
  return '<path d="'+d+'" fill="'+SC.future+'" fill-rule="evenodd" fill-opacity="'+(level==='0.95'?.11:.29)+'" stroke="'+SC.future+'" stroke-width="1.5" stroke-dasharray="'+(level==='0.95'?'5 3':'')+'"/>';
}
function figObservation(s){
  const clean=s.clean.input.observed_xy,n=s.r.results.iid_1__noisy.input.observed_xy,k=s.r.results.iid_1__filtered_mean;
  const corrected=k.input.observed_xy, ellipse=uqEllipse(k.filter.filter_R,n.at(-1));
  const p=projectFigure([...clean,...n,...corrected,...ellipse],v=>v);
  let body='<polygon points="'+p.points(ellipse)+'" fill="#f3d4b9" fill-opacity=".55" stroke="'+SC.noisy+'" stroke-dasharray="4 3"/>';
  for(const [path,c,dash] of [[clean,SC.clean,''],[n,SC.noisy,'4 3'],[corrected,SC.filtered_mean,'']]){
    body+=uqLine(p,path,c,2.6,'stroke-dasharray="'+dash+'"')+path.map(q=>dot(p.xy(q),3.6,c)).join('');
  }
  return svgFrame('동일한 IMPTC f2 과거 10개 시점',body+
    callout('기준 위치',p.xy(clean[3]),455,44,SC.clean)+callout('합성 관측',p.xy(n[3]),470,126,SC.noisy)+
    callout('칼만 보정',p.xy(corrected[7]),460,210,SC.filtered_mean)+callout('측정오차 95% 타원',p.xy(ellipse[38]),16,218,SC.noisy)+
    ruler(p,.25,'X','Y'),640,310);
}
function figForecast(s){
  const r=s.clean,past=r.input.observed_xy,best=r.hypothesis_confidence_scores.indexOf(Math.max(...r.hypothesis_confidence_scores));
  const paths=r.hypotheses_xy.map(path=>[past.at(-1),...path]),rep=paths[best],gt=s.r.future_GT_xy,region=r.regions[7];
  const p=projectFigure([...past,...paths.flat(),...gt,...Object.values(region).flat(2)],crossingAxes(s));
  let body=polygon(p,region['0.95'],'0.95')+polygon(p,region['0.68'],'0.68');
  for(const path of paths)body+=uqLine(p,path,SC.future,1,'opacity=".42"');
  body+=uqLine(p,rep,SC.future,3.7)+rep.slice(1).map(q=>dot(p.xy(q),3.6,SC.future)).join('')+
    uqLine(p,past,SC.clean,2.5)+past.map(q=>dot(p.xy(q),3.7,SC.clean)).join('')+
    uqLine(p,[past.at(-1),...gt],SC.gt,2.8,'stroke-dasharray="6 4"');
  return svgFrame('사전학습 DD-MDN의 실제 입력과 출력',body+
    callout('과거 10점 · 0.9초',p.xy(past[4]),35,90,SC.clean)+callout('대표 경로 · 8개 시각',p.xy(rep[4]),245,57,SC.future)+
    callout('가는 선 · 경로 후보',p.xy(paths[1][6]),497,37,SC.future,'end')+
    callout('+4초 · 68% / 95% 영역',p.xy(region['0.95'][0][0]),620,243,SC.future,'end')+
    callout('실제 미래',p.xy(gt[3]),245,249,SC.gt)+ruler(p,1),640,310);
}
function figFramework(){
  const dark='#334e58', linked='#637983';
  const arrow=(x,y,u,v)=>'<path d="M'+x+' '+y+'L'+u+' '+v+'" stroke="'+linked+'" stroke-width="2" fill="none" marker-end="url(#flow-tip)"/>';
  const box=(x,y,w,label,color)=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="38" rx="3" fill="white" stroke="'+color+'"/>'+ink(x+w/2,y+25,label,color,'middle',18);
  let b='<defs><marker id="flow-tip" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L8 4L0 8Z" fill="'+linked+'"/></marker></defs>';
  b+=ink(10,23,'경로 기반',SC.future)+ink(384,23,'시간 직접 추정','#355966')+
    box(10,37,331,'보행 위치 관측',SC.clean)+box(378,37,222,'거리 · 속도 · 가속도',dark)+
    arrow(60,75,60,150)+arrow(238,75,238,88)+box(123,90,218,'Kalman 보정 (비교 실험)',SC.filtered_mean)+
    arrow(238,128,238,150)+box(10,152,331,'사전학습 DD-MDN',SC.future)+
    arrow(175,190,175,205)+box(10,207,331,'확률적 미래 경로',SC.future)+
    arrow(90,245,90,266)+arrow(257,245,257,266)+box(10,268,159,'시점별 위치 영역',SC.future)+
    box(179,268,162,'Exit 통과확률',SC.future)+
    arrow(489,75,489,150)+box(378,152,222,'별도 학습 XGBoost AFT',dark)+
    arrow(489,190,489,205)+box(378,207,222,'잔여시간 분포',dark)+
    arrow(489,245,489,266)+box(378,268,222,'기한별 완료확률',dark)+
    arrow(90,306,90,327)+arrow(257,306,257,327)+arrow(489,306,489,327)+
    box(10,329,590,'실제 미래 위치 · 실제 Exit 통과와 대조',dark);
  return svgFrame('보행 기록에서 출발하는 두 예측 방법과 공통 정답 평가',b,610,376);
}
function figDistances(s){
  const r=s.r.results.iid_1__noisy, path=r.hypotheses_xy[r.hypothesis_confidence_scores.indexOf(Math.max(...r.hypothesis_confidence_scores))],gt=s.r.future_GT_xy;
  const p=projectFigure([...path,...gt],crossingAxes(s));
  let body='<defs><marker id="err-tip" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#526772"/></marker></defs>';
  path.forEach((q,i)=>{const [x,y]=p.xy(q),[u,v]=p.xy(gt[i]);body+='<path d="M'+x+' '+y+'L'+u+' '+v+'" stroke="#526772" stroke-width="'+(i===7?2.5:1.3)+'" stroke-dasharray="3 2" marker-end="url(#err-tip)"/>';});
  body+=uqLine(p,path,SC.future,3)+uqLine(p,gt,SC.gt,2.8,'stroke-dasharray="6 3"')+
    path.map(q=>dot(p.xy(q),4,SC.future)).join('')+gt.map(q=>dot(p.xy(q),4,SC.gt)).join('');
  const last=p.xy(path[7]).map((v,k)=>(v+p.xy(gt[7])[k])/2);
  return svgFrame('동일 시각의 대표 예측과 실제 위치 사이 거리',body+
    callout('대표 예측 위치',p.xy(path[3]),135,48,SC.future)+callout('실제 위치',p.xy(gt[4]),130,240,SC.gt)+
    callout('마지막 거리 d₈',last,610,75,'#364b59','end')+ruler(p,1),640,310);
}
function figHdr(){
  let b='<ellipse cx="149" cy="91" rx="105" ry="54" fill="#eeebf6" stroke="'+SC.future+'" stroke-dasharray="5 3"/><ellipse cx="149" cy="91" rx="56" ry="28" fill="#c3b8de" stroke="'+SC.future+'"/>';
  b+=ink(149,97,'HDR68',SC.future,'middle')+ink(152,52,'HDR95',SC.future,'middle')+
    dot([176,113],6,SC.gt)+callout('실제 위치 · 포함',[176,113],280,102,SC.gt)+dot([272,48],6,SC.gt)+ink(286,54,'실제 위치 · 밖',SC.gt);
  return svgFrame('한 시각의 위치 분포와 두 가지 정답 위치 예시',b,440,155);
}
function figCoverage(rows){
  const x=a=>66+(Math.log10(a)-Math.log10(4))/(3-Math.log10(4))*480,y=c=>209-(c-.68)/.32*160;
  let b=ink(15,24,'95% 범위의 실제 적중률 (%)')+segment(66,48,66,209,'#657980')+segment(66,209,552,209,'#657980');
  for(const v of [.7,.8,.9,.95,1]){
    b+=segment(66,y(v),552,y(v),v===.95?'#6f568c':'#dce3e5',v===.95?2:1,v===.95?'6 4':'')+ink(57,y(v)+5,Math.round(v*100),'#526772','end',15);
  }
  for(const a of [5,10,100,1000])b+=segment(x(a),209,x(a),215,'#657980')+ink(x(a),235,a,'#526772','middle',15);
  b+=ink(316,262,'95% 영역 면적 (m², 로그 눈금)','#344854','middle')+ink(540,y(.95)-6,'목표 95%','#705a85','end',15);
  for(const r of rows){
    const pt=[x(r.hdr95_area_m2),y(r.coverage95)],right=r.mode==='noisy';
    const dx=right?-10:10,anchor=right?'end':'start';
    b+=dot(pt,6.5,SC[r.mode])+ink(pt[0]+dx,pt[1]-5,UQ.names[r.mode],SC[r.mode],anchor,16)+
      ink(pt[0]+dx,pt[1]+13,UQ.pct(r.coverage95)+' · '+PN(r.hdr95_area_m2,2)+' m²',SC[r.mode],anchor,15);
  }
  return svgFrame('4초 후 Coverage95와 HDR95 면적의 관계',b,580,270);
}
function figCrossing(){
  const y=96,entry=52,exit=332;
  let b='<rect x="52" y="41" width="280" height="103" fill="#f0f4f4"/>'+segment(entry,38,entry,149,'#637c88',2,'4 3')+segment(exit,38,exit,149,'#b87508',3)+ink(entry,29,'Entry','#516773','middle')+ink(exit,29,'Exit','#b87508','middle');
  for(let i=0;i<10;i++){
    const success=i<6,end=success?356+6*i:260+11*(i-6),v=53+8*i;
    b+='<path d="M118 96Q218 '+y+' '+end+' '+v+'" stroke="'+SC.future+'" fill="none" stroke-width="1.8" stroke-dasharray="'+(success?'':'4 3')+'"/>'+dot([end,v],2.8,SC.future);
  }
  return svgFrame('개념도. H초 안에 표본 경로 10개 중 6개가 출구를 통과',b+dot([118,y],6,SC.clean)+ink(80,132,'현재 위치',SC.clean)+ink(404,65,'통과 6',SC.future)+ink(214,153,'미통과 4',SC.future)+ink(472,177,'개념도 · 비례 축척 없음','#657980','end',14),485,185);
}
function figBrier(){
  const x=p=>38+350*p,y=54;
  return svgFrame('개념 예시. 80% 예측과 완료 정답 1',segment(x(0),y,x(1),y,'#cad4d7',4)+
    segment(x(.8),y,x(1),y,SC.future,4)+dot([x(.8),y],6,SC.future)+dot([x(1),y],6,SC.gt)+
    ink(x(.8)-6,31,'예측 p = 0.8',SC.future,'end')+ink(x(1),28,'정답 y = 1',SC.gt,'middle')+
    ink(x(0),80,'0','#526772','middle')+ink(215,88,'차이 0.2 → 제곱오차 0.04','#263e48','middle'),450,96);
}
function figTraining(){
  const versions=UQ.evidence.audit.support;
  const maximum=Math.max(...versions.map(row=>row.n_train_origins));
  const labels=['1 m 미만','1~2 m 미만','2 m 이상'],palette=['#94610d','#527884','#c8d5d6'];
  let b='';
  for(const [i,r] of versions.entries()){
    const y=19+78*i;
    b+=ink(24,y,r.version==='original'?'기존 M1':'Exit-aware M1')+ink(602,y,r.n_train_origins.toLocaleString('en-US')+'개','#344954','end');
    let x=24;const counts=[r.n_train_lt1,r.n_train_lt2-r.n_train_lt1,r.n_train_origins-r.n_train_lt2];
    counts.forEach((n,j)=>{const width=n/maximum*578;b+='<rect x="'+x+'" y="'+(y+8)+'" width="'+width+'" height="22" fill="'+palette[j]+'"/>';x+=width;});
    b+=ink(24,y+51,labels.map((name,j)=>name+' '+counts[j].toLocaleString('en-US')+'개').join('  ·  '),'#435a63','start',16);
  }
  return svgFrame('학습 시점 분포. 같은 개수 축척의 거리 구간별 누적 막대',b,628,159);
}
function figQuestions(){
  let body='<rect x="88" y="66" width="392" height="132" fill="#eef3f1"/>';
  body+=segment(88,56,88,205,'#597687',2,'5 4')+segment(480,56,480,205,'#b87508',3)+ink(88,45,'Entry','#526772','middle')+ink(480,45,'Exit','#b87508','middle');
  body+=segment(100,145,191,133,SC.clean,4)+dot([191,133],7,SC.clean);
  for(const [x,y] of [[397,92],[511,124],[544,171]])body+='<path d="M191 133 Q315 130 '+x+' '+y+'" fill="none" stroke="'+SC.future+'" stroke-width="2"/>';
  return svgFrame('개념도. 현재 위치에서 여러 미래와 기한 안의 Exit 통과를 묻는다',body+
    callout('① 현재 위치',[191,133],110,244,SC.clean)+callout('② 가능한 미래',[355,110],235,45,SC.future)+
    callout('③ 기한 안에 통과?',[480,123],570,242,'#925c06','end'),620,265);
}
function figSources(){
  const left=ink(25,34,'과거의 한 시각','#35535e')+
    '<ellipse cx="134" cy="114" rx="52" ry="35" fill="#fff4e8" stroke="'+SC.noisy+'" stroke-dasharray="4 3"/>'+
    dot([127,124],7,SC.clean)+dot([154,99],7,SC.noisy)+callout('기준 위치',[127,124],26,181,SC.clean)+callout('합성 관측',[154,99],185,74,SC.noisy);
  const start=[353,126];let right=ink(339,34,'같은 과거 이후','#35535e')+segment(323,128,...start,SC.clean,4);
  for(const [x,y] of [[552,64],[566,119],[551,164]])right+='<path d="M353 126Q453 124 '+x+' '+y+'" fill="none" stroke="'+SC.future+'" stroke-width="2"/>';
  return svgFrame('개념도. 관측 위치의 흔들림과 미래 경로의 퍼짐',left+segment(300,36,300,183,'#d9e2e1')+right+dot(start,6,SC.clean)+ink(363,194,'움직임에 따라 갈라지는 미래',SC.future),610,217);
}

// Both comparisons use linear bars from zero. Direct labels carry the saved precision.
function figGroupedBars({title,groups,series,maximum,ticks,axis,decimals}){
  const left=90,right=533,top=67,barHeight=13,step=25;
  const groupHeight=series.length*step+15;
  const bottom=top+groups.length*groupHeight-14;
  const x=v=>left+(right-left)*v/maximum;
  let body=ink(left,22,axis,'#344954','start',16);
  series.forEach(({label,color},i)=>{
    const xpos=left+i*137;
    body+=segment(xpos,45,xpos+17,45,color,6)+ink(xpos+23,50,label,color,'start',16);
  });
  for(const t of ticks){
    body+=segment(x(t),top-5,x(t),bottom,'#d7e0df')+ink(x(t),bottom+22,t,'#526772','middle',15);
  }
  for(const [i,g] of groups.entries()){
    const y=top+i*groupHeight;
    body+=ink(left-14,y+(series.length-1)*step/2+10,g.label,'#273f48','end',18);
    for(const [j,v] of g.values.entries()){
      const by=y+j*step;
      body+='<rect x="'+left+'" y="'+by+'" width="'+(x(v)-left)+'" height="'+barHeight+'" fill="'+series[j].color+'"/>'+
        ink(x(v)+7,by+12,PN(v,decimals),series[j].color,'start',16);
    }
  }
  return svgFrame(title,body,620,bottom+32);
}

function figCompletionBars(s){
  const p=s.clean.exit.probabilities,exit=s.e.GT.exit_s-s.r.origin_s;
  const left=86,width=249;
  let body=ink(left,20,'기한 안에 완료할 확률','#405761','start',16)+ink(461,20,'실제 결과',SC.gt,'middle',16);
  for(const [i,h] of UQ.horizons.entries()){
    const y=41+30*i;
    body+=ink(78,y+10,h+'초 안에','#344954','end',16)+segment(left,y+5,left+width,y+5,'#e7e3ef',9)+
      segment(left,y+5,left+width*p[h],y+5,SC.future,9)+ink(394,y+10,UQ.pct(p[h]),SC.future,'end',16)+
      ink(461,y+10,exit<=h?'완료':'미완료',SC.gt,'middle',16);
  }
  return svgFrame('IMPTC f2의 네 기한별 완료확률과 실제 완료 여부',body,510,158);
}

// Each vertex is a released CDF sample (time in seconds, cumulative probability).
function figAftCdf(s,model,remaining){
  const points=V2R.curve(s,model);
  const x=t=>45+220*t/4,y=p=>107-74*p;
  let body='';
  for(const p of [0,.5,1]){
    body+=segment(45,y(p),265,y(p),'#dae2e2')+ink(38,y(p)+4,100*p+'%','#526772','end',15);
  }
  for(const h of [0,...UQ.horizons])body+=ink(x(h),126,h+'초','#526772','middle',15);
  body+='<polyline fill="none" stroke="'+SC.future+'" stroke-width="3" points="'+points.map(([t,p])=>x(t)+','+y(p)).join(' ')+'"/>';
  body+=segment(x(remaining),29,x(remaining),107,SC.gt,2,'4 3')+
    ink(x(remaining),18,'실제 통과 +'+PN(remaining,3)+'초',SC.gt,'middle',17);
  return svgFrame('f2의 저장된 잔여시간 누적분포와 실제 Exit 통과 시각',body,286,134);
}
