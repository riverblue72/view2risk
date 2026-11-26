'use strict';
const slides=[
 ['View2Risk · 목표','카메라로 본 보행자가 신호 안에 다 건널 수 있을까?','최종 목표는 보행자 구성과 날씨에 맞춘 상황 적응형 보행 신호다. 이번 학기에는 횡단 완료확률을 예측·검증하고, 국내 보행속도·고령인구·날씨를 반영해 신호 시간을 계산했다.'],
 ['접근','카메라 위치 오차와 보행 움직임을 서로 다른 자료에서 가져와 하나의 가상 횡단보도에 결합했다.','두 가지를 함께 담은 자료가 없어, 카메라 위치 오차는 V2X-SPD에서, 실제 보행 움직임은 IMPTC에서 가져왔다.'],
 ['방법','카메라 위치 오차를 보정한 뒤, 위치와 완료 시간을 확률로 예측한다.','도식의 각 상자가 무엇을 하는지 오른쪽에 순서대로 설명했다.'],
 ['결과 1 · 위치','합성 관측오차를 보정하자 향후 4초간 평균 위치 예측오차(ADE)가 81% 줄었다.','같은 예측 모델에 오차 없음, 카메라 오차, 보정 후 관측을 각각 넣어 비교했다.'],
 ['결과 2 · 신뢰도','보정 후 위치는 정확해졌지만, 예측 범위의 신뢰도는 회복되지 않았다.','모델이 "95% 확률로 이 안에 있다"고 제시한 범위에 실제 위치가 들어간 비율은 보정 후 79%였다. 오차 없음에서는 96%였다.'],
 ['결과 3 · 완료확률','몇 초 안에 다 건널지에 대한 확률 예측도 개선됐다.','DD-MDN의 경로 표본에서 기한별 Exit 통과율을 구하고, 관측 보정 전후의 4초 완료확률 오차를 비교했다.'],
 ['결과 4 · XGBoost AFT','횡단 완료시간의 불확실성을 직접 학습하고, 학습 데이터 구성을 개선했다.','출구에 가까운 학습 시점을 보강하자 1초 완료확률 예측이 가장 크게 개선됐다. 잔여시간 분포는 향후 신호 연장 판단에 활용할 수 있다.'],
 ['한국 적용','국내 보행속도로 계산하면 현행 신호 시간이 부족한 곳이 있다.','독일 자료로 방법을 검증하고, 속도는 국내 실측값과 고령인구 비율로 바꿔 계산했다.'],
 ['개선 제안','설계 속도를 횡단보도와 날씨에 맞춰 다르게 정할 수 있다.','현행 고정 속도 운영과 영상 기반 스마트 횡단시스템에 이번 결과를 연결한 제안이다.'],
 ['3D 시연','관측부터 예측, 횡단 완료까지 하나의 화면에서 확인한다.','실제 보행 기록을 재생하며 카메라 오차, 보정, 예측 범위, 완료확률, 실제 결과를 비교한다.'],
 ['결론','횡단 완료확률을 만들고 검증했으며, 한국 신호 시간에 적용할 방법을 제시했다.','남은 과제는 예측 범위의 신뢰도 회복과 국내 자료·현장에서의 검증이다.']
];
const notes=[
 '횡단보도를 건너다 신호가 깜빡여서 뛰어 본 적 있으시죠. 지금 보행 신호 시간은 모든 사람이 초속 1미터로 걷는다고 가정하고 정해집니다. 하지만 걷는 속도는 제각각이고, 카메라로 보행자를 본다면 카메라가 보는 위치에도 오차가 생깁니다. 저희의 최종 목표는 보행자 구성과 날씨에 맞춘 상황 적응형 보행 신호입니다. 이번 학기에는 그 전제로 보행자가 몇 초 안에 다 건널지를 확률로 예측해 검증하고, 국내 보행속도와 고령인구, 날씨를 반영해 신호 시간을 계산했습니다.',
 '불확실성은 두 가지입니다. 카메라가 위치를 잘못 볼 수 있다는 것, 그리고 같은 과거에서도 사람의 다음 움직임이 달라질 수 있다는 것입니다. 둘을 한 번에 담은 자료가 없어서, 카메라 위치 오차는 같은 사람을 카메라와 LiDAR로 함께 기록한 V2X-SPD에서 추정했고, 보행 움직임은 횡단보도 경계까지 있는 IMPTC에서 가져와 하나의 가상 횡단보도 위에 결합했습니다. 이 카메라 오차는 실제 카메라에서 잰 값이 아니라 두 위치 기록의 차이로 추정한 값입니다.',
 '도식을 위에서부터 보겠습니다. 먼저 SPD에서 같은 보행자에 대한 두 위치 주석의 불일치 RMSE는 23.8 cm입니다. 이를 합성 관측오차의 대리값으로 사용했습니다. 칼만 필터는 직전 위치와 속도로 예상한 위치와 카메라가 본 위치를 섞어 이 흔들림을 걸러냅니다. 보정을 켠 경우와 끈 경우를 비교하려고 비교 실험으로 표시했습니다. 왼쪽 DD-MDN은 공개된 보행 경로 예측 모델로, 최근 0.9초를 보고 4초 뒤까지의 경로와 위치 확률을 냅니다. 오른쪽 XGBoost는 저희가 직접 학습한 모델로, 남은 거리와 종방향 속도·가속도를 이용해 몇 초 뒤 다 건널지를 바로 예측합니다. 마지막으로 두 예측을 같은 기준의 횡단 완료확률로 바꿔 실제 기록과 비교했습니다.',
 '결과입니다. 카메라 오차가 들어가면 향후 4초간 평균 위치 예측오차(ADE)가 0.28미터에서 3.9미터까지 커졌습니다. 칼만 보정을 하자 0.74미터로 81% 줄었고, 다른 장소의 자료인 inD에서도 비슷하게 줄었습니다. 다만 오차가 없을 때만큼 회복되지는 않았습니다.',
 '위치 오차가 줄었다고 해서 예측을 그대로 믿을 수 있는 건 아닙니다. 모델은 95% 확률로 이 범위 안에 있다는 영역도 함께 내는데, 보정 후에는 실제 위치가 그 범위에 79%만 들어갔습니다. 오차가 없을 때는 96%였습니다. 잔여 관측오차가 한 가지 가능한 설명이지만, 이 비교만으로 원인을 확인할 수는 없습니다. 신호 시간에 이 확률을 쓰려면 이 비율을 95% 가까이 끌어올려야 하고, 이것이 남은 과제입니다.',
 '이번엔 몇 초 안에 다 건널지에 대한 예측입니다. 모델은 건넌다, 못 건넌다가 아니라 확률로 답합니다. 예시의 보행자는 실제로 2.06초 뒤에 건넜고, 모델은 3초 안에 건널 확률을 66%로 봤습니다. 이 확률이 실제와 맞는지는 여러 사람을 모아 Brier 점수로 평가했습니다. 예측 확률과 실제 결과의 차이를 제곱해 평균낸 값으로, 0에 가까울수록 정확합니다. 같은 합성 오차 조건에서 입력을 칼만 보정하자 4초 Brier가 74.4% 줄었습니다. 다음 장에서는 경로를 생성하지 않고 남은 시간을 직접 학습한 별도 모형을 봅니다.',
 '위쪽은 f2 보행자 한 명입니다. 거리, 종방향 속도·가속도를 넣으면 남은 시간의 누적분포가 나오고, H초에서 읽은 높이가 그때까지 건널 확률입니다. 실제로는 2.063초에 건넜습니다. 학습 정답은 실제 남은 통과시간이며, 관측이 먼저 끝나면 그때까지의 시간을 우측검열 하한으로 씁니다. 아래는 별도의 집계입니다. 동일한 Train에서 출구 가까이의 시점을 더 채집하자 평균 Brier가 약 71%, H1이 94.3% 감소했습니다. 학습량과 거리 구성이 함께 달라졌고, H3의 차이는 작습니다. 남은 시간을 직접 예측하는 모형은 향후 신호 연장 판단에 활용할 수 있습니다. 다음 장의 국내 계산은 국내 보행속도 통계와 시나리오 가정에 따른 별도 계산입니다.',
 '이제 원래 목표인 신호 시간으로 돌아갑니다. 독일 자료는 방법을 검증하는 데 썼고, 속도는 국내에서 실제로 잰 값으로 바꿨습니다. 독일 보행자가 더 빨라서 그대로 쓰면 신호를 너무 짧게 잡기 때문입니다. 16미터 횡단보도 기준으로 현행은 23초입니다. 고령인구 20%를 반영해 95%가 건너는 기준으로 보면 27초가 필요하고, 비가 오면 85% 기준으로도 29초가 필요합니다.',
 '그래서 세 가지를 제안합니다. 첫째, 횡단보도 주변의 연령 구성에 따라 설계 속도를 정합니다. 둘째, 비가 오면 점멸 시간을 늘립니다. 셋째, 영상으로 보행자를 감지해 신호를 연장하는 시스템에는 카메라 오차 보정이 함께 필요합니다. 저희 실험에서 카메라 오차가 그대로 들어가면 완료확률 예측 오차가 열 배 가까이 커졌기 때문입니다. 이 제안들은 계산 예시에 근거한 것으로 현장 검증 전입니다.',
 '실제 화면으로 보여드리겠습니다. 전체 횡단 재생을 누르면 같은 보행자를 오차 없음, 카메라 오차, 보정 후로 비교할 수 있습니다. 저장된 미래 예측 보기에서 예측 경로와 범위를 보고, 횡단 완료 단계에서 완료확률을 확인한 뒤 실제 정답을 공개합니다.',
 '정리하겠습니다. 카메라 오차를 보정하자 향후 4초간 평균 위치 예측오차(ADE)가 3.9미터에서 0.74미터로, 완료확률 예측 오차는 74% 줄었습니다. 하지만 95% 범위의 실제 적중률은 79%로, 신뢰도 회복은 남은 과제입니다. 별도로 국내 보행속도와 시나리오 가정으로 계산하면 16미터 횡단보도에서 95%가 건너려면 현행 23초보다 긴 27초가 필요합니다. 국내 자료와 실제 현장에서의 검증이 다음 단계입니다. 감사합니다.'
];
const fig=(heading,graphic,caption)=>'<figure class="sci-figure"><h2>'+heading+'</h2>'+graphic+'<figcaption>'+caption+'</figcaption></figure>';
const modeLabel=r=>'<b style="color:'+SC[r.mode]+'">'+UQ.names[r.mode]+'</b>';
const metricSource=UQ.source('r_robustness/r_robustness_metrics.csv','원본 집계표');
const aftSource=UQ.source('exit_aware/exit_aware_matched_metrics.csv','M1 평가표');
const kpi=(label,value,sub)=>'<div class="kpi"><span>'+label+'</span><strong>'+value+'</strong><em>'+sub+'</em></div>';
const ladder=()=>'<ol class="scope-ladder" aria-label="연구 범위"><li><b>최종 목표</b><span>보행자 구성과 날씨에 맞춘 상황 적응형 보행 신호</span><em>다음 단계</em></li><li class="now"><b>이번 학기</b><span>완료확률 예측·검증 → 연령·날씨 반영 신호 시간 계산</span><em>오늘 발표</em></li><li><b>출발점</b><span>신호 시간 = 진입시간 + 거리 ÷ 1.0 m/s</span><em>모두 같은 속도로 가정</em></li></ol>';
const step=(n,title,body)=>'<div class="m-step"><b>'+n+'</b><div><h3>'+title+'</h3><p>'+body+'</p></div></div>';

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
    '<p class="aft-result"><b>평균 약 '+Math.round(100*(1-means[1]/means[0]))+'% 감소</b> · H1에서 '+UQ.reduction(paired[0][0].event_weighted_brier,paired[1][0].event_weighted_brier)+' 감소</p>'+
    '<p class="caption">매칭 IMPTC Test '+paired[0][0].n_origins+'시점 · '+paired[0][0].n_events+'건. 사건별 가중 Brier는 낮을수록 좋다. H1~H4 정답 수 '+paired[0].map(r=>r.n_known).join(' / ')+'. 비교 기준은 기존 M1이다. '+aftSource+'</p></article></div></div>';
}

