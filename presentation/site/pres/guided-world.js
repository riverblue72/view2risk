'use strict';

// The deck and the original explorer call app.js's initScene. Only the replay clock
// and forecast layers differ. All geometry below is in the explorer's world XY (m).
function guidedWorld(canvas, s, tick) {
  DATA=V2R.catalog;
  caseData=s.c;
  initScene(canvas,tick);
  camera.inputs.removeByType('ArcRotateCameraKeyboardMoveInput');
  const resize=new ResizeObserver(()=>engine.resize());
  resize.observe(canvas);
  const C3=UQ.colors, amber='#d58805';
  const keep=[], layers=[];
  let boundaryExit, historyKey='', lastIndex=-1;
  let trail=null;
  const scene=sc;
  let inputRing=null;
  const forecastPerson=person.clone('forecast pedestrian');
  const forecastMaterial=material(C3.future,.86);
  forecastMaterial.emissiveColor=color(C3.future).scale(.4);
  for(const part of forecastPerson.getChildMeshes()){part.material=forecastMaterial;part.isPickable=false;}
  forecastPerson.setEnabled(false);
  function stroke(name,xy,hex,radius,height,alpha=1,bag=layers) {
    if(xy.length<2)return;
    const m=BABYLON.MeshBuilder.CreateTube(name,{path:xy.map(([x,y])=>new BABYLON.Vector3(x,height,y)),radius,tessellation:6,cap:BABYLON.Mesh.CAP_ALL},scene);
    m.material=material(hex,alpha);
    m.material.emissiveColor=color(hex).scale(.52);
    m.isPickable=false;bag.push(m);return m;
  }
  // Rasterise the saved contours with the even-odd fill rule. This preserves
  // disconnected components, concavities and holes on one horizontal plane.
  function fillContours(contours,level) {
    if(!contours.length)return;
    const points=contours.flat();
    const bounds=[0,1].map(k=>[Math.min(...points.map(p=>p[k]))-.05,Math.max(...points.map(p=>p[k]))+.05]);
    const [[x0,x1],[z0,z1]]=bounds;
    const tex=new BABYLON.DynamicTexture('HDR '+level,512,scene,false);
    tex.hasAlpha=true;
    const ctx=tex.getContext();
    ctx.beginPath();
    for(const poly of contours) {
      poly.forEach(([x,z],i)=>ctx[i?'lineTo':'moveTo']((x-x0)*512/(x1-x0),(z1-z)*512/(z1-z0)));
      ctx.closePath();
    }
    ctx.fillStyle=C3.future;ctx.fill('evenodd');tex.update();
    const ground=BABYLON.MeshBuilder.CreateGround('HDR '+level,{width:x1-x0,height:z1-z0},scene);
    ground.position.set((x0+x1)/2,level==='0.95'?.044:.05,(z0+z1)/2);
    const mat=material('#ffffff',level==='0.95'?.24:.44);
    mat.disableLighting=true;mat.emissiveColor=BABYLON.Color3.White();mat.diffuseTexture=tex;
    mat.useAlphaFromDiffuseTexture=true;mat.backFaceCulling=false;ground.material=mat;
    ground.alphaIndex=level==='0.95'?0:1;ground.isPickable=false;layers.push(ground);
    contours.forEach(path=>stroke('contour '+level,[...path,path[0]],level==='0.95'?'#9281dc':'#5943ad',level==='0.95'?.026:.038,.083));
  }
  function clear(bag){bag.splice(0).forEach(mesh=>mesh.dispose(false,true));}
  function bounds(data){
    clear(keep);boundaryMeshes.splice(0).forEach(mesh=>mesh.dispose(false,true));
    const g=data.geometry;
    for(const [idx,end] of (data.c.direction===1?['end_A','end_B']:['end_B','end_A']).entries()){
      const xy=V2R.boundary(g,end),hex=idx?amber:'#336386';
      const mesh=stroke(idx?'Exit':'Entry',xy,hex,.075,.09,1,keep);
      if(idx)boundaryExit=mesh;
      label(idx?'EXIT':'ENTRY',[xy[0][0]-g.normal[0]*.65,xy[0][1]-g.normal[1]*.65],hex);
    }
  }
  function view(data,kind="crossing",st=null){
    caseData=data.c;resetCamera();
    const dir=data.c.direction,g=data.geometry;
    // Side-on angle keeps longitudinal progress visible across the wide panel.
    camera.alpha=Math.atan2(dir*g.axis[1],dir*g.axis[0])+Math.PI/2;
    camera.beta=kind==='crossing'?.91:.018;
    const span=Math.max(10,g.nominal_length_m+5);
    const aspect=canvas.clientWidth/Math.max(1,canvas.clientHeight);
    camera.radius=Math.max(15,span/(2*Math.tan(camera.fov/2)*Math.min(2.15,aspect)),span*.76);
    if(st?.stage===0){
      const edges=['end_A','end_B'].flatMap(e=>V2R.boundary(g,e));
      const all=[...edges,...data.c.actual_observations.xy];
      if(kind==='full'){
        all.push(...uqComparisonExtent(st).all);
        for(const f of data.c.forecasts){
          const r=f.conditions.clean,i=r.future_times_s.indexOf(st.h);
          all.push(...r.regions[i]['0.95'].flat(),...r.hypotheses_xy.flatMap(path=>path.slice(0,i+1)));
        }
      }
      const axes=[g.axis,g.normal];
      const limits=axes.map(a=>{const v=all.map(p=>a[0]*p[0]+a[1]*p[1]);return [Math.min(...v),Math.max(...v)];});
      const mid=limits.map(([lo,hi])=>(lo+hi)/2),half=limits.map(([lo,hi])=>(hi-lo)/2);
      camera.target.set(mid[0]*g.axis[0]+mid[1]*g.normal[0],0,mid[0]*g.axis[1]+mid[1]*g.normal[1]);
      const distance=(Math.max((half[0]+1)/aspect,half[1]+2))/Math.tan(camera.fov/2)+half[1]+2;
      camera.upperRadiusLimit=Math.max(130,distance*1.1);camera.radius=Math.max(15,distance);
    }
    if(kind==='full'&&st?.stage>=3){
      const {all}=uqComparisonExtent(st);
      const mid=[0,1].map(k=>(Math.min(...all.map(p=>p[k]))+Math.max(...all.map(p=>p[k])))/2);
      const radius=Math.max(...all.map(p=>Math.hypot(p[0]-mid[0],p[1]-mid[1])));
      camera.target.set(mid[0],0,mid[1]);
      const distance=(radius+1)/Math.sin(camera.fov/2)/Math.min(1,aspect);
      camera.upperRadiusLimit=Math.max(130,distance*1.1);camera.radius=distance;
    }
    camera.inertialAlphaOffset=camera.inertialBetaOffset=camera.inertialRadiusOffset=0;
  }
  function overlay(st){
    const {data,stage,mode,scenario,h,truth,result}=st;
    clear(layers);inputRing=null;historyKey='';lastIndex=-1;
    boundaryExit.material.emissiveColor=color(amber).scale(stage===4?1:.5);
    if(stage===1)return;
    const xy=result.input.observed_xy;
    const noisy=data.r.results[scenario+'__noisy'], corrected=data.r.results[scenario+'__filtered_mean'];
    const filter=corrected.filter, simultaneous=stage===2&&st.compare;
    if(mode!=='clean'||simultaneous)stroke('reference history',data.clean.input.observed_xy,C3.clean,.044,.125);
    if(mode==='filtered_mean'||(simultaneous&&mode!=='noisy'))
      stroke('noisy context',noisy.input.observed_xy,C3.noisy,.039,.145,.62);
    if(simultaneous&&mode!=='filtered_mean')
      stroke('corrected context',corrected.input.observed_xy,C3.filtered_mean,.055,.165);
    if(stage===2){
      if((mode!=='clean'||simultaneous)&&filter?.filter_R){
        const centre=noisy.input.observed_xy[filter.observed_points-1];
        stroke('measurement ellipse',uqEllipse(filter.filter_R,centre),C3.noisy,.025,.10);
      }
      const shown=mode==='noisy'?xy.slice(0,filter.observed_points):xy;
      for(const pt of shown){
        const m=BABYLON.MeshBuilder.CreateSphere('observation',{diameter:.14,segments:8},scene);
        m.position.set(pt[0],.22,pt[1]);m.material=material(C3[mode]);layers.push(m);
      }
    }
    stroke('model input',xy,C3[mode],mode==='filtered_mean'?.073:.052,.18);
    const last=xy.at(-1);
    const ring=BABYLON.MeshBuilder.CreateTorus('observed endpoint',{diameter:.56,thickness:.085,tessellation:32},scene);
    ring.position.set(last[0],.24,last[1]);ring.material=material(C3[mode]);ring.material.emissiveColor=color(C3[mode]).scale(.45);
    layers.push(ring);inputRing=ring;
    if(stage<3)return;
    const end=result.future_times_s.indexOf(h), regions=result.regions[end];
    ['0.95','0.68'].forEach(level=>fillContours(regions[level],level));
    const best=result.hypothesis_confidence_scores.indexOf(Math.max(...result.hypothesis_confidence_scores));
    result.hypotheses_xy.forEach((path,i)=>stroke(i===best?'representative':'candidate',[xy.at(-1),...path.slice(0,end+1)],i===best?C3.future:'#907dd0',i===best?.045:.016,i===best?.14:.105,i===best?1:.65));
    if(truth)stroke('actual future',[data.clean.input.observed_xy.at(-1),...data.r.future_GT_xy.slice(0,end+1)],C3.gt,.053,.185);
  }
  function cursor(st,sample){
    forecastPerson.setEnabled(st.stage>=3&&sample.index>0);
    if(st.stage===2&&inputRing)inputRing.position.set(sample.point[0],.24,sample.point[1]);
    if(st.stage<3||sample.index===0)return;
    const [x,z]=sample.point;
    const previous=sample.index===1?st.result.input.observed_xy.at(-1):st.representative[sample.index-2];
    forecastPerson.position.set(x,0,z);
    forecastPerson.rotation.y=Math.atan2(x-previous[0],z-previous[1]);
  }
  function pose(st,idx,visible){
    const {data,stage,time,running}=st;
    const rec=data.c.actual_observations;
    person.setEnabled(visible);
    if(!visible)return;
    const xy=rec.xy[idx],prior=rec.xy[Math.max(0,idx-1)];
    person.position.set(xy[0],0,xy[1]);
    if(idx>0&&rec.elapsed_s[idx]-rec.elapsed_s[idx-1]<.061){
      const dx=xy[0]-prior[0],dz=xy[1]-prior[1];
      if(Math.hypot(dx,dz)>.001)person.rotation.y=Math.atan2(dx,dz);
    }
    if(idx!==lastIndex&&running&&lastIndex>=0&&idx>lastIndex&&idx-lastIndex<10)legPhase+=BABYLON.Vector2.Distance(BABYLON.Vector2.FromArray(rec.xy[lastIndex]),BABYLON.Vector2.FromArray(xy))*Math.PI*2/.75;
    for(const m of person.getChildren())if(m.name==='leg'||m.name==='arm')
      m.rotation.x=(running?Math.sin(legPhase)*.32:0)*Math.sign(m.position.x)*(m.name==='arm'?-1:1);
    lastIndex=idx;
    const key=stage<=1?data.r.uid+':'+idx:'off';
    if(historyKey===key)return;
    historyKey=key;trail?.dispose(false,true);trail=null;
    if(stage<=1){
      let first=idx;
      while(first>0&&(stage===0||time-rec.elapsed_s[first-1]<=3.2)&&rec.elapsed_s[first]-rec.elapsed_s[first-1]<.061)first--;
      if(first<idx){const bag=[];trail=stroke('recorded past',rec.xy.slice(first,idx+1),C3.clean,.047,.115,1,bag);}
    }
  }
  bounds(s);view(s);
  return {overlay,pose,cursor,view,change(data){bounds(data);view(data);legPhase=0;},dispose(){
    resize.disconnect();engine.stopRenderLoop();scene.dispose();engine.dispose();boundaryMeshes=[];objects=[];
  }};
}
