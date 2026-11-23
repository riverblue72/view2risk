import fs from 'node:fs/promises';
const root=process.env.V2R_CHECK_OUTPUT||'presentation/redesign-evidence',host=process.env.V2R_PUBLIC_URL||'http://127.0.0.1:18779/presentation',cdp='http://127.0.0.1:18776';
const tab=await(await fetch(cdp+'/json/new?'+encodeURIComponent('about:blank'),{method:'PUT'})).json();
const ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
let id=0,pending=new Map(),errors=[],checks=[],networkFailures=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(p)m.error?p.reject(m.error):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);if(m.method==='Network.responseReceived'&&m.params.response.status>=400)networkFailures.push({url:m.params.response.url,status:m.params.response.status});};
function call(method,params={}){return new Promise((resolve,reject)=>{const n=++id,t=setTimeout(()=>reject(Error(method+' timeout')),45000);pending.set(n,{resolve:x=>{clearTimeout(t);resolve(x)},reject:x=>{clearTimeout(t);reject(x)}});ws.send(JSON.stringify({id:n,method,params}));});}
async function ev(expression){const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(expr,seconds=100){const end=Date.now()+seconds*1000;while(Date.now()<end){if(await ev(expr))return;await new Promise(r=>setTimeout(r,250));}throw Error('Timeout '+expr);}
async function check(name,expr){const x=await ev(expr);checks.push({name,passed:!!x});console.log(name,!!x);if(!x)throw Error(name);}
async function screenshot(name){await new Promise(r=>setTimeout(r,600));const s=await call('Page.captureScreenshot',{format:'png'});await fs.writeFile(root+'/screenshots/'+name,Buffer.from(s.data,'base64'));}
async function route(hash){await ev(`location.hash=${JSON.stringify(hash)}`);await new Promise(r=>setTimeout(r,350));}
async function fullshot(name){const m=await call('Page.getLayoutMetrics');const q=m.cssContentSize;const s=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:q.width,height:Math.min(q.height,5000),scale:1}});await fs.writeFile(root+'/screenshots/'+name,Buffer.from(s.data,'base64'));}



async function captureElement(selector,name){const box=await ev(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return {x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height};})()`);const s=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{...box,scale:1}});await fs.writeFile(root+'/screenshots/'+name,Buffer.from(s.data,'base64'));}
async function change(id,value){await ev(`document.getElementById(${JSON.stringify(id)}).value=${JSON.stringify(value)};document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event('change'))`);await until('!C_BUSY&&window.compareReady',120);}
await fs.mkdir(root+'/screenshots',{recursive:true});
try{
await call('Runtime.enable');await call('Network.enable');await call('Network.setCacheDisabled',{cacheDisabled:true});await call('Page.enable');await call('Page.bringToFront');
for(const width of [1440,1280,390]){
await call('Emulation.setDeviceMetricsOverride',{width,height:width===1280?720:900,deviceScaleFactor:1,mobile:width===390});
await call('Page.navigate',{url:host+'/methods.html'});await until('window.methodsReady');
await check('Architecture readable at '+width,'document.querySelector(".scientific-architecture").scrollWidth<=document.querySelector(".scientific-architecture").clientWidth+1&&document.documentElement.scrollWidth<=innerWidth');
await check('Two parallel predictors '+width,'document.querySelectorAll(".arch-model").length===2&&document.querySelectorAll(".arch-support p").length===2');
await captureElement('#mArchitecture','clean_architecture_'+width+'.png');
for(let i=0;i<6;i++){await ev('mShow('+i+');document.querySelectorAll("#mContent details").forEach(e=>e.open=true)');await check('Math and text chapter '+i+' width '+width,'!document.querySelector(".katex-error")&&!document.body.innerText.includes("�")&&document.documentElement.scrollWidth<=innerWidth');}
await ev('mShow(1);document.getElementById("mContent").scrollIntoView()');await screenshot('clean_text_'+width+'.png');
await call('Page.navigate',{url:host+'/presentation.html'});await until('window.presentationReady');await ev('pShow(2)');
await check('Presentation architecture layout '+width,width===390?'document.documentElement.scrollWidth<=innerWidth':'document.querySelector(".scientific-architecture").getBoundingClientRect().bottom<document.querySelector(".p-deck-footer").getBoundingClientRect().top');
await screenshot('clean_presentation_'+width+'.png');
}
await call('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});await call('Page.navigate',{url:host+'/compare.html'});await until('window.compareReady',180);await check('Compare same origin unaffected','compareSnapshot.event_id==="public-imptc-01"&&compareSnapshot.origin_s===8');await check('Compare math intact','!document.querySelector(".katex-error")&&document.querySelectorAll(".katex").length>=3');
await ev('document.fonts.ready');await check('Loaded math fonts healthy','[...document.fonts].every(f=>f.status!=="error")');
const out={passed:checks.every(x=>x.passed)&&!errors.length&&!networkFailures.length,checks,errors,networkFailures};await fs.writeFile(root+'/typography_check.json',JSON.stringify(out,null,2));console.log(JSON.stringify(out));
}catch(e){await screenshot('typography_failure.png');console.error(e);process.exitCode=1;}finally{ws.close();}