function content(i,s,ind){
  const rows=uqRobustRows(),[clean,noisy,corrected]=rows,train=V2R.evidence.r_proxy.train_fit;
  switch(i){
    case 0:return '<div class="lead-grid motivation"><article><h2>이번 발표의 범위</h2>'+ladder()+'</article>'+fig('한 사람에게 가능한 여러 미래',figQuestions(),'개념도 · 같은 과거에서도 여러 미래가 가능하고, 그중 일부만 기한 안에 반대편(Exit)에 닿는다.')+'</div>';
    case 1:return '<div class="pair">'+fig('두 가지 불확실성',figSources(),'왼쪽: 카메라가 같은 위치를 다르게 보는 카메라 위치 오차. 오른쪽: 같은 과거에서 갈라지는 미래 움직임.')+
      '<article><h2>자료를 나눠 쓴 이유</h2><dl class="data-roles"><dt>V2X-SPD</dt><dd>같은 보행자를 카메라와 LiDAR로 함께 기록 → 두 기록의 차이로 카메라 위치 오차를 추정</dd><dt>IMPTC</dt><dd>실제 보행 궤적과 횡단보도 경계 → 예측과 완료 여부 평가</dd><dt>결합</dt><dd>IMPTC 보행 기록 위에 SPD에서 추정한 카메라 오차를 입혀 하나의 가상 횡단보도에서 실험</dd></dl><p class="caption">이 카메라 오차는 실제 카메라에서 잰 값이 아니라 두 위치 기록의 차이로 추정한 값이다.</p></article></div>'+
      '<ol class="semester-steps" aria-label="한 학기 과정">'+['주제 선정 · 변수 축소','두 불확실성을 함께 담은 자료 부족','자료를 나눠 결합','예측·평가','한국 적용'].map(t=>'<li>'+t+'</li>').join('')+'</ol>';
    case 2:return '<div class="method-layout">'+fig('같은 보행 기록, 두 가지 예측',figFramework(),'왼쪽은 경로를 예측한 뒤 완료확률을 계산하고, 오른쪽은 남은 시간을 바로 예측한다. 두 방법은 병렬로 쓰인다.')+
      '<div class="m-steps">'+step(1,'칼만 보정 · 흔들리는 위치 다듬기','SPD 위치 주석 불일치의 RMSE는 '+PN(100*train.RMSE_m,1)+' cm다. 이 차이를 바탕으로 합성 오차를 더하고, 칼만 필터로 직전 상태와 현재 관측을 결합해 위치를 보정했다.')+
      step(2,'DD-MDN · 경로 기반 예측 (사전학습)','사전학습 모델에 과거 0.9초의 위치를 입력해 향후 4초의 경로 후보와 시각별 위치 분포를 얻는다.')+
      step(3,'XGBoost AFT · 완료시간 직접 예측 (별도 학습)','팀에서 별도로 학습한 M1은 남은 거리, 종방향 속도와 가속도로 Exit까지 남은 시간의 분포를 직접 추정한다.')+
      step(4,'횡단 완료확률 · 같은 기준으로 비교','DD-MDN은 예측 경로 중 기한 안에 반대편을 지난 비율로, XGBoost는 예측 시간이 기한 이하일 확률로 계산해 실제 기록과 비교한다.')+'</div></div>';
    case 3:{
      const series=rows.map(r=>({label:UQ.names[r.mode],color:SC[r.mode]}));
      const chart=figGroupedBars({title:'향후 4초간 평균 위치 예측오차(ADE)',series,groups:[rows,ind].map(a=>({label:a[0].dataset,values:a.map(r=>r.ade_m)})),maximum:5,ticks:[0,1,2,3,4,5],axis:'m · 낮을수록 정확',decimals:2});
      return '<div class="pair"><div class="kpi-col">'+kpi('오차 없음 · 향후 4초간 평균 위치 예측오차(ADE)',PN(clean.ade_m,2)+' m','기준')+kpi('카메라 오차 · 향후 4초간 평균 위치 예측오차(ADE)',PN(noisy.ade_m,2)+' m','오차 없음보다 약 '+PN(noisy.ade_m/clean.ade_m,0)+'배 커짐')+kpi('보정 후 · 향후 4초간 평균 위치 예측오차(ADE)',PN(corrected.ade_m,2)+' m','카메라 오차 대비 '+UQ.reduction(noisy.ade_m,corrected.ade_m)+' 감소')+'</div>'+
        fig('두 데이터셋에서 같은 경향',chart,'IMPTC 215개, inD 99개 예측 시점 · SPD 기반 IID 1×. ADE는 +0.5~4초의 여덟 시각에서 대표 예측과 실제 위치 사이 거리를 평균한 값이다. '+metricSource)+'</div>';
    }
    case 4:return '<div class="pair spatial-layout"><article><div class="kpi-col">'+kpi('오차 없음 · 95% 범위의 실제 적중률',UQ.pct(clean.coverage95),'목표 95%에 맞음')+kpi('보정 후 · 95% 범위의 실제 적중률',UQ.pct(corrected.coverage95),'목표 95%에 미달')+'</div>'+
      '<dl class="data-roles"><dt>해석</dt><dd>보정 후에도 실제 포함률은 목표에 미달했다. 남은 관측오차가 영향을 주었을 수 있지만 그 원인은 별도로 검증하지 않았다.</dd><dt>의미</dt><dd>신호 시간 판단에 확률을 쓰려면 이 비율이 95%에 가까워야 한다. 남은 과제다.</dd></dl></article>'+
      fig('적중률과 범위 넓이',figCoverage(rows),'IMPTC 4초 뒤 위치. 점선이 목표 95%. 가로축은 95% 범위의 넓이. '+metricSource)+'</div>';
    case 5:return '<div class="pair completion-slide"><article><h2>예: 한 보행자에 대해 모델이 낸 확률</h2>'+figCompletionBars(s)+'<p class="caption">모델은 건넌다·못 건넌다가 아니라 기한별 확률로 답한다. 이 보행자는 실제로 '+PN(s.e.GT.exit_s-s.r.origin_s,2)+'초 뒤 반대편을 지났다.</p></article>'+
      '<article><h2>전체 평가 · 확률이 실제와 얼마나 맞았나</h2><p class="formula">Brier 점수 = (모델이 낸 확률 − 실제 결과)²의 평균 · 실제 결과는 건넜으면 1, 못 건넜으면 0 · 0에 가까울수록 정확</p><div class="kpi-col">'+
      kpi('DD-MDN · 4초 이내 완료확률의 Brier',PN(noisy.brier,5)+' → '+PN(corrected.brier,5),'합성 오차 보정 전후 '+UQ.reduction(noisy.brier,corrected.brier)+' 감소 · 오차 없음 '+PN(clean.brier,5))+'</div><p class="caption">IMPTC Test · SPD 기반 IID 1× · 120건, 4초 완료 여부 확인 218시점. '+metricSource+'</p></article></div>';
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
