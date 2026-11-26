'use strict';

function mountDemonstration(root, data) {
  let release, revision=0;
  function open(full) {
    const token=++revision;
    release?.();release=null;
    const body=document.createElement('div');
    root.replaceChildren(body);
    if(!full){
      release=mountGuided(body,data);
      const back=document.createElement('button');
      back.id='showTracking';back.textContent='← f2 전체 위치 추적';
      back.onclick=()=>open(true);
      body.querySelector('.g-head nav').prepend(back);
      return;
    }
    body.textContent='f2 전체 횡단 기록을 읽는 중입니다.';
    V2R.json('demo/f2-full-track.json').then(track=>{
      if(token!==revision)return;
      if(track.event_id!==data.c.event_id)throw Error('f2 기록 식별자 불일치');
      release=mountTracking(body,data,track,()=>open(false));
    }).catch(error=>{
      if(token!==revision)return;
      body.textContent='';bodyError(body,error);
      const button=document.createElement('button');
      button.textContent='저장된 미래 예측 열기';button.onclick=()=>open(false);body.append(button);
    });
  }
  open(true);
  return ()=>{revision++;release?.();};
}

function mountTracking(root,data,track,openForecast){
  const modes=Object.keys(UQ.names), descriptions={clean:'기준 위치',noisy:'합성 관측',filtered_mean:'칼만 보정'};
  const buttons=modes.map(mode=>'<button data-track-mode="'+mode+'" style="--condition:'+UQ.colors[mode]+'">'+UQ.names[mode]+' · '+descriptions[mode]+'</button>').join('');
  const times=track.elapsed_s,end=times.at(-1), rec={xy:track.clean,elapsed_s:times};
  const st={data,record:rec,stage:5,single:true,time:0,running:false};
  let selection='all',index=-1,lastStamp=0,world,drawTraces,fallbackFrame=0,disposed=false;
  root.className='guided full-tracking';
  root.innerHTML='<div class="g-head"><strong>전체 위치 추적 · IMPTC f2</strong><button id="showForecast">저장된 미래 예측 보기 →</button></div>'+
    '<div class="g-grid"><section class="g-viewport"><div class="track-conditions" role="group" aria-label="표시할 관측"><button data-track-mode="all">세 조건 겹쳐 보기</button>'+buttons+'</div>'+
    '<div class="g-views"><canvas id="gCanvas" aria-label="같은 보행자의 Entry부터 Exit까지 위치 추적"></canvas><div id="gFallback" hidden></div>'+
    '<div class="g-map-tools"><button id="trackCross">횡단부</button><button id="trackTop">상단 보기</button></div></div></section>'+
    '<aside class="g-info"><div class="g-meta">한 보행 기록 · 합성 독립 오차 1×</div><h2>현재 관측 위치의 오차</h2>'+
    '<p>사람은 파란 기준 경로를 걷습니다. 주황 고리는 오차를 더한 관측, 청록 고리는 그때까지의 관측으로 보정한 위치입니다.</p>'+
    '<h3>기준 위치에서 본 차이</h3><svg id="trackDetail" viewBox="0 0 300 116" role="img" aria-label="지도 X/Y축에서 기준 위치를 중심으로 본 관측 위치 차이"></svg>'+
    '<div class="g-kpis"><div><small>합성 관측 오차</small><strong id="trackNoisy"></strong></div><div><small>보정 후 오차</small><strong id="trackCorrected"></strong></div></div>'+
    '<small id="trackInstant">이 시각의 기준 위치까지 직선거리입니다. 세 궤적은 Entry에서 같은 위치로 시작합니다.</small><p id="trackSummary" class="caption" hidden></p></aside></div>'+
    '<div class="g-controls"><div class="g-time"><button id="gPlay"></button><button id="gReset">Entry로</button><label for="gTime">Entry → Exit</label><input id="gTime" type="range" min="0" step="any"><output for="gTime" id="gClock"></output></div></div>';
  const get=id=>root.querySelector('#'+id);
  get('showForecast').onclick=openForecast;
  const slider=get('gTime'), canvas=get('gCanvas'), fallback=get('gFallback');
  slider.max=end;
  const meanCm=mode=>100*track[mode].reduce((sum,[x,y],i)=>
    sum+Math.hypot(x-track.clean[i][0],y-track.clean[i][1]),0)/times.length;
  const noisyMean=meanCm('noisy'),correctedMean=meanCm('filtered_mean');
  get('trackSummary').textContent='f2 한 건 · '+times.length+'시점의 평균 관측 위치 오차: Noisy '+PN(noisyMean,2)+' cm → Corrected '+PN(correctedMean,2)+' cm ('+UQ.reduction(noisyMean,correctedMean)+' 감소).';
  const edges=(data.c.direction===1?['end_A','end_B']:['end_B','end_A']).map(k=>V2R.boundary(data.geometry,k));
  const project=p=>[data.geometry.axis,data.geometry.normal].map(a=>data.c.direction*(p[0]*a[0]+p[1]*a[1]));
  const plot=uqProjection([...edges.flat(),...modes.flatMap(m=>track[m])],680,270,project);
  const maxError=Math.max(...modes.flatMap(m=>track[m].map((p,i)=>Math.hypot(p[0]-track.clean[i][0],p[1]-track.clean[i][1]))));
  const scale=50/Math.max(.5,maxError);
  const dot=(x,y,r,color)=>'<circle cx="'+x+'" cy="'+y+'" r="'+r+'" fill="'+color+'" stroke="white" stroke-width="1"/>';
  function drawDetail(){
    const clean=track.clean[index],detail=get('trackDetail');
    let graphic='<path d="M65 57H235 M150 4V110" fill="none" stroke="#c5d1d5" stroke-dasharray="3 3"/><g font-size="11" fill="#435762"><text x="238" y="61">+X</text><text x="156" y="12">+Y</text></g>';
    for(const mode of modes){
      if(mode!=='clean'&&selection!=='all'&&selection!==mode)continue;
      const [x,y]=track[mode][index],cx=150+(x-clean[0])*scale,cy=57-(y-clean[1])*scale;
      graphic+='<path d="M150 57L'+cx+' '+cy+'" stroke="'+UQ.colors[mode]+'"/>'+dot(cx,cy,mode==='clean'?6:4,UQ.colors[mode]);
    }
    detail.innerHTML=graphic+'<path d="M8 100h'+scale*.25+'" stroke="#435762" stroke-width="2"/><text x="8" y="92" font-size="12">25 cm</text>';
    for(const [mode,id] of [['noisy','trackNoisy'],['filtered_mean','trackCorrected']]){
      const [x,y]=track[mode][index];get(id).textContent=(100*Math.hypot(x-clean[0],y-clean[1])).toFixed(1)+' cm';
    }
  }
  function drawFallback(){
    let svg='';
    for(const [j,line] of edges.entries()){
      const [x,y]=plot.xy(line[0]);
      svg+=uqLine(plot,line,j?'#b87508':'#336386',3)+'<text x="'+x+'" y="'+(y-7)+'" text-anchor="middle">'+(j?'Exit':'Entry')+'</text>';
    }
    for(const mode of modes){
      if(selection!=='all'&&selection!==mode)continue;
      const path=track[mode].slice(0,index+1),[x,y]=plot.xy(path.at(-1));
      svg+=uqLine(plot,path,UQ.colors[mode],mode==='noisy'?1.7:2.6)+dot(x,y,4,UQ.colors[mode]);
    }
    const [x,y]=plot.xy(track.clean[index]);
    fallback.innerHTML='<svg viewBox="0 0 680 270" class="field" role="img" aria-label="2D 횡단보도 위치 추적">'+svg+'<circle cx="'+x+'" cy="'+y+'" r="7" fill="none" stroke="'+UQ.colors.clean+'"/>'+uqScale(plot.scale,1,270)+'</svg>';
  }
  function paint(force=false){
    if(disposed)return;
    const now=performance.now();
    if(st.running){
      st.time=Math.min(end,st.time+(now-lastStamp)/1000);
      if(st.time>=end){st.running=false;force=true;}
    }
    lastStamp=now;
    const next=times.findLastIndex(t=>t<=st.time+1e-9);
    if(next===index&&!force)return;
    index=next;root.dataset.index=index;
    const complete=index===times.length-1;
    get('trackInstant').hidden=complete;
    get('trackSummary').hidden=!complete;
    slider.value=st.time;
    get('gClock').textContent=st.time.toFixed(2)+' s / '+end.toFixed(2)+' s';
    get('gPlay').textContent=st.running?'Ⅱ 일시정지':st.time>=end?'▶ 다시 재생':'▶ 전체 횡단 재생';
    if(world){world.pose(st,index,true);drawTraces(index,selection);}
    else drawFallback();
    drawDetail();
  }
  function choose(mode){
    selection=mode;root.dataset.mode=mode;
    root.querySelectorAll('[data-track-mode]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.trackMode===mode));
    paint(true);
  }
  root.querySelectorAll('[data-track-mode]').forEach(b=>b.onclick=()=>choose(b.dataset.trackMode));
  get('gPlay').onclick=()=>{if(!st.running&&st.time>=end)st.time=0;st.running=!st.running;lastStamp=performance.now();paint(true);};
  get('gReset').onclick=()=>{st.running=false;st.time=0;paint(true);};
  slider.oninput=()=>{st.running=false;st.time=+slider.value;paint(true);};
  try{
    world=guidedWorld(canvas,data,paint);
    drawTraces=world.trackingLayers(track);
    function view(kind){
      world.view(data,kind,st);
      get('trackCross').setAttribute('aria-pressed',kind==='crossing');
      get('trackTop').setAttribute('aria-pressed',kind==='top');
    }
    get('trackCross').onclick=()=>view('crossing');get('trackTop').onclick=()=>view('top');
    view('crossing');root.dataset.renderer='babylon';
  }catch(error){
    world?.dispose();world=null;
    canvas.hidden=true;fallback.hidden=false;root.dataset.renderer='2d';
    root.querySelector('.g-map-tools').textContent='2D 기록 보기';
    function loop(){if(!disposed){paint();fallbackFrame=requestAnimationFrame(loop);}}
    fallbackFrame=requestAnimationFrame(loop);
  }
  choose('all');
  return ()=>{disposed=true;cancelAnimationFrame(fallbackFrame);world?.dispose();};
}
