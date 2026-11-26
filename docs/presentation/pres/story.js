'use strict';
const slides=[
 ['View2Risk · 연구 동기','보행자 예측에는 미래 위치뿐 아니라 불확실성도 고려해야 한다.','최종 목표는 보행자에 맞춘 보행 신호 시간이며, 이번 학기에는 그 전제인 횡단 완료확률을 만들고 신뢰도를 검증했다.'],
 ['연구 설계','관측 불확실성과 미래 이동 불확실성을 구분하여 분석한다.','SPD에서 관측오차를 추정하고, IMPTC에서 미래 위치와 횡단 완료를 평가했다. inD는 위치 평가를 보완한다.'],
 ['관측오차 모형','보행자 위치 주석의 차이로부터 관측오차 분포를 추정했다.','같은 사람에 대한 두 위치 주석의 차이를 이용해, 기록된 보행에 어느 정도의 측정 오차를 더할지 정했다.'],
 ['공간·시간 예측 구조','확률적 미래 경로와 직접 시간 예측을 통해 공간·시간 UQ를 구성했다.','경로 기반 방법은 어디로, 언제 건너는지를 함께 추정한다. 직접 시간 모형은 출구까지 얼마나 남았는지에 집중한다.'],
 ['실험 결과 · 위치 오차','관측오차 보정으로 미래 위치 예측오차를 약 81% 감소시켰다.',({noisy,corrected,ind})=>'SPD 기반 독립 합성 오차(IID 1×)에서 Noisy 대비 4초 ADE 감소율은 IMPTC '+UQ.reduction(noisy.ade_m,corrected.ade_m)+', inD '+UQ.reduction(ind[1].ade_m,ind[2].ade_m)+'였다.'],
 ['실험 결과 · 예측영역','위치 예측 정확도의 회복이 불확실성의 신뢰성까지 보장하지는 않았다.',({noisy,corrected})=>'칼만 보정으로 95% 영역의 평균 면적은 '+PN(noisy.hdr95_area_m2,2)+' m²에서 '+PN(corrected.hdr95_area_m2,2)+' m²로 줄었지만, 실제 위치 포함률은 '+UQ.pct(corrected.coverage95)+'에 머물렀다.'],
 ['실험 결과 · 완료확률','미래 이동분포를 횡단 완료확률로 변환하고 실제 기록으로 평가했다.',({noisy,corrected})=>'IMPTC에서 4초 이내 완료확률의 Brier Score는 관측 보정 후 Noisy 대비 '+UQ.reduction(noisy.brier,corrected.brier)+' 감소했다.'],
 ['별도 실험 · XGBoost AFT','횡단 완료 직전의 학습 데이터를 보완해 시간 예측 성능을 개선했다.','경로 없이 잔여시간을 직접 예측하는 M1에서, Exit 부근의 학습 시점을 보강하자 특히 1초 완료확률의 오차가 줄었다.'],
 ['원래 목표와의 연결','고정 보행속도 대신 실제 분포로 보행 신호 시간을 정할 수 있다.','현행 산정식의 1.0 m/s를 관측 기반 속도·완료시간 분포로 바꾸고, 날씨와 군집은 시나리오와 입력 변수로 다룬다.'],
 ['통합 3D 시연','관측부터 미래 예측과 횡단 완료까지 하나의 시스템으로 구현했다.','f2의 Entry → Exit 위치 추적을 재생한 뒤, 저장된 예측 시점에서 경로 분포와 완료확률을 실제 결과와 비교한다.'],
 ['결론','보행자의 공간·시간 불확실성을 정량화하고 검증하는 시스템을 구축했다.','위치와 완료확률의 오차는 줄었다. 실제 위치를 충분히 포함하는 예측영역을 만드는 일은 남아 있다.']
];
const notes=[
 '횡단보도를 건너다 신호가 깜빡여서 뛰어 본 적 있으시죠. 지금 보행 신호 시간은 모든 사람이 초속 1미터로 걷는다고 가정하고 정해집니다. 하지만 실제로는 걷는 속도가 제각각이고, 카메라로 보행자를 본다면 그 위치에도 오차가 생깁니다. 저희의 최종 목표는 보행자에 맞춘 신호 시간입니다. 그런데 신호를 바꾸려면 먼저 이 사람이 몇 초 안에 다 건널지를 믿을 수 있게 예측해야 합니다. 그래서 이번 학기에는 횡단 완료확률을 만들고 얼마나 믿을 수 있는지 검증하는 것에 집중했습니다. 마지막에는 이 확률을 신호 시간으로 어떻게 연결할 수 있는지도 보여드리겠습니다.',
 '처음에는 한 데이터셋에서 카메라 오차와 보행 움직임을 모두 얻으려 했지만, 두 가지를 동시에 제공하는 자료가 없었습니다. 그래서 카메라 위치 오차는 같은 보행자를 카메라와 LiDAR로 함께 기록한 V2X-SPD에서, 실제 보행 움직임은 횡단 경계까지 있는 IMPTC에서 가져왔습니다. 그리고 IMPTC의 실제 보행 기록 위에 SPD에서 추정한 오차를 입혀, 하나의 가상 횡단보도 공간에서 두 불확실성을 함께 다룰 수 있게 만들었습니다. inD는 보조 위치 평가에만 씁니다. 첫 단계인 R의 추정부터 보겠습니다.',
 'SPD 학습 주석 쌍의 좌표 차이에서 편향과 공분산 R을 구했습니다. f2 예시에서는 보행과 실제 미래를 고정하고 입력만 바꿉니다. 타원은 합성 관측오차의 95% 범위입니다. 다음 장의 미래 위치 영역과는 대상 시점도 의미도 다릅니다.',
 '왼쪽에서 기준 입력은 DD-MDN에 바로 들어갑니다. 합성 관측에는 선택적으로 칼만 보정을 적용합니다. DD-MDN은 사전학습 모형이고, 직접 시간 모형은 관측 특징과 잔여시간 정답으로 별도 학습했습니다. 먼저 입력 보정이 대표 경로의 오차를 얼마나 줄였는지 봅니다.',
 '각 화살표는 같은 시각의 예측과 실제 위치 사이 거리입니다. 두 데이터셋의 막대는 같은 미터 눈금을 씁니다. 비교 기준은 각 데이터셋의 Noisy입니다. 이 결과의 적용 범위는 조사한 합성 조건입니다. 다음에는 대표 경로와 별개로 예측 분포의 신뢰성을 봅니다.',
 '산점도에서 오른쪽은 넓은 영역, 점선은 목표 포함률입니다. Noisy는 매우 넓어도 실제 위치를 자주 놓칩니다. Corrected는 면적을 크게 줄였지만 여전히 목표 아래입니다. 위치 영역이 담는 확률과 출구 통과 사건의 확률을 구별해 다음 장으로 넘어갑니다.',
 '먼저 같은 기한까지 Exit에 닿은 경로 표본의 비율을 읽습니다. f2의 실제 통과는 예측 후 2.063초여서 2초에는 미완료, 3초에는 완료입니다. 오른쪽 Brier는 여러 시점의 확률 오차를 모읍니다. 이번에는 경로를 생성하지 않고 시간을 직접 학습한 결과를 보겠습니다.',
 'M1은 거리, 종방향 속도와 가속도로 남은 시간의 분포를 학습합니다. 완료 자료는 통과 구간, 우측 검열 자료는 관측 가능한 하한을 제공합니다. 학습량과 거리 구성이 함께 달라졌으므로 각각의 효과를 분리할 수 없습니다. 가장 큰 차이는 H1이고 H3의 차이는 작습니다. 다음은 이 결과를 개별 기록에서 읽는 시연입니다.',
 '저희 프로젝트의 원래 목표는 보행 신호 시간이었습니다. 현재 신호 시간은 진입시간에 횡단거리를 초속 1미터로 나눈 값을 더해 정합니다. 저희는 이 고정 속도 대신 실제 기록에서 얻은 속도와 완료시간 분포를 넣을 수 있습니다. 16미터 횡단보도를 예로 들면, 맑은 날에는 현행 기준보다 짧은 시간으로도 대부분이 건너지만, 비로 속도가 25% 줄면 현행 기준보다 긴 시간이 필요합니다. 또 카메라 오차가 속도를 부풀리면 신호 시간을 너무 짧게 줄 수 있어, 앞에서 보인 관측오차 보정이 필요합니다. 주변 인원 정보도 입력에 넣어 보았지만 효과는 확인하지 못했습니다. 이 표의 수치는 계산 방법을 보여주는 예시입니다. 다음은 실제 기록 재생 시연입니다.',
 '전체 횡단 재생을 눌러 동일 보행의 세 관측을 비교합니다. Exit에서 전 구간 평균 관측오차를 읽습니다. 저장된 미래 예측 보기에서 미래 운동과 비교 시점으로를 선택해 경로와 HDR을 봅니다. 횡단 완료에서 같은 기한의 확률을 확인한 후 실제 정답을 공개합니다. 마지막 장은 이 한 사례와 별개인 집계 결과입니다.',
 '위 세 행은 합성 오차 입력 보정, 마지막 행은 직접 시간 모형의 학습 자료 개선입니다. 비교 기준과 평가 가능한 시점 수가 다릅니다. 관측부터 실제 기록 대조까지 연결한 것이 연구 기여입니다. 새로운 자료에서의 검증과 공간 포함률 회복, 그리고 처음에 보여드린 최종 목표인 보행 신호 시간의 실제 검증이 다음 과제입니다.'
];
const fig=(heading,graphic,caption)=>'<figure class="sci-figure"><h2>'+heading+'</h2>'+graphic+'<figcaption>'+caption+'</figcaption></figure>';
const modeLabel=r=>'<b style="color:'+SC[r.mode]+'">'+UQ.names[r.mode]+'</b>';
const metricSource=UQ.source('r_robustness/r_robustness_metrics.csv','원본 집계표');
const aftSource=UQ.source('exit_aware/exit_aware_matched_metrics.csv','M1 평가표');

