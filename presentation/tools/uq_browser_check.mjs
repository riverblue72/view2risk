// Run against a static deployment and a running Chrome DevTools endpoint.
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';

const base=process.env.V2R_PUBLIC_URL||'http://127.0.0.1:19864/presentation';
const cdp=process.env.V2R_CDP||'http://127.0.0.1:19865';
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
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');
  await viewport(1440,900);await goto('presentation.html#scene-1');
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
  const ready3=()=>until('document.querySelector(".guided")?.dataset.renderer==="babylon" && !!sc.getMeshByName("actualMap") && sc.isReady()');
  const layout=()=>ev(`(()=>{
    const rect=id=>PS(id).getBoundingClientRect();
    const next=rect('gNext'), footer=document.querySelector('.deck-footer')?.getBoundingClientRect();
    return {width:innerWidth,height:innerHeight,canvas:[rect('gCanvas').width,rect('gCanvas').height],bottom:next.bottom,
      fits:document.documentElement.scrollWidth<=innerWidth+1 && (!footer||next.bottom<=footer.top+1) && next.bottom<=innerHeight &&
        [...document.querySelectorAll('.guided button:not(:disabled),.guided select:not(:disabled),#gTime:not(:disabled)')].filter(el=>el.offsetWidth).every(el=>{
          const r=el.getBoundingClientRect(), hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return hit===el||el.contains(hit);})};
  })()`);
  for(let n=1;n<=8;n++){
    await ev('location.hash="#scene-'+n+'"');await until('document.querySelector("#pProgress a[aria-current]").textContent==="'+n+'"');
    if(n===7){await ready3();await set('gTime',7);await ev('gTime.dispatchEvent(new Event("input"))');}
    await capture('scene-'+n);
  }
  await ev('location.hash="#scene-7"');await ready3();
  for(const [w,h] of [[1920,1080],[1440,900],[1366,768]]){
    await viewport(w,h);
    for(const n of [1,2,3,4]){
      await step(n);if(n===4)await click('gReveal');await until('sc.isReady()');
      const box=await layout();if(n===4)console.log('layout',box);assert(box.fits,JSON.stringify(box));
    }
  }
  await call('Page.bringToFront');
  const fsClick=async()=>{
    const {x,y}=await ev("(()=>{const r=PS('pFullscreen').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()");
    for(const type of ['mousePressed','mouseReleased'])await call('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});
  };
  await fsClick();await until('!!document.fullscreenElement');assert((await layout()).fits);await fsClick();await until('!document.fullscreenElement');
  await viewport(1440,900);await click('gReset');
  await click('gPlay');await until('Number(gTime.value)>Number(gTime.min)+.2');await click('gPlay');
  const paused=await ev('gTime.value');await new Promise(r=>setTimeout(r,240));assert.equal(await ev('gTime.value'),paused);
  await ev('gTime.value=7.4;gTime.dispatchEvent(new Event("input"))');await capture('stage-1');
  await click('gPlay');await until('Number(gTime.value)>=8 && gPlay.textContent.includes("재생")');
  assert(await ev('!sc.getMeshByName("actual future")&&!sc.getMeshByName("representative")&&!gProb.textContent'));
  const pose=()=>ev('person.position.asArray()');
  assert(await ev('JSON.stringify([person.position.x,person.position.z])===JSON.stringify(caseData.actual_observations.xy[caseData.actual_observations.elapsed_s.findLastIndex(t=>t<=+gTime.value+1e-6)])'));
  const atOrigin=await pose();const cam=()=>ev('[camera.alpha,camera.beta,camera.radius,...camera.target.asArray()]');
  const locked=await cam();
  await click('gNext');await set('gMode','noisy');await until('sc.isReady()');await capture('stage-2');
  assert(await ev('!!sc.getMeshByName("measurement ellipse") && !sc.getMeshByName("representative")'));assert.deepEqual(await pose(),atOrigin);
  await click('gNext');await set('gMode','filtered_mean');await until('sc.isReady()');await capture('stage-3');
  assert(await ev('!!sc.getMeshByName("HDR 0.95") && !!sc.getMeshByName("HDR 0.68") && !sc.getMeshByName("actual future") && !gProb.textContent'));
  await click('gNext');assert(await ev('!gOutcome.textContent && !sc.getMeshByName("actual future")'));await click('gReveal');
  await until('sc.isReady()');await capture('stage-4');
  let combos=0;
  for(const uid of ['o0008','o0000','o0011']){
    await set('gCase',uid);await until('document.querySelector(".guided").dataset.uid==="'+uid+'"&&!document.querySelector(".guided").inert');
    await step(4);await click('gReveal');
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
        set('gNoise',noise);set('gMode',mode);set('gH',h);
        const r=s.r.results[mode==='clean'?'clean':noise+'__'+mode],i=r.future_times_s.indexOf(h),best=r.hypothesis_confidence_scores.indexOf(Math.max(...r.hypothesis_confidence_scores));
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
    assert(await ev('!sc.getMeshByName("actual future") && !gOutcome.textContent && +gTime.value===+gTime.min'));
  }
  assert.equal(combos,180);await set('gCase','o0008');await until('gCase.value==="o0008"&&!document.querySelector(".guided").inert');
  await click('gTop');assert(await ev('camera.beta<.05'));await click('gCamera');assert.deepEqual(await cam(),locked);
  await click('pPrev');await until('location.hash==="#scene-6" && !PS("gCanvas")');
  await ev('history.back()');await ready3();await click('pNotesButton');assert(await ev('!pNotes.hidden'));await click('pNotesButton');
  await step(3);await set('gMode','noisy');await set('gH',4);await click('gTop');
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
  checks.push('8 slides, four guided stages, all three requested viewports, fullscreen, navigation, camera and playback');
  checks.push('180 WebGL case/condition/noise/horizon combinations matched cached probabilities, representative, HDR and GT vertices');
  await goto('demo.html');await ready3();await ev('PS("extra2D").open=true');await until('document.querySelector("#uqCase")');
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
  await goto('presentation.html#scene-7');await until('document.querySelector(".guided")?.dataset.renderer==="2d"');
  await step(3);assert(await ev('!!gFallback.querySelector(".forecast")&&!gFallback.querySelector("[data-path=truth]")'));
  await step(4);await click('gReveal');assert(await ev('!!gFallback.querySelector("[data-path=truth]")'));
  await call('Page.removeScriptToEvaluateOnNewDocument',{identifier:injected.identifier});
  checks.push('forced WebGL failure, recorded 2D fallback and GT reveal');
  assert.deepEqual(errors,[]);console.log(JSON.stringify({base,checks,errors},null,2));
}finally{ws.close();await fetch(cdp+'/json/close/'+tab.id);}
