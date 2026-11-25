// Run against a static deployment and a running Chrome DevTools endpoint.
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';

const base=process.env.V2R_PUBLIC_URL||'http://127.0.0.1:19854/presentation';
const cdp=process.env.V2R_CDP||'http://127.0.0.1:19855';
const tab=await (await fetch(cdp+'/json/new?about:blank',{method:'PUT'})).json();
const ws=new WebSocket(tab.webSocketDebuggerUrl);
await new Promise(resolve=>ws.onopen=resolve);
const pending=new Map(), errors=[];
let id=0;
ws.onmessage=({data})=>{
  const m=JSON.parse(data);
  if(m.id){pending.get(m.id)?.(m);pending.delete(m.id);}
  if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);
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
  for(const [width,height] of [[1366,768],[390,844]]){
    await viewport(width,height);await goto('presentation.html#scene-1');
    await until('document.querySelector("#pProgress a")');
    for(let i=1;i<=8;i++){
      await until('document.querySelector("#pProgress a[aria-current]")?.textContent==="'+i+'"');
      assert(await ev('document.documentElement.scrollWidth<=innerWidth+1 && !document.querySelector("[role=alert]")'));
      if(i===4)for(const value of ['0.283','3.925','0.742','0.03472','0.33527','0.08594','81.1%','74.4%','96.05%','74.12%','78.51%','7.37','748.20','10.27'])assert((await ev('pScene.textContent')).includes(value),value);
      if(i===5)assert((await ev('pScene.textContent')).includes('2.063'));
      if(i===6)for(const value of ['1,113','2,322','2.19','0.059','393','0.05646','0.01635','0.10827','0.00618','71.0%','94.3%'])assert((await ev('pScene.textContent')).includes(value),value);
      if(i===7){await click('uqReveal');assert(await ev('!!document.querySelector("[data-path=truth]")'));await click('uqReveal');}
      if(i===8)break;
      await click('pNext');
    }
    checks.push('8 slides and embedded GT at '+width+'px');
  }
  await click('pPrev');await until('!!document.querySelector("#slideReplay")');
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowLeft'});await until('location.hash==="#scene-6"');
  await ev('history.back()');await until('location.hash==="#scene-7"');
  await ev('document.querySelector("#pProgress a").click()');await until('location.hash==="#scene-1"');
  await click('pNotesButton');assert(await ev('pNotes.hidden===false'));
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape'});assert(await ev('pNotes.hidden'));
  await call('Page.bringToFront');
  const fsSupported=await ev('document.fullscreenEnabled');
  if(fsSupported) {
    const fsClick=async()=>{
      const {x,y}=await ev("(()=>{const el=PS('pFullscreen');el.scrollIntoView();const r=el.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()");
      for(const type of ['mousePressed','mouseReleased'])await call('Input.dispatchMouseEvent',{type,x,y,button:'left',clickCount:1});
    };
    await fsClick();await until('!!document.fullscreenElement');await fsClick();await until('!document.fullscreenElement');
  }
  console.log('Fullscreen API supported:',fsSupported);
  checks.push('previous, keyboard, browser history, numbered navigation, notes and fullscreen');
  await viewport(1366,768);await goto('demo.html');await until('document.querySelector("#uqCase")');
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
      document.querySelector('.direct summary').click();
      if(!document.querySelector('.direct[open]')||document.querySelector('.direct').textContent.includes('자료 없음'))throw Error('AFT unavailable');
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
  assert.deepEqual(errors,[]);console.log(JSON.stringify({base,checks,errors},null,2));
  if(process.env.V2R_SCREENSHOT){
    await viewport(1366,768);await goto('presentation.html#scene-7');await until('document.querySelector(".forecast")');
    const shot=await call('Page.captureScreenshot',{format:'png'});await writeFile(process.env.V2R_SCREENSHOT,Buffer.from(shot.data,'base64'));
  }
} finally {ws.close();await fetch(cdp+'/json/close/'+tab.id);}
