'use strict';
const slides=[
 ['연구 목표 · 보행 예측에서 무엇을 검증할까?','View2Risk는 보행의 가능한 결과와 그 확률을 검증한다','불확실성 정량화(Uncertainty Quantification)의 목표는 한 점의 예측을 넘어, 가능한 미래에 확률을 부여하고 그 확률을 실제 보행 기록과 대조하는 것이다.'],
 ['연구 자료 · 같은 보행에서 무엇이 불확실한가?','관측 위치, 미래 경로, 횡단 완료시간을 구분한다','지금까지의 관측 위치에는 오차가 있고, 같은 과거에서도 미래 경로는 갈라진다. 그 경로 차이가 출구 도착 시각의 차이로 이어진다.'],
 ['통합 UQ 프레임워크 · 관측과 실제 완료를 어떻게 연결할까?','같은 횡단 사건을 경로 분포와 잔여시간 분포로 예측한다','주석 차이로 입력 오차를 모형화하고, 동일한 보행 기록에서 입력 조건만 바꿔 미래 위치 분포와 횡단 완료확률을 평가한다.'],
 ['관측오차 민감도 · 입력이 흔들리면 미래 위치 예측은 얼마나 달라질까?','합성 관측오차를 보정하자 두 자료에서 ADE가 약 81% 줄었다',({noisy,corrected,ind})=>'SPD 기반 합성 오차(IID 1×)에서 보정 후 4초 평균 위치 예측오차(ADE)는 Noisy 대비 IMPTC '+UQ.reduction(noisy.ade_m,corrected.ade_m)+', inD '+UQ.reduction(ind[1].ade_m,ind[2].ade_m)+' 줄었다.'],
 ['공간 예측 불확실성 · 위치 오차가 줄면 95% 영역도 신뢰할 수 있을까?','보정 후에도 실제 위치의 78.51%만 95% 예측영역에 들었다',({noisy,corrected})=>'IMPTC에서 대표 경로의 ADE는 '+UQ.reduction(noisy.ade_m,corrected.ade_m)+' 줄었다. 위치 분포는 실제 위치를 얼마나 자주 포함하는지, 그 영역이 얼마나 넓은지로 평가했다.'],
 ['횡단 완료 불확실성 · 미래 경로에서 완료확률을 어떻게 구할까?','출구를 처음 지나는 시각으로 기한별 완료확률을 구했다',({noisy,corrected})=>'경로마다 처음 Exit를 지나는 시각을 구했다. IMPTC에서 합성 관측을 보정하자 4초 완료확률의 Brier 점수가 '+PN(noisy.brier,5)+'에서 '+PN(corrected.brier,5)+'로 줄었다.'],
 ['직접 시간 예측 · 경로 없이 남은 횡단시간의 분포를 학습할 수 있을까?','출구 직전의 학습 시점을 보강하자 XGBoost의 1초 확률 오차가 줄었다','경로 기반 방법과 같은 완료 사건을 이번에는 잔여시간 분포로 예측했다. 동일한 Test 기록에서 기존 M1과 Exit-aware M1의 기한별 오차를 비교했다.'],
 ['한국 적용','국내 보행속도로 계산하면 현행 신호 시간이 부족한 곳이 있다.','독일 자료로 방법을 검증하고, 속도는 국내 실측값과 고령인구 비율로 바꿔 계산했다.'],
 ['개선 제안','설계 속도를 횡단보도와 날씨에 맞춰 다르게 정할 수 있다.','현행 고정 속도 운영과 영상 기반 스마트 횡단시스템에 이번 결과를 연결한 제안이다.'],
 ['3D 시연','관측부터 예측, 횡단 완료까지 하나의 화면에서 확인한다.','실제 보행 기록을 재생하며 카메라 오차, 보정, 예측 범위, 완료확률, 실제 결과를 비교한다.'],
 ['결론','횡단 완료확률을 만들고 검증했으며, 한국 신호 시간에 적용할 방법을 제시했다.','남은 과제는 예측 범위의 신뢰도 회복과 국내 자료·현장에서의 검증이다.']
];
const notes=[
 '보행자를 한 점으로 표시해도 그 점을 얼마나 정확히 관측했는지는 알 수 없습니다. 가능한 미래 경로가 여러 개면 출구에 도착하는 시각도 여러 개입니다. 연구 목표는 이 가능성에 확률을 부여하고 기록을 통해 그 신뢰성을 검증하는 것입니다. 먼저 어떤 자료가 각 질문에 답하는지 보겠습니다.',
 'SPD는 같은 보행자의 위치 주석 차이를 제공합니다. IMPTC는 보행 궤적과 경계를 함께 제공해 위치·완료를 모두 검증할 수 있습니다. inD는 다른 수집 환경에서 위치 민감도를 확인하는 보조 자료입니다. 이제 이 자료를 한 평가 절차에 어떻게 연결했는지 보겠습니다.',
 'SPD Train에서 위치 주석 쌍별로 평면 좌표 차이를 계산하고, 그 평균으로 편향을, 평균을 뺀 차이들의 공분산으로 R을 추정했습니다. 합성 오차를 더하기 전, 더한 후, 칼만 보정한 후를 같은 경로 예측기로 비교했습니다. 아래쪽 AFT는 관측 특징에서 시간을 직접 학습한 독립 분기입니다. 다음 장부터 위쪽 경로 분기의 결과를 살펴봅니다.',
 '회색 화살표는 예측 위치와 같은 시각의 실제 위치 사이 거리입니다. ADE는 0.5~4초의 여덟 거리를 평균합니다. 보정이 회복한 오차의 크기는 두 자료에서 비슷했지만 보정 후에도 Clean보다 오차가 큽니다. 이제 한 경로에서 위치분포 전체로 평가 대상을 옮깁니다.',
 '안쪽과 바깥쪽 윤곽은 모델이 부여한 68%, 95% 질량입니다. 실제 관측의 포함률과 영역 면적을 함께 봐야 과도하게 넓거나 실제를 놓치는 영역을 알아볼 수 있습니다. 이번 실험에서는 보정 후에도 목표보다 낮았습니다. 남은 오차가 왜 생겼는지는 이 비교로 식별할 수 없습니다. 다음에는 위치 영역과 다른 사건인 출구 통과를 다룹니다.',
 '기한 H에 경로의 끝이 어디인가만 보지 않고 그 전에 처음 출구를 통과했는지 셉니다. f2의 실제 통과는 2.063초여서 H2는 0, H3는 1입니다. 이 사례는 기전을 설명하고, 집계 Brier는 확률과 실제 사건 사이 오차를 평가합니다. 공간 포함률이나 단일 사례만으로 완료확률의 calibration을 확인할 수 없습니다.',
 '위쪽은 f2 한 사례의 실제 저장 CDF입니다. 거리에 종방향 속도·가속도를 더해 M1을 별도로 학습했고, 검열 사건에는 관측 종료 시점까지의 하한을 사용했습니다. 아래는 같은 Test 자료에서 학습 구성을 바꾼 비교입니다. View2Risk는 관측 불확실성이 미래 이동분포에 미치는 영향을 평가하고, 경로 기반과 직접 시간 예측 두 방식으로 완료 불확실성을 정량화합니다. 다음 장의 국내 신호시간은 국내 속도 통계와 시나리오에서 별도로 계산한 값입니다.',
 '이제 원래 목표인 신호 시간으로 돌아갑니다. 독일 자료는 방법을 검증하는 데 썼고, 속도는 국내에서 실제로 잰 값으로 바꿨습니다. 독일 보행자가 더 빨라서 그대로 쓰면 신호를 너무 짧게 잡기 때문입니다. 16미터 횡단보도 기준으로 현행은 23초입니다. 고령인구 20%를 반영해 95%가 건너는 기준으로 보면 27초가 필요하고, 비가 오면 85% 기준으로도 29초가 필요합니다.',
 '그래서 세 가지를 제안합니다. 첫째, 횡단보도 주변의 연령 구성에 따라 설계 속도를 정합니다. 둘째, 비가 오면 점멸 시간을 늘립니다. 셋째, 영상으로 보행자를 감지해 신호를 연장하는 시스템에는 카메라 오차 보정이 함께 필요합니다. 저희 실험에서 카메라 오차가 그대로 들어가면 완료확률 예측 오차가 열 배 가까이 커졌기 때문입니다. 이 제안들은 계산 예시에 근거한 것으로 현장 검증 전입니다.',
 '실제 화면으로 보여드리겠습니다. 전체 횡단 재생을 누르면 같은 보행자를 오차 없음, 카메라 오차, 보정 후로 비교할 수 있습니다. 저장된 미래 예측 보기에서 예측 경로와 범위를 보고, 횡단 완료 단계에서 완료확률을 확인한 뒤 실제 정답을 공개합니다.',
 '정리하겠습니다. 카메라 오차를 보정하자 향후 4초간 평균 위치 예측오차(ADE)가 3.9미터에서 0.74미터로, 완료확률 예측 오차는 74% 줄었습니다. 하지만 95% 범위의 실제 적중률은 79%로, 신뢰도 회복은 남은 과제입니다. 별도로 국내 보행속도와 시나리오 가정으로 계산하면 16미터 횡단보도에서 95%가 건너려면 현행 23초보다 긴 27초가 필요합니다. 국내 자료와 실제 현장에서의 검증이 다음 단계입니다. 감사합니다.'
];
const fig=(heading,graphic,caption)=>'<figure class="sci-figure"><h2>'+heading+'</h2>'+graphic+'<figcaption>'+caption+'</figcaption></figure>';
const metricSource=UQ.source('r_robustness/r_robustness_metrics.csv','원본 집계표');
const aftSource=UQ.source('exit_aware/exit_aware_matched_metrics.csv','M1 평가표');
const kpi=(label,value,sub)=>'<div class="kpi"><span>'+label+'</span><strong>'+value+'</strong><em>'+sub+'</em></div>';
const ladder=()=>'<ol class="scope-ladder" aria-label="연구 범위"><li><b>최종 목표</b><span>보행자 구성과 날씨에 맞춘 상황 적응형 보행 신호</span><em>다음 단계</em></li><li class="now"><b>이번 학기</b><span>완료확률 예측·검증 → 연령·날씨 반영 신호 시간 계산</span><em>오늘 발표</em></li><li><b>출발점</b><span>신호 시간 = 진입시간 + 거리 ÷ 1.0 m/s</span><em>모두 같은 속도로 가정</em></li></ol>';

