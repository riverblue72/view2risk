'use strict';
const UQ_SCENARIOS = [
  ['iid_0.5','독립 오차 0.5×'],['iid_1','독립 오차 1×'],['iid_2','독립 오차 2×'],
  ['correlated_1','시간 상관 오차 1×'],['dropout_1','관측 누락 1×']
];
function uqSelect(id,label,items,value) {
  return '<label>'+label+' <select id="'+id+'">'+items.map(([key,name])=>'<option value="'+key+'" '+(key===value?'selected':'')+'>'+name+'</option>').join('')+'</select></label>';
}
function uqOutcome(s,h) {
  const y=V2R.gt(s,h), time=s.e.GT.exit_s;
  const actual=time==null?'통과 시각 미확정':('예측 후 '+PN(time-s.key.origin_s,3)+'초에 Exit 통과');
  return '<div class="outcome"><strong>'+actual+'</strong><span>'+h+'초 이내 '+(y===1?'완료':y===0?'미완료':'판정 불가')+'</span></div>';
}
function uqDirect(s) {
  return '<details class="direct"><summary>같은 기준 관측에서 시간을 직접 예측한 결과</summary><p>Conditional AFT와 Exit-aware XGBoost AFT는 거리·속도 등에서 잔여시간을 직접 추정합니다. 아래 값은 원래 관측 입력에 고정됩니다.</p>'+
    pTable(['독립적인 시간 모델',...UQ.horizons.map(h=>h+'초')],['conditional_AFT__calibrated','EA_M1__calibrated'].map(m=>[P_MODELS[m][0],...UQ.horizons.map(h=>UQ.pct(V2R.p(s,m,h)))]))+
    '<p class="caption">'+UQ.source('data/public/ui-completion.json')+' · '+UQ.source('data/public/exit-aware.json')+'</p></details>';
}

