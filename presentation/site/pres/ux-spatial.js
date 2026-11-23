'use strict';
// A single top-down coordinate frame, fixed across scenario / visibility / H changes.
function uxSpatial(s,scenario,modes,h,truth){const g=s.geometry,A=V2R.boundary(g,'end_A'),B=V2R.boundary(g,'end_B'),r=s.r,hi=h*2-1;
 if(!s.rBounds){const pts=[...A,...B,...s.clean.input.observed_xy];for(const v of Object.values(r.results)){pts.push(...v.input.observed_xy,...(v.hypotheses_xy?.[0]||[]));for(const region of v.regions||[])for(const polygon of region?.['0.95']||[])pts.push(...polygon);}const finite=pts.filter(x=>x?.length===2&&x.every(Number.isFinite));const lo=[0,1].map(k=>Math.min(...finite.map(p=>p[k]))-1),up=[0,1].map(k=>Math.max(...finite.map(p=>p[k]))+1);s.rBounds={lo,up};}
 const {lo,up}=s.rBounds,W=740,H=440,scale=Math.min(620/(up[0]-lo[0]),320/(up[1]-lo[1])),ox=60+(620-scale*(up[0]-lo[0]))/2,oy=380-(320-scale*(up[1]-lo[1]))/2,X=p=>ox+(p[0]-lo[0])*scale,Y=p=>oy-(p[1]-lo[1])*scale;
 const line=(pts,col,width=2,dash='')=>`<polyline fill="none" stroke="${col}" stroke-width="${width}" ${dash?'stroke-dasharray="'+dash+'"':''} points="${pts.filter(p=>p?.length===2&&p.every(Number.isFinite)).map(p=>X(p)+','+Y(p)).join(' ')}"/>`;
 let svg=`<svg class="ux-r-map" viewBox="0 0 ${W} ${H}" role="img" aria-label="같은 XY 축과 미터 축척에서 비교한 저장 경로" data-bounds="${PE(JSON.stringify(s.rBounds))}"><rect x="0" y="0" width="740" height="440" fill="#f6f9fb"/>`;
 svg+=`<polygon fill="#dce9ec" points="${[...A,...[...B].reverse()].map(p=>X(p)+','+Y(p)).join(' ')}"/>`;
 for(const [p,label,col] of [[A,s.c.direction===1?'Entry':'Exit',s.c.direction===1?'#62849b':'#d96a35'],[B,s.c.direction===1?'Exit':'Entry',s.c.direction===1?'#d96a35':'#62849b']]){svg+=line(p,col,3)+`<text x="${X(p[10])+7}" y="${Y(p[10])-6}" fill="${col}">${label}</text>`;}
 for(const mode of modes){const v=r.results[mode==='clean'?'clean':scenario+'__'+mode];if(!v)continue;const col=C_R[mode][1];svg+=`<g data-mode="${mode}">`+line(v.input.observed_xy,col,2,'2 3')+line([v.input.translation,...(v.hypotheses_xy?.[0]||[]).slice(0,hi+1)],col,2.6);for(const p of v.regions?.[hi]?.['0.95']||[])svg+=line(p,col,1.6,'6 4');svg+='</g>';}
 svg+=line(s.clean.input.observed_xy,'#2470c6',3);const cur=s.clean.input.observed_xy.at(-1);svg+=`<circle cx="${X(cur)}" cy="${Y(cur)}" r="5" fill="#18354c"/>`;if(truth)svg+=line([cur,...s.f.future_GT_xy.slice(0,hi+1)],'#c44178',3.5);
 const meter=Math.max(1,Math.pow(10,Math.floor(Math.log10(100/scale)))) ;svg+=`<path d="M55 405h${meter*scale}" stroke="#18354c" stroke-width="3"/><text x="55" y="429">${meter} m · world XY · +${h}초 · 모든 조건에 같은 축척</text></svg>`;return svg;
}
