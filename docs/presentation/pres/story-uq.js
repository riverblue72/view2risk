'use strict';
const slides=[
 ['연구 목표 · 기한 안에 횡단을 마칠 가능성은 얼마인가?','보행자의 미래 위치와 횡단 완료시간의 불확실성을 정량화한다.','View2Risk는 보행자 불확실성 정량화(Uncertainty Quantification) 프레임워크다. 가능한 미래 경로와 기한별 횡단 완료확률을 추정하고 실제 보행 기록으로 평가한다.'],
 ['연구 자료 · 위치를 관측하는 오차가 횡단 완료시간과 어떻게 연결될까?','같은 보행에서도 관측 위치가 달라지면 예측하는 완료확률이 달라질 수 있다.','관측 위치는 경로 예측의 입력이다. 같은 입력에서도 미래 이동은 여러 가지이며, 경로마다 출구를 처음 지나는 시각이 다르다.'],
 ['통합 UQ 프레임워크 · 두 예측 방법을 무엇으로 검증할까?','경로 분포와 잔여시간 분포에서 같은 횡단 완료 사건을 예측한다.','경로 분기에서는 같은 보행 기록에 입력 오차를 가해 위치와 완료를 평가한다. 직접 시간 분기에서는 보행 상태로 잔여시간 분포를 별도로 학습한다.'],
 ['관측오차 민감도 · SPD에서 추정한 오차에 경로 예측은 얼마나 민감한가?','합성 관측오차를 보정하자 두 자료에서 미래 위치 오차가 약 81% 줄었다.',({noisy,corrected,ind})=>'주석 불일치 RMSE가 '+PN(100*V2R.evidence.r_proxy.train_fit.RMSE_m,1)+' cm인 SPD 자료로 합성 오차(IID 1×)를 구성했다. 보정 후 ADE는 Noisy 대비 IMPTC에서 '+UQ.reduction(noisy.ade_m,corrected.ade_m)+', inD에서 '+UQ.reduction(ind[1].ade_m,ind[2].ade_m)+' 줄었다.'],
 ['공간 UQ 검증 · 대표 경로가 정확해지면 95% 영역도 신뢰할 수 있을까?','위치 예측 정확도의 개선이 불확실성의 신뢰성까지 보장하지는 않는다.',({noisy,corrected})=>'IMPTC에서 대표 경로의 ADE는 '+UQ.reduction(noisy.ade_m,corrected.ade_m)+' 감소했다. 그러나 4초 뒤 실제 위치가 보정 후 95% 예측영역에 든 비율은 '+UQ.pct(corrected.coverage95)+'였다.'],
 ['경로 기반 시간 UQ · 여러 미래 경로에서 하나의 기한별 완료확률을 어떻게 구할까?','미래 경로가 출구를 처음 지나는 시각으로 횡단 완료확률을 구했다.',({noisy,corrected})=>'IMPTC에서 합성 관측을 보정하자 4초 이내 완료확률의 Brier 점수가 '+PN(noisy.brier,5)+'에서 '+PN(corrected.brier,5)+'로 줄었다.'],
 ['직접 시간 UQ · 출구에 가까운 보행을 학습하면 완료확률은 어떻게 달라질까?','횡단 완료 직전의 학습 데이터를 보완하여 완료확률 예측오차를 평균 71% 줄였다.','앞에서는 관측오차가 미래 경로와 완료확률에 미치는 영향을 평가했다. 여기서는 보행 상태로 잔여시간 분포를 직접 학습해 같은 완료 사건을 예측했다.'],
 ['한국 적용','국내 보행속도로 계산하면 현행 신호 시간이 부족한 곳이 있다.','독일 자료로 방법을 검증하고, 속도는 국내 실측값과 고령인구 비율로 바꿔 계산했다.'],
 ['개선 제안','설계 속도를 횡단보도와 날씨에 맞춰 다르게 정할 수 있다.','현행 고정 속도 운영과 영상 기반 스마트 횡단시스템에 이번 결과를 연결한 제안이다.'],
 ['3D 시연','관측부터 예측, 횡단 완료까지 하나의 화면에서 확인한다.','실제 보행 기록을 재생하며 카메라 오차, 보정, 예측 범위, 완료확률, 실제 결과를 비교한다.'],
 ['결론','횡단 완료확률을 만들고 검증했으며, 한국 신호 시간에 적용할 방법을 제시했다.','남은 과제는 예측 범위의 신뢰도 회복과 국내 자료·현장에서의 검증이다.']
];
const notes=[
 '오늘의 최종 예측 대상은 출구까지 남은 시간의 불확실성입니다. 예를 들어 보행자가 2초 안에 횡단을 마칠 확률과 3초 안에 마칠 확률은 다릅니다. 가능한 경로를 예측하고, 기한별 확률이 실제 결과와 얼마나 맞는지 확인합니다. 먼저 이 확률에 어떤 불확실성이 관여하는지 살펴보겠습니다.',
 '그림 왼쪽에서 위치 기록이 흔들리면 예측기가 보는 과거가 달라집니다. 오른쪽에서는 같은 과거를 주어도 미래 이동이 갈라집니다. 그 차이를 출구 도착시간으로 옮기는 것이 시간 UQ입니다. SPD는 관측오차 대리값, IMPTC는 실제 경로와 통과 기록, inD는 다른 환경에서의 위치 민감도 비교를 제공합니다.',
 '회색 밑줄은 기존 기법입니다. 팀은 SPD 주석 차이의 평균과 공분산을 추정하고 같은 예측 시점에 합성 오차를 적용했습니다. 위쪽은 칼만 보정 전후를 같은 사전학습 DD-MDN으로 비교합니다. 아래쪽은 Entry와 Exit를 정의한 뒤 기록에서 만든 잔여시간을 학습 목표로 삼아 XGBoost AFT를 독립적으로 학습한 경로입니다. 두 분기는 동일한 완료 사건으로 검증하지만, 이어지는 보정 실험은 위쪽 분기에 해당합니다.',
 '23.8 cm는 SPD의 두 위치 주석 간 차이의 RMSE입니다. 이 분포에서 합성 오차를 가한 뒤 같은 예측기와 기록으로 비교했습니다. IMPTC에서는 향후 4초간 ADE가 0.283 m에서 3.925 m로 커졌다가 칼만 보정 후 0.742 m가 됐습니다. inD에서도 4.569 m에서 0.871 m로 줄었습니다. 이 민감도는 두 데이터셋에서 시험한 합성 오차 조건에 해당합니다. 다음은 대표 경로 대신 분포 전체를 검증한 결과입니다.',
 'ADE는 대표 예측까지의 거리, Coverage95는 실제 위치의 포함 빈도, HDR95 Area는 그 영역에 할당한 공간의 크기입니다. 보정 후 영역이 크게 작아졌지만 실제 포함률은 78.51%에 머물렀습니다. 이 비교에서는 남은 격차의 원인을 분리할 수 없습니다. 횡단 완료확률은 위치의 포함 여부와 다른 사건이므로 별도의 평가가 필요합니다.',
 '각 미래 경로에서 기한 전 최초 Exit 통과 여부를 기록합니다. 특정 시각의 위치 영역 하나만으로는 그 전에 출구를 지났는지 알 수 없습니다. f2의 실제 완료시간은 2.063초여서 H2는 미완료이고 H3는 완료입니다. 집계 Brier는 각 확률과 실제 0·1 결과의 제곱 차이를 평가합니다. 같은 사건을 경로 없이 직접 예측하는 방법이 다음 장입니다.',
 'M1은 잔여 거리, 종방향 속도와 가속도로 남은 횡단시간의 분포를 학습합니다. 출구에 닿기 전에 기록이 끝난 경우에는 관측한 시간만큼은 아직 완료되지 않았다는 하한을 사용합니다. Exit 직전 표본을 추가하면서 학습량과 거리 구성이 함께 달라졌습니다. 기존 M1 대비 평균 Brier는 약 71%, H1 Brier는 약 94.3% 줄었습니다. H1은 앞으로 1초 안에 완료할 확률을 평가하는 기한이며 실제 보행시간이 1초 단축됐다는 뜻이 아닙니다. 여기까지 View2Risk는 관측 불확실성이 미래 이동 예측에 미치는 영향을 검증하고, 경로와 잔여시간 분포 두 방식으로 완료 불확실성을 정량화했습니다. 다음 장의 국내 신호시간은 국내 속도 통계와 시나리오로 별도 계산했습니다.',
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
    '<article><h2>집계 평가 · 같은 M1의 Brier 비교</h2>'+pTable(['학습 구성',...horizons.map(h=>'H'+h),'평균'],paired.map((rows,i)=>[i?'Exit-aware':'Original',...rows.map(r=>PN(r.event_weighted_brier,5)),PN(means[i],5)]))+
    '<p class="aft-result"><b>H1은 1초 이내 횡단 완료확률</b>이다. 이 확률의 Brier는 기존 M1 대비 '+UQ.reduction(paired[0][0].event_weighted_brier,paired[1][0].event_weighted_brier)+' 감소했다.</p>'+
    '<p class="caption">매칭 IMPTC Test '+paired[0][0].n_origins+'시점 · '+paired[0][0].n_events+'건. 평균은 H1~H4 사건별 가중 Brier의 산술평균이며 낮을수록 좋다. 기한별 정답 수 '+paired[0].map(r=>r.n_known).join(' / ')+'. 비교 기준은 기존 M1이다. '+aftSource+' · '+UQ.source('results.html','전체 기준선 비교')+'</p></article></div></div>';
}

