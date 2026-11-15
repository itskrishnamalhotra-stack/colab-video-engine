// Reusable horror staging vocabulary. The story supplies decisions and coverage;
// these routines supply deterministic, contact-observable physical performances.
import * as THREE from 'three';
import {DirectionalActor as Actor,loadActors} from './directional_actor.js';
import {V,box,card,words} from './world.js';
import {hospital} from './hospital.js';
import {stairGait} from './stair_gait.mjs';
import {pathState} from './directional_motion.mjs';
import {EntityRegistry} from './entity_registry.mjs';
import {furnishHospital} from './hospital_continuity.js';
import {makeFlashlight,makeRadio,makeCamera,makeCameraBag,makeTripod,makeEquipmentCase} from './equipment.js';
import {hospitalSideSets,makeGurney,makePhone,makeMonitor} from './hospital_props.js';
const clamp=x=>Math.max(0,Math.min(1,x)),sm=x=>{x=clamp(x);return x*x*(3-2*x);};
const step=(u,a=.15,b=.75)=>sm((u-a)/(b-a));
export async function hospitalPerformance(E){
 await loadActors();const lobby=hospital(E),side=hospitalSideSets(E);furnishHospital(lobby,side);
 const sets={lobby,service:side.service,outside:side.out,ward:side.ward,edit:side.edit};
 const registry=new EntityRegistry();lobby.table.name='reception_table';lobby.cable.name='stair_cable';lobby.cable.userData.optionalVisibility=true;
 for(const [name,set] of Object.entries(sets)){
  registry.define(name+'_room',{factory:()=>set.scene,required:name==='lobby'?['reception_table','stair_cable']:[]});
  await registry.spawn(name+'_room');
 }
 lobby.table.children[0].name='table_surface';
 registry.define('center_table',{factory:()=>lobby.table,required:['table_surface']});await registry.spawn('center_table');
 const appearance={mara:{coat:'#7C8F7B',hat:'#273B40',look:{hat:'cap',pattern:'trench',neck:'collar',extra:[],detail:'tailored',patchCol:'#C4B68D'}},
 nia:{coat:'#687F97',hat:'#59473D',look:{hat:'bun',pattern:'trench',neck:'collar',extra:['glasses'],detail:'tailored',patchCol:'#B6C9C1'}},
 ben:{coat:'#C08050',hat:'#8E5C3B',look:{hat:'beanie',pattern:'trench',neck:'collar',extra:[],detail:'tailored',patchCol:'#E2CB69'}}};
 const cast={};
 for(const name of ['mara','nia','ben','impostor']){
  registry.define(name,{factory:()=>new Actor(lobby.scene,{id:name,...appearance[name==='impostor'?'ben':name]}),required:['character_body','wardrobe_and_face',name+'.l_grip',name+'.r_grip']});
  cast[name]=await registry.spawn(name);
 }
 const {mara,nia,ben,impostor}=cast;
 const bags=[makeCameraBag(),makeCameraBag()];ben.group.add(bags[0]);impostor.group.add(bags[1]);bags.forEach(b=>b.position.set(-.29,.75,.07));
 const torch=makeFlashlight({range:6,angle:.18,power:16}),radio=makeRadio(),offRadio=makeRadio();
 const camera=makeCamera(),tripod=makeTripod(),downCamera=makeCamera(),downTripod=makeTripod(),gear=makeEquipmentCase();
 const phoneMara=makePhone(lobby.scene,{color:'#344A67'}),phoneNia=makePhone(lobby.scene,{color:'#657754'}),monitor=makeMonitor(lobby.scene,{appearance:ben.toon.look});let phone=phoneNia;
 phoneMara.name='mara_phone';phoneNia.name='nia_phone';phoneMara.userData.identityOwner='mara';phoneNia.userData.identityOwner='nia';camera.name='upper_camera';downCamera.name='downstairs_camera';
 const blanket=box(ben.group,.63,.92,.035,'#718C91',0,.80,.045);blanket.name='rescue_blanket';blanket.visible=false;
 const cart=makeGurney(lobby.scene),paper=card(lobby.scene,words(['SERVICE EXIT','RECEPTION  >  LAUNDRY'],{paper:'#C7CCB1',ink:'#35504C'}),.48,.33,0,0,0);
 const laptop=makeMonitor(lobby.scene,{portable:true,appearance:ben.toon.look});
 const warning=card(lobby.scene,words(['DO NOT','ANSWER'],{paper:'#C7CCB1',ink:'#294447'}),.43,.29,0,0,0);
 const props={torch,radio,offRadio,camera,upperCamera:camera,downCamera,tripod,downTripod,gear,phone,phoneMara,phoneNia,monitor,laptop,cart,paper,warning};
 let scene=lobby.scene,contacts={},mounted=false,playing=false,aim=V(-2.6,.8,-2.5),activeRow;
 const pose=(a,t,options={})=>a.pose(t,{mood:'worried',left:[.28,1.01,.24],right:[-.27,1.02,.28],...options});
 function place(a,x=0,y=0,z=0,yaw=0){a.group.visible=true;a.at(x,y,z,yaw);return a;}
 function travel(a,from,to,u,t,options={}){
  const motion=pathState(from,to,u,{turnFrom:options.turnFrom??0,turnFraction:.12});
  place(a,...motion.position,motion.yaw);
  pose(a,t,{...options,walking:motion.movement>0&&motion.movement<1,distance:motion.distance,
   walkWeight:Math.min(1,motion.movement/.10,(1-motion.movement)/.10),expression:options.expression||'concern'});
  a.group.userData.headingDot=Math.hypot(to[0]-from[0],to[2]-from[2])<1e-8?1:
   (Math.sin(motion.yaw)*(to[0]-from[0])+Math.cos(motion.yaw)*(to[2]-from[2]))/Math.hypot(to[0]-from[0],to[2]-from[2]);
  if(!motion.movement)a.group.userData.headingDot=1;
  return motion;
 }
 function hold(a,p,hand='r'){p.visible=true;a.grip(p,hand);}
 function worldGrip(a,p,point,hand='r',t=0,options={}){
  a.group.updateWorldMatrix(true,false);pose(a,t,{...options,[hand==='r'?'right':'left']:a.group.worldToLocal(point.clone()).toArray()});
  if(p)hold(a,p,hand);
 }
 function receiver(t,rx){hold(mara,radio,'r');radio.setState({power:true,rx});}
 function flashlight(){hold(mara,torch,'l');torch.setEnabled(true);}
 function body(t,{onCart=false}={}){
  if(onCart){cart.visible=true;cart.patient.add(ben.group);place(ben,0,0,0);ben.lieDown(t,{pitch:Math.PI/2});}
  else{place(ben,-2.65,.29,-1.73);ben.lieDown(t,{pitch:-1.02});}
  blanket.visible=activeRow.index>=46;ben.toon.tint('#C4CFC3');ben.group.add(offRadio);offRadio.visible=true;offRadio.position.set(-.24,.85,.09);offRadio.rotation.set(0,0,0);offRadio.setState({power:false});
 }
 function pair(t,{walk=0,shift=0,z=0}={}){
  const yaw=walk>.05?Math.PI+Math.atan2(-shift,1):.16;
  place(mara,-1.05+shift,0,z+.25,yaw);place(nia,1.10+shift,0,z-.10,yaw);
  const distance=Math.hypot(shift,activeRow.index<6?.6-z:z);
  pose(mara,t,{walking:walk>.05,distance,walkWeight:walk,expression:'concern',headYaw:-.1,right:[-.25,1.08,.30],left:[.32,1.02,.34]});
  pose(nia,t,{walking:walk>.05,distance:distance+.22,walkWeight:walk,expression:'concern',headYaw:.1,left:[.25,1.02,.29],right:[-.26,1.04,.30]});flashlight();
  if(activeRow.index>=9||activeRow.index<3){mara.group.add(radio);radio.visible=true;radio.position.set(-.29,.83,.12);radio.setState({power:true,rx:false});}
 }
 function cartMotion(u,t,{distance=1.8,stalled=false}={}){
  const index=activeRow.index,rampShot=activeRow.location==='service'&&[68,69,71,72].includes(index);
  let progress=u,turn=.12,from=V(.8,0,.35),to=V(-1.8,0,-1.3),startYaw=0;
  if(index>=47){from=V(-1.8,0,-1.3);to=V(-.15,0,-3.4);startYaw=Math.PI/2;}
  if(rampShot){
   from=V(1.5,0,-2.2);to=V(1.5,0,-3.9);turn=0;startYaw=0;
   progress=index===68?.45*u:index===69?.45+.14*Math.min(1,u/.45):index===71?.59+.06*step(u,.45,.88):.65+.35*u;
  }
  if(activeRow.location==='outside'){from=V(0,0,-1.5);to=V(0,0,-.4);turn=0;startYaw=Math.PI;}
  const delta=to.clone().sub(from),length=delta.length(),heading=Math.atan2(delta.x,delta.z),cartYaw=heading-Math.PI;
  const moving=turn?clamp((progress-turn)/(1-turn)):progress;
  let angle=cartYaw-startYaw;angle=Math.atan2(Math.sin(angle),Math.cos(angle));
  const yaw=startYaw+angle*(turn?sm(Math.min(1,progress/turn)):1);
  cart.visible=true;cart.position.copy(from).lerp(to,moving);cart.rotation.set(0,yaw,0);
  if(rampShot){cart.position.y=.18+(cart.position.z+3.4)*Math.tan(.15);cart.rotation.x=-.15;}
  if(index===71)cart.position.y+=.05*Math.sin(Math.PI*step(u,.35,.85));
  const caught=(index===69&&u>=.45)||(index===71&&u<.45);
  for(const {pivot,tyre} of cart.wheels){pivot.rotation.y=caught?.8:0;tyre.rotation.x=-moving*length/.13;}
  cart.updateWorldMatrix(true,true);const contact=cart.wheels[0].contact.getWorldPosition(V()),surface=rampShot?.18+(contact.z+3.4)*Math.tan(.15):0;
  cart.userData.tick=contact.y-surface<.005;cart.userData.caught=caught;
  if(index>=46)body(t,{onCart:true});
  const back=V(Math.sin(yaw),0,Math.cos(yaw)),right=V(Math.cos(yaw),0,-Math.sin(yaw));
  const pusher=cart.position.clone().addScaledVector(back,1.45).addScaledVector(right,.68);
  const guide=cart.position.clone().addScaledVector(back,-.35).addScaledVector(right,-1.22);
  place(nia,pusher.x,0,pusher.z,heading);place(mara,guide.x,0,guide.z,heading);
  const travel=moving*length+Math.abs(yaw-startYaw)*.7;
  pose(mara,t,{walking:!caught,distance:travel,walkWeight:.65,expression:'concern',headYaw:-.14,left:[.33,1.06,.31]});flashlight();
  cart.updateWorldMatrix(true,true);const handle=cart.grip.getWorldPosition(V());
  worldGrip(nia,null,handle,'r',t,{walking:!caught,distance:travel+.22,walkWeight:.65,expression:'concern',left:[.2,1.02,.3]});
 }
 function reset(row){
  activeRow=row;scene=sets[row.location].scene;contacts={};mounted=playing=false;aim=V(-2.6,.8,-2.5);
  phone=[56,57,59,61,62,63,82,83,84,85,87].includes(row.index)||row.focus==='impostor'?phoneMara:phoneNia;props.phone=phone;props.camera=row.index===11?downCamera:camera;blanket.visible=false;
  for(const a of Object.values(cast)){scene.add(a.group);a.group.visible=false;a.at(0,0,0);a.group.userData.headingDot=1;a.toon.mesh.visible=true;a.toon.blob.visible=true;a.toon.tint('#FFFFFF');for(const limb of Object.values(a.arms))limb.segments.forEach(o=>o.visible=true);}
  for(const p of Object.values(props)){scene.add(p);p.visible=false;p.position.set(0,0,0);p.rotation.set(0,0,0);p.scale.setScalar(1);}
  torch.setEnabled(false);radio.setState();offRadio.setState({power:false});camera.setRecording(false);downCamera.setRecording(false);
  gear.lid.rotation.x=0;gear.latches.forEach(l=>l.rotation.x=0);gear.position.set(.8,.84,.35);
  monitor.position.set(1.15,.9,.12);monitor.setMode('ben');phone.setMode('play');
  laptop.position.set(.9,.86,.12);laptop.lid.rotation.x=0;laptop.setMode('impostor');
  cart.patient.position.set(0,.9,-.85);cart.userData.tick=cart.userData.caught=false;
  lobby.cable.visible=false;side.ambulance.visible=false;side.ramp.visible=row.action==='gurney'||row.action==='wheel';
  for(const d of[side.fireDoor,side.exit,side.outerDoor]){d.leaf.rotation.y=0;d.latch.position.x=.56;d.handle.rotation.z=0;}
 }
 function stage(row,index,u,t,rx){
  reset({...row,index});activeRow={...row,index};const q=step(u);pair(t);let focus=cast[row.focus]||radio,detail=null,important=[],allowStairs=false;
  // Shared equipment has a home or an explicit owner; it does not disappear
  // merely because a new camera angle no longer mentions it.
  if(row.location==='lobby'&&index>=6){gear.visible=monitor.visible=true;gear.lid.rotation.x=index>6?-1.3:0;}
  if(index>=11&&index<80&&row.location==='lobby'){downTripod.visible=true;downTripod.position.set(.55,0,-.15);downTripod.rotation.y=-2.03;if(index>11){downTripod.socket.add(downCamera);downCamera.position.set(0,.09,0);downCamera.rotation.set(0,0,0);downCamera.visible=true;downCamera.setRecording(true);}}
  if(index>=15&&row.location==='ward'){tripod.visible=camera.visible=true;tripod.position.set(.55,0,.9);tripod.rotation.y=Math.PI;tripod.socket.add(camera);camera.position.set(0,.09,0);camera.rotation.set(0,0,0);camera.setRecording(true);}
  if(row.location==='edit'){laptop.visible=true;}
  const action=row.action;
  if(row.location==='outside'){
   aim=V(0,1.4,-2.7);side.out.lights.key.intensity=index>70?2.9:1.9;
   if(index<6){place(ben,-2.55,0,-.3);pose(ben,t,{walk:.35,mood:'neutral',right:[-.23,1.05,.28]});hold(ben,camera);pair(t,{walk:.35,z:.6-q*.9});}
   if(index===78)side.ambulance.visible=true;
  }
   if(action==='entry'){if(index<6){
    travel(mara,[-1.1,0,2],[-1.1,0,.15],q,t,{turnFrom:Math.PI,left:[.32,1.03,.34]});
    travel(nia,[1.05,0,1.65],[1.05,0,-.2],q,t,{turnFrom:Math.PI});
    travel(ben,[-2.5,0,1.4],[-2.5,0,-.45],q,t,{turnFrom:Math.PI,expression:'neutral'});hold(ben,camera);flashlight();
   }else{side.ambulance.position.z=-q*1.4;}}
  if(action==='case'){
   gear.visible=true;gear.latches.forEach(l=>l.rotation.x=-1.15*step(u,.08,.24));gear.lid.rotation.x=-1.3*step(u,.28,.72);
   mara.at(-2.2,0,.15);place(nia,1.85,0,-.1);place(ben,-.1,0,.4);pose(ben,t,{mood:'neutral'});scene.updateMatrixWorld(true);const p=gear.latches[1].getWorldPosition(V()).lerp(gear.lid.localToWorld(V(0,.02,.32)),step(u,.24,.30));worldGrip(ben,null,p,'l',t,{head:-.17});detail=gear;
  }
  if(action==='map'||action==='silent'){
   paper.visible=action==='map';warning.visible=action==='silent';const p=action==='map'?paper:warning;
   pose(nia,t,{head:-.15,left:[.23,.77+.34*q,.35],right:[-.18,1.12,.36],mood:'worried'});hold(nia,p,'l');detail=p;
   if(index===41)pose(mara,t,{mood:'sad',right:[-.33,.86,.38],head:-.25});
  }
  if(action==='radio'||action==='radiooff'){
   receiver(t,rx);pose(mara,t,{head:-.15,mood:index<20?'neutral':'worried',right:[-.17,1.23,.41],left:[.34,1.04,.34]});receiver(t,rx);flashlight();detail=radio;
   if(row.focus==='ben'){mara.group.visible=nia.group.visible=false;place(ben,0,0,0);pose(ben,t,{mood:'neutral',right:[-.20,1.1,.35]});hold(ben,offRadio);offRadio.setState({power:true,rx});focus=ben;detail=offRadio;}
   if(row.focus==='impostor'){mara.group.visible=nia.group.visible=false;place(impostor,0,0,-.3);pose(impostor,t,{mood:'smug',blink:0,headTilt:-5});impostor.toon.tint('#A9B8AB');focus=impostor;detail=impostor;}
   if(action==='radiooff'){radio.setState({power:u<.58,rx:rx&&u<.58});radio.dial.rotation.y=.6*(1-step(u,.30,.58));}
  }
  if(action==='torch'){pose(mara,t,{head:-.15* Math.sin(u*2),left:[.32,1.1,.38],right:[-.24,1.13,.3]});flashlight();aim=V(-2.8+q*5,1.0,-3.2);detail=torch.shell;}
  if(action==='mount'){
   mara.group.visible=nia.group.visible=false;const who=row.focus==='ben'?ben:nia;
   const stand=index===11?downTripod:tripod,unit=index===11?downCamera:camera;
   place(who,index===11?-.15:0,0,index===11?.15:.35);stand.visible=unit.visible=true;stand.position.set(.55,0,index===11?-.15:.9);stand.rotation.y=index===11?-2.03:Math.PI;scene.updateMatrixWorld(true);
   const socket=stand.socket.localToWorld(V(0,.09,0)),hand=who.group.worldToLocal(socket.clone());
   pose(who,t,{mood:'neutral',head:-.15,right:V(-.25,1.1,.25).lerp(hand,step(u,.05,.50)).toArray()});
   if(u<.53)hold(who,unit);else{stand.socket.add(unit);unit.position.set(0,.09,0);unit.rotation.set(0,0,0);mounted=true;}
   unit.setRecording(u>.72);focus=who;detail=unit;
  }
  if(action==='stairs'||action==='stairdetail'){
   Object.values(cast).forEach(a=>a.group.visible=false);const who=index===29?mara:ben;
   const range=index===12?[0,.35]:index===13?[.35,.7]:index===14?[.7,1]:[0,1];
   const stairs=index===29?{...lobby.stairs,count:1,x:-1.95}:lobby.stairs;
   const gait=stairGait(range[0]+(range[1]-range[0])*q,stairs);place(who,gait.root.x,gait.root.y,gait.root.z,Math.PI);
   const feet={};for(const [name,f] of Object.entries(gait.feet)){const p=who.group.worldToLocal(V(f.x,f.y,f.z));feet[name]={x:p.x,y:p.y,z:p.z,contact:f.contact};}
   pose(who,t,{feet,mood:'worried',head:-.12,right:[-.25,1.1,.32],left:[.29,1.06,.3]});contacts=gait.feet;focus=who;
   if(who===ben)hold(ben,camera);else flashlight();
   detail=action==='stairdetail'?who.stepLegs.left.shoe:null;allowStairs=true;
  }
  if(action==='monitor'){
   const display=row.location==='edit'?laptop:monitor;display.visible=true;place(nia,.45,0,.70);mara.at(-1.65,0,-.05);pose(nia,t,{head:-.18,right:[-.22,1.1,.34]});
   const mode=index===16?(u<.5?'ben':'trolley'):index===20?'door':index===23?'waveform':index===81?(u<.45?'covered':'impostor'):'impostor';
   display.setMode(mode);display.playhead.position.x=-.3+.6*q;scene.updateMatrixWorld(true);
   const target=display.localToWorld(V(.25,.12,.1));worldGrip(nia,null,target,'r',t,{head:-.2});detail=display;focus=nia;
  }
  if(action==='cable'||action==='walk'){
   travel(mara,[-1.05,0,.25],[-1.30,0,-1.3],q,t,{left:[.32,1.03,.34],right:[-.25,1.08,.30]});
   travel(nia,[1.1,0,-.1],[.85,0,-1.65],q,t,{right:[-.29,.82,.36],left:[.22,1.03,.25]});
   flashlight();if(index>=9)receiver(t,rx);lobby.cable.visible=row.location==='lobby';aim=V(-2.6,.3,-1.8-q);detail=row.location==='lobby'?lobby.cableFocus:nia;
   if(index===26){monitor.visible=true;monitor.setMode('black');detail=monitor;}
  }
  if(['body','bodywide','offradio'].includes(action)){
   pair(t);mara.at(.05,0,-.2);nia.at(1.65,0,-.3);body(t);lobby.cable.visible=true;
   pose(mara,t,{mood:'shock',right:[-.19,1.18,.36],left:[.33,1.05,.34],head:-.20});receiver(t,rx);flashlight();pose(nia,t,{mood:'sad',head:-.25});
   detail=action==='offradio'?offRadio:ben;important=[ben.group];focus=action==='offradio'?offRadio:ben;
   if(row.location==='outside'){cartMotion(.6,t,{distance:0});focus=ben;detail=ben;important=[cart];}
   if(action==='bodywide'){
    // Keep the standing duplicate in its own screen column behind the crew.
    // Depth alone does not separate silhouettes under a perspective camera.
    mara.at(-.45,0,-.2);nia.at(.95,0,-.3);place(impostor,3.45,0,-2.7);
    pose(impostor,t,{mood:'smug',blink:0,headTilt:-5});impostor.toon.tint('#A4B6A8');
   }
  }
  if(action==='reveal'){
   pair(t);place(impostor,index>=37?3.25:3.45,0,index>=37?-2.35:-2.7);pose(impostor,t,{mood:'smug',blink:0,headTilt:-5+q*2,right:[-.27,.95+.20*q,.16]});
   impostor.toon.tint('#A4B6A8');focus=impostor;detail=impostor;
   aim=impostor.group.position.clone().add(V(0,1.25,0));
   if(index===34){body(t);mara.at(-.15,0,.25);nia.at(1.25,0,-.05);important=[ben.group];impostor.group.visible=u>.20;}
   if(index===57){travel(impostor,[2.65,0,-2.4],[1.45,0,-.65],Math.min(1,q/.65),t,{expression:'neutral'});aim=impostor.group.position.clone().add(V(0,1.25,0));}
   if(index===62){nia.group.visible=false;travel(impostor,[2.65,0,-2.4],[.85,0,.2],q,t,{expression:'neutral'});travel(mara,[-2.4,0,-.1],[-2.45,0,-1.9],q,t,{turnFrom:Math.PI});flashlight();phone.visible=true;phone.position.set(.8,.86,.35);phone.rotation.x=-.9;playing=true;}
   if(row.location==='ward'){mara.group.visible=nia.group.visible=false;impostor.at(0,0,-.3+q*.25);pose(impostor,t,{mood:'smug',blink:0,headTilt:-6,lean:.07*q});hold(impostor,phone,'r');}
  }
  if(action==='reaction'){
   const who=cast[row.focus]||mara;pose(who,t,{mood:index<11?'neutral':index<30?'worried':index>73?'sad':'shock',head:(index%2?-.15:.15)*q,left:[.29,1.02,.27],right:[-.24,1.08,.33]});
   if(who===mara)flashlight();focus=who;detail=who;
   if(index===17||index===22){monitor.visible=true;monitor.setMode(index===17?'trolley':'waveform');detail=monitor;}
   if(index===33){scene.updateMatrixWorld(true);worldGrip(nia,null,mara.handPoint('r'),'l',t,{mood:'shock',head:-.1});}
   if(index===37){mara.at(-.45,0,.15);nia.at(.55,0,-.35);scene.updateMatrixWorld(true);worldGrip(nia,null,mara.group.localToWorld(V(.1,1.43,.12)),'l',t,{mood:'worried',head:-.12});}
   if(row.location==='ward'){mara.group.visible=nia.group.visible=false;place(impostor,0,0,-.2+q*.1);pose(impostor,t,{mood:'smug',blink:0,lean:q*.06,headTilt:-5});focus=detail=impostor;}
  }
  if(action==='phone'){
   const who=cast[row.focus]||nia;pose(who,t,{head:-.18,right:[-.19,1.19,.39],left:[.23,1.06,.32]});hold(who,phone);phone.setMode(index===44?'help':index===58?'plan':index===76?'call':index===86?'silence':'play');
   playing=[56,61,83].includes(index)&&u>.35;phone.userData.playing=playing;
   if(index===61){mara.at(.10,0,.90,Math.PI/3);scene.add(phone);phone.position.set(.8,.86,.35);phone.rotation.x=-.9;gear.visible=true;scene.updateMatrixWorld(true);worldGrip(mara,null,phone.localToWorld(V(0,0,.03)),'r',t,{head:-.18});}
   focus=who;detail=phone;
   if(who===impostor){mara.group.visible=nia.group.visible=false;place(impostor,0,0,-.3);pose(impostor,t,{head:-.1,mood:'smug',blink:0,right:[-.22,1.11,.38]});hold(impostor,phone);
    if(index===83&&q>.4){scene.updateMatrixWorld(true);const point=tripod.socket.localToWorld(V(.18,.18,.03)),local=impostor.group.worldToLocal(point.clone());worldGrip(impostor,phone,V(-.22,1.11,.38).lerp(local,step(q,.4,.67)).applyMatrix4(impostor.group.matrixWorld),'r',t,{mood:'smug',blink:0});}
   }
  }
  if(action==='laptop'){
   laptop.visible=true;laptop.lid.rotation.x=Math.PI/2*step(u,.25,.80);mara.group.visible=false;place(nia,.5,0,.8);scene.updateMatrixWorld(true);
   worldGrip(nia,null,laptop.lid.localToWorld(V(.25,.62,.02)),'r',t,{mood:'worried',head:-.2});focus=nia;detail=laptop;
  }
  if(action==='transfer'){
   if(index===46){
    body(t);cart.visible=true;cart.position.set(-1.8,0,-1.3);cart.rotation.y=Math.PI/2;
    const destination=cart.patient.getWorldPosition(V());ben.group.position.copy(destination.clone().add(V(-.4,-.61,0)).lerp(destination,step(u,.2,.8)));
    ben.group.quaternion.copy(cart.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(V(1,0,0),Math.PI/2));
    nia.at(-.55,0,-.9);mara.at(-3.15,0,-.9);scene.updateMatrixWorld(true);
    worldGrip(nia,null,ben.group.localToWorld(V(.16,1.05,.04)),'r',t,{mood:'sad',head:-.18,left:[.15,.87,.5]});
    worldGrip(mara,null,ben.group.localToWorld(V(-.16,.35,.04)),'l',t,{mood:'sad',head:-.17});detail=cart;important=[cart,ben.group];
   }else{
    const start=V(.83,1.1,.20),meet=V(.05,1.1,.25),end=V(-.70,1.1,.30);
    const position=u<.57?start.clone().lerp(meet,step(u,.12,.53)):meet.clone().lerp(end,step(u,.57,.88));
    scene.updateMatrixWorld(true);
    const giver=nia.group.worldToLocal((u<.57?position:meet).clone()),receiver=mara.group.worldToLocal(position.clone());
    const reach=V(-.25,1.02,.22).lerp(receiver,step(u,.22,.53));
    pose(nia,t,{right:giver.toArray(),head:-.12});pose(mara,t,{right:reach.toArray(),left:[.30,1.02,.3],head:.10});
    hold(u<.57?nia:mara,phone,'r');phone.setMode('play');phone.userData.handoff=u>=.57;detail=phone;
   }
  }
  if(action==='gurney'||action==='wheel'){
   cartMotion(u,t,{distance:row.location==='outside'?1.1:1.7,stalled:action==='wheel'});detail=action==='wheel'?cart.wheels[0].pivot:cart;focus=nia;important=[cart];
   if(index===71){const wheel=cart.wheels[0].pivot.getWorldPosition(V());mara.at(wheel.x-.45,0,wheel.z+.35);worldGrip(mara,null,wheel,'r',t,{legs:'sit',mood:'worried',head:-.2,left:[.27,.75,.30]});}
  }
  if(action==='ramp'){
   side.ramp.visible=true;side.ramp.rotation.x=THREE.MathUtils.lerp(1.2,-.15,q);scene.updateMatrixWorld(true);
   place(nia,2.45,0,-2.9);place(mara,.1,0,-2.7);worldGrip(nia,null,side.ramp.localToWorld(V(.5,.03,1.0)),'r',t,{head:-.18});worldGrip(mara,null,side.ramp.localToWorld(V(-.5,.03,1.0)),'l',t,{head:-.18});focus=nia;detail=side.ramp;
  }
  if(action==='door'||action==='exit'||action==='latch'){
   const door=action==='exit'?side.exit:side.fireDoor;const who=cast[row.focus]||mara;
   const p=door.getWorldPosition(V());place(who,p.x+.9,0,p.z+.8);pose(who,t,{head:-.1});scene.updateMatrixWorld(true);
   if(action==='exit'){place(who,p.x+.4,0,p.z+.35);pose(who,t,{head:-.1,lean:.12*step(u)});}
   const other=who===nia?mara:nia;if(other.group.visible)other.at(p.x-1.05,0,p.z+1.0);
   door.leaf.rotation.y=action==='latch'?0:(index===64?1-q:q)*-.95;
   door.handle.rotation.z=-.3*step(u,.1,.35);door.latch.position.x=.56+(action==='latch'?.25*step(u,.15,.7):0);
   worldGrip(who,null,(action==='latch'?door.latch:door.handle).getWorldPosition(V()),'r',t,{head:-.15});focus=who;detail=action==='latch'?door.latch:door;
   if(row.focus==='impostor'){mara.group.visible=nia.group.visible=false;place(impostor,p.x,0,p.z-.3);pose(impostor,t,{mood:'smug',blink:0,right:[-.23,1.90,.48]});}
  }
  if(row.location==='service'&&index>=48&&index<74&&!cart.visible){
   cart.visible=true;cart.position.set(-2.7,0,-.3);cart.rotation.y=Math.PI/2;
   if(index===70||index===73){const progress=index===70?.59:1;cart.position.set(1.5,.18+(-2.2-progress*1.7+3.4)*Math.tan(.15),-2.2-progress*1.7);cart.rotation.set(-.15,0,0);}
   body(t,{onCart:true});
  }
  if(index===60){nia.group.visible=false;travel(mara,[-1.5,0,-2.3],[-2.35,0,.6],q,t,{turnFrom:0});flashlight();}
  if(index===61||index===63)nia.group.visible=false;
  if(row.location==='lobby'&&[61,62,63].includes(index)&&action!=='phone'){scene.add(phoneMara);phoneMara.visible=true;phoneMara.position.set(.8,.86,.35);phoneMara.rotation.x=-.9;}
  if(row.location==='ward'&&(index>=84||(index===83&&q>.67))){tripod.socket.add(phoneMara);phoneMara.visible=true;phoneMara.position.set(.18,.18,.03);phoneMara.rotation.set(-.1,0,0);phoneMara.userData.owner='upper_tripod';}
  if(row.location==='lobby'&&index>=30&&index<46&&!ben.group.visible)body(t);
  if(row.location==='lobby'&&index>=43&&index<46&&!cart.visible){cart.visible=true;cart.position.set(-1.8,0,-1.3);cart.rotation.y=Math.atan2(2.6,1.65);}
  if(row.location==='lobby'&&index>34&&index<64&&!impostor.group.visible){
   place(impostor,index===63?.85:index>=37?3.25:3.45,0,index===63?.2:index>=37?-2.35:-2.7);
   pose(impostor,t,{mood:'smug',blink:0,headTilt:-5,head:index===42?-.23*q:0});impostor.toon.tint('#A4B6A8');
  }
  if(row.location==='outside'&&index>=74&&index<=79&&!cart.visible){cart.visible=true;cart.position.set(2.65,0,-.65);body(t,{onCart:true});}
  for(const a of Object.values(cast))if(a.group.visible)a.group.updateWorldMatrix(true,true);
  const visible=Object.values(cast).filter(a=>a.group.visible);
  for(const a of visible)a.assertIntact();registry.assertContinuity();
  const paperLift=[paper,warning].some(p=>p.visible&&p.getWorldPosition(V()).y>.98);
  return {scene,cast:visible,focus,detail,important,props,side,contacts,mounted,playing,aim,allowStairs,row,index,continuity:true,paperLift};
 }
 return {stage,cast,props,sets,side,registry,get contacts(){return contacts;},get mounted(){return mounted;},get playing(){return playing;}};
}
