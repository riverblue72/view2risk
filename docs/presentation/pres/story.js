'use strict';
const slides=[
 ['Motivation','한 줄의 예상 경로만으로 횡단을 설명할 수 있을까?','View2Risk · 보행자의 관측과 움직임에서 횡단 완료확률까지'],
 ['Data','현재 위치와 미래 움직임은 왜 서로 다르게 불확실할까?','같은 사람을 보는 두 관측의 차이와, 같은 과거에서 가능한 여러 미래를 구분합니다.'],
 ['Observation model','보행자 위치의 흔들림을 어떻게 모형화할까?','관측오차 공분산 R은 두 주석의 위치 차이가 어느 방향으로 얼마나 퍼지는지 요약합니다.'],
 ['Trajectory model','과거 0.9초에서 다음 4초의 위치 분포를 어떻게 얻을까?','공식 사전학습 DD-MDN은 과거 위치와 장면 정보를 받아 여러 미래 경로와 시점별 위치 분포를 출력합니다.'],
 ['Trajectory accuracy','관측을 보정하면 미래 위치가 실제 기록에 가까워질까?','예측과 실제 위치를 같은 시각끼리 짝지어 미터 단위로 거리를 잽니다.'],
 ['Spatial uncertainty','95% 예측영역은 실제 위치를 얼마나 자주 포함할까?','한 시각에 예측한 위치 분포의 확률 질량과, 여러 사례에서 측정한 실제 포함률을 구분합니다.'],
 ['Crossing completion','앞으로 H초 안에 횡단을 마칠 가능성은 얼마일까?','경로의 첫 Exit 통과를 시간별 확률로 바꾸고, 각 기한의 실제 완료 여부와 비교합니다.'],
 ['Exit-aware training','출구 직전의 기록을 학습하면 시간 예측이 달라질까?','별도 실험 · XGBoost AFT는 현재 거리와 속도 등의 특징으로 남은 횡단 시간을 직접 예측합니다.'],
 ['Interactive demonstration','같은 보행자의 관측을 바꾸면 무엇이 달라질까?','공개 IMPTC 기록 재생 · 같은 예측 시점의 관측, 미래 위치 분포와 완료확률 비교'],
 ['Contributions & limitations','어디까지 검증했고, 무엇이 남았을까?','View2Risk는 관측오차가 미래 움직임과 횡단 완료확률에 미치는 영향을 실제 기록으로 평가했습니다.']
];
const notes=[
 '현재 위치의 관측오차, 가능한 미래 위치의 퍼짐, 특정 시간 안에 횡단할 가능성은 서로 다른 질문입니다. 자율주행 및 신호 운영에서 의미 있는 질문이지만 현장 안전 효과는 평가하지 않았습니다.',
 'SPD는 관측오차 대리 모형 추정에, IMPTC는 궤적·횡단 경계·실제 완료 구성에 사용했습니다. inD는 위치 평가를 보완하며 검증된 Exit 정답이 없습니다.',
 '점은 각 시각의 위치입니다. 주황 점선은 합성 오차를 더한 관측, 초록 선은 이 시점까지의 관측으로 보정한 과거입니다. 타원은 마지막 유효 합성 측정에 표시한 Gaussian 측정오차 범위입니다.',
 '기준 과거는 그대로 입력합니다. 합성 관측은 보정 전후를 비교합니다. 위치 영역은 시점별 혼합분포의 고밀도 윤곽, 완료확률은 별도의 joint 경로 표본 통과율입니다.',
 '미래 0.5초부터 4초까지 대표 예측의 8개 위치를 실제 기록과 대조합니다. ADE는 8개 거리를 평균하고 FDE는 마지막 거리를 취합니다. 사례 그림과 전체 평가 표의 분모를 구분합니다.',
 'HDR의 질량은 모델이 배정한 확률입니다. 95% Coverage라면 평가 가능한 실제 위치 100개 중 약 95개를 포함합니다. 영역을 크게 만드는 것만으로 정확하고 유용한 분포가 되지는 않습니다.',
 '예측영역은 특정 시각의 위치를 묻습니다. 경로 전체의 통로나 충돌 위험은 별도 문제입니다. 실제 첫 통과를 보간하고 이후 최소 0.12초 관측을 확인했습니다. H에서 완료 여부가 불명확하면 해당 점수에서 제외했습니다. Brier는 예측확률과 0·1 결과 간 차이의 제곱을 평균합니다.',
 '학습 시점의 양과 구성이 함께 바뀌었습니다. 같은 M1 두 설정을 같은 Test에서 비교한 결과입니다. 기존 단순 기준선과 Conditional AFT의 전체 결과는 부록에 있습니다.',
 '같은 시점에서 Clean, Noisy, Corrected를 누르세요. 전체 영역과 횡단부를 비교하고, 4단계에서 정답을 공개하세요. 한 사례의 오차는 집계 점수와 구분해서 읽습니다.',
 '정지·재출발, 실제 센서 오차 전이, 새로운 날짜에서의 보정 및 배포 환경 검증은 남아 있습니다.'
];
const fig=(heading,graphic,caption)=>'<figure class="sci-figure"><h2>'+heading+'</h2>'+graphic+'<figcaption>'+caption+'</figcaption></figure>';
const takeaway=text=>'<p class="sci-conclusion">'+text+'</p>';
const modeLabel=r=>'<b style="color:'+SC[r.mode]+'">'+UQ.names[r.mode]+'</b>';
function content(i,s){
  const rows=uqRobustRows(),[clean,noisy,corrected]=rows;
  const base='IMPTC Test · IID 1× · 같은 237개 시점 / 120건';
  const source=UQ.source('r_robustness/r_robustness_metrics.csv','원본 집계표');
  const train=V2R.evidence.r_proxy.train_fit;
  switch(i){
    case 0:return '<div class="lead-grid"><article><p class="lede">보행자가 어디에 있는지, 어디로 갈지, 언제 횡단을 마칠지는 각각 다른 질문입니다.</p><ol class="questions"><li>지금 관측한 위치는 얼마나 정확한가?</li><li>다음 몇 초 동안 어디에 있을 수 있는가?</li><li>그중 몇 경로가 기한 안에 Exit를 지나는가?</li></ol><p>자율주행 상황 인지와 지능형 교통 신호 운영에서 제기되는 질문입니다.</p></article>'+fig('현재에서 Exit까지',figQuestions(),'<b>개념도</b> · Entry는 보행자가 들어오는 경계, Exit는 건너편 도착 경계입니다. 파란 선은 관측한 과거, 보라색은 가능한 미래입니다. 선택한 기한까지 출구에 이르지 못하는 경로도 있습니다.')+'</div>'+takeaway('위치 하나를 고르는 것만으로는 완료 시각의 불확실성을 설명할 수 없습니다.');
    case 1:return '<div class="pair">'+fig('두 종류의 불확실성',figSources(),'<b>개념도</b> · 왼쪽 타원은 측정 위치의 흔들림, 오른쪽 선들은 같은 과거에서 가능한 미래 방향입니다.')+'<article class="research-flow"><h2>어떤 기록으로 확인했나?</h2><p><b>SPD · 관측오차 추정</b>카메라와 가상 LiDAR가 같은 보행자에 남긴 위치 주석의 차이를 측정합니다.</p><p><b>IMPTC · 미래와 정답</b>보행 궤적과 횡단 지도로 미래 위치와 실제 출구 통과를 확인합니다.</p><p><b>inD · 보조 궤적 평가</b>다른 장면에서 위치 예측을 비교합니다. 공개 화면에는 집계 결과만 사용합니다.</p></article></div>'+takeaway('관측오차는 입력 위치에, 미래 운동의 불확실성은 예측 분포에 나타납니다.');
    case 2:return '<div class="pair">'+fig('A　같은 과거의 기준·합성·보정 위치',figObservation(s),'실제 f2 과거 + IID 1× 합성 오차 · 점은 0.1초 간격. 타원은 마지막 합성 관측 위치에 그린 R의 95% 범위입니다. '+UQ.source('data/public/r/o0008.json','f2 저장 자료')+'')+'<article><h2>SPD 주석에서 얻은 오차의 크기</h2>'+pTable(['Train 주석 쌍','X 표준편차','Y 표준편차','위치 RMSE'],[[train.n.toLocaleString('en-US'),PN(100*Math.sqrt(train.covariance_m2[0][0]),1)+' cm',PN(100*Math.sqrt(train.covariance_m2[1][1]),1)+' cm',PN(train.RMSE_m*100,1)+' cm']])+'<p>R은 주석 위치 차이의 공분산입니다. RMSE는 두 위치 사이 거리의 제곱평균에 제곱근을 취한 값입니다.</p><p>이 대리 모형으로 과거 관측에 오차를 더하고, 칼만 필터로 그 위치를 보정했습니다. IMPTC 검출기의 실측 오차는 별도 검증이 필요합니다.</p></article></div>'+takeaway('실제 보행은 그대로 두고 관측만 교란해, 입력 오차의 영향을 비교했습니다.');
    case 3:return '<div class="pair">'+fig('B　입력 10점 → 미래의 8개 예측 시각',figForecast(s),'IMPTC f2 · 기준 입력. 보라색 점은 +0.5초부터 +4초까지 0.5초 간격의 대표 위치입니다. 진한 안쪽 영역은 +4초 위치의 68%, 옅은 바깥 영역은 95% 확률 질량을 담습니다.')+'<article class="framework-figure"><h2>관측에서 실제 기록 대조까지</h2>'+figFramework()+'<p class="caption">View2Risk는 관측 보정 실험, 위치 영역·완료확률 계산 및 평가를 구현했습니다. DD-MDN의 분포에서 물리적 과정잡음 공분산 Q를 별도로 식별하지 않았습니다. Conditional AFT와 XGBoost AFT는 완료 시간을 직접 추정하는 별도 경로입니다.</p></article></div>'+takeaway('같은 예측 분포로 미래의 위치와 횡단 완료 시각에 관한 두 질문에 답합니다.');
    case 4:return '<div class="pair">'+fig('C　같은 시각의 예측과 실제 위치를 연결',figDistances(s),'IMPTC f2 · Noisy 단일 사례. 회색 화살표 하나가 한 시각의 거리 오차 dₜ입니다.')+'<article><h2>위치 오차가 작을수록 실제 위치에 가깝습니다</h2><p><b>ADE</b> (Average Displacement Error)는 미래 전체의 평균 거리, <b>FDE</b> (Final Displacement Error)는 마지막 시각의 거리입니다.</p><p class="formula">ADE = (d₁ + … + d₈) / 8　·　FDE = d₈</p>'+pTable(['집계 조건','ADE (m)','FDE (m)'],rows.map(r=>[modeLabel(r),PN(r.ade_m),PN(r.fde_m)]))+'<p class="caption">'+base+' · ADE 유효 215개, 4초 FDE 유효 228개. '+source+'</p></article></div>'+takeaway('합성 오차 입력을 보정하자 ADE가 '+PN(noisy.ade_m)+' m에서 '+PN(corrected.ade_m)+' m로 줄었습니다. Noisy 대비 '+UQ.reduction(noisy.ade_m,corrected.ade_m)+' 감소입니다.');
    case 5:{
      const table=pTable(['집계 조건','Coverage95','HDR95 면적'],rows.map(r=>[modeLabel(r),UQ.pct(r.coverage95),PN(r.hdr95_area_m2,2)+' m²']));
      return '<div class="pair coverage-slide"><article>'+fig('D　한 시각의 위치 예측영역',figHdr(),'<b>개념도</b> · 분홍 점은 가능한 두 실제 위치입니다. HDR(최고밀도영역)은 예측 확률 질량의 68% 또는 95%를 담습니다.')+table+'</article><article>'+fig('면적이 넓어도 정답을 놓칠 수 있습니다',figCoverage(rows),base+' · 4초 실제 위치 n=228, 면적 n=237. '+source)+'<p><b>Coverage95</b>는 95% 영역 안에 든 실제 위치의 비율입니다. <b>HDR95 Area</b>는 그 영역의 넓이(m²)입니다.</p></article></div>'+takeaway('보정은 과도한 면적을 줄였지만 실제 포함률은 '+UQ.pct(corrected.coverage95)+'로 목표 95%에 미달했습니다. 영역이 나타내는 대상은 특정 시각의 보행자 위치입니다.');
    }
    case 6:return '<div class="pair completion-slide"><article><h2>E　경로에서 완료확률로</h2>'+figCrossing()+'<p><b>개념 예시</b> · 같은 H초에 10개 중 6개가 Exit를 지나면 P(T<sub>exit</sub> ≤ H) = 60%입니다.</p>'+pTable(['실제 f2 · Clean',...UQ.horizons.map(h=>h+'초')],[['누적 완료확률',...UQ.horizons.map(h=>UQ.pct(s.clean.exit.probabilities[h]))]])+'<p class="case-note">남은 거리 '+PN(s.features.distance_m,2)+' m · 종방향 속도 '+PN(s.features.v_long_mps,2)+' m/s. 실제 통과는 +'+PN(s.e.GT.exit_s-s.r.origin_s,3)+'초이므로 H2는 미완료(0), H3는 완료(1)입니다.</p><p class="caption">실제 확률은 저장된 joint 표본 통과율입니다. 화면에 그린 후보 20개의 개수와 구분합니다.</p></article><article><h2>F　Brier Score로 확률 오차 평가</h2>'+figBrier()+'<p><b>개념 예시</b> · 완료를 80%로 예측하고 실제로 완료했다면 (0.8 − 1)² = 0.04입니다.</p><p class="formula">Brier = 평균[(예측확률 p − 실제 결과 y)²]</p>'+pTable(['집계 조건','H4 Brier'],rows.map(r=>[modeLabel(r),PN(r.brier,5)]))+'<p class="caption">'+base+' · H4 정답 확인 218개. Brier는 분류 정확도와 다른 확률 예측 오차이며 작을수록 좋습니다. '+source+'</p></article></div>'+takeaway('보정 후 H4 Brier가 Noisy 대비 '+UQ.reduction(noisy.brier,corrected.brier)+' 감소했습니다. f2 한 사례로 집단 전체의 확률 보정 수준을 판단할 수는 없습니다.');
    case 7:return '<div class="pair">'+fig('G　Exit까지 남은 거리별 학습 분포',figTraining(),'IMPTC Train · 원래 시점과 Exit-aware 시점. 막대 길이는 같은 개수 축척이며 왼쪽부터 세 거리 구간을 누적했습니다.').replace('</figure>','<p>가장 가까운 학습 위치가 Exit 전방 2.19 m에서 0.059 m로 바뀌었습니다.</p></figure>')+'<article><h2>같은 평가 집단에서 본 M1의 변화</h2>'+uqM1()+'<p>Exit 1 m 이내의 학습 시점이 0개에서 393개로 늘었습니다. 학습량과 표본 구성이 함께 달라졌습니다.</p></article></div>'+takeaway('기존 XGBoost AFT 설정 대비 평균 Brier가 약 71.0%, H1이 94.3% 감소했습니다. 전체 기준선에 대한 일관된 우위는 확인되지 않았습니다.');
    case 8:return '<div id="slideReplay"></div>';
    case 9:return '<div class="summary-grid"><article><h2>세 가지 기여</h2><ol class="contributions"><li><b>관측·운동 불확실성 모델링</b><span>주석 차이로 관측오차를 추정하고, 입력 보정이 미래 분포에 미치는 영향을 측정했습니다.</span></li><li><b>횡단 완료 불확실성 정량화</b><span>미래 경로의 Exit 통과를 시간별 확률로 변환했습니다.</span></li><li><b>예측과 실제 기록의 대화형 검증</b><span>동일 시점에서 공간영역, 완료확률, 실제 결과를 함께 조회할 수 있습니다.</span></li></ol></article>'+
      '<article><h2>해석할 때 남는 한계</h2><ul class="limits"><li>미래 운동은 사전학습 DD-MDN에 의존하며, R은 SPD 주석 불일치의 대리값입니다.</li><li>필터링 후 예측영역의 포함률 회복은 불완전했고, FFBS 영역은 지나치게 넓었습니다.</li><li>정지·재출발 사례가 적고, 단순 기준선 대비 일관된 우위도 확인되지 않았습니다.</li><li>여러 번 사용한 과거 Test 자료에서 최대 4초까지 평가했습니다.</li><li>평가는 오프라인 기록 재생에 한정되며 현장 배포 성능은 검증되지 않았습니다.</li></ul><p><a href="results.html">전체 결과와 실험 부록 →</a>　<a href="DATA_POLICY.md">자료 이용 범위</a></p></article></div>';
  }
}
(async()=>{
  PS('pHeader').innerHTML=pNav('presentation');
  const s=await UQ.load();
  let index=0,release=null;
  function show(){
    const matched=/^#scene-([1-9]|10)$/.exec(location.hash);
    index=matched?Number(matched[1])-1:0;
    const [section,title,sub]=slides[index];
    PS('pEyebrow').textContent=section;PS('pTitle').textContent=title;PS('pSubtitle').textContent=sub;
    release?.();release=null;document.body.classList.toggle('on-guided-slide',index===8);
    PS('pScene').innerHTML=content(index,s);
    if(index===8)release=mountGuided(PS('slideReplay'),s);
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