function aftSlide(s){
  const model='EA_M1__calibrated',features=s.a.features;
  const remaining=s.e.GT.exit_s-s.a.origin_s;
  const horizons=UQ.horizons;
  const probabilities=horizons.map(h=>{
    const p=V2R.p(s,model,h);
    return p<.00005?'약 0%':p>.99995?'약 100%':UQ.pct(p);
  });
  const models=['M1__calibrated',model];
  const paired=models.map(name=>horizons.map(h=>UQ.evidence.audit.matched.find(r=>
    r.model===name&&r.horizon_s===h&&r.split==='test'&&r.cohort==='dd_matched')));
  const means=models.map(name=>UQ.evidence.key_table.find(r=>r.model===name).mean_brier);
  const [old,next]=['original','exit_aware'].map(version=>UQ.evidence.audit.support.find(r=>r.version===version));
  return '<div class="aft-study"><h2>한 사례 · IMPTC f2의 같은 예측 시점</h2>'+
    '<ol class="aft-pipeline" aria-label="보행 상태에서 기한별 완료확률까지"><li><h3>보행 상태</h3><dl>'+
    '<dt>Exit까지 거리</dt><dd>'+PN(features.distance_m,2)+' m</dd><dt>종방향 속도</dt><dd>'+PN(features.v_long_mps,2)+' m/s</dd><dt>종방향 가속도</dt><dd>'+PN(features.a_long_mps2,3).replace('-','−')+' m/s²</dd></dl></li>'+
    '<li><h3>XGBoost AFT · M1</h3><p>학습 목표는 실제 Exit 통과까지 남은 시간이다. 통과 전에 관측이 끝나면 마지막 관측까지의 시간을 하한으로 학습한다(우측검열).</p></li>'+
    '<li><h3>잔여시간 누적분포</h3>'+figAftCdf(s,model,remaining)+'</li>'+
    '<li><h3>기한별 완료확률</h3><dl>'+horizons.map((h,i)=>'<dt>'+h+'초 이내</dt><dd>'+probabilities[i]+'</dd>').join('')+'</dl></li></ol>'+
    '<p class="caption">f2 / o0008 · Exit-aware M1 · 곡선은 저장된 0.05초 간격의 누적확률이다. 분홍 점선은 실제 통과 시각이다. '+UQ.source('data/public/exit-aware.json','사례 예측')+'</p>'+
    '<div class="pair aft-evidence">'+fig('학습 자료 · Exit 직전 시점 보강',figTraining(),'기존 Train에는 Exit 1 m 이내 시점이 없었다. 같은 Train에서 '+next.n_train_lt1+'개를 확보해 최소 잔여 거리를 '+PN(old.min_distance_m,2)+' → '+PN(next.min_distance_m,3)+' m로 줄였다. 학습량과 거리 구성이 함께 달라졌다.')+
    '<article><h2>집계 평가 · 같은 M1의 Brier 비교</h2>'+pTable(['학습 구성',...horizons.map(h=>'H'+h)],paired.map((rows,i)=>[i?'Exit-aware':'Original',...rows.map(r=>PN(r.event_weighted_brier,5))]))+
    '<p class="aft-result"><b>평균 Brier '+PN(means[0],5)+' → '+PN(means[1],5)+'</b> · 약 '+Math.round(100*(1-means[1]/means[0]))+'% 감소 · H1 '+UQ.reduction(paired[0][0].event_weighted_brier,paired[1][0].event_weighted_brier)+' 감소</p>'+
    '<p class="caption">매칭 IMPTC Test '+paired[0][0].n_origins+'시점 · '+paired[0][0].n_events+'건. 사건별 가중 Brier는 낮을수록 좋다. H1~H4 정답 수 '+paired[0].map(r=>r.n_known).join(' / ')+'. 비교 기준은 기존 M1이다. '+aftSource+' · '+UQ.source('results.html','전체 기준선 비교')+'</p></article></div></div>';
}

