'use strict';

const GUIDE_STAGES=[
  ['실제 보행','재생하면 예측 시점에서 멈춥니다. 이때 이후의 움직임은 아직 알 수 없습니다.'],
  ['관측 오차','기준·합성·보정 관측을 바꿔 보세요. 합성 오차의 타원은 저장된 측정 공분산 R에서 계산했습니다.'],
  ['미래 운동','가는 선은 미래 경로 후보, 굵은 선은 대표 경로입니다. 영역은 선택 시각의 위치 분포입니다.'],
  ['횡단 완료','각 막대는 그 시간 안에 Exit를 지날 확률입니다. 정답을 열어 실제 통과와 비교하세요.']
];
function mountGuided(root,initial) {
  const st={data:initial,stage:1,h:3,mode:'clean',scenario:'iid_1',truth:false,running:false,time:0};
  let world,disposed=false,revision=0,lastStamp=0,lastFrame=-2,fallbackFrame=0,overlayKey;
  const $g=id=>root.querySelector('#g'+id);
  const origin=()=>st.data.r.elapsed_s;
  const start=()=>Math.max(st.data.c.actual_observations.elapsed_s[0],origin()-4);
  const end=()=>st.truth?Math.min(origin()+st.h,st.data.c.actual_observations.elapsed_s.at(-1)):origin();
  const result=()=>st.data.r.results[st.mode==='clean'?'clean':st.scenario+'__'+st.mode];
  st.time=start();
  root.classList.add('guided');
  root.innerHTML='<div class="g-head"><nav aria-label="3D 시연 단계">'+GUIDE_STAGES.map(([name],i)=>'<button data-stage="'+(i+1)+'">'+(i+1)+'　'+name+'</button>').join('')+'</nav>'+
    uqSelect('gCase','기록',V2R.ri.map(r=>[r.uid,r.location+' · '+r.event_id.slice(-2)+' · +'+r.origin_s+'초']),initial.r.uid)+'</div>'+
    '<div class="g-grid"><section class="g-viewport"><canvas id="gCanvas" aria-label="IMPTC 기록의 3D 횡단보도와 보행자"></canvas><div id="gFallback" hidden></div><div class="g-map-tools"><button id="gTop">위에서 보기</button></div><div id="gLegend"></div></section>'+
    '<aside class="g-info"><div class="g-meta" id="gMeta"></div><h2 id="gStageTitle"></h2><p id="gText"></p><div class="g-kpis"><div><small id="gDistanceLabel">Exit까지 거리</small><strong id="gDistance"></strong></div><div><small id="gSpeedLabel">종방향 속도</small><strong id="gSpeed"></strong></div></div><div id="gProb"></div><div id="gOutcome"></div></aside></div>'+
    '<div class="g-controls"><div class="g-time"><button id="gPlay">▶ 재생</button><button id="gReset">처음부터</button><label for="gTime">기록 시간</label><input id="gTime" type="range" step="any"><output for="gTime" id="gClock"></output></div>'+
    '<div class="g-settings">'+uqSelect('gMode','관측',Object.entries(UQ.names),'clean')+uqSelect('gNoise','오차',UQ_SCENARIOS,'iid_1')+
    uqSelect('gH','예측 시간',UQ.horizons.map(h=>[h,h+'초']),3)+'<button id="gReveal">실제 정답 공개</button><button id="gCamera">카메라 초기화</button><button id="gNext">다음 단계 →</button></div></div>';
  const canvas=$g('Canvas'),fallback=$g('Fallback');
  const status=()=>{root.dataset.stage=st.stage;root.dataset.uid=st.data.r.uid;root.dataset.truth=st.truth;root.dataset.mode=st.mode;root.dataset.h=st.h;};
  function fallbackPlot(idx) {
    if(st.stage===1){
      const r=st.data.c.actual_observations, lim=Math.max(0,idx),g=st.data.geometry;
      const edges=['end_A','end_B'].map(e=>V2R.boundary(g,e));
      const past=r.xy.slice(Math.max(0,lim-78),lim+1);
      const plot=uqProjection([...edges.flat(),...past],640,290);
      fallback.innerHTML='<svg class="field" viewBox="0 0 640 290" aria-label="실제 과거 관측">'+edges.map((xy,i)=>uqLine(plot,xy,(i===1)===(st.data.c.direction===1)?'#b87508':'#506975',3)).join('')+uqLine(plot,past,UQ.colors.clean,4)+uqScale(plot.scale,1,290)+'</svg>';
    }else fallback.innerHTML=st.stage===2?uqHistory(st.data,st.scenario):uqMap(st.data,result(),st.mode,st.h,st.truth);
  }
  function frame(force=false){
    if(disposed)return;
    const now=performance.now();
    if(st.running){
      st.time=Math.min(end(),st.time+(now-lastStamp)/1000);
      if(st.time>=end()){st.running=false;$g('Play').textContent='▶ 재생';}
    }
    lastStamp=now;
    const rec=st.data.c.actual_observations;
    const idx=rec.elapsed_s.findLastIndex(v=>v<=st.time+1e-6);
    const visible=idx>=0&&st.time-rec.elapsed_s[idx]<.061;
    if(idx!==lastFrame||force||!st.running&&$g('Time').valueAsNumber!==st.time){
      if(world)world.pose(st,idx,visible);
      else if(!fallback.hidden&&(st.stage===1||force))fallbackPlot(idx);
      const atOrigin=st.stage>1||Math.abs(st.time-origin())<.001;
      let d=null,v=null;
      if(atOrigin){d=st.data.features.distance_m;v=st.data.features.v_long_mps;}
      else if(visible){
        d=geometryDistances(st.data.geometry,rec.xy[idx],st.data.c.direction)?.remaining;
        const j=rec.elapsed_s.findLastIndex(t=>t<=rec.elapsed_s[idx]-.6);
        if(j>=0&&rec.elapsed_s.slice(j+1,idx+1).every((t,k)=>t-rec.elapsed_s[j+k]<.061)){
          const dt=rec.elapsed_s[idx]-rec.elapsed_s[j],g=st.data.geometry;
          v=st.data.c.direction*g.axis.reduce((a,axis,k)=>a+axis*(rec.xy[idx][k]-rec.xy[j][k]),0)/dt;
        }
      }
      $g('Distance').textContent=d==null?'—':PN(d,2)+' m';
      $g('Speed').textContent=v==null?'—':PN(v,2)+' m/s';
      $g('Clock').textContent=PN(st.time,2)+' s / '+PN(end(),2)+' s';
      $g('Time').value=st.time;lastFrame=idx;
    }
  }
  function render(){
    status();st.result=result();
    const {data,stage,mode,h,truth}=st;
    const canPlay=stage===1||truth, time=$g('Time');
    time.min=stage===1?start():origin();time.max=end();time.disabled=!canPlay;
    $g('Play').disabled=!canPlay;$g('Play').textContent=st.running?'Ⅱ 일시정지':'▶ 재생';
    $g('Mode').disabled=stage<2;$g('Mode').value=mode;$g('Noise').disabled=stage<2;$g('Noise').value=st.scenario;
    $g('H').disabled=stage<3;$g('H').value=h;
    $g('Reveal').disabled=stage!==4;$g('Reveal').textContent=truth?'정답 숨기기':'실제 정답 공개';$g('Reveal').setAttribute('aria-pressed',truth);
    $g('Next').disabled=stage===4;
    root.querySelectorAll('[data-stage]').forEach(b=>b.setAttribute('aria-pressed',+b.dataset.stage===stage));
    $g('Meta').textContent=data.c.crosswalk+' · '+UQ.names[mode]+' · 예측 시점 '+PN(origin(),1)+' s'+(stage>=3?' · H='+h+'초':'');
    $g('StageTitle').textContent=GUIDE_STAGES[stage-1][0];$g('Text').textContent=truth?'분홍 선이 실제 미래입니다. 선택 기한의 예측과 실제 완료 여부를 비교하세요.':GUIDE_STAGES[stage-1][1];
    $g('Prob').innerHTML=stage===4?'<h3>시간별 횡단 완료확률</h3>'+uqBars(result(),h):'';
    $g('Outcome').innerHTML=truth?uqOutcome(data,h)+'<small>이 한 사례로 전체 집단의 확률 보정 수준을 판단할 수 없습니다.</small>':'';
    let entries=[['기준 관측',UQ.colors.clean],['Exit','#b87508']];
    if(stage>=2&&mode!=='clean')entries.push([UQ.names[mode],UQ.colors[mode]]);
    if(stage===2&&mode!=='clean')entries.push(['측정오차 95%',UQ.colors.noisy]);
    if(stage>=3)entries.push(['예측 경로',UQ.colors.future],['HDR 진한 68% · 옅은 95%','#8f7dd3']);
    if(truth)entries.push(['실제 미래',UQ.colors.gt]);
    $g('Legend').innerHTML=uqLegend(entries);
    $g('Top').textContent=stage>=3?'전체 영역 위에서 보기':'위에서 보기';
    $g('DistanceLabel').textContent=stage===1?'현재 Exit 거리':'예측 시점 Exit 거리';
    $g('SpeedLabel').textContent=stage===1?'현재 종방향 속도':'예측 시점 종방향 속도';
    const nextKey=[data.r.uid,stage,mode,st.scenario,h,truth].join('|');
    if(world&&overlayKey!==nextKey){world.overlay(st);overlayKey=nextKey;}
    frame(true);
  }
  function stageTo(n){
    st.running=false;st.stage=n;st.truth=false;st.time=n===1?start():origin();
    if(n===1)st.mode='clean';
    render();
  }
  function reset(){
    st.h=3;st.scenario='iid_1';stageTo(1);world?.view(st.data);
  }
  root.querySelectorAll('button[data-stage]').forEach(b=>b.onclick=()=>stageTo(+b.dataset.stage));
  $g('Next').onclick=()=>stageTo(st.stage+1);
  $g('Play').onclick=()=>{
    if(!st.running&&st.time>=end())st.time=st.stage===1?start():origin();
    st.running=!st.running;lastStamp=performance.now();render();
  };
  $g('Reset').onclick=reset;
  $g('Time').oninput=e=>{st.running=false;st.time=+e.target.value;render();};
  $g('Mode').onchange=e=>{st.mode=e.target.value;render();};
  $g('Noise').onchange=e=>{st.scenario=e.target.value;render();};
  $g('H').onchange=e=>{st.h=+e.target.value;st.time=Math.min(end(),st.time);render();};
  $g('Reveal').onclick=()=>{st.truth=!st.truth;st.running=false;st.time=origin();render();};
  $g('Camera').onclick=()=>world?.view(st.data);
  $g('Top').onclick=()=>world?.view(st.data,true,st);
  $g('Case').onchange=async e=>{
    const token=++revision, uid=e.target.value;
    st.running=false;root.inert=true;
    try{
      const data=await UQ.caseAt(V2R.ri.find(row=>row.uid===uid));
      if(disposed||revision!==token)return;
      st.data=data;world?.change(data);reset();
    }catch(error){if(!disposed){e.target.value=st.data.r.uid;bodyError(root,error);}}
    finally{root.inert=false;}
  };
  try{
    world=guidedWorld(canvas,initial,frame);
    root.dataset.renderer='babylon';
  }catch(error){
    canvas.hidden=true;fallback.hidden=false;
    $g('Camera').hidden=$g('Top').hidden=true;
    root.dataset.renderer='2d';
    fallback.setAttribute('aria-label','WebGL 사용 불가 · 저장된 위치 자료의 평면 보기');
    const badge=document.createElement('span');badge.className='g-fallback-label';badge.textContent='WebGL 사용 불가 · 2D 기록 보기';fallback.before(badge);
    const animate=()=>{if(disposed)return;frame();fallbackFrame=requestAnimationFrame(animate);};
    fallbackFrame=requestAnimationFrame(animate);
  }
  render();
  return ()=>{disposed=true;st.running=false;revision++;cancelAnimationFrame(fallbackFrame);world?.dispose();};
}