function content(i,s,ind){
  const rows=uqRobustRows(),[clean,noisy,corrected]=rows,train=V2R.evidence.r_proxy.train_fit;
  const models=['M1__calibrated','EA_M1__calibrated'];
  const m1=models.map(model=>UQ.evidence.key_table.find(row=>row.model===model));
  switch(i){
    case 0:return '<div class="lead-grid motivation"><article><h2>횡단을 설명하는 세 가지 질문</h2><ol class="questions"><li>현재 위치를 얼마나 정확히 관측했는가?</li><li>다음 몇 초 동안 어디로 움직일 수 있는가?</li><li>언제 건너편 출구에 도달하는가?</li></ol><ol class="scope-ladder" aria-label="연구 범위"><li><b>최종 목표</b><span>보행자에 맞춘 보행 신호 시간</span><em>다음 단계</em></li><li class="now"><b>이번 학기</b><span>횡단 완료확률을 믿을 수 있게 만들기</span><em>오늘 발표</em></li><li><b>출발점</b><span>신호 시간 = 진입시간 + 거리 ÷ 1.0 m/s</span><em>모두 같은 속도로 가정</em></li></ol></article>'+fig('한 사람에게 가능한 여러 미래',figQuestions(),'개념도 · 파랑은 관측한 과거, 보라는 가능한 미래다. 같은 기한에도 일부 경로만 Exit를 지난다.')+'</div>';
    case 1:return '<div class="pair">'+fig('입력 위치의 흔들림과 미래 경로의 갈라짐',figSources(),'개념도 · 왼쪽은 한 시각의 관측 차이, 오른쪽은 같은 과거에서 가능한 미래다.')+'<dl class="data-roles"><dt>SPD</dt><dd>같은 보행자의 카메라·가상 LiDAR 주석 차이로 관측오차를 추정</dd><dt>IMPTC</dt><dd>보행 기록과 횡단 경계로 미래 위치 및 실제 Exit 통과를 평가</dd><dt>inD</dt><dd>다른 교통 장면의 보행 기록으로 궤적 예측의 강건성을 보조 평가</dd></dl></div><ol class="semester-steps" aria-label="한 학기 과정">'+['주제 선정 · 변수 축소','두 불확실성을 함께 담은 자료 부족','R은 V2X-SPD, 보행 기록은 IMPTC','한 가상 횡단보도에서 결합','실제 기록으로 평가'].map(t=>'<li>'+t+'</li>').join('')+'</ol><ol class="study-roadmap" aria-label="연구 순서">'+['관측오차 모형화','확률 경로 예측','관측 보정 비교','공간 UQ 평가','완료시간 UQ','3D 통합 시연'].map(t=>'<li>'+t+'</li>').join('')+'</ol>';
    case 2:return '<div class="lead-grid obs-layout">'+fig('같은 보행의 세 관측',figObservation(s),'IMPTC f2 한 사례 · IID 1× · 0.1초 간격의 과거 10점. 타원은 마지막 합성 관측을 중심으로 한 95% 측정오차 범위다. '+UQ.source('data/public/r/o0008.json','저장 좌표'))+
      '<article><h2>SPD 학습 주석 '+train.n.toLocaleString('en-US')+'쌍</h2>'+pTable(['주석 위치 차이','크기'],[['X축 표준편차',PN(100*Math.sqrt(train.covariance_m2[0][0]),1)+' cm'],['Y축 표준편차',PN(100*Math.sqrt(train.covariance_m2[1][1]),1)+' cm'],['위치 불일치 RMSE',PN(100*train.RMSE_m,1)+' cm']])+
      '<p><b>R</b>은 두 주석의 좌표 차이에서 얻은 공분산이다. IMPTC에는 이 분포를 합성 오차로 적용했다.</p><p class="caption">RMSE는 두 위치 간 거리를 제곱하여 평균한 뒤 제곱근을 취한 값이다. IMPTC 검출기의 실측오차는 별도 검증이 필요하다. '+UQ.source('data/public/demo-evidence.json','SPD 추정값')+'</p></article></div>';
    case 3:return '<div class="pair framework-layout">'+fig('동일한 보행 기록, 두 가지 예측 방법',figFramework(),'기존 기법은 Kalman 필터, 사전학습 DD-MDN, AFT 알고리즘이다. View2Risk는 관측오차 실험, AFT 학습, 횡단 경계·완료확률 계산, 실제 기록 평가와 시각화를 구현했다.')+
      fig('DD-MDN의 입력과 출력',figForecast(s),'IMPTC f2 · Clean 한 사례. 과거 0.9초의 10점으로 +0.5~4초의 8개 시각을 예측한다. 영역은 +4초 위치 분포다. 이 예측으로 물리적 과정잡음 공분산 Q를 별도 식별하지 않았다.')+'</div>';
    case 4:{
      const series=rows.map(r=>({label:UQ.names[r.mode],color:SC[r.mode]}));
      const chart=figGroupedBars({title:'데이터셋별 4초 ADE',series,groups:[rows,ind].map(a=>({label:a[0].dataset,values:a.map(r=>r.ade_m)})),maximum:5,ticks:[0,1,2,3,4,5],axis:'4초 ADE (m)  ·  낮을수록 정확',decimals:3});
      return '<div class="pair">'+fig('예측 위치와 실제 위치의 거리',figDistances(s),'IMPTC f2 · IID 1× Noisy 한 사례. 화살표는 같은 시각의 거리 오차다. ADE = (d₁ + … + d₈) / 8, FDE = d₈. 둘 다 m 단위이며 작을수록 정확하다.')+
        fig('같은 합성 오차에서의 데이터셋별 비교',chart,'SPD 기반 IID 1× · Test · 0.5~4초. IMPTC 120건·237시점 중 ADE 유효 215개, inD 11개 궤적·99시점 모두 유효. '+metricSource)+'</div><p class="study-footnote">IMPTC의 다른 오차 강도, 시간 상관 오차, 관측 누락에서도 보정 후 ADE가 감소했다. '+UQ.source('r_robustness/FINAL_R_ROBUSTNESS_REPORT.md','전체 오차 조건 비교')+'</p>';
    }
    case 5:return '<div class="pair spatial-layout">'+fig('한 시각의 예측 분포와 실제 위치',figHdr(),'개념도 · HDR68과 HDR95는 각각 예측 질량의 68%, 95%를 담는 최고밀도영역이다. 분홍 점은 실제 위치가 영역 안이나 밖에 있는 두 예다.')+
      fig('포함률과 면적을 함께 본 4초 위치 예측',figCoverage(rows),'IMPTC Test · IID 1× · 120건. Coverage95는 실제 위치가 95% 영역에 든 비율(n=228), HDR95 Area는 평균 영역 면적(n=237)이다. 점선 95%에 가까운지, 그때 영역이 얼마나 넓은지를 함께 읽는다. '+metricSource)+'</div>';
    case 6:return '<div class="pair completion-slide"><article><h2>경로가 기한 안에 Exit를 지날 확률</h2>'+figCrossing()+'<p class="caption">개념도 · 공동 경로 표본 중 H초 안에 Exit를 지난 비율이 P(T<sub>exit</sub> ≤ H)다. 예시에서는 6/10 = 60%다.</p>'+
      figCompletionBars(s)+'<p class="caption">IMPTC f2 한 사례 · Clean · 예측 시점 +8초. 실제 잔여시간 '+PN(s.e.GT.exit_s-s.r.origin_s,3)+'초. 막대는 H=1~4초의 저장된 joint 표본 통과율이다. '+UQ.source('data/public/r/o0008.json','f2 예측')+'</p></article>'+
      '<article><h2>집계 평가 · 4초 완료확률의 오차</h2>'+figBrier()+'<p class="formula">Brier = 평균[(예측확률 − 실제 완료 여부)²]</p>'+pTable(['관측 조건','H4 Brier ↓'],rows.map(r=>[modeLabel(r),PN(r.brier,5)]))+'<p class="caption">IMPTC Test · IID 1× · 237시점 중 H4 완료 여부를 확인한 218개. Brier는 확률 예측의 제곱오차(무단위)다. 작을수록 좋으며 분류 정확도나 보정 수준만을 뜻하지 않는다. '+metricSource+'</p></article></div>';
    case 7:{
      const groups=UQ.horizons.map(h=>({label:'H'+h,values:models.map(model=>UQ.evidence.audit.matched.find(r=>r.cohort==='dd_matched'&&r.split==='test'&&r.horizon_s===h&&r.model===model).event_weighted_brier)}));
      const chart=figGroupedBars({title:'M1 학습 구성별 기한별 Brier',groups,series:[{label:'Original M1',color:'#526873'},{label:'Exit-aware M1',color:'#245d59'}],maximum:.12,ticks:[0,.03,.06,.09,.12],axis:'사건별 가중 Brier (무단위)  ·  낮을수록 정확',decimals:5});
      return '<p class="aft-flow">Exit까지 거리 · 종방향 속도 · 가속도 <span>→</span> XGBoost AFT <span>→</span> 잔여시간 분포 <span>→</span> 기한별 완료확률</p><div class="pair">'+
        fig('학습 시점은 Exit에서 얼마나 떨어져 있었나',figTraining(),'IMPTC Train · 목표값은 실제 남은 통과시간의 구간 또는 우측검열 하한이다. 1 m 이내 시점이 0개에서 393개로 늘었고, 학습량과 거리 구성이 함께 달라졌다.')+
        fig('같은 M1에서 바뀐 기한별 확률 오차',chart,'IMPTC 매칭 Test · 120건·236시점. H1~H4 유효 수 236 / 224 / 222 / 217. 네 기한 평균 Brier는 기존 '+PN(m1[0].mean_brier,5)+'에서 '+PN(m1[1].mean_brier,5)+'로 약 71% 감소했다. '+aftSource)+'</div>';
    }
    case 8:return '<div class="pair signal-slide"><article><h2>보행 신호 시간 산정식</h2><p class="formula">신호 시간 = 진입시간 + 횡단거리 ÷ 설계 보행속도</p><p>현행 일반 기준은 설계 보행속도 1.0 m/s다. 이 값 대신 관측 기반 속도 분포의 하위 백분위나, 완료확률이 95%에 이르는 시간을 쓸 수 있다.</p>'+
      pTable(['조건 · 16 m 예시','설계 속도','신호 시간'],[['현행 기준','1.0 m/s','7 + 16.0 = 23.0초'],['IMPTC 하위 10% 속도 · 맑음','1.22 m/s','7 + 13.1 = 20.1초'],['강한 비 시나리오 (−25%)','0.92 m/s','7 + 17.4 = 24.4초']])+
      '<p class="caption">계산 방법을 보여주는 예시다. 1.22 m/s는 IMPTC Test 거리 구간별 종방향 속도 하위 10%(1.22~1.26 m/s)에서 취했다. IMPTC는 독일 자료라 국내 보행자에 그대로 적용할 수 없고, 실제 횡단보도에서 검증하지 않았다.</p></article>'+
      '<article><h2>보조 변수의 반영</h2><dl class="data-roles"><dt>카메라 오차</dt><dd>속도가 부풀려지면 신호 시간을 짧게 줄 위험 → 관측오차 보정이 필요</dd><dt>군집</dt><dd>3 m 이내 주변 인원을 XGBoost 입력(M2)에 추가했으나 성능 향상은 확인하지 못함</dd><dt>날씨</dt><dd>자료에 강우 라벨이 없어 학습하지 않음 → 문헌의 강우 시 속도 감소(약 25%)를 시나리오로 적용</dd></dl><p class="caption">강우 감소율: Deng 외(2017), J. Eastern Asia Society for Transportation Studies 12, 통제 실험 자유흐름 속도 73.6 → 55.5 m/min(0.1 → 15 mm/h).</p></article></div>';
    case 9:return '<div id="slideReplay"></div>';
    case 10:return '<div class="final-results"><h2>두 실험의 보정 전후</h2>'+pTable(['비교 조건','평가 지표','이전','이후'],[
      ['Noisy → Kalman','IMPTC ADE ↓',PN(noisy.ade_m)+' m',PN(corrected.ade_m)+' m'],
      ['Noisy → Kalman','IMPTC Coverage95 · 목표 95%',UQ.pct(noisy.coverage95),UQ.pct(corrected.coverage95)],
      ['Noisy → Kalman','IMPTC H4 Brier ↓',PN(noisy.brier,5),PN(corrected.brier,5)],
      ['Original → Exit-aware','XGBoost M1 평균 Brier ↓',PN(m1[0].mean_brier,5),PN(m1[1].mean_brier,5)]])+
      '<p class="caption">IMPTC Test · 위 세 행은 SPD IID 1×, 4초 평가(유효 n=215 / 228 / 218). 마지막 행은 같은 120건·236시점에서 사건별 가중 H1~H4 Brier를 평균했다. '+metricSource+' · '+aftSource+'</p></div>'+
      '<div class="final-text"><section><h2>연구 기여</h2><ul><li>위치 주석 차이에 기반한 관측오차 모형</li><li>미래 위치 분포와 횡단 완료확률의 정량화</li><li>직접 완료시간 모형 학습과 출구 부근 자료 보강</li><li>3D 재생과 실제 기록 대조를 통합한 검증 시스템</li></ul></section>'+
      '<section><h2>해석 범위</h2><ul><li>합성 관측오차와 사전학습 궤적 예측기에 의존</li><li>공간 포함률 회복은 불완전하며 단순 기준선 대비 일관된 우위도 없음</li><li>과거 Test 재사용, 독립 검증 및 정지·재출발 사례 제한</li><li>오프라인 기록 평가, 검증된 예측 기한은 최대 4초</li></ul></section></div><a class="appendix-link" href="results.html">전체 기준선·보정·행동 분석 부록 →</a>';
  }
}
(async()=>{
  PS('pHeader').innerHTML=pNav('presentation');
  const [s,robust]=await Promise.all([UQ.load(),V2R.json('r_robustness/r_robustness_summary.json')]);
  const ind=uqRobustRows('inD',robust.metrics);
  const [,noisy,corrected]=uqRobustRows();
  let index=0,release=null;
  function show(){
    const matched=/^#scene-([1-9]|1[01])$/.exec(location.hash);
    index=matched?Number(matched[1])-1:0;
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
