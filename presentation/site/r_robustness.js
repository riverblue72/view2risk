'use strict';
let R_INDEX=[],R_SUMMARY=null,R_CURRENT=null,R_REQUEST=0,R_ACTIVE_KEY='',R_LAST_RENDER='',R_CACHE=new Map();
let R_LINES=[];
function rClearLines(){for(const m of R_LINES)m.dispose();R_LINES=[];}
function rWorldLine(points,hex,y=.13){let run=[];const emit=()=>{if(run.length>=2){const mesh=BABYLON.MeshBuilder.CreateLines('R_observation_comparison',{points:run.map(p=>new BABYLON.Vector3(p[0],y,p[1]))},sc);mesh.color=BABYLON.Color3.FromHexString(hex);R_LINES.push(mesh);}run=[];};for(const p of points){if(p&&p.every(Number.isFinite))run.push(p);else emit();}emit();}
const rnum=(v,n=3)=>v===null||v===undefined||!Number.isFinite(Number(v))?'NA':Number(v).toFixed(n);
const resc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rkey=(e,o)=>e+'|'+Number(o).toFixed(5);
function rPanels(){
 const section=document.createElement('section');section.id='r-analysis';section.className='results';
 section.innerHTML=`<div class="section-title"><span>OPTIONAL OBSERVATION ROBUSTNESS</span><h2>How Robust Are Crossing Predictions to Observation Noise?</h2><p>실제 DD-MDN 추론 · SPD Train annotation-disagreement proxy · 합성 관측오차 비교 · 기본 Predictor는 Q-only</p></div>
 <div class="r-controls"><label>평가된 실제 사례 / origin<select id="rCase"></select></label><button id="rChoose">해당 실제 시점으로 이동</button><label>Noise scenario<select id="rScenario"><option value="iid_0.5">IID λ0.5 · covariance 0.25R</option><option value="iid_1" selected>IID λ1 · covariance R</option><option value="iid_2">IID λ2 · covariance 4R</option><option value="correlated_1">AR(1) ρ0.8 · λ1</option><option value="dropout_1">마지막 0.4초 누락 · λ1</option></select></label><label>표시 모드<select id="rMode"><option value="clean">Clean Q-only (λ0)</option><option value="noisy">Noisy Q</option><option value="filtered_mean">R-aware filtered mean</option><option value="rq">FFBS R+Q</option><option value="side">Side-by-side comparison</option></select></label></div>
 <p id="rAvailability">평가 결과 로딩 중</p><p class="r-warning">Simulation-based completion probability — not independently calibrated. λ는 측정된 카메라 성능 범위가 아닙니다. AR 조건에서도 기존 white-noise 필터를 유지하여 모델 불일치가 존재합니다.</p>
 <div class="r-grid"><article><h3>Matched crossing probabilities</h3><div id="rProbabilities"></div></article><article><h3>Conditions & robustness</h3><div id="rState"></div></article></div>
 <div id="rCompare" class="r-comparison"></div><p>비교 그림: 짙은 회색 = 실제 과거, 주황 = 오차 포함 과거, 초록 = 필터 평균, 파랑 = 실제 DD-MDN 미래. 옅은 영역선 = 선택 horizon의 68/95% HDR. 점선 검정 = 실제 미래 GT(기존 GT 스위치). 지도와 3D 좌표는 위 시뮬레이터에서 확인합니다.</p>
 <div id="rMetrics"></div><div id="rPlots" class="condition-plots"></div><details><summary>정의·평가 범위·보고서</summary><div id="rDefinitions"></div></details>`;
 $('results').before(section);const note=document.createElement('div');note.id='rSceneNote';note.className='comparison-note';note.hidden=true;document.querySelector('.scene .transport').after(note);$('rChoose').onclick=rChoose;$('rScenario').onchange=()=>{R_LAST_RENDER='';rApply();};$('rMode').onchange=()=>{R_LAST_RENDER='';rApply();};
}
function rModeResult(mode){return R_CURRENT?.results[mode==='clean'?'clean':$('rScenario').value+'__'+mode];}
async function rChoose(){const x=R_INDEX.find(x=>x.uid===$('rCase').value);if(!x)return;
 const n=DATA.cases.findIndex(c=>c.event_id===x.event_id);if(n<0){$('rAvailability').textContent='NOT EVALUATED in current viewer catalog';return;}
 $('dataset').value=x.dataset;populateCases(true);$('location').value=x.location;populateCases(false);$('case').value=n;$('interval').value='1';$('condition').value='clean';await chooseCase();t=x.elapsed_s;$('time').value=t;lastKey='';draw();await rLoad();}