function figUqArchitecture(){
  const neutral='#37545d',edge='#72838a';
  function node(x,y,w,h,title,lines,color){
    const box='<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="3" fill="white" stroke="'+color+'" stroke-width="1.5"/>';
    return box+ink(x+12,y+25,title,color,'start',19)+lines.map((t,i)=>ink(x+12,y+49+21*i,t,neutral,'start',16)).join('');
  }
  const arrow=(x,y,u,v)=>'<path d="M'+x+' '+y+' L'+u+' '+v+'" fill="none" stroke="'+edge+'" stroke-width="1.7" marker-end="url(#uq-flow-arrow)"/>';
  let b='<defs><marker id="uq-flow-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="'+edge+'"/></marker></defs>';
  b+=ink(8,22,'경로 기반 예측',SC.future,'start',20);
  b+=node(8,38,188,103,'SPD 학습 주석 쌍',['두 좌표의 차이','→ 편향 b, 공분산 R'],SC.noisy);
  b+=node(221,38,238,103,'기록된 보행에 합성 오차',['기준 / 합성 / 칼만 보정','보정은 합성 관측에 선택 적용'],SC.clean);
  b+=node(487,38,202,103,'사전학습 DD-MDN',['과거 0.9초를 입력','미래 경로 분포를 출력'],SC.future);
  b+=node(728,30,215,59,'공간 · 시점별 위치',['68%·95% 최고밀도영역'],SC.future);
  b+=node(728,99,215,59,'시간 · 최초 Exit 통과',['기한 안에 통과한 표본 비율'],SC.future);
  b+=node(972,30,223,59,'실제 위치와 대조',['ADE · 포함률 · 영역 면적'],neutral);
  b+=node(972,99,223,59,'실제 완료와 대조',['기한별 결과 0/1 · Brier'],neutral);
  b+=arrow(196,85,217,85)+arrow(459,85,483,85)+arrow(689,84,723,61)+arrow(689,92,723,124)+arrow(943,60,968,60)+arrow(943,127,968,127);
  b+=segment(8,178,1195,178,'#ccd8d9')+ink(8,209,'직접 시간 예측',SC.filtered_mean,'start',20);
  b+=node(8,225,287,76,'보행 상태',['잔여 거리 · 종방향 속도 · 가속도'],SC.clean);
  b+=node(325,225,205,76,'XGBoost AFT',['팀에서 독립 학습한 M1'],SC.filtered_mean);
  b+=node(560,225,208,76,'잔여시간의 분포',['기한 H에서 누적확률을 읽음'],SC.filtered_mean);
  b+=node(798,225,189,76,'횡단 완료확률',['P(T_exit ≤ H)'],SC.filtered_mean);
  b+=node(1017,225,178,76,'실제 완료와 대조',['같은 기한의 Brier'],neutral);
  b+=arrow(295,262,321,262)+arrow(530,262,556,262)+arrow(768,262,794,262)+arrow(987,262,1013,262);
  return svgFrame('주석 차이에서 두 예측 분기와 실제 보행 기록 검증까지',b,1205,310);
}

