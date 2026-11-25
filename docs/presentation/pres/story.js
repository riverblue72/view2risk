'use strict';
const slides=[
  ['Motivation','보행자는 언제 횡단을 마칠까?','View2Risk: Uncertainty Quantification of Pedestrian Motion and Crossing Completion'],
  ['Data','무엇을 관측했고, 어디에 불확실성이 있을까?','현재 위치의 측정오차와 앞으로의 움직임은 서로 다른 근거로 설명합니다.'],
  ['Framework','관측의 불확실성을 어떻게 횡단 완료까지 연결할까?','View2Risk는 기존 예측기를 횡단 경계, 시간별 확률, 실제 기록 평가에 연결합니다.'],
  ['Observation robustness','합성 관측오차를 보정하면 얼마나 회복될까?','SPD 주석 차이로 추정한 R을 이용해 IMPTC의 과거 위치를 교란하고, 칼만 필터로 보정한 입력을 비교했습니다.'],
  ['Future motion uncertainty','관측 보정 후 미래 위치의 불확실성도 회복될까?','저장된 미래 경로의 분산과 실제 위치의 포함률을 함께 봅니다.'],
  ['Crossing completion','언제 횡단을 마칠까?','DD-MDN 경로에서 시간별 완료확률을 구하고, 별도 시간 예측 실험에서 Exit 직전 학습 자료의 영향을 평가했습니다.'],
  ['Integrated 3D demonstration','한 보행자의 관측에서 횡단 완료까지','IMPTC 기록 재생 · 공식 사전학습 DD-MDN의 저장 예측'],
  ['Contributions & limitations','이 연구가 보여 준 것과 검증 범위','보행자의 현재 위치와 미래 움직임에 담긴 불확실성을 횡단 완료확률로 옮기고, 실제 기록과 대조했습니다.']
];
const notes=[
  '보행자가 횡단을 마칠 가능성을 신호 운영이나 자율주행 상황 인지에 활용할 여지가 있습니다. 여기서 평가한 대상은 기록 기반 예측의 신뢰도입니다.',
  'R은 SPD Train 카메라와 가상 LiDAR의 보행자 주석 차이로 추정했습니다. 이를 IMPTC의 좌표축에 적용하는 것은 전이 가정입니다. inD에는 검증된 Exit 정답이 없어 위치 평가에만 사용했습니다.',
  '깨끗한 과거는 그대로 입력합니다. 합성 관측은 그대로 넣거나 관측 시점까지 칼만 보정한 뒤 넣습니다. 위치의 시점별 혼합분포로 HDR을, joint 경로분포의 표본으로 완료확률을 평가했습니다.',
  '교란 단계에서 SPD Train의 평균 편향과 공분산을 사용했습니다. 필터는 편향을 빼고 최근 위치와 속도를 추정합니다. 보정 후 영역이 줄어도 목표 95%와 실제 포함률 사이의 간격은 남습니다.',
  '회복된 점 예측과 공간영역 보정은 다른 지표입니다. 표의 Coverage와 면적을 함께 읽고 단일 사례 확률과 구분합니다.',
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
    case 3:return '<div class="pair"><figure><h2>같은 과거 위치의 세 가지 입력</h2>'+uqHistory(s,'iid_1')+'<figcaption>SPD Train의 카메라·가상 LiDAR 주석 2,465쌍에서 편향과 R을 추정했습니다. IMPTC 위치에 합성 오차를 더하고 Kalman으로 위치와 속도를 보정했습니다. '+UQ.caseSource(s)+'</figcaption></figure>'+uqRobustness('accuracy')+'</div><p class="caption">IMPTC Test · IID 1× · 동일 237개 시점 / 120건. ADE는 4초간 대표 경로의 평균 위치 오차(n=215), H4 Brier는 4초 내 완료확률의 제곱오차(n=218)입니다. '+UQ.source('r_robustness/r_robustness_metrics.csv')+'</p>';
    case 4:return '<div class="pair"><figure><h2>Kalman 보정 입력의 미래 분포</h2>'+uqMap(s,s.r.results.iid_1__filtered_mean,'filtered_mean',4,true)+'<figcaption>f2 단일 사례 · 얇은 선은 미래 경로 후보, 영역은 +4초 위치 HDR입니다. '+UQ.caseSource(s)+'</figcaption></figure>'+uqRobustness('spatial')+'</div><p class="takeaway">보정 후 영역은 작아졌지만, 95%를 목표로 한 영역의 실제 위치 포함률은 78.51%였습니다.</p><p class="caption">IMPTC Test · IID 1× · 237개 시점 / 120건. Coverage95는 4초 후 GT 포함률(n=228), HDR95는 해당 예측영역의 면적(n=237)입니다. '+UQ.source('r_robustness/r_robustness_metrics.csv')+'</p>';
    case 5:return '<div class="pair completion-slide"><article><h2>경로의 Exit 통과 비율</h2><p>Entry는 진입 쪽, Exit는 반대편 경계입니다. joint 분포에서 뽑은 경로 중 H초 안에 Exit를 처음 넘는 비율이 P(T<sub>exit</sub> ≤ H)입니다.</p>'+uqBars(s.r.results.clean,3)+uqOutcome(s,3)+'<p class="caption">IMPTC f2 · Clean · 실제 추적점의 첫 통과를 보간하고 이후 0.12초 관측으로 확인했습니다. '+UQ.caseSource(s)+'</p></article><article><h2>별도 실험 · 직접 시간 예측</h2>'+uqTraining()+uqM1()+'<p class="caption">IMPTC Train · 학습량과 거리 구성이 함께 달라졌습니다. '+UQ.source('exit_aware/exit_aware_summary.json')+'</p></article></div>';
    case 6:return '<div id="slideReplay"></div>';
    case 7:return '<div class="summary-grid"><article><h2>세 가지 기여</h2><ol class="contributions"><li><b>관측·운동 불확실성 모델링</b><span>주석 차이로 관측오차를 추정하고, 입력 보정이 미래 분포에 미치는 영향을 측정했습니다.</span></li><li><b>횡단 완료 불확실성 정량화</b><span>미래 경로의 Exit 통과를 시간별 확률로 변환했습니다.</span></li><li><b>예측과 실제 기록의 대화형 검증</b><span>동일 시점에서 공간영역, 완료확률, 실제 결과를 함께 조회할 수 있습니다.</span></li></ol></article>'+
      '<article><h2>해석할 때 남는 한계</h2><ul class="limits"><li>미래 운동은 사전학습 DD-MDN에 의존하며, R은 SPD 주석 불일치의 대리값입니다.</li><li>필터링 후 예측영역의 포함률 회복은 불완전했고, FFBS 영역은 지나치게 넓었습니다.</li><li>정지·재출발 사례가 적고, 단순 기준선 대비 일관된 우위도 확인되지 않았습니다.</li><li>여러 번 사용한 과거 Test 자료에서 최대 4초까지 평가했습니다.</li><li>평가는 오프라인 기록 재생에 한정되며 현장 배포 성능은 검증되지 않았습니다.</li></ul><p><a href="results.html">전체 결과와 실험 부록 →</a>　<a href="DATA_POLICY.md">자료 이용 범위</a></p></article></div>';
  }
}
(async()=>{
  PS('pHeader').innerHTML=pNav('presentation');
  const s=await UQ.load();
  let index=0,release=null;
  function show(){
    const matched=/^#scene-([1-8])$/.exec(location.hash);
    index=matched?Number(matched[1])-1:0;
    const [section,title,sub]=slides[index];
    PS('pEyebrow').textContent=section;PS('pTitle').textContent=title;PS('pSubtitle').textContent=sub;
    release?.();release=null;document.body.classList.toggle('on-guided-slide',index===6);
    PS('pScene').innerHTML=content(index,s);
    if(index===6)release=mountGuided(PS('slideReplay'),s);
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