async function rLoad(){
 if(!packet||!caseData)return;const key=rkey(caseData.event_id,packet.origin_s);if(key===R_ACTIVE_KEY)return;R_ACTIVE_KEY=key;R_CURRENT=null;R_LAST_RENDER='';rClearLines();$('rSceneNote').hidden=true;const request=++R_REQUEST;
 const x=R_INDEX.find(x=>rkey(x.event_id,x.origin_s)===key);
 if(!x){$('rAvailability').textContent='NOT EVALUATED: 현재 origin에는 matched R stress 결과가 없습니다. 위 목록에서 평가된 실제 시점을 선택하세요.';$('rProbabilities').textContent='NA';$('rState').textContent='NA';$('rCompare').innerHTML='';return;}
 $('rCase').value=x.uid;$('rAvailability').textContent='저장된 실제 추론 로딩 중…';
 try{let d=R_CACHE.get(x.uid);if(!d){const res=await fetch('data/public/r/'+x.file);if(!res.ok)throw Error('HTTP '+res.status);d=await res.json();R_CACHE.set(x.uid,d);if(R_CACHE.size>8)R_CACHE.delete(R_CACHE.keys().next().value);}
 if(request!==R_REQUEST)return;R_CURRENT=d;$('rAvailability').textContent=`${d.dataset} / ${d.event_id} · origin +${d.elapsed_s}s · noise seed ${d.seed} · 동일 관측/미래 GT 비교`;
 for(const [id,z] of Object.entries(d.results)){const name='rstress_'+id;packet.conditions[name]=z;if(!$('condition').querySelector(`option[value="${name}"]`)){const op=document.createElement('option');op.value=name;op.textContent='R stress '+id;$('condition').append(op);}}
 rApply();
 }catch(e){$('rAvailability').textContent='R result unavailable: '+e.message;console.error(e);}}
let R_APPLYING=false;
function rApply(){if(!R_CURRENT||R_APPLYING)return;R_APPLYING=true;try{
 const mode=$('rMode').value,sid=$('rScenario').value;
 for(const op of $('rMode').options)op.disabled=!['clean','side'].includes(op.value)&&!rModeResult(op.value);
 const z=rModeResult(mode==='side'?'clean':mode);
 if(!z){$('rAvailability').textContent='NOT EVALUATED: 해당 조합은 계산되지 않았습니다.';return;}
 $('condition').value=mode==='clean'||mode==='side'?'clean':'rstress_'+sid+'__'+mode;
 $('robustness').checked=mode!=='clean';$('conditionLabel').hidden=mode==='clean';lastKey='';draw();R_LAST_RENDER='';rRender();
 }finally{R_APPLYING=false;}}
function rSVG(z){if(!z)return '<p>NOT EVALUATED</p>';const d=R_CURRENT,clean=d.results.clean,x=clean.input.observed_xy,noise=z.robust_history?.observed_xy,mean=z.robust_history?.mean_xy,path=z.hypotheses_xy[0],gt=d.future_GT_xy,h=Number($('horizon').value),regions=z.regions[h];
 const arrays=[x,path,...(regions?.['0.95']||[])];for(const m of ['clean','noisy','filtered_mean','rq']){const a=rModeResult(m);if(a){arrays.push(a.hypotheses_xy[0],...(a.regions[h]['0.95']||[]));if(a.robust_history)arrays.push(a.robust_history.observed_xy,a.robust_history.mean_xy);}}if($('gt').checked)arrays.push(gt);
 const ps=arrays.flat().filter(p=>p&&p.every(Number.isFinite));const lo=[0,1].map(j=>Math.min(...ps.map(p=>p[j]))),hi=[0,1].map(j=>Math.max(...ps.map(p=>p[j])));const span=Math.max(1,hi[0]-lo[0],hi[1]-lo[1]),cx=(lo[0]+hi[0])/2,cy=(lo[1]+hi[1])/2;
 const xy=p=>[155+(p[0]-cx)*240/span,150-(p[1]-cy)*240/span];
 const poly=(a,c,width=2,dash='')=>{let runs=[],run=[];for(const p of a){if(p&&p.every(Number.isFinite))run.push(p);else{runs.push(run);run=[];}}runs.push(run);return runs.filter(x=>x.length>1).map(x=>`<polyline points="${x.map(p=>xy(p).join(',')).join(' ')}" fill="none" stroke="${c}" stroke-width="${width}" ${dash?'stroke-dasharray="4 3"':''}/>`).join('');};
 let out=`<svg viewBox="0 0 310 300" role="img" aria-label="Actual computed past and future trajectories"><rect width="310" height="300" fill="#f5f8fb"/>`;
 for(const [lev,col] of [['0.95','#9bc5dc'],['0.68','#668eae']])for(const seg of regions[lev])out+=poly(seg,col,1);
 out+=poly(x,'#35414a',3);if(noise)out+=poly(noise,'#dc793d');if(mean)out+=poly(mean,'#2c956f');out+=poly([z.input.translation,...path],'#316bdd',2.5);if($('gt').checked)out+=poly([x.at(-1),...gt],'#222',1,'dash');
 const origin=xy(z.input.translation);out+=`<circle cx="${origin[0]}" cy="${origin[1]}" r="4" fill="#222"/><text x="10" y="290" font-size="11">${rnum(span,1)}m window · +${(h+1)*.5}s HDR · shared scale</text></svg>`;return out;}
