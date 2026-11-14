// Reusable horror staging vocabulary. The story supplies decisions and coverage;
// these routines supply deterministic, contact-observable physical performances.
import * as THREE from 'three';
import {DirectionalActor as Actor,loadActors} from './directional_actor.js';
import {V,card,words} from './world.js';
import {hospital} from './hospital.js';
import {stairGait} from './stair_gait.mjs';
import {makeFlashlight,makeRadio,makeCamera,makeCameraBag,makeTripod,makeEquipmentCase} from './equipment.js';
import {hospitalSideSets,makeGurney,makePhone,makeMonitor} from './hospital_props.js';
const clamp=x=>Math.max(0,Math.min(1,x)),sm=x=>{x=clamp(x);return x*x*(3-2*x);};
const step=(u,a=.15,b=.75)=>sm((u-a)/(b-a));
export async function hospitalPerformance(E){
 await loadActors();const lobby=hospital(E),side=hospitalSideSets(E);
 const sets={lobby,service:side.service,outside:side.out,ward:side.ward,edit:side.edit};
 const mara=new Actor(lobby.scene,{coat:'#7C8F7B',hat:'#273B40'}),nia=new Actor(lobby.scene,{coat:'#687F97',hat:'#59473D'});
 const ben=new Actor(lobby.scene,{coat:'#AA7956',hat:'#A96A42'}),impostor=new Actor(lobby.scene,{coat:'#AA7956',hat:'#A96A42'});
 const cast={mara,nia,ben,impostor};
 const bags=[makeCameraBag(),makeCameraBag()];ben.group.add(bags[0]);impostor.group.add(bags[1]);bags.forEach(b=>b.position.set(-.29,.75,.07));
 mara.toon.restyle({hat:'cap',pattern:'plain',extra:[]});nia.toon.restyle({hat:'bun',pattern:'plain',extra:[]});
 for(const a of[ben,impostor])a.toon.restyle({hat:'beanie',pattern:'plain',extra:[]});
 const torch=makeFlashlight({range:6,angle:.18,power:16}),radio=makeRadio(),offRadio=makeRadio();
 const camera=makeCamera(),tripod=makeTripod(),gear=makeEquipmentCase(),phone=makePhone(lobby.scene),monitor=makeMonitor(lobby.scene);
 const cart=makeGurney(lobby.scene),paper=card(lobby.scene,words(['SERVICE EXIT','RECEPTION  >  LAUNDRY'],{paper:'#C7CCB1',ink:'#35504C'}),.48,.33,0,0,0);
 const laptop=makeMonitor(lobby.scene,{portable:true});
 const warning=card(lobby.scene,words(['DO NOT','ANSWER'],{paper:'#C7CCB1',ink:'#294447'}),.43,.29,0,0,0);
 const props={torch,radio,offRadio,camera,tripod,gear,phone,monitor,laptop,cart,paper,warning};
 let scene=lobby.scene,contacts={},mounted=false,playing=false,aim=V(-2.6,.8,-2.5),activeRow;
 const pose=(a,t,options={})=>a.pose(t,{mood:'worried',left:[.28,1.01,.24],right:[-.27,1.02,.28],...options});
 function place(a,x=0,y=0,z=0){a.group.visible=true;a.at(x,y,z);return a;}
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
  ben.toon.tint('#C4CFC3');offRadio.visible=!onCart;offRadio.position.set(-2.10,.31,-1.55);offRadio.rotation.set(-.72,.05,0);offRadio.setState({power:false});
 }
 function pair(t,{walk=0,shift=0,z=0}={}){
  place(mara,-.85+shift,0,z+.25);place(nia,1.15+shift,0,z-.15);
  if(walk>.05){mara.group.rotation.y=Math.PI;nia.group.rotation.y=Math.PI;}
  pose(mara,t,{walk,head:-.1,right:[-.20,1.17,.40],left:[.32,1.05,.36]});
  pose(nia,t,{walk,head:.12,left:[.25,1.04,.29],right:[-.26,1.11,.35]});flashlight();
 }
 function cartMotion(u,t,{distance=1.8,stalled=false}={}){
  const movement=stalled?(u<.45?u:(u<.68?.45:u-.23)):u;
  cart.visible=true;cart.position.set(-.15,0,-movement*distance);cart.rotation.y=Math.PI/2;
  const rampShot=activeRow.location==='service'&&[68,69,71,72].includes(activeRow.index);
  if(rampShot){cart.position.set(1.5,.18+(-2.2-movement*distance+3.4)*Math.tan(.15),-2.2-movement*distance);cart.rotation.set(-.15,0,0);}
  for(const {pivot,tyre} of cart.wheels){pivot.rotation.y=stalled&&u>.45&&u<.68?.8:0;tyre.rotation.x=-movement*distance/.13;}
  cart.updateWorldMatrix(true,true);const contact=cart.wheels[0].contact.getWorldPosition(V());
  const surface=rampShot ? .18+(contact.z+3.4)*Math.tan(.15) : 0;
  cart.userData.tick=contact.y-surface<.005;cart.userData.caught=stalled&&u>=.45&&u<.68;
  body(t,{onCart:true});place(nia,.95,0,cart.position.z+.65);place(mara,-1.5,0,cart.position.z-.2);
  nia.group.rotation.y=Math.PI;mara.group.rotation.y=Math.PI;
  pose(mara,t,{walk:stalled&&u>.45&&u<.68?0:.5,head:-.14,left:[.33,1.06,.31]});flashlight();
  cart.updateWorldMatrix(true,true);const handle=cart.grip.getWorldPosition(V());
  worldGrip(nia,null,handle,'r',t,{walk:stalled&&u>.45&&u<.68?0:.5,mood:'worried',left:[.2,1.02,.3]});
 }
 function reset(row){
  activeRow=row;scene=sets[row.location].scene;contacts={};mounted=playing=false;aim=V(-2.6,.8,-2.5);
  for(const a of Object.values(cast)){scene.add(a.group);a.group.visible=false;a.at(0,0,0);a.toon.mesh.visible=true;a.toon.blob.visible=true;a.toon.tint('#FFFFFF');for(const limb of Object.values(a.arms))limb.segments.forEach(o=>o.visible=true);}
  for(const p of Object.values(props)){scene.add(p);p.visible=false;p.position.set(0,0,0);p.rotation.set(0,0,0);p.scale.setScalar(1);}
  torch.setEnabled(false);radio.setState();offRadio.setState({power:false});camera.setRecording(false);
  gear.lid.rotation.x=0;gear.latches.forEach(l=>l.rotation.x=0);gear.position.set(.8,.84,.35);
  monitor.position.set(1.15,.9,.12);monitor.setMode('ben');phone.setMode('play');
  laptop.position.set(.9,.86,.12);laptop.lid.rotation.x=0;laptop.setMode('impostor');
  cart.patient.position.set(0,.9,-.85);cart.userData.tick=cart.userData.caught=false;
  lobby.cable.visible=false;side.ambulance.visible=false;side.ramp.visible=row.action==='gurney'||row.action==='wheel';
  for(const d of[side.fireDoor,side.exit,side.outerDoor]){d.leaf.rotation.y=0;d.latch.position.x=.56;d.handle.rotation.z=0;}
 }
 function stage(row,index,u,t,rx){
  reset(row);activeRow={...row,index};const q=step(u);pair(t);let focus=cast[row.focus]||radio,detail=null,important=[],allowStairs=false;
  const action=row.action;
  if(row.location==='outside'){
   aim=V(0,1.4,-2.7);side.out.lights.key.intensity=index>70?2.9:1.9;
   if(index<6){place(ben,-2.55,0,-.3);pose(ben,t,{walk:.35,mood:'neutral',right:[-.23,1.05,.28]});hold(ben,camera);pair(t,{walk:.35,z:.6-q*.9});}
   if(index===78)side.ambulance.visible=true;
  }
  if(action==='entry'){pair(t,{walk:index<6?.45:0,z:index<6?1.0-q*1.5:0});if(index<6){place(ben,-2.55,0,.3-q);pose(ben,t,{walk:.45,mood:'neutral'});hold(ben,camera);}else{side.ambulance.position.z=-q*1.4;}}
  if(action==='case'){
   gear.visible=true;gear.latches.forEach(l=>l.rotation.x=-1.15*step(u,.08,.24));gear.lid.rotation.x=-1.3*step(u,.28,.72);
   mara.at(-2.2,0,.15);place(nia,1.85,0,-.1);place(ben,-.1,0,.4);pose(ben,t,{mood:'neutral'});scene.updateMatrixWorld(true);const p=gear.latches[1].getWorldPosition(V()).lerp(gear.lid.localToWorld(V(0,.02,.32)),step(u,.24,.30));worldGrip(ben,null,p,'l',t,{head:-.17});detail=gear;
  }
  if(action==='map'||action==='silent'){
   paper.visible=action==='map';warning.visible=action==='silent';const p=action==='map'?paper:warning;
   pose(nia,t,{head:-.15,left:[.23,1.1,.35],right:[-.18,1.12,.36],mood:'worried'});hold(nia,p,'l');detail=p;
   if(index===41)pose(mara,t,{mood:'sad',right:[-.33,.86,.38],head:-.25});
  }
  if(action==='radio'||action==='radiooff'){
   receiver(t,rx);pose(mara,t,{head:-.15,mood:index<20?'neutral':'worried',right:[-.17,1.23,.41],left:[.34,1.04,.34]});receiver(t,rx);flashlight();detail=radio;
   if(row.focus==='ben'){mara.group.visible=nia.group.visible=false;place(ben,0,row.location==='ward'?0:0,0);pose(ben,t,{mood:'neutral',right:[-.20,1.2,.39]});hold(ben,radio);radio.setState({power:true,rx});focus=ben;}
   if(row.focus==='impostor'){mara.group.visible=nia.group.visible=false;place(impostor,0,0,-.3);pose(impostor,t,{mood:'smug',blink:0,headTilt:-5});impostor.toon.tint('#A9B8AB');focus=impostor;detail=impostor;}
   if(action==='radiooff'){radio.setState({power:u<.58,rx:rx&&u<.58});radio.dial.rotation.y=.6*(1-step(u,.30,.58));}
  }
  if(action==='torch'){pose(mara,t,{head:-.15* Math.sin(u*2),left:[.32,1.1,.38],right:[-.24,1.13,.3]});flashlight();aim=V(-2.8+q*5,1.0,-3.2);detail=torch.shell;}
  if(action==='mount'){
   mara.group.visible=nia.group.visible=false;const who=row.focus==='ben'?ben:nia;
   place(who,-.65,0,.15);tripod.visible=camera.visible=true;tripod.position.set(.55,0,-.15);scene.updateMatrixWorld(true);
   const socket=tripod.socket.localToWorld(V(0,.09,0)),hand=who.group.worldToLocal(socket.clone());
   pose(who,t,{mood:'neutral',head:-.15,right:V(-.25,1.1,.25).lerp(hand,step(u,.05,.50)).toArray()});
   if(u<.53)hold(who,camera);else{tripod.socket.add(camera);camera.position.set(0,.09,0);camera.rotation.set(0,0,0);mounted=true;}
   camera.setRecording(u>.72);focus=who;detail=camera;
  }
  if(action==='stairs'||action==='stairdetail'){
   Object.values(cast).forEach(a=>a.group.visible=false);const who=index===29?mara:ben;
   const range=index===12?[0,.35]:index===13?[.35,.7]:index===14?[.7,1]:[0,1];
   const stairs=index===29?{...lobby.stairs,count:1,x:-1.95}:lobby.stairs;
   const gait=stairGait(range[0]+(range[1]-range[0])*q,stairs);place(who,gait.root.x,gait.root.y,gait.root.z);
   const feet={};for(const [name,f] of Object.entries(gait.feet)){const p=who.group.worldToLocal(V(f.x,f.y,f.z));feet[name]={x:p.x,y:p.y,z:p.z,contact:f.contact};}
   pose(who,t,{feet,mood:'worried',head:-.12,right:[-.25,1.1,.32],left:[.29,1.06,.3]});contacts=gait.feet;focus=who;
   if(who===ben)hold(ben,camera);else flashlight();
   detail=action==='stairdetail'?who.stepLegs.left.shoe:null;allowStairs=true;
  }
  if(action==='monitor'){
   const display=row.location==='edit'?laptop:monitor;display.visible=true;place(nia,-.35,0,.25);mara.at(-2.4,0,-.2);pose(nia,t,{head:-.18,right:[-.22,1.1,.34]});
   const mode=index===16?(u<.5?'ben':'trolley'):index===20?'door':index===23?'waveform':index===81?(u<.45?'covered':'impostor'):'impostor';
   display.setMode(mode);display.playhead.position.x=-.3+.6*q;scene.updateMatrixWorld(true);
   const target=display.localToWorld(V(.25,.12,.1));worldGrip(nia,null,target,'r',t,{head:-.2});detail=display;focus=nia;
  }
  if(action==='cable'||action==='walk'){
   pair(t,{walk:.6,z:-q*1.3,shift:-q*.25});lobby.cable.visible=row.location==='lobby';
   pose(nia,t,{walk:.55,head:-.2,right:[-.29,.77,.36],left:[.22,1.05,.25]});aim=V(-2.6,.3,-1.8-q);detail=row.location==='lobby'?lobby.cableFocus:nia;
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
    mara.at(-.45,0,-.2);nia.at(.95,0,-.3);place(impostor,3.45,0,-2.2);
    pose(impostor,t,{mood:'smug',blink:0,headTilt:-5});impostor.toon.tint('#A4B6A8');
   }
  }
  if(action==='reveal'){
   pair(t);place(impostor,2.65-q*.25,0,-2.1+q*.2);pose(impostor,t,{mood:'smug',blink:0,headTilt:-5+q*2,right:[-.27,.95+.20*q,.16]});impostor.toon.tint('#A4B6A8');focus=impostor;detail=impostor;
   if(index===34){body(t);mara.at(-.15,0,.25);nia.at(1.25,0,-.05);important=[ben.group];}
   if(row.location==='ward'){mara.group.visible=nia.group.visible=false;impostor.at(0,0,-.3+q*.25);pose(impostor,t,{mood:'smug',blink:0,headTilt:-6,lean:.07*q});hold(impostor,phone,'r');}
  }
  if(action==='reaction'){
   const who=cast[row.focus]||mara;pose(who,t,{mood:index<11?'neutral':index<30?'worried':index>73?'sad':'shock',head:(index%2?-.15:.15)*q,left:[.29,1.02,.27],right:[-.24,1.08,.33]});
   if(who===mara)flashlight();focus=who;detail=who;
   if(index===17||index===22){monitor.visible=true;monitor.setMode(index===17?'trolley':'waveform');detail=monitor;}
   if(index===33){scene.updateMatrixWorld(true);worldGrip(nia,null,mara.handPoint('r'),'l',t,{mood:'shock',head:-.1});}
   if(index===37){nia.at(.10,0,-.1);scene.updateMatrixWorld(true);worldGrip(nia,null,mara.group.localToWorld(V(.05,1.39,.12)),'l',t,{mood:'worried',head:-.12});}
   if(row.location==='ward'){mara.group.visible=nia.group.visible=false;place(impostor,0,0,-.2+q*.1);pose(impostor,t,{mood:'smug',blink:0,lean:q*.06,headTilt:-5});focus=detail=impostor;}
  }
  if(action==='phone'){
   const who=cast[row.focus]||nia;pose(who,t,{head:-.18,right:[-.19,1.19,.39],left:[.23,1.06,.32]});hold(who,phone);phone.setMode(index===44?'help':index===58?'plan':index===76?'call':index===86?'silence':'play');
   playing=[56,61,83].includes(index)&&u>.35;phone.userData.playing=playing;
   if(index===61){scene.add(phone);phone.position.set(.8,.86,.35);phone.rotation.x=-.9;gear.visible=true;scene.updateMatrixWorld(true);worldGrip(mara,null,phone.localToWorld(V(0,0,.03)),'r',t,{head:-.18});}
   focus=who;detail=phone;
   if(who===impostor){mara.group.visible=nia.group.visible=false;place(impostor,0,0,-.3);pose(impostor,t,{head:-.1,mood:'smug',blink:0,right:[-.22,1.11,.38]});hold(impostor,phone);}
  }
  if(action==='laptop'){
   laptop.visible=true;laptop.lid.rotation.x=Math.PI/2*step(u,.25,.80);mara.group.visible=false;place(nia,-.3,0,.3);scene.updateMatrixWorld(true);
   worldGrip(nia,null,laptop.lid.localToWorld(V(.25,.62,.02)),'r',t,{mood:'worried',head:-.2});focus=nia;detail=laptop;
  }
  if(action==='transfer'){
   if(index===46){
    body(t);cart.visible=true;cart.position.set(-1.5,0,-.4);cart.rotation.y=Math.PI/2;
    const destination=cart.patient.getWorldPosition(V());ben.group.position.copy(destination.clone().add(V(-.4,-.61,0)).lerp(destination,step(u,.2,.8)));
    ben.group.quaternion.copy(cart.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(V(1,0,0),Math.PI/2));
    nia.at(-.45,0,.20);mara.at(-3.4,0,.20);scene.updateMatrixWorld(true);
    worldGrip(nia,null,ben.group.localToWorld(V(.16,1.05,.04)),'r',t,{mood:'sad',head:-.18,left:[.15,.87,.5]});
    worldGrip(mara,null,ben.group.localToWorld(V(-.16,.35,.04)),'l',t,{mood:'sad',head:-.17});detail=cart;important=[cart,ben.group];
   }else{
    const start=V(.95,1.15,.28),end=V(-.55,1.15,.38),position=start.clone().lerp(end,step(u,.15,.7));
    pose(nia,t,{right:nia.group.worldToLocal(position.clone()).toArray(),head:-.12});pose(mara,t,{left:mara.group.worldToLocal(position.clone()).toArray(),right:[-.25,1.1,.25],head:.10});
    phone.visible=true;phone.position.copy(position);phone.setMode('play');detail=phone;
   }
  }
  if(action==='gurney'||action==='wheel'){
   cartMotion(u,t,{distance:row.location==='outside'?1.1:1.7,stalled:action==='wheel'});detail=action==='wheel'?cart.wheels[0].pivot:cart;focus=nia;important=[cart];
   if(index===71){mara.at(-.9,0,cart.position.z+.25);pose(mara,t,{legs:'sit',mood:'worried',head:-.2,right:[-.3,.42,.45],left:[.27,.75,.30]});}
  }
  if(action==='ramp'){
   side.ramp.visible=true;side.ramp.rotation.x=THREE.MathUtils.lerp(1.2,-.15,q);scene.updateMatrixWorld(true);
   place(nia,2.45,0,-2.9);place(mara,.1,0,-2.7);worldGrip(nia,null,side.ramp.localToWorld(V(.5,.03,1.0)),'r',t,{head:-.18});worldGrip(mara,null,side.ramp.localToWorld(V(-.5,.03,1.0)),'l',t,{head:-.18});focus=nia;detail=side.ramp;
  }
  if(action==='door'||action==='exit'||action==='latch'){
   const door=action==='exit'?side.exit:side.fireDoor;const who=cast[row.focus]||mara;
   const p=door.getWorldPosition(V());place(who,p.x+.9,0,p.z+.8);pose(who,t,{head:-.1});scene.updateMatrixWorld(true);
   const other=who===nia?mara:nia;if(other.group.visible)other.at(1.7,0,p.z+1.0);
   door.leaf.rotation.y=action==='latch'?0:(index===64?1-q:q)*-.95;
   door.handle.rotation.z=-.3*step(u,.1,.35);door.latch.position.x=.56+(action==='latch'?.25*step(u,.15,.7):0);
   worldGrip(who,null,(action==='latch'?door.latch:door.handle).getWorldPosition(V()),'r',t,{head:-.15});focus=who;detail=action==='latch'?door.latch:door;
   if(row.focus==='impostor'){mara.group.visible=nia.group.visible=false;place(impostor,p.x,0,p.z-.3);pose(impostor,t,{mood:'smug',blink:0,right:[-.23,1.2,.3]});}
  }
  if(row.location==='service'&&index>=48&&index<74&&!cart.visible){cart.visible=true;cart.position.set(-2.7,0,-.3);cart.rotation.y=Math.PI/2;body(t,{onCart:true});}
  for(const a of Object.values(cast))if(a.group.visible)a.group.updateWorldMatrix(true,true);
  const visible=Object.values(cast).filter(a=>a.group.visible);
  return {scene,cast:visible,focus,detail,important,props,side,contacts,mounted,playing,aim,allowStairs,row,index};
 }
 return {stage,cast,props,sets,side,get contacts(){return contacts;},get mounted(){return mounted;},get playing(){return playing;}};
}