function figUqArchitecture(){
  const neutral='#37545d',edge='#72838a';
  function node(x,y,w,h,title,lines,color,method){
    const box='<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="3" fill="white" stroke="'+color+'" stroke-width="1.5"/>';
    const label=(text,baseline,fill,size)=>{
      const markup=ink(x+12,y+baseline,text,fill,'start',size);
      return text===method?'<g class="uq-existing-method">'+markup+'</g>':markup;
    };
    return box+label(title,25,color,19)+lines.map((t,i)=>label(t,49+21*i,neutral,16)).join('');
  }
  const arrow=(x,y,u,v)=>'<path d="M'+x+' '+y+' L'+u+' '+v+'" fill="none" stroke="'+edge+'" stroke-width="1.7" marker-end="url(#uq-flow-arrow)"/>';
  let b='<defs><marker id="uq-flow-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="'+edge+'"/></marker></defs>';
  b+=ink(8,22,'경로 기반 예측',SC.future,'start',20);
  b+=node(8,38,188,103,'SPD 학습 주석 쌍',['두 좌표의 차이','→ 편향 b, 공분산 R'],SC.noisy);
  b+=node(221,38,238,103,'기록된 보행에 합성 오차',['칼만 필터','합성 관측에 선택 적용'],SC.clean,'칼만 필터');
  b+=node(487,38,202,103,'사전학습 DD-MDN',['과거 0.9초를 입력','미래 경로 분포를 출력'],SC.future,'사전학습 DD-MDN');
  b+=node(728,30,215,59,'공간 · 시점별 위치',['68%·95% 최고밀도영역'],SC.future);
  b+=node(728,99,215,59,'시간 · 최초 Exit 통과',['기한 안에 통과한 표본 비율'],SC.future);
  b+=node(972,30,223,59,'실제 위치와 대조',['ADE · 포함률 · 영역 면적'],neutral);
  b+=node(972,99,223,59,'실제 완료와 대조',['기한별 결과 0/1 · Brier'],neutral);
  b+=arrow(196,85,217,85)+arrow(459,85,483,85)+arrow(689,84,723,61)+arrow(689,92,723,124)+arrow(943,60,968,60)+arrow(943,127,968,127);
  b+=segment(8,178,1195,178,'#ccd8d9')+ink(8,209,'직접 시간 예측',SC.filtered_mean,'start',20);
  b+=node(8,225,287,76,'보행 상태',['잔여 거리 · 종방향 속도 · 가속도'],SC.clean);
  b+=node(325,225,205,76,'XGBoost AFT',['팀에서 독립 학습한 M1'],SC.filtered_mean,'XGBoost AFT');
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
    case 0:return '<div class="lead-grid"><article><h2>한 번의 횡단에서 묻는 세 가지</h2><ol class="questions"><li>지금까지 관측한 위치는 얼마나 정확한가?</li><li>같은 과거에서 앞으로 어디에 있을 수 있는가?</li><li>주어진 시간 안에 출구를 지날 확률은 얼마인가?</li></ol><p>최종 예측 대상은 지금부터 횡단을 마치기까지 남은 시간의 분포다.</p></article>'+
      fig('한 보행 기록에서 갈라지는 미래',figQuestions(),'개념도 · 파랑은 관측한 과거, 보라는 가능한 미래다. 같은 시간 동안에도 일부 경로만 출구에 닿는다.')+'</div>';
    case 1:return '<div class="pair"><article><h2>무엇이 불확실한가</h2><dl class="uq-terms"><dt>관측 불확실성</dt><dd>과거와 현재의 관측 위치가 기준 위치에서 벗어나는 정도.</dd><dt>공간 예측 불확실성</dt><dd>관측 이력이 주어졌을 때 미래 각 시각의 위치가 퍼지는 정도.</dd><dt>횡단 완료 불확실성</dt><dd>가능한 경로에서 얻은 잔여시간의 분포와 기한별 Exit 통과확률.</dd></dl></article>'+
      fig('관측 위치의 차이와 가능한 미래 경로',figSources(),'개념도 · 왼쪽의 오차는 이미 관측한 시각에 있고, 오른쪽의 퍼짐은 아직 관측하지 않은 미래에 있다.')+'</div>'+
      '<div class="uq-data-row"><div><b>SPD</b><span>두 주석의 차이로 관측오차 대리 모형 추정</span></div><div><b>IMPTC</b><span>실제 궤적·횡단 경계로 미래 위치와 완료 평가</span></div><div><b>inD</b><span>다른 수집 환경에서 궤적 예측의 강건성 보조 평가</span></div></div>';
    case 2:return '<figure class="uq-system">'+figUqArchitecture()+'<figcaption><b>기존 기법(회색 밑줄)</b>　칼만 필터 · 사전학습 DD-MDN · XGBoost AFT<br><b>팀이 구현한 절차</b>　Entry·Exit 경계 정의, 같은 시점의 관측 보정 비교, 경로별 완료확률 계산, 잔여시간 학습 목표 구성과 M1 개선, 실제 기록 대조·대화형 시각화</figcaption></figure>'+
      '<div class="uq-r-method"><h2>R은 어떻게 얻었나?</h2><p>SPD Train '+train.n.toLocaleString('en-US')+'쌍의 위치 주석에서 좌표 차이를 구했다. 차이의 평균은 <b>편향 b</b>, 평균을 뺀 차이의 공분산은 <b>R</b>이다. X/Y 표준편차는 <b>'+PN(Math.sqrt(train.covariance_m2[0][0])*100,1)+' / '+PN(Math.sqrt(train.covariance_m2[1][1])*100,1)+' cm</b>, 주석 불일치 RMSE는 <b>'+PN(train.RMSE_m*100,1)+' cm</b>였다. 이 값은 SPD 주석에서 얻은 관측오차 대리값이다. IMPTC에서 검출기 오차를 직접 측정한 값과 구분한다. '+UQ.source('data/public/demo-evidence.json','SPD 추정값')+'</p></div>';
    case 3:{
      const chart=figGroupedBars({title:'자료별 향후 4초간 평균 위치 예측오차(ADE)',series:rows.map((r,j)=>({label:['Clean','Noisy','Corrected'][j],color:SC[r.mode]})),groups:[rows,ind].map(a=>({label:a[0].dataset,values:a.map(r=>r.ade_m)})),maximum:5,ticks:[0,1,2,3,4,5],axis:'4초 ADE (m) · 작을수록 정확',decimals:3});
      return '<div class="pair">'+fig('같은 시각의 예측과 실제 위치',figDistances(s),'IMPTC f2 · 합성 오차 1× 한 사례. ADE는 향후 0.5~4초의 여덟 시각에서 대표 예측과 실제 위치 간 거리를 평균한다.')+
        fig('향후 4초간 평균 위치 예측오차(ADE)',chart,'Test · IMPTC 120건 중 ADE 유효 215시점, inD 11개 궤적·99시점. 같은 합성 오차에서 IMPTC ADE는 Clean 대비 '+PN(noisy.ade_m/clean.ade_m,1)+'배가 됐다. '+metricSource)+'</div>'+
        '<p class="uq-transition">위치 예측오차는 크게 줄었지만, 확률적 예측영역의 신뢰성도 회복되었는지 확인할 필요가 있다.</p>';
    }
    case 4:return '<div class="pair spatial-layout">'+fig('예측 확률 질량과 실제 위치',figHdr(),'개념도 · HDR95는 모델이 한 시각의 예측 질량 95%를 배정한 최고밀도영역이다. Coverage95는 실제 위치 중 각 예측영역 안에 든 비율이다.')+
      fig('목표 포함률과 영역 크기의 관계',figCoverage(rows),'IMPTC Test · +4초 실제 위치 n=228, 영역 n=237. 주황은 SPD 기반 합성 오차(IID 1×)다. HDR95 Area는 95% 영역의 평균 넓이(m²)이며 가로축은 로그 눈금이다. '+metricSource)+'</div>'+
      '<p class="uq-transition">보정 후 평균 면적은 '+PN(noisy.hdr95_area_m2,2)+' → '+PN(corrected.hdr95_area_m2,2)+' m²로 줄었다. 포함률 미달의 원인은 이 비교로 특정할 수 없다. 횡단 완료확률은 실제 통과 기록으로 따로 검증한다.</p>';
    case 5:return '<div class="pair uq-passage"><article><h2>미래 경로의 결합분포 → 최초 Exit 통과 → 완료확률</h2>'+figCrossing()+'<p>각 경로에서 시간 순서를 따라 출구를 처음 통과하는 시각을 찾는다. 한 시각의 위치 영역만으로는 이전의 통과 여부를 알 수 없다. 기한 H까지 통과한 경로의 비율이 <b>P(T<sub>exit</sub> ≤ H)</b>다.</p><p class="caption">개념도 · 10개 중 6개가 통과하면 60%다. 실제 f2 확률은 저장된 공동 경로 표본의 집계값이다.</p></article>'+
      '<article><h2>한 사례 · IMPTC f2, Clean</h2>'+figCompletionBars(s)+'<p class="caption">실제 완료는 예측 후 <b>'+PN(s.e.GT.exit_s-s.r.origin_s,3)+'초</b>다. 2초 기한의 결과는 0, 3초 기한의 결과는 1이다.</p>'+
      '<h3>집계 · H4 Brier</h3><p>예측확률과 실제 완료 여부(0 또는 1)의 차이를 제곱해 평균한다. 값이 작을수록 확률 오차가 작다.</p><p class="caption">IMPTC IID 1× · 4초 결과가 확인된 218시점. Clean 기준 '+PN(clean.brier,5)+'. Noisy 대비 보정 후 '+UQ.reduction(noisy.brier,corrected.brier)+' 감소. 공간 포함률은 위치를 검증하며, 완료확률의 보정 수준은 예측확률과 실제 완료 빈도로 따로 확인해야 한다. '+metricSource+'</p></article></div>'+
      '<p class="uq-transition">미래 경로를 먼저 예측하지 않고, 횡단 완료시간의 확률분포를 직접 학습할 수도 있지 않을까?</p>';
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