function rRender(){if(!R_CURRENT||!packet||rkey(R_CURRENT.event_id,R_CURRENT.origin_s)!==rkey(caseData.event_id,packet.origin_s))return;
 if(!$('robustness').checked&&$('condition').value==='clean')$('rMode').value='clean';
 const k=[R_CURRENT.uid,$('rScenario').value,$('rMode').value,$('horizon').value,$('gt').checked,$('region').checked,t>=packet.elapsed_s+4].join('|');if(k===R_LAST_RENDER)return;R_LAST_RENDER=k;
 const expired=t>=packet.elapsed_s+4,methods=['clean','noisy','filtered_mean','rq'],zs=methods.map(rModeResult),d=R_CURRENT,f=d.feature;
 $('rState').innerHTML=`<dl><dt>Origin speed / state</dt><dd>${rnum(f.speed_mps,2)} m/s · ${resc(f.motion_state)}</dd><dt>Recent acceleration</dt><dd>${rnum(f.acceleration_mps2,2)} m/s²</dd><dt>Remaining Exit</dt><dd>${d.dataset==='inD'?'Exit GT not validated':rnum(f.distance_m,2)+' m'}</dd><dt>Neighbors / density</dt><dd>${f.neighbor_count} within3m / ${rnum(f.density_person_m2,4)} persons/m² (${resc(f.density_region)})</dd><dt>Condition</dt><dd>${resc($('rScenario').selectedOptions[0].text)}</dd></dl>`;
 if(d.dataset==='inD')$('rProbabilities').textContent='Exit GT not validated — position robustness only.';
 else if(expired)$('rProbabilities').textContent='Forecast expired; saved origin probabilities must not be interpreted as current forecasts.';
 else $('rProbabilities').innerHTML='<div class="r-table"><table><tr><th>H</th>'+methods.map(m=>'<th>'+m+'</th>').join('')+'<th>GT</th></tr>'+[1,2,3,4].map(H=>'<tr><td>'+H+'s</td>'+zs.map(z=>'<td>'+(z?.exit.probabilities?.[H]===null||z?.exit.probabilities?.[H]===undefined?'NA':rnum(z.exit.probabilities[H]*100,1)+'%')+'</td>').join('')+'<td>'+(zs[0].exit.GT_by_horizon[H]===null?'Unknown':zs[0].exit.GT_by_horizon[H]?'Complete':'Not complete')+'</td></tr>').join('')+'</table></div>';
 const show=$('rMode').value==='side'?methods:[$('rMode').value];
 $('rSceneNote').hidden=expired||$('rMode').value==='clean';$('rSceneNote').textContent=$('rMode').value==='side'?'R 비교 오버레이: 주황=Noisy, 초록=Filtered mean, 보라=FFBS R+Q. 오른쪽 기본 수치는 Clean이며 네 방법의 수치는 아래 R 비교 패널에 표시됩니다.':'R 관측 이력: 회색=실제 과거, 주황=합성 오차 관측, 초록=필터 평균. 미래 경로와 오른쪽 수치는 현재 선택한 R 방법입니다.';
 rClearLines();if(!expired&&$('rMode').value!=='clean'){const base=rModeResult('rq')||rModeResult('noisy'),h=Number($('horizon').value);if(base?.robust_history){rWorldLine(base.robust_history.actual_xy,'#35414a');rWorldLine(base.robust_history.observed_xy,'#dc793d',.16);rWorldLine(base.robust_history.mean_xy,'#2c956f',.19);}if($('rMode').value==='side')for(const m of ['noisy','filtered_mean','rq']){const z=rModeResult(m),c={noisy:'#dc793d',filtered_mean:'#2c956f',rq:'#8857aa'}[m];if(z){rWorldLine([z.input.translation,...z.hypotheses_xy[0]],c);if($('region').checked)for(const level of ['0.68','0.95'])for(const seg of z.regions[h][level])rWorldLine(seg,c,.1);}}}
 $('rCompare').innerHTML=show.map(m=>{const z=rModeResult(m),base=zs[0];const dp=z?.exit.probabilities?.['4']!=null&&base.exit.probabilities?.['4']!=null?(z.exit.probabilities['4']-base.exit.probabilities['4'])*100:null;const da=z?.metrics.ADE_full4s_m!=null&&base.metrics.ADE_full4s_m!=null?z.metrics.ADE_full4s_m-base.metrics.ADE_full4s_m:null;return `<article><h4>${resc(m)}</h4>${rSVG(z)}<p>ADE ${rnum(z?.metrics.ADE_full4s_m)}m · ΔADE ${rnum(da)}m<br>ΔP4 ${rnum(dp,1)}pp · HDR95(+4s) ${rnum(z?.area_m2['0.95'][7],2)}m²<br>입력 이력 최근속도 ${rnum(z?.amplification?.recent_speed_mps,2)}m/s${m==='rq'?' (8개 이력 평균)':''}</p></article>`;}).join('');
}
function rDashboard(){const s=R_SUMMARY,q=s.metrics.filter(r=>r.condition==='overall'&&r.horizon_s===4);$('rMetrics').innerHTML='<h3>Measured R robustness — H=4 seconds</h3><div class="r-table"><table><tr>'+['Dataset','Scenario','Mode','Events / origins','ADE m','Cov95 / HDR95 m²','Brier / n','|ΔP| pp','Recovery Brier','Evidence'].map(x=>'<th>'+x+'</th>').join('')+'</tr>'+q.map(r=>`<tr><td>${r.dataset}</td><td>${r.noise_type} λ${r.noise_scale}</td><td>${r.mode}</td><td>${r.n_events} / ${r.n_origins}</td><td>${rnum(r.ade_m)}</td><td>${rnum(r.coverage95*100,1)}% / ${rnum(r.hdr95_area_m2,2)}</td><td>${rnum(r.brier,4)} / ${r.n_completion_evaluable}</td><td>${rnum(r.mean_abs_prob_shift,1)}</td><td>${rnum(r.recovery_brier,4)}</td><td>${r.status}</td></tr>`).join('')+'</table></div>';
 $('rPlots').innerHTML=s.plots.map(n=>`<figure><img src="r_robustness/plots/${n}" loading="lazy" alt="Measured R robustness ${n}"><figcaption>${n} · synthetic SPD proxy · matched origins; clustered intervals where supported. Position coverage and area must be considered together.</figcaption></figure>`).join('');
 $('rDefinitions').innerHTML='<p>Frozen SPD Train R, λ² covariance, AR rho0.8, last0.4s dropout. CV4 q=0.5m²/s³ and priors unchanged. Eight FFBS histories;3200 joint future samples. R is not physically identified camera noise. Noisy context is target-only; maps/neighbors assumed exact.</p><p>Complete-case Brier; unknown censoring remains NA. Small behavior groups are INSUFFICIENT DATA. Test historically reused. inD Exit unavailable. XGBoost AFT NOT_IMPLEMENTED. Existing official full-Test results stay separate.</p><p><a href="r_robustness/FINAL_R_ROBUSTNESS_REPORT.md">Measured report</a> · <a href="r_robustness/r_robustness_metrics.csv">Aggregate CSV</a> · <a href="r_robustness/FINAL_R_INTEGRATION_CHECK.md">Integration check</a></p>';
}
async function rStart(){while(!window.conditionReady)await new Promise(r=>setTimeout(r,100));rPanels();
 try{R_INDEX=await(await fetch('data/public/r-index.json')).json();R_SUMMARY=await(await fetch('r_robustness/r_robustness_summary.json')).json();$('rCase').innerHTML=R_INDEX.map(x=>`<option value="${x.uid}">${resc(x.dataset+' / '+x.location+' / '+x.event_id+' / +'+x.elapsed_s+'s')}</option>`).join('');rDashboard();const oldDraw=draw;draw=function(){oldDraw();if(!R_APPLYING){rLoad();rRender();}};await rLoad();window.rReady=true;}catch(e){$('rAvailability').textContent='R analysis unavailable: '+e.message;console.error(e);}}
rStart();
