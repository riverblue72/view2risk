import fs from 'node:fs/promises';
const root=process.env.V2R_CHECK_OUTPUT||'presentation/browser-evidence',host=process.env.V2R_PUBLIC_URL||'http://127.0.0.1:18779/presentation',cdp=process.env.V2R_CDP||'http://127.0.0.1:18776';
await fs.mkdir(root,{recursive:true});
const tab=await(await fetch(cdp+'/json/new?'+encodeURIComponent('about:blank'),{method:'PUT'})).json();
const ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
let id=0,pending=new Map(),errors=[],checks=[],networkFailures=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(p)m.error?p.reject(m.error):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);if(m.method==='Network.responseReceived'&&m.params.response.status>=400)networkFailures.push({url:m.params.response.url,status:m.params.response.status});};
function call(method,params={}){return new Promise((resolve,reject)=>{const n=++id,t=setTimeout(()=>reject(Error(method+' timeout')),45000);pending.set(n,{resolve:x=>{clearTimeout(t);resolve(x)},reject:x=>{clearTimeout(t);reject(x)}});ws.send(JSON.stringify({id:n,method,params}));});}
async function ev(expression){const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(expr,seconds=100){const end=Date.now()+seconds*1000;while(Date.now()<end){if(await ev(expr))return;await new Promise(r=>setTimeout(r,250));}throw Error('Timeout '+expr);}
async function check(name,expr){const x=await ev(expr);checks.push({name,passed:!!x});console.log(name,!!x);if(!x)throw Error(name);}
async function screenshot(name){await new Promise(r=>setTimeout(r,600));const s=await call('Page.captureScreenshot',{format:'png'});await fs.writeFile(root+'/'+name,Buffer.from(s.data,'base64'));}
async function route(hash){await ev(`location.hash=${JSON.stringify(hash)}`);await new Promise(r=>setTimeout(r,350));}
async function fullshot(name){const m=await call('Page.getLayoutMetrics');const q=m.cssContentSize;const s=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:q.width,height:Math.min(q.height,5000),scale:1}});await fs.writeFile(root+'/'+name,Buffer.from(s.data,'base64'));}


