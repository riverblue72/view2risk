'use strict';
const slides=[
  ['Motivation','보행자는 언제 횡단을 마칠까?','View2Risk: Uncertainty Quantification of Pedestrian Motion and Crossing Completion'],
  ['Data','무엇을 관측했고, 어디에 불확실성이 있을까?','현재 위치의 측정오차와 앞으로의 움직임은 서로 다른 근거로 설명합니다.'],
  ['Framework','관측의 불확실성을 어떻게 횡단 완료까지 연결할까?','View2Risk는 기존 예측기를 횡단 경계, 시간별 확률, 실제 기록 평가에 연결합니다.'],
  ['Observation robustness','합성 관측오차를 보정하면 얼마나 회복될까?','SPD 주석 차이로 추정한 R을 이용해 IMPTC의 과거 위치를 교란하고, 칼만 필터로 보정한 입력을 비교했습니다.'],
  ['Crossing completion','미래 경로를 어떻게 완료확률로 읽을까?','한 경로가 Exit를 처음 지나는 시각을 모으면, 정해진 시간 안에 횡단을 마칠 확률을 구할 수 있습니다.'],
  ['Completion-time UQ','Exit 직전의 관측을 학습에 포함하면 무엇이 달라질까?','남은 시간을 직접 예측하는 XGBoost AFT의 기존 M1과 Exit-aware M1을 비교했습니다.'],
  ['Interactive demonstration','같은 보행자의 관측을 바꾸면 예측은 어떻게 달라질까?','기록 사례와 조건을 선택하고, 공간 예측과 시간별 확률을 읽은 뒤 실제 정답을 공개하세요.'],
  ['Contributions & limitations','이 연구가 보여 준 것과 검증 범위','보행자의 현재 위치와 미래 움직임에 담긴 불확실성을 횡단 완료확률로 옮기고, 실제 기록과 대조했습니다.']
];
const notes=[
  '보행자가 횡단을 마칠 가능성을 신호 운영이나 자율주행 상황 인지에 활용할 여지가 있습니다. 여기서 평가한 대상은 기록 기반 예측의 신뢰도입니다.',
  'R은 SPD Train 카메라와 가상 LiDAR의 보행자 주석 차이로 추정했습니다. 이를 IMPTC의 좌표축에 적용하는 것은 전이 가정입니다. inD에는 검증된 Exit 정답이 없어 위치 평가에만 사용했습니다.',
  '깨끗한 과거는 그대로 입력합니다. 합성 관측은 그대로 넣거나 관측 시점까지 칼만 보정한 뒤 넣습니다. 위치의 시점별 혼합분포로 HDR을, joint 경로분포의 표본으로 완료확률을 평가했습니다.',
  '교란 단계에서 SPD Train의 평균 편향과 공분산을 사용했습니다. 필터는 편향을 빼고 최근 위치와 속도를 추정합니다. 보정 후 영역이 줄어도 목표 95%와 실제 포함률 사이의 간격은 남습니다.',
  'IMPTC 지도에서 횡단보도 양 끝을 추정하고 진행 방향으로 Entry와 Exit를 지정했습니다. 제공된 추적점이 Exit를 처음 넘는 시각을 보간하고 이후 0.12초 이상 관측으로 확인했습니다. 미확정 자료는 실패로 치환하지 않았습니다.',
  '두 M1은 같은 모델 계열과 입력 특징을 사용했습니다. Exit 근방을 포함하도록 과거 학습 시점을 다시 선택하면서 학습 자료 수와 사건 구성도 함께 바뀌었습니다.',
  '기본 f2 사례에서 2초와 3초를 번갈아 보세요. Clean에서 Noisy, Kalman 보정으로 바꿔도 보행자와 기준 시점, 실제 미래는 같습니다. 실제 완료 시각이 4초를 넘는 사례에서는 관측된 시간만 알려 줍니다.',
  '단순 기준선과 Conditional AFT를 포함한 원래 비교, FFBS, 보정 실험, 행동별 분석은 전체 결과와 부록에 남아 있습니다.'
];
function architecture() {
  return '<figure class="architecture" aria-label="관측에서 정답 평가까지의 경로"><div class="flow-main">'+
    '<div class="node start"><small>입력</small><b>보행자 과거 관측</b><span>최근 위치 · 주변 환경 · 횡단 지도</span></div><div class="flow-arrow">↓</div>'+
    '<div class="flow-split"><div class="node"><b>기준 관측</b><span>관측 그대로 입력</span></div><div class="node green"><b>관측오차 R</b><span>합성 관측 그대로 또는 Kalman 보정 후 입력</span></div></div><div class="flow-arrow">↓</div>'+
    '<div class="node pretrained"><small>공식 사전학습 모델</small><b>DD-MDN → 확률적 미래 궤적</b></div><div class="flow-arrow">↓</div>'+
    '<div class="flow-split"><div class="node"><b>공간 불확실성</b><span>미래 위치 · 68% / 95% 예측영역</span></div><div class="node"><b>시간 불확실성</b><span>joint 경로의 Exit 통과 비율</span></div></div><div class="flow-arrow">↓</div>'+
    '<div class="node evaluation"><b>실제 미래 위치 · 횡단 완료 기록과 대조</b></div></div>'+
    '<aside><h2>View2Risk의 구현</h2><p>관측오차 실험을 구성하고, 지도에서 Entry·Exit를 정의해 위치 분포와 시간별 완료확률을 같은 기록으로 평가했습니다.</p>'+
    '<h2>별도의 시간 예측</h2><p>거리·속도 등 관측 특징<br>↓<br>Conditional AFT 또는 XGBoost AFT<br>↓<br>잔여 완료시간 분포</p></aside></figure><p class="caption">IMPTC 기록 · SPD 기반 관측오차 실험 · <a href="METHODOLOGY.md">METHODOLOGY.md</a> · <a href="exit_aware/EXIT_AWARE_FINAL_REPORT.md">Exit-aware 실험 기록</a></p>';
}
function content(i,s) {
  const map=truth=>uqMap(s,s.r.results.clean,'clean',3,truth);
  switch(i){
    case 0:return '<div class="lead-grid"><article><p class="lede">한 줄의 예상 경로만으로는 위치가 얼마나 정확한지, 다른 속도로 걸을 가능성이 얼마나 큰지 알기 어렵습니다.</p><ol class="questions"><li>보행자는 지금 어디에 있는가?</li><li>앞으로 어디로 움직일 수 있는가?</li><li>언제 횡단을 마칠 수 있는가?</li></ol><p>자율주행의 보행자 상황 인지와 지능형 교통 신호 운영에서 물을 수 있는 질문입니다. 안전 개선 효과는 후속 검증 과제입니다.</p></article><figure><h2>실제 관측에서 본 다음 3초</h2>'+map(false)+'<figcaption>'+UQ.caseSource(s)+'</figcaption></figure></div>';
    case 1:return '<div class="dataset-strip"><div><b>SPD</b><span>카메라·가상 LiDAR 주석 차이 → 측정오차 R 추정</span></div><div><b>IMPTC</b><span>보행 궤적·횡단 경계 → 위치와 완료 정답</span></div><div><b>inD</b><span>별도 주행 기록 → 궤적 평가 보완</span></div></div>'+
      '<div class="pair"><figure><h2>현재 · 관측 위치의 흔들림</h2>'+uqHistory(s,'iid_1')+'<figcaption>SPD의 오차 모형을 같은 IMPTC 과거에 적용한 예입니다.</figcaption></figure><figure><h2>미래 · 가능한 이동 경로의 분산</h2>'+map(false)+'<figcaption>DD-MDN은 과거에 조건화한 미래 위치 분포를 제공합니다. 물리적인 과정잡음 공분산 Q는 이 실험에서 식별되지 않았습니다.</figcaption></figure></div><p class="caption">'+UQ.caseSource(s)+'</p>';
    case 2:return architecture();
    case 3:return '<p class="protocol"><b>실험 방법</b>　SPD Train 주석 2,465쌍의 차이 → 편향과 공분산 R 추정 → 기준 위치에 독립 오차 추가 → Kalman으로 위치·속도 보정 → 같은 DD-MDN에 입력</p>'+uqRobustness()+'<p class="takeaway">합성 관측오차 실험에서 위치와 완료 예측의 정확도는 크게 회복됐습니다. 95% 공간영역의 보정은 불완전했습니다. 실제 검출기에서의 성능은 별도 검증이 필요합니다.</p>';
    case 4:return '<div class="map-time"><figure><h2>진행 방향의 입구와 출구</h2>'+map(true)+'<figcaption>Entry는 횡단을 시작한 쪽, Exit는 반대편 경계입니다. 실제 추적점의 첫 Exit 통과를 보간하고 후속 0.12초 관측으로 확인했습니다.</figcaption></figure>'+
      '<article><h2>P(T<sub>exit</sub> ≤ H)</h2>'+uqBars(s.r.results.clean,3)+uqOutcome(s,3)+'<p>기존 joint 분포에서 표본 경로를 뽑아 H초 안에 Exit를 넘은 비율을 계산했습니다. 한 개의 예상 완료 시각과 달리, 기한별로 완료 가능성을 읽을 수 있습니다.</p></article></div><p class="caption">단일 사례 · Clean · 경로와 HDR은 +3초, 막대는 H=1·2·3·4초. '+UQ.caseSource(s)+'</p>';
    case 5:return '<div class="pair"><article><h2>Exit 직전의 학습 공백</h2>'+uqTraining()+'<p class="caption">IMPTC Train · 선별된 학습 시작 시점과 횡단축 기준 잔여 거리. '+UQ.source('exit_aware/exit_aware_summary.json','exit_aware/exit_aware_summary.json')+'</p></article><article><h2>같은 Test에서 본 완료확률 오차</h2>'+uqM1()+'</article></div><p class="takeaway">기존 M1 대비 개선은 1초 예측에서 가장 컸습니다. 학습 자료의 양과 구성이 함께 바뀌어, 거리만의 효과를 분리할 수는 없습니다.</p>';
    case 6:return '<div id="slideReplay"></div>';
    case 7:return '<div class="summary-grid"><article><h2>세 가지 기여</h2><ol class="contributions"><li><b>관측·운동 불확실성 모델링</b><span>주석 차이로 관측오차를 추정하고, 입력 보정이 미래 분포에 미치는 영향을 측정했습니다.</span></li><li><b>횡단 완료 불확실성 정량화</b><span>미래 경로의 Exit 통과를 시간별 확률로 변환했습니다.</span></li><li><b>예측과 실제 기록의 대화형 검증</b><span>동일 시점에서 공간영역, 완료확률, 실제 결과를 함께 조회할 수 있습니다.</span></li></ol></article>'+
      '<article><h2>해석할 때 남는 한계</h2><ul class="limits"><li>미래 운동은 사전학습 DD-MDN에 의존하며, R은 SPD 주석 불일치의 대리값입니다.</li><li>필터링 후 예측영역의 포함률 회복은 불완전했고, FFBS 영역은 지나치게 넓었습니다.</li><li>정지·재출발 사례가 적고, 단순 기준선 대비 일관된 우위도 확인되지 않았습니다.</li><li>여러 번 사용한 과거 Test 자료에서 최대 4초까지 평가했습니다.</li><li>평가는 오프라인 기록 재생에 한정되며 현장 배포 성능은 검증되지 않았습니다.</li></ul><p><a href="results.html">전체 결과와 실험 부록 →</a>　<a href="DATA_POLICY.md">자료 이용 범위</a></p></article></div>';
  }
}
(async()=>{
  PS('pHeader').innerHTML=pNav('presentation');
  const s=await UQ.load();
  let index=0;
  function show(){
    const matched=/^#scene-([1-8])$/.exec(location.hash);
    index=matched?Number(matched[1])-1:0;
    const [section,title,sub]=slides[index];
    PS('pEyebrow').textContent=section;PS('pTitle').textContent=title;PS('pSubtitle').textContent=sub;
    PS('pScene').innerHTML=content(index,s);
    if(index===6)mountUqReplay(PS('slideReplay'),s);
    PS('pNotes').textContent=notes[index];PS('pProgressText').textContent=(index+1)+' / '+slides.length;
    PS('pPrev').disabled=index===0;PS('pNext').disabled=index===slides.length-1;
    PS('pProgress').innerHTML=slides.map(([section,title],i)=>'<a href="#scene-'+(i+1)+'" aria-label="'+(i+1)+'. '+title+'" title="'+section+'" '+(index===i?'aria-current="step"':'')+'>'+(i+1)+'</a>').join('');
    window.scrollTo(0,0);
  }
  function move(step){const n=index+step;if(n>=0&&n<slides.length)location.hash='scene-'+(n+1);}
  PS('pPrev').onclick=()=>move(-1);PS('pNext').onclick=()=>move(1);
  PS('pNotesButton').onclick=()=>{PS('pNotes').hidden=!PS('pNotes').hidden;PS('pNotesButton').setAttribute('aria-expanded',String(!PS('pNotes').hidden));};
  PS('pFullscreen').hidden=!document.fullscreenEnabled;
  PS('pFullscreen').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
  document.addEventListener('keydown',e=>{
    if(e.altKey||e.ctrlKey||e.metaKey||e.target.closest('select,input,textarea'))return;
    if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();move(e.key==='ArrowRight'?1:-1);}
    if(e.key==='Escape'&&!PS('pNotes').hidden)PS('pNotesButton').click();
  });
  window.addEventListener('hashchange',show);show();
})().catch(error=>bodyError(PS('pScene'),error));
