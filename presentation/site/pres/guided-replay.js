'use strict';

const GUIDE_STAGES=[
  ['실제 보행','재생하면 예측 시점에서 멈춥니다. 이때 이후의 움직임은 아직 알 수 없습니다.'],
  ['관측 오차','기준·합성·보정 관측을 바꿔 보세요. 합성 오차의 타원은 저장된 측정 공분산 R에서 계산했습니다.'],
  ['미래 운동','가는 선은 미래 경로 후보, 굵은 선은 대표 경로입니다. 영역은 선택 시각의 위치 분포입니다.'],
  ['횡단 완료','각 막대는 그 시간 안에 Exit를 지날 확률입니다. 정답을 열어 실제 통과와 비교하세요.']
];
// Use the annotated first passage, interpolated between its two recorded frames.
function recordFromEntry(data){
  const raw=data.c.actual_observations, t=data.e.GT.entry_s-data.c.origin0_s;
  const next=raw.elapsed_s.findIndex(v=>v>t);
  if(!Number.isFinite(t)||next<1)throw Error('Entry 시각을 포함하는 두 기록 좌표가 필요합니다.');
  const i=next-1, w=(t-raw.elapsed_s[i])/(raw.elapsed_s[next]-raw.elapsed_s[i]);
  const entry=raw.xy[i].map((v,k)=>v+w*(raw.xy[next][k]-v));
  return {elapsed_s:[t,...raw.elapsed_s.slice(next)],xy:[entry,...raw.xy.slice(next)],sourceOffset:i};
}
function mountGuided(root,initial) {
  const st={data:initial,stage:0,h:4,single:false,mode:'clean',compare:false,view:'crossing',scenario:'iid_1',truth:false,running:false,time:0};
  let world,disposed=false,revision=0,lastStamp=0,lastFrame=-2,fallbackFrame=0,overlayKey,journeyKey;
  const $g=id=>root.querySelector('#g'+id);
  const origin=()=>st.data.r.elapsed_s;
  st.record=recordFromEntry(initial);
  const start=()=>st.record.elapsed_s[0];
  const waitingForInput=()=>st.stage>=2&&st.time<(st.stage===2?origin()+st.data.clean.input.history_times_s[0]-st.data.clean.input.origin_s:origin())-1e-6;
  const end=()=>st.stage===0?st.data.c.actual_observations.elapsed_s.at(-1):st.stage<3?origin():st.truth?Math.min(origin()+st.h,st.data.c.actual_observations.elapsed_s.at(-1)):origin()+st.h;
  const playLabel=()=>st.running?'Ⅱ 일시정지':st.stage===0?'▶ 전체 횡단 재생':'▶ '+['기록 재생','관측 재생','예측 재생',st.truth?'예측·실제 재생':'예측 재생'][st.stage-1];
  const modes=Object.keys(UQ.names);
  const result=(mode=st.mode)=>st.data.r.results[mode==='clean'?'clean':st.scenario+'__'+mode];
  st.time=start();
  root.classList.add('guided');
  const selectors='<div class="g-segments" role="group" aria-label="관측 조건">'+modes.map(mode=>'<button data-condition="'+mode+'" style="--condition:'+UQ.colors[mode]+'"><b>'+UQ.names[mode]+'</b><span class="g-history-mini"></span></button>').join('')+'</div>';
  root.innerHTML='<div class="g-head"><nav aria-label="3D 시연 단계"><button id="gJourney">전체 횡단</button>'+GUIDE_STAGES.map(([name],i)=>'<button data-stage="'+(i+1)+'">'+(i+1)+'　'+name+'</button>').join('')+'</nav>'+
    uqSelect('gCase','기록',V2R.ri.map(r=>[r.uid,r.location+' · '+r.event_id.slice(-2)]),initial.r.uid)+'</div>'+
    '<div class="g-conditionbar"><span id="gHint"></span><label id="gCompareWrap" hidden><input id="gCompare" type="checkbox"> 세 조건 겹쳐 보기</label></div>'+
    '<div class="g-grid"><section class="g-viewport">'+selectors+'<div class="g-views"><canvas id="gCanvas" aria-label="IMPTC 기록의 3D 횡단보도와 보행자"></canvas><div id="gFallback" hidden></div><div class="g-map-tools"><button id="gSingle">선택 조건 확대</button><button id="gCross">횡단부</button><button id="gTop">상단 비교</button><button id="gFull">전체 영역</button></div><div id="gInset" hidden></div><div id="gLegend"></div></div></section>'+
    '<aside class="g-info"><div class="g-meta" id="gMeta"></div><h2 id="gStageTitle"></h2><p id="gText"></p><div class="g-kpis"><div><small id="gDistanceLabel">Exit까지 거리</small><strong id="gDistance"></strong></div><div><small id="gSpeedLabel">종방향 속도</small><strong id="gSpeed"></strong></div></div><div id="gInputDetail"></div><div id="gProb"></div><div id="gOutcome"></div><div id="gCaseMetrics"></div></aside></div>'+
    '<div class="g-controls"><div class="g-time"><button id="gPlay">▶ 재생</button><button id="gReset">처음부터</button><label for="gTime" id="gTimeLabel">기록 시간</label><input id="gTime" type="range" step="any"><output for="gTime" id="gClock"></output></div>'+
    '<div class="g-settings">'+uqSelect('gNoise','오차',UQ_SCENARIOS,'iid_1')+
    uqSelect('gH','예측 시간',UQ.horizons.map(h=>[h,h+'초']),3)+'<button id="gReveal">실제 정답 공개</button><button id="gCamera">카메라 초기화</button><button id="gJump" hidden>비교 시점으로</button><button id="gNext">다음 단계 →</button></div></div>';
  const canvas=$g('Canvas'),fallback=$g('Fallback');
  const status=()=>{root.dataset.stage=st.stage;root.dataset.uid=st.data.r.uid;root.dataset.truth=st.truth;root.dataset.mode=st.mode;root.dataset.h=st.h;};
  function fallbackPanels(draw){
    const shown=st.single?[st.mode]:modes;
    fallback.innerHTML=shown.map(m=>'<div class="fallback-panel" data-panel="'+m+'">'+draw(m)+'</div>').join('');
  }
  // Select only forecasts already issued by this point in the recorded crossing.
  function journeyForecast(mode){
    const {data,time,h}=st,gt=data.e.GT;
    if(time>=gt.confirmation_s && Number.isFinite(gt.confirmation_s))return null;
    const f=mode==='clean'?data.c.forecasts.findLast(f=>f.elapsed_s<=time):data.f;
    if(!f||time<f.elapsed_s||time>f.elapsed_s+h)return null;
    return {at:f.elapsed_s,result:mode==='clean'?f.conditions.clean:result(mode)};
  }
  function journeyLayers(){
    const {data,time,mode,h}=st,gt=data.e.GT;
    const forecasts=modes.map(journeyForecast),forecast=forecasts[modes.indexOf(mode)];
    const complete=Number.isFinite(gt.confirmation_s)&&time>=gt.confirmation_s;
    const phase=complete?'Exit 통과 확인':time>=gt.entry_s?'횡단 중':'Entry 접근';
    const key=[data.r.uid,mode,st.scenario,h,...forecasts.map(f=>f?.at),phase,st.single].join('|');
    if(key===journeyKey)return;
    journeyKey=key;
    root.dataset.forecastOrigin=forecast?.at??'';
    $g('Meta').textContent=data.c.crosswalk+' · '+phase+' · '+UQ.names[mode];
    $g('StageTitle').textContent='전체 횡단';
    $g('Text').textContent=forecast?'재생 '+PN(forecast.at-start(),2)+'초에 저장된 예측입니다. 보라색 영역은 그 시점에서 '+h+'초 뒤의 위치입니다.':
      complete?'기록에서 Exit 통과를 확인했습니다. 이후 보행도 이어서 재생합니다.':
      mode==='clean'?'첫 저장 예측에 도달하면 경로와 위치 영역이 나타납니다.':'이 조건의 예측은 재생 '+PN(origin()-start(),2)+'초 한 시점에 저장되어 있습니다.';
    $g('InputDetail').hidden=!!forecast||complete;
    $g('Outcome').textContent=complete?'실제 Entry → Exit　'+PN(gt.exit_s-gt.entry_s,2)+'초':'';
    $g('Prob').innerHTML=forecast?'<h3>이 예측 시점부터의 완료확률</h3>'+uqBars(forecast.result,h):'';
    if(world)world.overlay(st,modes.map((m,i)=>({...st,mode:m,stage:forecasts[i]?3:1,result:forecasts[i]?.result||result(m),truth:false})));
    if(!fallback.hidden)drawJourneyMap(forecasts);
  }
  let journeyPlot=null;
  function drawJourneyMap(forecasts=[]){
    const {data,h}=st;
    const edges=['end_A','end_B'].map(end=>V2R.boundary(data.geometry,end));
    const points=[...edges.flat(),...data.c.actual_observations.xy];
    for(const f of forecasts.filter(Boolean)){
      const r=f.result,i=r.future_times_s.indexOf(h);
      points.push(...r.regions[i]['0.95'].flat(),...r.hypotheses_xy.flatMap(path=>path.slice(0,i+1)));
    }
    journeyPlot=uqProjection(points,640,290,crossingAxes(data));
    fallbackPanels(m=>{
      const r=forecasts[modes.indexOf(m)]?.result,i=r?.future_times_s.indexOf(h);
      let svg=edges.map((line,j)=>uqLine(journeyPlot,line,(j===1)===(data.c.direction===1)?'#b87508':'#506975',3)).join('');
      const input=(r||result(m)).input.observed_xy;
      svg+=uqLine(journeyPlot,input,UQ.colors[m],4)+dot(journeyPlot.xy(input.at(-1)),5,UQ.colors[m]);
      if(r){
        for(const level of ['0.95','0.68'])svg+=polygon(journeyPlot,r.regions[i][level],level);
        const best=r.hypothesis_confidence_scores.indexOf(Math.max(...r.hypothesis_confidence_scores));
        r.hypotheses_xy.forEach((path,j)=>{svg+=uqLine(journeyPlot,[r.input.observed_xy.at(-1),...path.slice(0,i+1)],UQ.colors.future,j===best?3:1);});
      }
      return svgFrame('전체 보행 기록과 해당 시점의 저장 예측',svg+'<polyline data-trail="" fill="none" stroke="'+UQ.colors.clean+'" stroke-width="3"/>'+uqReplayDot(UQ.colors.clean)+uqScale(journeyPlot.scale,1,290),640,290);
    });
  }
  function frame(force=false){
    if(disposed||(!st.running&&!force))return;
    const now=performance.now();
    if(st.running){
      st.time=Math.min(end(),st.time+(now-lastStamp)/1000);
      if(st.time>=end()){st.running=false;$g('Play').textContent=playLabel();}
    }
    lastStamp=now;
    if(st.leadIn!==waitingForInput()){render();return;}
    if(st.stage===0)journeyLayers();
    const rec=st.record;
    const personTime=st.stage>=3&&!st.truth?Math.min(origin(),st.time):st.time;
    const idx=rec.elapsed_s.findLastIndex(v=>v<=personTime+1e-6);
    const visible=idx>=0&&personTime-rec.elapsed_s[idx]<.061;
    const delta=st.time-origin(),r=st.result;
    // The two clocks share the saved origin. The cursor only visits stored positions.
    let cursor=null;
    if(st.stage===2&&!st.leadIn){
      const j=Math.max(0,r.input.history_times_s.findLastIndex(t=>t<=r.input.origin_s+delta+1e-6));
      cursor={point:r.input.observed_xy[j],index:j};
    }else if(st.stage>=3&&!st.leadIn){
      const j=r.future_times_s.findLastIndex(t=>t<=delta+1e-6);
      cursor={point:j<0?r.input.observed_xy.at(-1):st.representative[j],index:j+1};
    }
    if(world)world.cursor(st,cursor);
    if(force||idx!==lastFrame){
      if(world)world.pose(st,idx,visible);
      else if((st.stage<=1||st.leadIn)&&journeyPlot){
        let first=idx;
        while(first>0&&rec.elapsed_s[first]-rec.elapsed_s[first-1]<.061)first--;
        const points=visible?journeyPlot.points(rec.xy.slice(first,idx+1)):'';
        for(const panel of fallback.children){
          const marker=panel.querySelector('[data-replay-cursor]');
          marker.setAttribute('visibility',visible?'visible':'hidden');
          if(visible){
            const [x,y]=journeyPlot.xy(rec.xy[idx]);marker.setAttribute('cx',x);marker.setAttribute('cy',y);
            panel.querySelector('[data-trail]').setAttribute('points',points);
          }
        }
      }
      const atOrigin=st.stage>=2&&st.time>=origin()||Math.abs(st.time-origin())<.00001;
      let d=null,v=null;
      if(atOrigin){d=st.data.features.distance_m;v=st.data.features.v_long_mps;}
      else if(visible){
        d=geometryDistances(st.data.geometry,rec.xy[idx],st.data.c.direction)?.remaining;
        const raw=st.data.c.actual_observations, ri=rec.sourceOffset+idx;
        const j=raw.elapsed_s.findLastIndex(t=>t<=rec.elapsed_s[idx]-.6);
        if(j>=0&&raw.elapsed_s.slice(j+1,ri+1).every((t,k)=>t-raw.elapsed_s[j+k]<.061)){
          const dt=rec.elapsed_s[idx]-raw.elapsed_s[j],g=st.data.geometry;
          v=st.data.c.direction*g.axis.reduce((a,axis,k)=>a+axis*(rec.xy[idx][k]-raw.xy[j][k]),0)/dt;
        }
      }
      $g('Distance').textContent=d==null?'—':PN(d,2)+' m';
      $g('Speed').textContent=v==null?'—':PN(v,2)+' m/s';
      lastFrame=idx;
    }
    if(cursor)for(const host of world?[$g('Inset')]:fallback.children){
      const path=host.querySelector('[data-replay-path]')||host.querySelector('[data-path="representative"]');
      const marker=host.querySelector('[data-replay-cursor]');
      const point=path?.points[cursor.index];
      if(marker&&point){marker.setAttribute('cx',point.x);marker.setAttribute('cy',point.y);}
      const actual=host.querySelector('[data-actual-cursor]');
      if(actual){
        actual.setAttribute('visibility',visible?'visible':'hidden');
        const recorded=host.querySelector('[data-recorded-path]').points[idx+rec.sourceOffset];
        if(visible&&recorded){actual.setAttribute('cx',recorded.x);actual.setAttribute('cy',recorded.y);}
      }
    }
    const clock=PN(Math.max(0,st.time-start()),2)+' s / '+PN(end()-start(),2)+' s';
    if($g('Clock').textContent!==clock)$g('Clock').textContent=clock;
    if($g('Time').valueAsNumber!==st.time)$g('Time').value=st.time;
  }
  function render(){
    st.leadIn=waitingForInput();status();st.result=result();
    const scores=st.result.hypothesis_confidence_scores;
    st.representative=st.result.hypotheses_xy[scores.indexOf(Math.max(...scores))];
    delete root.dataset.forecastOrigin;
    root.dataset.resultKey=st.mode==='clean'?'clean':st.scenario+'__'+st.mode;
    const {data,stage,mode,h,truth}=st;
    const time=$g('Time');
    time.min=start();time.max=end();
    $g('Play').textContent=playLabel();
    $g('TimeLabel').textContent='Entry부터';
    $g('Journey').setAttribute('aria-pressed',stage===0);
    root.querySelectorAll('[data-condition]').forEach(btn=>{btn.setAttribute('aria-pressed',btn.dataset.condition===mode);});
    $g('CompareWrap').hidden=stage!==2||st.leadIn;$g('Compare').checked=st.compare;
    $g('Noise').value=st.scenario;
    $g('H').value=h;
    $g('Jump').hidden=stage===0;
    $g('Reveal').disabled=stage!==4||st.leadIn;$g('Reveal').textContent=truth?'정답 숨기기':'실제 정답 공개';$g('Reveal').setAttribute('aria-pressed',truth);
    $g('Next').disabled=stage===4;$g('Next').textContent=stage===0?'비교 시점으로':'다음 단계 →';
    root.querySelectorAll('[data-stage]').forEach(b=>b.setAttribute('aria-pressed',+b.dataset.stage===stage));
    $g('Meta').textContent=data.c.crosswalk+' · '+UQ.names[mode]+' · '+$g('Noise').selectedOptions[0].textContent+' · 저장 원점 Entry +'+PN(origin()-start(),2)+'초'+(stage>=3?' · H='+h+'초':'');
    $g('StageTitle').textContent=GUIDE_STAGES[stage-1]?.[0]||'';$g('Text').textContent=truth?'':GUIDE_STAGES[stage-1]?.[1]||'';
    $g('Prob').innerHTML=stage===4&&!st.leadIn?'<h3>시간별 횡단 완료확률</h3>'+uqBars(st.result,h):'';
    $g('Outcome').innerHTML=truth?uqOutcome(data,h):'';
    const metrics=[];
    if(stage>=3&&!st.leadIn){
      const i=st.result.future_times_s.indexOf(h), area=st.result.area_m2?.['0.95']?.[i];
      if(Number.isFinite(area))metrics.push('HDR95 면적 <b>'+PN(area,2)+' m²</b>');
      if(truth){
        const scores=st.result.hypothesis_confidence_scores,rep=st.result.hypotheses_xy[scores.indexOf(Math.max(...scores))][i],gt=data.r.future_GT_xy[i];
        if(gt?.every(Number.isFinite))metrics.push('끝점 오차 <b>'+PN(Math.hypot(rep[0]-gt[0],rep[1]-gt[1]),2)+' m</b>');
        const y=V2R.gt(data,h),prob=st.result.exit.probabilities[h];
        if(y!=null&&Number.isFinite(prob))metrics.push('완료 제곱오차 <b>'+PN((prob-y)**2,4)+'</b>');
      }
    }
    $g('CaseMetrics').innerHTML=metrics.length?'<small>이 사례 · +'+h+'초</small> '+metrics.join('　'):'';
    let entries=[['기준 관측',UQ.colors.clean],['Exit','#b87508']];
    if(stage>=2&&mode!=='clean')entries.push([UQ.names[mode],UQ.colors[mode]]);
    if(mode==='filtered_mean'||stage===2&&st.compare&&mode!=='noisy')entries.push(['합성 관측',UQ.colors.noisy]);
    if(stage===2&&st.compare&&mode!=='filtered_mean')entries.push(['보정 관측',UQ.colors.filtered_mean]);
    if(stage===2&&(mode!=='clean'||st.compare))entries.push(['측정오차 95%',UQ.colors.noisy]);
    if(stage===0||stage>=3)entries.push(['예측 경로',UQ.colors.future],['HDR 진한 68% · 옅은 95%','#8f7dd3']);
    if(truth)entries.push(['실제 미래',UQ.colors.gt]);
    if(st.leadIn){
      entries=[['실제 기록',UQ.colors.clean],['Entry','#336386'],['Exit','#b87508']];
      $g('Meta').textContent=data.c.crosswalk+' · '+UQ.names[mode]+' · Entry에서 비교 시점까지';
      $g('Text').textContent='이 사례의 비교 예측은 Entry 통과 후 '+PN(origin()-start(),2)+'초에 저장되었습니다.';
    }
    if(!st.single&&world){
      entries=[['실제 기록',UQ.colors.clean],...modes.map(m=>[UQ.names[m],UQ.colors[m]]),['Exit','#b87508']];
      if((stage===0||stage>=3)&&!st.leadIn)entries.push(['예측 · HDR',UQ.colors.future]);
      if(truth)entries.push(['실제 미래',UQ.colors.gt]);
    }
    $g('Legend').innerHTML=uqLegend(entries);
    const inputTime=PN(origin()-start(),2);
    $g('Hint').textContent='파란 사람 = Entry 출발 실제 보행자　·　조건 이름 옆 그림 = Entry +'+inputTime+'초의 저장 입력 10점';
    const extent=modes.flatMap(m=>result(m).input.observed_xy);
    const axis=crossingAxes(data),plot=uqProjection(extent,280,170,axis);
    const zoom=uqProjection(extent,340,140,axis);
    let paths='';
    const detailModes=modes.filter(m=>m!==mode).concat(mode);
    for(const m of detailModes){
      const xy=result(m).input.observed_xy;
      paths+=uqLine(zoom,xy,UQ.colors[m],m===mode?3.5:1.8,m==='noisy'?'stroke-dasharray="5 3"':'')+dot(zoom.xy(xy.at(-1)),m===mode?5:3,UQ.colors[m]);
    }
    const selectedEnd=st.result.input.observed_xy.at(-1),referenceEnd=data.clean.input.observed_xy.at(-1);
    const area=st.result.area_m2?.['0.95']?.[st.result.future_times_s.indexOf(h)];
    const separation=Math.hypot(selectedEnd[0]-referenceEnd[0],selectedEnd[1]-referenceEnd[1]);
    $g('InputDetail').hidden=stage>=3&&!st.leadIn;
    $g('InputDetail').innerHTML='<h3>저장 관측 확대 · Entry +'+inputTime+'초</h3>'+svgFrame('세 조건의 저장된 입력 위치',paths+uqScale(zoom.scale,.25,140),340,140)+
      '<small>'+UQ.names[mode]+' 끝점과 기준 위치의 차이　<b>'+PN(separation,2)+' m</b>'+(Number.isFinite(area)?' · '+h+'초 HDR95 '+PN(area,2)+' m²':'')+'</small>';
    for(const button of root.querySelectorAll('[data-condition]')){
      const m=button.dataset.condition,r=result(m),xy=r.input.observed_xy;
      const line=uqLine(plot,xy,UQ.colors[m],4,'data-input="'+m+'"')+dot(plot.xy(xy.at(-1)),5,UQ.colors[m]);
      button.querySelector('.g-history-mini').innerHTML=svgFrame(UQ.names[m]+' 저장 입력',line,280,170);
      button.title=UQ.names[m]+' 상세 정보 · Entry +'+inputTime+'초 저장 입력';
    }
    root.dataset.single=st.single;
    $g('Single').textContent=st.single?'세 조건 나란히':'선택 조건 확대';
    $g('Single').setAttribute('aria-pressed',st.single);
    for(const [id,view] of [['Cross','crossing'],['Top','top'],['Full','full']])$g(id).setAttribute('aria-pressed',st.view===view);
    $g('Inset').hidden=!world||!st.single||stage<2||st.leadIn;
    if(!$g('Inset').hidden)$g('Inset').innerHTML=uqReplayInset(st);
    $g('DistanceLabel').textContent=stage<=1||st.leadIn||stage===2?'현재 Exit 거리':'기준 관측 · Exit 거리';
    $g('SpeedLabel').textContent=stage<=1||st.leadIn||stage===2?'현재 종방향 속도':'기준 관측 · 종방향 속도';
    const nextKey=[data.r.uid,stage,mode,st.scenario,h,truth,st.compare,st.leadIn,st.single].join('|');
    if(stage===0){journeyKey=null;overlayKey=null;}
    if(stage!==0&&world&&overlayKey!==nextKey){world.overlay(st,modes.map(m=>({...st,mode:m,result:result(m)})));overlayKey=nextKey;}
    if(!world&&stage!==0){
      if(stage===1||st.leadIn)drawJourneyMap();
      else fallbackPanels(m=>stage===2?uqReplayInset({...st,mode:m,result:result(m)}):uqMap(data,result(m),m,h,truth,true));
    }
    frame(true);
  }
  function stageTo(n){
    const wasJourney=st.stage===0;
    st.running=false;st.stage=n;st.truth=false;st.time=start();

    if(n===0||wasJourney||(n<3&&st.view==='full')){st.view='crossing';world?.view(st.data,'crossing',st);}
    render();
  }
  function reset(stage=0){
    st.compare=false;st.view='crossing';stageTo(stage);
  }
  root.querySelectorAll('button[data-stage]').forEach(b=>b.onclick=()=>stageTo(+b.dataset.stage));
  $g('Journey').onclick=()=>stageTo(0);
  $g('Jump').onclick=()=>{st.time=origin();st.running=false;render();};
  $g('Next').onclick=()=>{
    if(st.stage!==0){stageTo(st.stage+1);return;}
    st.time=origin();st.running=false;render();
  };
  $g('Play').onclick=()=>{
    if(!st.running&&st.time>=end())st.time=start();
    st.running=!st.running;lastStamp=performance.now();render();
  };
  $g('Reset').onclick=()=>stageTo(st.stage);
  $g('Time').oninput=e=>{st.running=false;st.time=Math.max(start(),+e.target.value);if(st.time<origin())st.truth=false;render();};
  root.querySelectorAll('[data-condition]').forEach(btn=>btn.onclick=()=>{
    st.mode=btn.dataset.condition;render();
  });
  $g('Compare').onchange=e=>{st.compare=e.target.checked;render();};
  function setView(view){st.view=view;world?.view(st.data,view,st);render();}
  $g('Single').onclick=()=>{st.single=!st.single;world?.view(st.data,st.view,st);render();};
  $g('Noise').onchange=e=>{st.scenario=e.target.value;if(st.view==='full')world?.view(st.data,'full',st);render();};
  $g('H').onchange=e=>{st.h=+e.target.value;st.time=Math.min(end(),st.time);if(st.view==='full')world?.view(st.data,'full',st);render();};
  $g('Reveal').onclick=()=>{st.truth=!st.truth;st.running=false;st.time=origin();render();};
  $g('Camera').onclick=$g('Cross').onclick=()=>setView('crossing');
  $g('Top').onclick=()=>setView('top');
  $g('Full').onclick=()=>setView('full');
  $g('Case').onchange=async e=>{
    const token=++revision, uid=e.target.value;
    st.running=false;root.inert=true;
    try{
      const data=await UQ.caseAt(V2R.ri.find(row=>row.uid===uid));
      if(disposed||revision!==token)return;
      st.record=recordFromEntry(data);st.data=data;world?.change(data);reset();
    }catch(error){if(!disposed){e.target.value=st.data.r.uid;bodyError(root,error);}}
    finally{root.inert=false;}
  };
  try{
    world=guidedWorld(canvas,initial,frame);world.view(initial,'crossing',st);
    root.dataset.renderer='babylon';
  }catch(error){
    canvas.hidden=true;fallback.hidden=false;
    $g('Camera').hidden=$g('Top').hidden=$g('Full').hidden=$g('Cross').hidden=true;
    root.dataset.renderer='2d';
    fallback.setAttribute('aria-label','WebGL 사용 불가 · 저장된 위치 자료의 평면 보기');
    const badge=document.createElement('span');badge.className='g-fallback-label';badge.textContent='WebGL 사용 불가 · 2D 기록 보기';fallback.before(badge);
    const animate=()=>{if(disposed)return;frame();fallbackFrame=requestAnimationFrame(animate);};
    fallbackFrame=requestAnimationFrame(animate);
  }
  render();
  return ()=>{disposed=true;st.running=false;revision++;cancelAnimationFrame(fallbackFrame);world?.dispose();};
}