try{
await call('Runtime.enable');await call('Network.enable');await call('Network.setCacheDisabled',{cacheDisabled:true});await call('Page.enable');await call('Page.bringToFront');await call('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url:host+'/?case=o0008#/simulation'});await until('window.presentationViewerReady===true',220);
await check('Normal viewer opens with predictions','P_LIVE_STAGE===4&&!$("gt").checked');
await check('Play and slider are enabled','!$("play").disabled&&!$("time").disabled');
const start=await ev('({t,x:person.position.x,z:person.position.z,origin:packet.origin_s})');await ev('$("play").click()');await new Promise(r=>setTimeout(r,1800));const moved=await ev('({t,x:person.position.x,z:person.position.z,origin:packet.origin_s})');await ev('$("play").click()');
checks.push({name:'Actual time and pedestrian advance',passed:moved.t>start.t+.5&&Math.hypot(moved.x-start.x,moved.z-start.z)>.05,start,moved});if(!checks.at(-1).passed)throw Error('No real playback');
await check('Rolling origin advanced','packet.elapsed_s>=9&&!D_GUIDED');
await check('Right panel matches current origin','$("pCaseStamp").textContent.includes("origin +"+packet.elapsed_s+"s")');
await ev('$("pPinNow").click()');const pinned=await ev('t');await new Promise(r=>setTimeout(r,600));await check('Pin freezes the current origin','D_GUIDED&&!playing&&t==='+pinned);
await ev('$("time").value=9;$("time").dispatchEvent(new Event("input"))');await check('Seeking releases old anchor','Math.abs(t-9)<.025&&packet.elapsed_s===9&&!D_GUIDED');
await check('Saved DD probability used at replay origin','$("pRight").textContent.includes(PP(packet.conditions.clean.exit.model_probability_4s))&&$("pRight").textContent.includes("H1–H3은 NOT AVAILABLE")');
await ev('$("pCompletionModel").value="EA_M1__calibrated";$("pCompletionModel").dispatchEvent(new Event("change"))');await check('Missing AFT cannot reuse old origin','!dEvent()&&$("pRight").textContent.includes("NOT AVAILABLE")');
await ev('$("pCompletionModel").value="DDMDN";$("pCompletionModel").dispatchEvent(new Event("change"))');
await ev('$("time").value=$("time").min;$("time").dispatchEvent(new Event("input"))');await check('Preforecast period clears old values','!packet&&$("pRight").textContent.includes("유효한 예측 origin 없음")&&!ghost.isEnabled()');
await ev('$("time").value=8;$("time").dispatchEvent(new Event("input"));$("pPinNow").click()');await check('Back to matched original origin','packet.elapsed_s===8&&dEvent().uid==="o0008"');
await ev('$("pRevealGT").click()');await check('GT reveal separately enabled','P_LIVE_STAGE===5&&$("gt").checked');await ev('$("pRevealGT").click()');await check('GT can be hidden again','!$("gt").checked');
await ev('$("pCross").value="f1";$("pCross").dispatchEvent(new Event("change"))');const pending=await ev('$("pCases").value');await new Promise(r=>setTimeout(r,800));await check('Pending choice not overwritten by refresh','$("pCases").value==='+JSON.stringify(pending)+'&&caseData.crosswalk==="f2"');await ev('$("pCaseApply").click()');await until('!D_BUSY&&caseData.crosswalk==="f1"',120);await check('Apply updates actual case and view','P_LIVE_STAGE===4&&$("pCaseStamp").textContent.startsWith("f1")');
await ev('$("pCross").value="all";pCaseOptions();$("pCases").value=EXIT_DATA.cases.findIndex(c=>c.uid==="o0008");$("pCaseApply").click()');await until('!D_BUSY&&dEvent()?.uid==="o0008"',120);await fullshot('simulation_fixed_desktop.png');
for(const width of [756,390]){await call('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width===390});await ev('engine.resize()');await check('Layout '+width+' usable','document.documentElement.scrollWidth<=innerWidth&&document.querySelector("#uStage>.scene").getBoundingClientRect().width>300');if(width===390)await fullshot('simulation_fixed_mobile.png');}
await call('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url:host+'/presentation.html'});await until('window.presentationReady===true',220);await ev('pShow(3);pDemoStage(4)');const a=await ev('pSnapshot().c.origin_s');await ev('pDemoStage(5)');await check('Presentation still locks same origin','pSnapshot().c.origin_s==='+a+'&&document.querySelector("iframe").contentDocument.getElementById("play").disabled');

await check('Public case ID, relative origin, stored probability','P_STATE.c.event_id==="public-imptc-01"&&Math.abs(P_STATE.c.origin_s-8)<1e-5&&P_STATE.c.cdf.DDMDN[60]===.6625');
await call('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowLeft',code:'ArrowLeft'});await check('Presentation keyboard navigation','P_STAGE===4');
await call('Page.navigate',{url:host+'/methods.html'});await until('window.methodsReady===true&&document.querySelectorAll(".katex").length>0',90);for(let step=0;step<6;step++){await ev('mShow('+step+')');await check('Methods chapter '+step+' equations','document.querySelectorAll(".katex").length>0&&document.querySelectorAll(".katex-error").length===0');}await screenshot('methods_public.png');
await call('Page.navigate',{url:host+'/?case=o0008#/noise'});await until('window.presentationViewerReady===true&&uMatchedR()',180);
const fixed=await ev('({id:caseData.event_id,origin:packet.origin_s})');
for(const scenario of ['iid_0.5','iid_1','iid_2','correlated_1','dropout_1']){
await ev(`$('dNoiseScenario').value=${JSON.stringify(scenario)};$('dNoiseMode').value='side';dNoiseApply()`);
await check('Same origin / stored R '+scenario,`caseData.event_id===${JSON.stringify(fixed.id)}&&packet.origin_s===${fixed.origin}&&!!R_CURRENT.results[${JSON.stringify(scenario+'__rq')}]&&$('dNoiseProbabilities').textContent.includes(up(R_CURRENT.results[${JSON.stringify(scenario+'__rq')}].exit.probabilities['4']))`);
}
await screenshot('noise_public.png');
await check('Only allowlisted IMPTC cases','CONDITION_INDEX.length===3&&CONDITION_INDEX.every(c=>c.dataset==="IMPTC")&&R_INDEX.length===3');
for(const tab of ['trajectory','completion','exit','robustness','limitations']){await route('#/results/'+tab);await check('Results '+tab,'document.getElementById("uResultBody").innerText.length>50');}
await screenshot('results_public.png');
for(const old of ['#condition-analysis','#r-analysis','#clearance-aft','#exit-final']){await route(old);await check('Legacy route '+old,'document.body.innerText.length>1000');}
await route('#/simulation');await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await ev('engine.resize()');await check('Public mobile no overflow','document.documentElement.scrollWidth<=innerWidth');await screenshot('public_mobile.png');
await call('Page.navigate',{url:host+'/modeling.html'});await until('window.GUIDE_DATA_READY===true',60);await check('Modeling legacy page','document.body.innerText.includes("DD-MDN")');

const out={passed:checks.every(x=>x.passed)&&!errors.length&&!networkFailures.length,checks,errors,networkFailures};await fs.writeFile(root+'/browser_check.json',JSON.stringify(out,null,2));console.log(JSON.stringify(out));
}catch(e){await fs.writeFile(root+'/failure.json',JSON.stringify({message:e.message,checks,errors,networkFailures},null,2));await screenshot('failure.png');throw e;}finally{ws.close();}