function content(i,s,ind){
  const rows=uqRobustRows(),[clean,noisy,corrected]=rows,train=V2R.evidence.r_proxy.train_fit;
  switch(i){
    // UQ edition opening. The application, replay and conclusion follow the original deck.
    case 0:return '<div class="lead-grid"><article><h2>한 번의 횡단에서 묻는 세 가지</h2><ol class="questions"><li>지금까지 관측한 위치는 얼마나 정확한가?</li><li>같은 과거에서 앞으로 어디에 있을 수 있는가?</li><li>주어진 시간 안에 출구를 지날 확률은 얼마인가?</li></ol><p>View2Risk의 연구 대상은 이 질문들을 하나의 횡단 과제로 연결하고, 예측을 실제 위치와 통과 기록에 대조하는 과정이다.</p></article>'+
      fig('한 보행 기록에서 갈라지는 미래',figQuestions(),'개념도 · 파랑은 관측한 과거, 보라는 가능한 미래다. 같은 시간 동안에도 일부 경로만 출구에 닿는다.')+'</div>';
    case 1:return '<div class="pair"><article><h2>무엇이 불확실한가</h2><dl class="uq-terms"><dt>관측 불확실성</dt><dd>현재와 과거에 기록된 위치가 기준 위치에서 얼마나 흔들리는가.</dd><dt>공간 예측 불확실성</dt><dd>같은 관측에서 출발할 때 앞으로 각 시각의 위치가 어디에 분포하는가.</dd><dt>횡단 완료 불확실성</dt><dd>남은 횡단시간이 어떻게 분포하고, 기한 안에 Exit를 지날 가능성은 얼마인가.</dd></dl></article>'+
      fig('관측 위치의 차이와 가능한 미래 경로',figSources(),'개념도 · 왼쪽의 오차는 이미 관측한 시각에 있고, 오른쪽의 퍼짐은 아직 관측하지 않은 미래에 있다.')+'</div>'+
      '<div class="uq-data-row"><div><b>SPD</b><span>두 주석의 차이로 관측오차 대리 모형 추정</span></div><div><b>IMPTC</b><span>실제 궤적·횡단 경계로 미래 위치와 완료 평가</span></div><div><b>inD</b><span>다른 수집 환경에서 궤적 예측의 강건성 보조 평가</span></div></div>';
    case 2:return '<figure class="uq-system">'+figUqArchitecture()+'<figcaption>기존 기법인 칼만 필터와 사전학습 DD-MDN을 사용했다. 팀은 오차 모형화·보정 비교, 공간·시간 검증, 직접 시간 모형 학습과 시각화를 구현했다.</figcaption></figure>'+
      '<div class="uq-r-method"><h2>R은 어떻게 얻었나?</h2><p>SPD Train '+train.n.toLocaleString('en-US')+'쌍의 위치 주석에서 좌표 차이를 구했다. 차이의 평균은 <b>편향 b</b>, 평균을 뺀 차이의 공분산은 <b>R</b>이다. X/Y 표준편차는 <b>'+PN(Math.sqrt(train.covariance_m2[0][0])*100,1)+' / '+PN(Math.sqrt(train.covariance_m2[1][1])*100,1)+' cm</b>, 주석 불일치 RMSE는 <b>'+PN(train.RMSE_m*100,1)+' cm</b>였다. 이 값은 SPD 주석에서 얻은 관측오차 대리값이다. IMPTC에서 검출기 오차를 직접 측정한 값과 구분한다. '+UQ.source('data/public/demo-evidence.json','SPD 추정값')+'</p></div>';
    case 3:{
      const chart=figGroupedBars({title:'자료별 향후 4초간 평균 위치 예측오차(ADE)',series:rows.map((r,j)=>({label:['Clean','Noisy','Corrected'][j],color:SC[r.mode]})),groups:[rows,ind].map(a=>({label:a[0].dataset,values:a.map(r=>r.ade_m)})),maximum:5,ticks:[0,1,2,3,4,5],axis:'4초 ADE (m) · 작을수록 정확',decimals:3});
      return '<div class="pair">'+fig('같은 시각의 예측과 실제 위치',figDistances(s),'IMPTC f2 · 합성 오차 1× 한 사례. ADE는 향후 0.5~4초의 여덟 시각에서 대표 예측과 실제 위치 간 거리를 평균한다.')+
        fig('기록과 예측기를 고정한 입력 비교',chart,'Test · IMPTC 120건 중 ADE 유효 215시점, inD 11개 궤적·99시점. 같은 합성 오차에서 IMPTC ADE는 Clean 대비 '+PN(noisy.ade_m/clean.ade_m,1)+'배가 됐다. '+metricSource)+'</div>'+
        '<p class="uq-transition">위치 예측오차는 감소했지만, 확률적 예측영역의 신뢰성도 회복되었는지 확인할 필요가 있다.</p>';
    }
    case 4:return '<div class="pair spatial-layout">'+fig('예측 확률 질량과 실제 위치',figHdr(),'개념도 · HDR95는 모델이 한 시각의 예측 질량 95%를 배정한 최고밀도영역이다. Coverage95는 실제 위치 중 각 예측영역 안에 든 비율이다.')+
      fig('목표 포함률과 영역 크기의 관계',figCoverage(rows),'IMPTC Test · SPD 기반 IID 1× · +4초 실제 위치 n=228, 영역 n=237. HDR95 Area는 95% 영역의 평균 넓이(m²)다. 세로축은 포함률, 가로축은 면적의 로그 눈금이다. '+metricSource)+'</div>'+
      '<p class="uq-transition">칼만 보정 후 평균 면적은 '+PN(noisy.hdr95_area_m2,2)+' → '+PN(corrected.hdr95_area_m2,2)+' m²로 줄었다. 포함률이 95%에 미달한 원인은 이 비교만으로 특정할 수 없다.</p>';
    case 5:return '<div class="pair uq-passage"><article><h2>처음 출구를 지난 시각 T<sub>exit</sub></h2>'+figCrossing()+'<p>같은 미래 경로의 위치들을 함께 추출한 뒤, 각 경로가 처음 Exit를 지나는 시각을 찾는다. 그 시각이 H 이하인 표본의 비율이 <b>P(T<sub>exit</sub> ≤ H)</b>다.</p><p class="caption">개념도 · 10개 중 6개가 통과하면 60%다. 실제 f2 확률은 저장된 공동 경로 표본의 집계값이다.</p></article>'+
      '<article><h2>한 사례 · IMPTC f2, Clean</h2>'+figCompletionBars(s)+'<p class="caption">실제 완료는 예측 후 <b>'+PN(s.e.GT.exit_s-s.r.origin_s,3)+'초</b>다. 2초 기한의 결과는 0, 3초 기한의 결과는 1이다.</p>'+
      '<h3>집계 · H4 Brier</h3><p>예측확률과 실제 완료 여부(0 또는 1)의 차이를 제곱해 평균한다. 값이 작을수록 확률 오차가 작다.</p><p class="caption">IMPTC IID 1× · 4초 결과가 확인된 218시점. Clean 기준 '+PN(clean.brier,5)+'. Noisy 대비 보정 후 '+UQ.reduction(noisy.brier,corrected.brier)+' 감소. 공간 포함률은 위치를 검증하며, 완료확률의 보정 수준은 예측확률과 실제 완료 빈도로 따로 확인해야 한다. '+metricSource+'</p></article></div>'+
      '<p class="uq-transition">경로를 먼저 예측하는 대신, 횡단 완료시간의 확률분포를 직접 학습할 수도 있지 않을까?</p>';
    case 6:return aftSlide(s);
    case 7:return '<div class="pair signal-slide"><article><h2>16 m 횡단보도의 보행 신호 시간</h2>'+
      pTable(['조건','설계 속도','신호 시간'],[['현행 기준','1.00 m/s','23.0초'],['노인 20% · 85% 완료','0.97 m/s','23.5초'],['<b>노인 20% · 95% 완료</b>','<b>0.80 m/s</b>','<b>27.0초</b>'],['노인 20% · 85% · 비 오는 날','0.73 m/s','29.0초']])+
      '<p class="caption">신호 시간 = 진입 7초 + 거리 ÷ 설계 속도. 국내 속도 통계와 시나리오 가정으로 계산했다. XGBoost 예측값은 이 계산에 사용하지 않았다.</p></article>'+
      '<article><h2>독일 자료를 한국에 맞춘 방법</h2><dl class="data-roles"><dt>독일 IMPTC</dt><dd>방법 검증: 카메라 오차의 영향과 보정 효과</dd><dt>국내 실측</dt><dd>보행속도: 일반인 하위 15% 1.01 m/s, 노인 0.85 m/s</dd><dt>통계청</dt><dd>2025년 고령인구 20.3%로 일반인·노인 분포를 혼합</dd><dt>문헌</dt><dd>비 오는 날 보행속도 약 25% 감소</dd></dl><p class="caption">독일 보행자는 더 빨라(하위 15% 약 1.30 m/s) 그대로 쓰면 신호를 3.5초 짧게 잡는다. 출처: KoreaScience JAKO202025551105671, 통계청 2025 고령자 통계, Deng 외(2017).</p></article></div>';
    case 8:return '<div class="cards3">'+
      '<article><h2>1. 연령 구성 반영</h2><p>현행: 일반도로 1.0 m/s, 보호구역 0.7 m/s 두 가지</p><p class="takeaway">횡단보도 주변 노인 비율로 설계 속도를 정한다</p><p class="caption">노인 40% 지역, 95% 기준 28.0초 (현행 23.0초)</p></article>'+
      '<article><h2>2. 날씨 반영</h2><p>현행: 날씨와 무관한 고정 시간</p><p class="takeaway">비가 오면 점멸 시간을 늘린다</p><p class="caption">85% 기준 23.5 → 29.0초 (+5.5초)</p></article>'+
      '<article><h2>3. 영상 감지에 카메라 오차 보정</h2><p>현행: 영상으로 보행자를 감지하는 스마트 횡단시스템</p><p class="takeaway">완료확률이 낮을 때만 연장하고, 카메라 위치 오차를 함께 보정한다</p><p class="caption">카메라 오차가 그대로 들어가면 완료확률 예측 오차 약 10배 (0.035 → 0.335)</p></article></div>'+
      '<p class="caption">현행 기준: 경찰청 교통신호기 설치·관리 매뉴얼, 2022 업무편람 개정. 제안은 이번 프로젝트의 계산 예시에 근거하며 현장 검증 전이다.</p>';
    case 9:return '<div id="slideReplay"></div>';
    case 10:return '<div class="kpi-row four">'+
      kpi('카메라 오차 보정 후 · 향후 4초간 평균 위치 예측오차(ADE)',PN(noisy.ade_m,2)+' → '+PN(corrected.ade_m,2)+' m',UQ.reduction(noisy.ade_m,corrected.ade_m)+' 감소 · 오차 없음은 '+PN(clean.ade_m,2)+' m')+
      kpi('카메라 오차 보정 후 · 완료확률 예측 오차',PN(noisy.brier,3)+' → '+PN(corrected.brier,3),UQ.reduction(noisy.brier,corrected.brier)+' 감소 · 0에 가까울수록 정확')+
      kpi('보정 후 · 95% 범위의 실제 적중률',UQ.pct(corrected.coverage95),'목표 95% · 오차 없음은 '+UQ.pct(clean.coverage95))+
      kpi('16 m 횡단보도에 필요한 신호 시간','23초 → 27초','노인 20%, 보행자 95%가 건너는 기준')+'</div>'+
      '<div class="cards3"><article><h2>목표</h2>'+ladder()+'</article>'+
      '<article><h2>이뤄낸 것</h2><ul><li>서로 다른 자료를 결합해 카메라 위치 오차와 보행 불확실성을 함께 다룸</li><li>횡단 완료확률을 만들고 실제 기록으로 검증</li><li>XGBoost AFT로 잔여시간 분포를 학습하고 Exit 부근의 학습 자료를 보강</li><li>국내 보행속도·고령인구·날씨로 신호 시간 계산 방법 제시</li><li>3D 검증 시스템 구현</li></ul></article>'+
      '<article><h2>남은 과제</h2><ul><li>95% 범위의 실제 적중률 회복 (79% → 95%)</li><li>실제 카메라 오차와 국내 보행 자료로 재검증</li><li>현장 신호 운영에서의 효과 검증</li></ul></article></div>';
  }
}
(async()=>{
  PS('pHeader').innerHTML=pNav('presentation');
  for(const link of PS('pHeader').querySelectorAll('.p-brand,[aria-current="page"]'))link.href='presentation-uq.html#scene-1';
  const [s,robust]=await Promise.all([UQ.load(),V2R.json('r_robustness/r_robustness_summary.json')]);
  const ind=uqRobustRows('inD',robust.metrics);
  const [,noisy,corrected]=uqRobustRows();
  let index=0,release=null;
  function show(){
    const matched=/^#scene-([1-9]\d*)$/.exec(location.hash);
    index=matched&&Number(matched[1])<=slides.length?Number(matched[1])-1:0;
    const [section,title,sub]=slides[index];
    PS('pEyebrow').textContent=section;PS('pTitle').textContent=title;PS('pSubtitle').textContent=typeof sub==='function'?sub({noisy,corrected,ind}):sub;
    release?.();release=null;document.body.classList.toggle('on-guided-slide',index===9);
    PS('pScene').dataset.scene=index+1;
    PS('pScene').innerHTML=content(index,s,ind);
    if(index===9)release=mountDemonstration(PS('slideReplay'),s);
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
