// Run against a static deployment and a running Chrome DevTools endpoint.
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';

const base=process.env.V2R_PUBLIC_URL||'http://127.0.0.1:19864/presentation';
const cdp=process.env.V2R_CDP||'http://127.0.0.1:19865';
const uqEdition=process.env.V2R_DECK==='uq';
const deck=uqEdition?'presentation-uq.html':'presentation.html';
const tab=await (await fetch(cdp+'/json/new?about:blank',{method:'PUT'})).json();
const ws=new WebSocket(tab.webSocketDebuggerUrl);
await new Promise(resolve=>ws.onopen=resolve);
const pending=new Map(), errors=[];
let id=0;
ws.onmessage=({data})=>{
  const m=JSON.parse(data);
  if(m.id){pending.get(m.id)?.(m);pending.delete(m.id);}
  if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);
  if(m.method==="Network.loadingFailed"&&!m.params.canceled&&m.params.errorText!=="net::ERR_ABORTED")errors.push(m.params.errorText);
  if(m.method==='Network.responseReceived'&&m.params.response.status>=400)errors.push(m.params.response.url);
};
async function call(method,params={}) {
  const n=++id;
  const reply=await new Promise(resolve=>{pending.set(n,resolve);ws.send(JSON.stringify({id:n,method,params}));});
  assert(!reply.error,JSON.stringify(reply.error));return reply.result;
}
async function ev(expression,userGesture=false) {
  const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture});
  assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;
}
async function until(expr) {
  for(let i=0;i<300;i++){
    if(await ev(expr))return;
    await new Promise(r=>setTimeout(r,100));
  }
  throw Error('Timed out waiting for '+expr);
}
const click=id=>ev('document.getElementById('+JSON.stringify(id)+').click()',true);
const goto=path=>call('Page.navigate',{url:base+'/'+path});
const viewport=(width,height)=>call('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
const checks=[];
try {
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');await call('Network.setCacheDisabled',{cacheDisabled:true});
  await viewport(1440,900);await goto(deck+'#scene-1');
  await until('document.querySelector("#pProgress a")');
  const dest=process.env.V2R_SHOTS;
  async function capture(name){
    if(!dest)return;
    const shot=await call('Page.captureScreenshot',{format:'jpeg',quality:87});
    await writeFile(dest+'/'+name+'.jpg',Buffer.from(shot.data,'base64'));
  }
  const step=async n=>{
    await ev('document.querySelectorAll("button[data-stage]")['+(n-1)+'].click()');
    await until('document.querySelector(".guided").dataset.stage==="'+n+'"');
  };
  const set=async(id,value)=>ev('(()=>{const e=PS('+JSON.stringify(id)+');e.value='+JSON.stringify(value)+';e.dispatchEvent(new Event("change"));})()');
  async function condition(mode){
    const {x,y}=await ev(`(()=>{const r=document.querySelector('button[data-condition="${mode}"]').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    for(const type of ['mousePressed','mouseReleased'])await call('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});
    await until('document.querySelector(".guided").dataset.mode==="'+mode+'"');
  }
  const ready3=()=>until('document.querySelector(".guided")?.dataset.renderer==="babylon" && !!sc.getMeshByName("actualMap") && sc.isReady()');
  if(uqEdition){
    async function preservedScenes(page){
      await goto(page+'#scene-8');
      await until('location.pathname.endsWith("/'+page+'") && PS("pProgressText")?.textContent==="8 / 11"');
      const snapshots=[];
      for(const n of [8,9,10,11]){
        await ev('location.hash="#scene-'+n+'"');
        await until('PS("pProgressText").textContent==="'+n+' / 11"');
        if(n===10)await ready3();
        snapshots.push(await ev(`({
          heading:PS('pTitle').textContent,subtitle:PS('pSubtitle').textContent,notes:PS('pNotes').textContent,
          body:${n}===10?PS('pScene').innerText:PS('pScene').innerHTML,
          scripts:[...document.scripts].map(s=>s.src).filter(src=>!src.includes('/pres/story'))
        })`));
      }
      return snapshots;
    }
    const oldScenes=await preservedScenes('presentation.html');
    assert.deepEqual(await preservedScenes(deck),oldScenes);
    checks.push('both editions match on scenes 8–11, presenter notes, initial 3D controls and shared simulation scripts');
  }
  const layout=()=>ev(`(()=>{
    const rect=id=>PS(id).getBoundingClientRect();
    const next=rect('gNext'), footer=document.querySelector('.deck-footer')?.getBoundingClientRect();
    return {width:innerWidth,height:innerHeight,canvas:[rect('gCanvas').width,rect('gCanvas').height],bottom:next.bottom,
      fits:document.documentElement.scrollWidth<=innerWidth+1 && (!footer||next.bottom<=footer.top+1) && next.bottom<=innerHeight &&
        [...document.querySelectorAll('.guided button:not(:disabled),.guided select:not(:disabled),#gTime:not(:disabled)')].filter(el=>el.offsetWidth).every(el=>{
          const r=el.getBoundingClientRect(), hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return hit===el||el.contains(hit);})};
  })()`);
  for(const [width,height,fullscreen] of [[1920,1080],[1366,768],[1440,900],[1440,900,true]]){
    await viewport(width,height);
    if(fullscreen){
      await call('Page.bringToFront');
      const {x,y}=await ev('(()=>{pFullscreen.scrollIntoView({block:"nearest"});const r=pFullscreen.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()');
      for(const type of ['mousePressed','mouseReleased'])await call('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});
      await until('!!document.fullscreenElement');
    }
    for(let n=1;n<=11;n++){
    await ev('location.hash="#scene-'+n+'"');await until('document.querySelector("#pProgress a[aria-current]").textContent==="'+n+'"');
    if(n===10){await ready3();await set('gTime',7);await ev('gTime.dispatchEvent(new Event("input"))');}
    const geom=await ev(`(()=>{const scene=PS('pScene');const f=document.querySelector('.deck-footer').getBoundingClientRect();
      return {slide:${n},w:innerWidth,bottom:scene.getBoundingClientRect().bottom,footer:f.top,overflow:document.documentElement.scrollWidth>innerWidth};})()`);
    if(geom.overflow||geom.bottom>geom.footer+1)console.log('slide layout',geom);
    assert(!geom.overflow && geom.bottom<=geom.footer+1,JSON.stringify(geom));
    const uqExpected={
      1:['Uncertainty Quantification','실제 보행 기록'],
      2:['관측 불확실성','공간 예측 불확실성','횡단 완료 불확실성','SPD','IMPTC','inD'],
      3:['2,465','15.7 / 17.8 cm','23.8 cm','공분산 R','독립 학습','선택 적용'],
      4:['0.283','3.925','0.742','0.418','4.569','0.871','81.1%','80.9%'],
      5:['78.51%','95%','10.27 m²','748.20','81.1%'],
      6:['2.063초','2.53%','66.25%','0.03472','0.33527','0.08594','74.4%']
    };
    const expected=(uqEdition&&uqExpected[n])||{3:['23.8 cm','주석 불일치','사전학습'],
      4:['향후 4초간 평균 위치 예측오차(ADE)','81.1%','0.74'],
      5:['78.51%','95%','원인은 별도로 검증'],
      6:['2.53%','66.25%','0.03472','0.33527','0.08594','74.4%'],
      7:['3.42 m','1.57 m/s','−0.012 m/s²','2.063초','약 0%','17.03%','99.96%','약 100%',
        '1,113개','2,322개','393개','2.19 → 0.059 m','0.10827','0.04634','0.02714','0.04410','0.00618','0.01021','0.02503','0.02396','71%','94.3%','236시점','120건'],
      8:['XGBoost 예측값은 이 계산에 사용하지 않았다','27.0초'],
      11:['XGBoost AFT','향후 4초간 평균 위치 예측오차(ADE)']}[n]||[];
    const visible=await ev('PS("deck").textContent');
    for(const value of expected)assert(visible.includes(value),'Scene '+n+' missing '+value);
    if(n===7){
      if(uqEdition)for(const value of ['0.05646','0.01635','전체 기준선 비교'])assert(visible.includes(value));
      assert.equal(await ev('document.querySelector(".aft-pipeline polyline").points.length'),81);
      assert.equal(await ev('PS("pProgress").children.length'),11);
    }
    await capture((fullscreen?'fullscreen-':width===1440?'':width+'-')+'scene-'+n);
    }
    if(fullscreen){await click('pFullscreen');await until('!document.fullscreenElement');}
  }
  await ev('location.hash="#scene-10"');await ready3();
  assert(await ev('gClock.textContent==="0.00 s / 10.08 s"'));
  const verifyTracking=await ev(`(async()=>{
    const t=await V2R.json('demo/f2-full-track.json'),modes=Object.keys(UQ.names);
    for(let i=0;i<t.elapsed_s.length;i++){
      gTime.value=t.elapsed_s[i];gTime.dispatchEvent(new Event('input'));
      if(+document.querySelector('.full-tracking').dataset.index!==i)throw Error('time index '+i);
      for(const mode of modes){
        const line=sc.getMeshByName('tracking trail '+mode),marker=sc.getMeshByName('tracking marker '+mode);
        if(line.subMeshes[0].indexCount!==line.getTotalIndices()*i/(t.elapsed_s.length-1)
          ||BABYLON.Vector2.Distance(new BABYLON.Vector2(marker.position.x,marker.position.z),BABYLON.Vector2.FromArray(t[mode][i]))>1e-6)
          throw Error('trail or marker '+mode+' at '+i);
      }
      if(Math.hypot(person.position.x-t.clean[i][0],person.position.z-t.clean[i][1])>1e-6)throw Error('actor');
    }
    for(const mode of modes){
      document.querySelector('[data-track-mode="'+mode+'"]').click();
      if(modes.some(m=>sc.getMeshByName('tracking marker '+m).isEnabled()!==(m===mode)))throw Error('selection');
    }
    document.querySelector('[data-track-mode="all"]').click();return t.elapsed_s.length;
  })()`);
  assert.equal(verifyTracking,254);
  assert(await ev('!trackSummary.hidden&&["21.16 cm","8.79 cm","58.4%"].every(v=>trackSummary.textContent.includes(v))'));
  await capture('full-track-exit');
  await click('gReset');await click('gPlay');await until('+gTime.value>.25');
  await click('gPlay');assert(await ev('gPlay.textContent.includes("재생")'));
  await ev('gTime.value=5;gTime.dispatchEvent(new Event("input"))');
  await click('trackTop');await capture('full-track-mid');await click('trackCross');
  await click('showForecast');await ready3();await click('showTracking');await ready3();
  assert(await ev('gClock.textContent==="0.00 s / 10.08 s"'));
  await click('showForecast');await ready3();
  checks.push('f2 Entry to Exit: 254 samples, three synchronized trails/markers, selection, replay, reset, camera and return');
  // The default replay traverses the complete public track. Read each forecast only
  // after its origin and remove overlays as soon as recorded completion is confirmed.
  const seekJourney=t=>ev('gTime.value='+t+';gTime.dispatchEvent(new Event("input"))');
  assert(await ev('PS("gJourney").getAttribute("aria-pressed")==="true" && gClock.textContent==="0.00 s / 13.06 s"'));
  for(const uid of ['o0008','o0000','o0011']){
    await set('gCase',uid);await until('document.querySelector(".guided").dataset.uid==="'+uid+'"&&!document.querySelector(".guided").inert');
    const checkEntry=async()=>assert(await ev(`(()=>{
      const gt=V2R.evidence.cases.find(c=>c.event_id===caseData.event_id).GT;
      const t=gt.entry_s-caseData.origin0_s,rec=caseData.actual_observations,i=rec.elapsed_s.findLastIndex(v=>v<=t);
      const w=(t-rec.elapsed_s[i])/(rec.elapsed_s[i+1]-rec.elapsed_s[i]);
      const xy=rec.xy[i].map((v,k)=>v+w*(rec.xy[i+1][k]-v));
      const geom=DATA.geometry[caseData.crosswalk],edge=V2R.boundary(geom,caseData.direction===1?'end_A':'end_B');
      const onBoundary=edge.slice(1).some(([x,z],j)=>{const [a,b]=edge[j];const dx=x-a,dz=z-b,l=dx*dx+dz*dz;
        if(!l)return false;const u=Math.max(0,Math.min(1,((xy[0]-a)*dx+(xy[1]-b)*dz)/l));
        return Math.hypot(xy[0]-a-u*dx,xy[1]-b-u*dz)<.00001;});
      return Math.abs(+gTime.value-t)<1e-6 && person.isEnabled() && onBoundary && Math.hypot(person.position.x-xy[0],person.position.z-xy[1])<1e-7;
    })()`));
    await checkEntry();
    for(const n of [1,2,3,4]){
      await step(n);await checkEntry();
      for(const mode of ['clean','noisy','filtered_mean']){
        await condition(mode);await checkEntry();
        assert(await ev(`sc.activeCameras.length===3 && !gNoise.disabled && !gH.disabled &&
          [...document.querySelectorAll('.g-segments button')].every((b,i)=>!b.disabled&&b.querySelector('[data-input="'+b.dataset.condition+'"]')&&sc.meshes.some(m=>m.metadata?.condition===b.dataset.condition&&m.layerMask===sc.activeCameras[i].layerMask))`));
      }
      if(n===2){
        await condition('noisy');await checkEntry();
        await click('gJump');await click('gReset');await checkEntry();
        if(uid==='o0008'){await until('sc.isReady()');await capture('entry-observation');}
      }
    }
    await click('gJourney');await condition('clean');
    assert(await ev('Number(gTime.min)===V2R.evidence.cases.find(c=>c.event_id===caseData.event_id).GT.entry_s-caseData.origin0_s && Number(gTime.max)===caseData.actual_observations.elapsed_s.at(-1) && !gOutcome.textContent && !sc.getMeshByName("representative")'));
    assert(await ev(`(()=>{sc.render();return caseData.actual_observations.xy.every(([x,z])=>{
      const pt=BABYLON.Vector3.Project(new BABYLON.Vector3(x,.9,z),BABYLON.Matrix.Identity(),sc.getTransformMatrix(),camera.viewport.toGlobal(engine.getRenderWidth(),engine.getRenderHeight()));
      return pt.x>=0 && pt.x<=engine.getRenderWidth() && pt.y>=0 && pt.y<=engine.getRenderHeight();});})()`));
    const selected=await ev('Number(V2R.ri.find(r=>r.uid===gCase.value).origin_s)');
    for(const f of await ev('caseData.forecasts.filter(f=>f.elapsed_s<caseData.GT_exit_elapsed_s).map(f=>f.elapsed_s)')){
      await seekJourney(f);
      assert(await ev(`(()=>{const r=caseData.forecasts.find(f=>f.elapsed_s===${f}).conditions.clean;
        const p=r.exit.probabilities?.[4]??r.exit.model_probability_4s;
        return +document.querySelector(".guided").dataset.forecastOrigin===${f} && !!sc.getMeshByName("representative") && !!sc.getMeshByName("HDR 0.95") && Number(gProb.querySelector('[data-t="4"]').dataset.probability)===p && (r.exit.probabilities?gProb.children.length>0:gProb.innerText.includes("미저장"));})()`));
    }
    for(const mode of ['noisy','filtered_mean']){
      await condition(mode);await seekJourney(selected-.1);
      assert(await ev('!sc.getMeshByName("representative")&&!gProb.textContent'));
      await click('gNext');assert(await ev('!!sc.getMeshByName("representative") && gTime.valueAsNumber==='+selected));
    }
    await seekJourney(await ev('caseData.actual_observations.elapsed_s.at(-1)'));
    assert(await ev('gOutcome.textContent.includes("Entry → Exit") && !sc.getMeshByName("representative")'));
  }
  await set('gCase','o0008');await until('document.querySelector(".guided").dataset.uid==="o0008"&&!document.querySelector(".guided").inert');
  await click('gPlay');await until('gTime.valueAsNumber>caseData.GT_exit_elapsed_s+.2');await until('Math.abs(gTime.valueAsNumber-Number(gTime.max))<.00001 && !gPlay.textContent.includes("일시정지")');
  assert(await ev('gOutcome.textContent.includes("10.08초") && gClock.textContent==="13.06 s / 13.06 s"'));
  await step(2);assert(await ev('gClock.textContent==="0.00 s / 8.02 s"'));
  checks.push('Actor starts on the recorded Entry boundary on all tabs, including Noisy and restart, across three cases');
  checks.push('Entry-aligned public tracks for all three cases, cached forecast updates, gated conditions, camera coverage and unbroken f2 playback through Exit');
  for(const [w,h] of [[1920,1080],[1440,900],[1366,768]]){
    await viewport(w,h);
    for(const n of [1,2,3,4]){
      await step(n);if(n>=2)await click('gJump');if(n===4)await click('gReveal');await until('sc.isReady()');
      const box=await layout();if(n===4)console.log('layout',box);assert(box.fits,JSON.stringify(box));
    }
  }
  await call('Page.bringToFront');
  await ev('PS("pFullscreen").scrollIntoView({block:"nearest"})');
  await click('pFullscreen');await until('!!document.fullscreenElement');assert((await layout()).fits);
  await click('pFullscreen');await until('!document.fullscreenElement');
  await viewport(1440,900);await step(1);await click('gReset');
  await click('gPlay');await until('Number(gTime.value)>Number(gTime.min)+.2');await click('gPlay');
  const paused=await ev('gTime.value');await new Promise(r=>setTimeout(r,240));assert.equal(await ev('gTime.value'),paused);
  await ev('gTime.value=7.4;gTime.dispatchEvent(new Event("input"))');await capture('stage-1');
  await click('gPlay');await until('Number(gTime.value)>=8 && gPlay.textContent.includes("재생")');
  assert(await ev('!sc.getMeshByName("actual future")&&!sc.getMeshByName("representative")&&!gProb.textContent'));
  const pose=()=>ev('person.position.asArray()');
  assert(await ev('JSON.stringify([person.position.x,person.position.z])===JSON.stringify(caseData.actual_observations.xy[caseData.actual_observations.elapsed_s.findLastIndex(t=>t<=+gTime.value+1e-6)])'));
  const atOrigin=await pose();const cam=()=>ev('[camera.alpha,camera.beta,camera.radius,...camera.target.asArray()]');
  const locked=await cam();
  assert(await ev('[...document.querySelectorAll("[data-condition]")].every(b=>!b.disabled)'));
  await click('gNext');await click('gJump');await click('gCompare');await condition('noisy');await until('sc.isReady()');await capture('stage-2');
  assert(await ev('!!sc.getMeshByName("measurement ellipse") && !sc.getMeshByName("representative")'));assert.deepEqual(await pose(),atOrigin);
  await click('gNext');await click('gJump');await condition('filtered_mean');await until('sc.isReady()');await capture('stage-3');
  assert(await ev('!!sc.getMeshByName("HDR 0.95") && !!sc.getMeshByName("HDR 0.68") && !sc.getMeshByName("actual future") && !gProb.textContent'));
  await click('gNext');await click('gJump');
  for(const truth of [false,true]){
    if(truth)await click('gReveal');
    for(const mode of ['clean','noisy','filtered_mean']){
      const old=await ev('sc.getMeshByName("representative").uniqueId');
      await condition(mode);await until('sc.isReady()');
      assert(await ev('!!sc.getMeshByName("observed endpoint") && sc.getMeshByName("representative").uniqueId!== '+old+' && !sc.meshes.some(m=>m.uniqueId==='+old+')'));
      assert.deepEqual(await pose(),atOrigin);assert.deepEqual(await cam(),locked);
      assert.equal(await ev('!!sc.getMeshByName("actual future")'),truth);
      assert.equal(await ev('gCaseMetrics.innerText.includes("끝점 오차")'),truth);
      if(truth)await capture('after-'+mode);
    }
  }
  await click('gReveal');assert(await ev('!gOutcome.textContent && !sc.getMeshByName("actual future")'));await click('gReveal');
  await until('sc.isReady()');await capture('stage-4');
  // Dispatch playback and seek through the same controls a presenter uses.
  const seek=async offset=>ev('gTime.value=8+'+offset+';gTime.dispatchEvent(new Event("input"))');
  for(const n of [2,3,4]){
    await step(n);
    for(const mode of ['clean','noisy','filtered_mean']){
      await condition(mode);
      assert(await ev('!gPlay.disabled && +gTime.max>+gTime.min'));
      await click('gPlay');await until('gTime.valueAsNumber>+gTime.min+.15');
      await until('!gPlay.textContent.includes("일시정지")||gTime.valueAsNumber>+gTime.min+.2');
      await seek(n===2?-.4:1);
      assert(await ev(`(async()=>{
        const s=await UQ.caseAt(V2R.ri.find(row=>row.uid==='o0008'));
        const r=s.r.results[document.querySelector('.guided').dataset.resultKey];
        const obs=${n}===2;
        const times=obs?r.input.history_times_s:r.future_times_s;
        const j=times.findLastIndex(t=>t<=(obs?7.6:1)+1e-6);
        const best=r.hypothesis_confidence_scores.indexOf(Math.max(...r.hypothesis_confidence_scores));
        const pt=(obs?r.input.observed_xy:r.hypotheses_xy[best])[j];
        const marker=obs?sc.getMeshByName('observed endpoint'):sc.getTransformNodeByName('forecast pedestrian');
        return marker.isEnabled() && marker.position.x===pt[0] && marker.position.z===pt[1] && !sc.getMeshByName('actual future');
      })()`));
      if(n>=3)assert.deepEqual(await pose(),atOrigin);
    }
  }
  await seek(0);await click('gPlay');await condition('clean');
  assert(await ev('gPlay.textContent.includes("일시정지")'));await until('gTime.valueAsNumber>+gTime.min+.5');
  await click('gReveal');await seek(1);
  assert(await ev('person.position.x===caseData.actual_observations.xy[caseData.actual_observations.elapsed_s.findLastIndex(t=>t<=9.000001)][0] && sc.getTransformNodeByName("forecast pedestrian").isEnabled()'));
  checks.push('Playback, selected history or forecast position and hidden truth in all nine stage/condition combinations; continued playback on switch and recorded future after reveal');
  let combos=0;
  for(const uid of ['o0008','o0000','o0011']){
    await set('gCase',uid);await until('document.querySelector(".guided").dataset.uid==="'+uid+'"&&!document.querySelector(".guided").inert');
    await step(4);await click('gJump');await click('gReveal');
    const match=await ev(`(async()=>{
      const row=V2R.ri.find(r=>r.uid===gCase.value),s=await UQ.caseAt(row);
      const set=(id,value)=>{const e=PS(id);e.value=value;e.dispatchEvent(new Event('change'));};
      const coords=()=>person.position.asArray().join(','), reference=coords();
      const camera0=[camera.alpha,camera.beta,camera.radius,...camera.target.asArray()].join(',');
      let count=0;
      const vertexMatches=(mesh,path)=>{
        // Tube rings have six sides plus a seam. Their centres recover the source XY.
        const vertices=mesh.getVerticesData(BABYLON.VertexBuffer.PositionKind), stride=7*3;
        const close=(a,b)=>Math.abs(a-b)<.002;
        const ringMatches=(index,p)=>{
          let x=0,z=0;for(let i=0;i<6;i++){x+=vertices[index*stride+i*3];z+=vertices[index*stride+i*3+2];}
          return close(x/6,p[0])&&close(z/6,p[1]);};
        // CAP_ALL prepends/appends two end rings, including the cap centre.
        return path.every((p,i)=>ringMatches(i+2,p));};
      for(const [noise] of UQ_SCENARIOS)for(const mode of Object.keys(UQ.names))for(const h of UQ.horizons){
        set('gNoise',noise);document.querySelectorAll('[data-condition]').forEach(b=>{if(b.dataset.condition===mode)b.click()});set('gH',h);
        const r=s.r.results[mode==='clean'?'clean':noise+'__'+mode],i=r.future_times_s.indexOf(h),best=r.hypothesis_confidence_scores.indexOf(Math.max(...r.hypothesis_confidence_scores));
        const key=mode==='clean'?'clean':noise+'__'+mode;
        if(document.querySelector('.guided').dataset.resultKey!==key||!gCaseMetrics.innerText.includes(r.area_m2['0.95'][i].toFixed(2)))throw Error('case metric/key');
        const pt=r.hypotheses_xy[best][i],gt=s.f.future_GT_xy[i],y=V2R.gt(s,h);
        if(gt?.every(Number.isFinite)&&!gCaseMetrics.innerText.includes(Math.hypot(pt[0]-gt[0],pt[1]-gt[1]).toFixed(2)+' m'))throw Error('case endpoint error');
        if(y!=null&&!gCaseMetrics.innerText.includes(((r.exit.probabilities[h]-y)**2).toFixed(4)))throw Error('case squared error');
        const end=r.input.observed_xy.at(-1),marker=sc.getMeshByName('observed endpoint').position;
        if(marker.x!==end[0]||marker.z!==end[1]||!vertexMatches(sc.getMeshByName('model input'),r.input.observed_xy))throw Error('input/marker');
        const candidates=sc.meshes.filter(m=>m.name==='candidate');
        const source=r.hypotheses_xy.filter((_,j)=>j!==best);
        if(candidates.length!==source.length||candidates.some((m,j)=>!vertexMatches(m,[end,...source[j].slice(0,i+1)])))throw Error('candidate meshes');
        if(mode==='filtered_mean'&&(!sc.getMeshByName('reference history')||!sc.getMeshByName('noisy context')))throw Error('missing comparison histories');
        for(const [panelIndex,panelMode] of Object.keys(UQ.names).entries()){
          const packet=s.r.results[panelMode==='clean'?'clean':noise+'__'+panelMode];
          const scores=packet.hypothesis_confidence_scores,top=scores.indexOf(Math.max(...scores));
          const mesh=sc.meshes.find(m=>m.metadata?.condition===panelMode&&m.metadata.layer==='representative');
          if(!mesh||mesh.layerMask!==sc.activeCameras[panelIndex].layerMask||
              !vertexMatches(mesh,[packet.input.observed_xy.at(-1),...packet.hypotheses_xy[top].slice(0,i+1)]))throw Error('cross-panel forecast mismatch');
        }
        if(coords()!==reference||camera0!==[camera.alpha,camera.beta,camera.radius,...camera.target.asArray()].join(','))throw Error('pose/camera changed');
        if(!vertexMatches(sc.getMeshByName('actual future'),[s.clean.input.observed_xy.at(-1),...s.f.future_GT_xy.slice(0,i+1)]))throw Error('3D GT vertices');
        if(!vertexMatches(sc.getMeshByName('representative'),[r.input.observed_xy.at(-1),...r.hypotheses_xy[best].slice(0,i+1)]))throw Error('representative vertices');
        for(const level of ['0.68','0.95']){
          const outlines=sc.meshes.filter(m=>m.name==='contour '+level);
          if(outlines.length!==r.regions[i][level].length||!outlines.every((m,j)=>vertexMatches(m,r.regions[i][level][j])))throw Error('HDR vertices');
        }
        for(const bar of gProb.querySelectorAll('[data-t]'))if(+bar.dataset.probability!==r.exit.probabilities[bar.dataset.t])throw Error('probability');
        if(+gProb.querySelector('.chosen').dataset.t!==h||!gOutcome.textContent.includes(V2R.gt(s,h)?'초 이내 완료':'초 이내 미완료'))throw Error('H/outcome');count++;
      }return count;
    })()`);combos+=match;
    await click('gPlay');await until('Number(gTime.value)>Number(gTime.min)+.1');await click('gReveal');
    assert(await ev('!sc.getMeshByName("actual future") && !gOutcome.textContent && +gTime.value===V2R.ri.find(row=>row.uid===gCase.value).origin_s'));
  }
  assert.equal(combos,180);await set('gCase','o0008');await until('gCase.value==="o0008"&&!document.querySelector(".guided").inert');
  await step(1);await click('gTop');assert(await ev('camera.beta<.05'));await click('gCamera');assert.deepEqual(await cam(),locked);
  await click('pPrev');await until('location.hash==="#scene-9" && !PS("gCanvas")');
  await ev('history.back()');await ready3();await click('showForecast');await ready3();await click('pNotesButton');assert(await ev('!pNotes.hidden'));await click('pNotesButton');
  await step(3);await click('gJump');await condition('noisy');await set('gH',4);await click('gFull');
  assert(await ev(`(()=>{
    sc.render();
    const visible=sc.meshes.filter(m=>m.name==='contour 0.95').every(m=>{
      const points=m.getVerticesData(BABYLON.VertexBuffer.PositionKind);
      for(let i=0;i<points.length;i+=3){
        const p=BABYLON.Vector3.Project(BABYLON.Vector3.FromArray(points,i),m.getWorldMatrix(),sc.getTransformMatrix(),camera.viewport.toGlobal(engine.getRenderWidth(),engine.getRenderHeight()));
        if(p.x<0||p.y<0||p.x>engine.getRenderWidth()||p.y>engine.getRenderHeight())return false;
      }return true;});
    return visible;
  })()`));
  await until('sc.isReady()');await capture('overview-noisy');
  checks.push('11 slides, four guided stages, all three requested viewports, fullscreen, navigation, camera and playback');
  checks.push('180 WebGL case/condition/noise/horizon combinations matched cached probabilities, representative, HDR and GT vertices');
  await goto('demo.html');await ready3();assert(await ev('!!PS("showForecast")'));await click('showForecast');await ready3();await ev('PS("extra2D").open=true');await until('document.querySelector("#uqCase")');
  const matrix=await ev(`(async()=>{
    const set=(id,value)=>{let el=PS(id);el.value=value;el.dispatchEvent(new Event('change'));};
    let count=0;
    for(const row of V2R.ri){
      set('uqCase',row.uid);
      while(PS('uqCase').disabled)await new Promise(r=>setTimeout(r,20));
      const s=await V2R.select(row.event_id,row.origin_s);
      if(PS('uqReveal').getAttribute('aria-pressed')!=='false')throw Error('new case truth leak');
      PS('uqReveal').click();
      // Recover the map transform from its Entry line and its one-metre scale bar.
      // Compare rendered vertices with the independent, unperturbed case forecast.
      function checkGroundTruth(map,h) {
        const g=s.geometry,dir=s.c.direction;
        const anchor=V2R.boundary(g,dir===1?'end_A':'end_B')[0];
        const pixel=map.querySelector('polyline').points[0];
        const scale=Number(map.querySelector('path').getAttribute('d').split('h')[1]);
        const rendered=map.querySelector('[data-path=truth]').points;
        const expected=[s.clean.input.observed_xy.at(-1),...s.f.future_GT_xy.slice(0,2*h)];
        if(rendered.length!==expected.length)throw Error('GT point count');
        expected.forEach(([x,y],i)=>{
          const delta=axis=>(x-anchor[0])*axis[0]+(y-anchor[1])*axis[1];
          if(Math.abs(rendered[i].x-pixel.x-dir*scale*delta(g.axis))>.025 ||
             Math.abs(rendered[i].y-pixel.y+dir*scale*delta(g.normal))>.025)throw Error('GT coordinate mismatch');
        });
      }
      for(const [noise] of UQ_SCENARIOS){
        PS('view-observation').click();set('uqNoise',noise);
        if(!document.querySelector('.history polygon'))throw Error('missing R ellipse');
        PS('view-motion').click();
        for(const mode of Object.keys(UQ.names)){
          set('uqMode',mode);
          const predicted=s.r.results[mode==='clean'?'clean':noise+'__'+mode];
          for(const h of UQ.horizons){
            set('uqH',h);
            const map=document.querySelector('.forecast'),prob=document.querySelector('.prob-row.chosen');
            if(map.dataset.h!=h||map.dataset.mode!==mode||prob.dataset.t!=h||+prob.dataset.probability!==predicted.exit.probabilities[h])throw Error('spatial/temporal mismatch');
            if(!map.querySelector('[data-path=representative]')||!map.querySelector('[data-level="0.68"]')||!map.querySelector('[data-level="0.95"]'))throw Error('missing forecast field');
            if(!map.querySelector('[data-path=truth]')||!document.querySelector('.outcome').textContent.endsWith(h+'초 이내 '+(V2R.gt(s,h)?'완료':'미완료')))throw Error('wrong outcome');
            checkGroundTruth(map,h);
            for(const bar of document.querySelectorAll('.prob-row')) {
              if(+bar.dataset.probability!==predicted.exit.probabilities[bar.dataset.t])throw Error('wrong discrete probability');
            }
            count++;
          }
        }
      }
      PS('uqReveal').click();
      if(document.querySelector('.outcome,[data-path=truth]'))throw Error('GT hide');
      document.querySelector('#extraReplay .direct summary').click();
      if(!document.querySelector('#extraReplay .direct[open]')||document.querySelector('#extraReplay .direct').textContent.includes('자료 없음'))throw Error('AFT unavailable');
    }
    return count;
  })()`);
  assert.equal(matrix,180);checks.push('180 cached case/setting/mode/horizon combinations');
  await click('view-validation');assert((await ev('replayBody.textContent')).includes('0.08594'));
  await click('view-observation');assert(await ev('!!document.querySelector(".history")'));
  await viewport(390,844);await click('view-motion');assert(await ev('document.documentElement.scrollWidth<=innerWidth+1'));
  await goto('results.html');await until('document.querySelector("#finding-noise")');
  assert(await ev('!!document.querySelector(\'a[href="r_robustness/FINAL_R_ROBUSTNESS_REPORT.md"]\')'));
  checks.push('aggregate view, mobile demo and historical appendix');
  await viewport(1366,768);await goto('index.html?case=o0008#/simulation');
  await until('window.demoReady&&typeof sc!=="undefined" && sc?.getMeshByName("actualMap") && !!caseData && sc.isReady()');
  assert(await ev('!!person && !!engine.getRenderingCanvas()'));checks.push('original Babylon explorer and map');
  const injected=await call('Page.addScriptToEvaluateOnNewDocument',{source:`const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return /webgl/i.test(type)?null:get.call(this,type,...args)};`});
  await goto(deck+'#scene-10');await until('document.querySelector(".guided")?.dataset.renderer==="2d"');
  await seekJourney(5);assert(await ev('!!gFallback.querySelector("polyline")&&+document.querySelector(".full-tracking").dataset.index>0'));
  await click('showForecast');await until('document.querySelector(".guided")?.dataset.renderer==="2d"');
  await seekJourney(8);assert(await ev('gFallback.querySelectorAll(".fallback-panel").length===3 && !!gFallback.querySelector("[data-trail]") && gProb.children.length>0'));
  await step(3);await click('gJump');assert(await ev('!!gFallback.querySelector(".forecast")&&!gFallback.querySelector("[data-path=truth]")'));
  await step(4);await click('gJump');await click('gReveal');assert(await ev('!!gFallback.querySelector("[data-path=truth]")'));
  await seek(1);
  assert(await ev('gFallback.querySelector("[data-replay-cursor]").cx.baseVal.value===gFallback.querySelector("[data-path=representative]").points[2].x && !!gFallback.querySelector("[data-actual-cursor]")'));
  await call('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected.identifier});
  checks.push('forced WebGL failure, recorded 2D fallback and GT reveal');
  assert.deepEqual(errors,[]);console.log(JSON.stringify({base,checks,errors},null,2));
}finally{ws.close();await fetch(cdp+'/json/close/'+tab.id);}