// One state drives history, map, forecast endpoint, probabilities and revealed outcome.
function mountUqReplay(root,initial) {
  let s=initial, view='motion', scenario='iid_1', mode='clean', h=3, truth=false, revision=0;
  function render(focusId) {
    const aggregate=view==='validation', motion=view==='motion';
    const result=s.r.results[mode==='clean'?'clean':scenario+'__'+mode];
    const tabs=[['observation','A · 관측 오차'],['motion','B–C · 미래 경로와 완료확률'],['validation','D · 집계 검증']];
    root.innerHTML='<nav class="view-tabs" aria-label="시연 보기">'+tabs.map(([key,label])=>'<button id="view-'+key+'" data-view="'+key+'" aria-pressed="'+(view===key)+'">'+label+'</button>').join('')+'</nav><div id="replayBody"></div>';
    const body=root.querySelector('#replayBody');
    if(aggregate) {
      body.innerHTML='<p class="kicker">전체 평가 집단 · 합성 관측오차</p>'+uqRobustness()+
        '<article class="aft-result"><h2>Exit-aware 학습 전후의 Brier</h2>'+uqM1()+'</article>';
    } else {
      const cases=V2R.ri.map(r=>[r.uid,r.location+' · '+r.event_id+' · +'+r.origin_s+'초']);
      const scenarios=UQ_SCENARIOS.filter(([key])=>s.r.results[key+'__noisy']&&s.r.results[key+'__filtered_mean']);
      body.innerHTML='<div class="controls">'+uqSelect('uqCase','기록 사례',cases,s.r.uid)+uqSelect('uqNoise','관측오차 설정',scenarios,scenario)+
        (motion?uqSelect('uqMode','예측 입력',Object.entries(UQ.names),mode)+uqSelect('uqH','예측 시간',UQ.horizons.map(t=>[t,t+'초']),h)+
          '<button id="uqReveal" aria-pressed="'+truth+'">'+(truth?'실제 정답 숨기기':'실제 정답 공개')+'</button>':'')+'</div>';
      if(motion) {
        body.insertAdjacentHTML('beforeend','<div class="map-time"><figure><h2>미래 위치 · +'+h+'초</h2>'+uqMap(s,result,mode,h,truth)+'</figure>'+
          '<article><h2>Exit를 지날 누적확률</h2>'+uqBars(result,h)+'<p class="case-features">기준 관측 · Exit까지 <b>'+PN(s.features.distance_m,2)+' m</b> · 종방향 속도 <b>'+PN(s.features.v_long_mps,2)+' m/s</b></p>'+
          (truth?uqOutcome(s,h):'<p class="unrevealed">실제 경로와 완료 시각은 정답 공개 후 표시됩니다.</p>')+'</article></div>'+
          '<p class="caption">'+UQ.caseSource(s)+' · 지도 축척은 표시 범위에 맞춰 조정됩니다. 영역은 선택한 시각의 위치 분포입니다. 각 막대는 joint 경로 표본의 누적 Exit 통과 비율입니다.</p>'+uqDirect(s));
      } else {
        body.insertAdjacentHTML('beforeend','<div class="pair observation"><figure><h2>같은 0.9초 동안 관측한 위치</h2>'+uqHistory(s,scenario)+'</figure>'+
          '<article><h2>관측 위치가 흔들리면</h2><p>파란 점은 기준 궤적, 주황 점은 합성 오차를 더한 위치입니다. 초록 선은 이 시점까지의 관측을 칼만 필터로 보정한 과거입니다.</p>'+
          '<p>점선 타원은 마지막 유효 합성 관측에 표시한 95% 측정오차 범위입니다. 크기와 방향은 이 설정에 저장된 측정 공분산 R에서 가져왔습니다.</p>'+
          (scenario==='dropout_1'?'<p>마지막 네 관측이 누락되었습니다. 예측기의 Noisy 입력은 마지막 관측을 유지하며, 필터는 새 측정 없이 진행합니다.</p>':'')+
          '<p class="annotation">같은 기록에서 입력만 바꿉니다. 실제 미래는 모든 조건에 공통입니다.</p></article></div><p class="caption">'+UQ.caseSource(s)+'</p>');
      }
    }
    root.querySelectorAll('[data-view]').forEach(btn=>btn.onclick=()=>{view=btn.dataset.view;render(btn.id);});
    if(!aggregate) {
      const get=id=>root.querySelector('#'+id);
      get('uqCase').onchange=async event=>{
        const token=++revision, uid=event.target.value;
        root.querySelectorAll('button,select').forEach(el=>el.disabled=true);
        try {
          const next=await UQ.caseAt(V2R.ri.find(row=>row.uid===uid));
          if(token!==revision||!root.isConnected)return;
          s=next;truth=false;render('uqCase');
        } catch(error) {render('uqCase');bodyError(root,error);}
      };
      get('uqNoise').onchange=e=>{scenario=e.target.value;render('uqNoise');};
      if(motion) {
        get('uqMode').onchange=e=>{mode=e.target.value;render('uqMode');};
        get('uqH').onchange=e=>{h=Number(e.target.value);render('uqH');};
        get('uqReveal').onclick=()=>{truth=!truth;render('uqReveal');};
      }
    }
    if(focusId)root.querySelector('#'+focusId)?.focus({preventScroll:true});
  }
  render();
}
function bodyError(root,error) {
  const p=document.createElement('p');p.setAttribute('role','alert');
  p.textContent='저장된 자료를 읽을 수 없습니다. '+error.message;root.prepend(p);
}
if(PS('standaloneReplay')) {
  PS('pHeader').innerHTML=pNav('compare');
  UQ.load().then(s=>{
    mountDemonstration(PS('standaloneReplay'),s);
    const extra=PS('extra2D');
    extra.ontoggle=()=>{if(extra.open&&!PS('extraReplay').children.length)mountUqReplay(PS('extraReplay'),s);};
  }).catch(error=>bodyError(PS('standaloneReplay'),error));
}
