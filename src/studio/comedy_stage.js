// Reusable staging and physical props for the original crime-comedy collection.
// Story intent and shot/action order stay in each project's story_data.js.
import * as THREE from 'three';
import {Actor,loadActors} from './actor.js';
import {upperBodyDrop} from './toon_state.mjs';
import {camera} from './engine.js';
import {V,mat,box,cylinder,card,words,texture,makeScene,street,key} from './world.js';
import {frameShot} from './camera_framing.mjs';
export const clamp=x=>THREE.MathUtils.clamp(x,0,1),sm=x=>{x=clamp(x);return x*x*(3-2*x);},lerp=THREE.MathUtils.lerp;
const motion=(u,a=.12,b=.65)=>sm((u-a)/(b-a));
function label(parent,text,w,h,x,y,z,paper='#E6D8B6'){return card(parent,words(text,{paper}),w,h,x,y,z);}
function painting(parent,x,y,z,index=0){
 const g=new THREE.Group();parent.add(g);g.position.set(x,y,z);box(g,.72,.86,.08,'#AB8652');
 const art=texture((c,w,h)=>{c.fillStyle=['#36544B','#434B68','#705349'][index%3];c.fillRect(0,0,w,h);c.fillStyle=['#D5AD71','#C2B991','#B8AF91'][index%3];c.beginPath();c.ellipse(w*.5,h*.43,w*.21,h*.25,0,0,7);c.fill();c.fillStyle='#263E39';c.beginPath();c.ellipse(w*.5,h*.98,w*.38,h*.37,0,0,7);c.fill();c.fillStyle='#4D3A31';c.fillRect(w*.3,h*.22,w*.4,h*.065);c.fillRect(w*.38,h*.12,w*.24,h*.14);});
 card(g,art,.61,.75,0,0,.047);return g;
}
function room(E,title,night=false){
 const S=makeScene(E,night),s=S.scene;
 box(s,9,.12,9,mat('white',{roughness:.9}),0,-.08,-1);s.children.at(-1).material=mat(night?'#775D4D':'#9B7D5A');
 box(s,9,3.8,.18,night?'#4E6864':'#9BA58B',0,1.9,-3.2);
 for(const y of[.15,1.1,3.55])box(s,9,.065,.09,'#B69C73',0,y,-3.06);
 label(s,[title],3.5,.4,0,3.23,-3.04);
 const window=new THREE.Group();s.add(window);window.position.set(-2.45,1.95,-3.02);
 box(window,1.55,1.6,.09,'#C7B996');box(window,1.42,1.47,.04,'#233347',0,0,.055);
 const pane=new THREE.Group();pane.position.set(-.69,0,.09);window.add(pane);window.pane=pane;
 box(pane,1.37,1.42,.04,night?'#435675':'#9FC8CF',.685);
 for(const x of[.02,.68,1.35])box(pane,.045,1.43,.03,'#D6C9AA',x,0,.03);
 box(pane,1.37,.045,.03,'#D6C9AA',.685,0,.03);
 const door=new THREE.Group();s.add(door);door.position.set(1.7,0,-2.94);box(door,1.16,2.6,.11,'#74583C',.58,1.3,0);
 for(const y of[.7,1.9])box(door,.86,.72,.025,'#886B4B',.58,y,.07);
 cylinder(door,.045,.05,'#D0B26E',1.0,1.2,.10).rotation.x=Math.PI/2;
 const desk=new THREE.Group();s.add(desk);box(desk,2.8,.13,1.0,'#9D7650',0,.99,-.8);
 for(const x of[-1.1,1.1])for(const z of[-1.15,-.45])box(desk,.1,1,.1,'#6B503A',x,.5,z);
 const chair=new THREE.Group();s.add(chair);chair.position.set(-2,0,-.2);box(chair,.62,.11,.65,'#8C6543',0,.52,0);box(chair,.62,.75,.10,'#99744D',0,.95,-.27);
 for(const x of[-.25,.25])for(const z of[-.25,.25])box(chair,.065,.5,.065,'#6A4D38',x,.25,z);
 const frames=[painting(s,-.9,2.15,-3.03,0),painting(s,.15,2.15,-3.03,1),painting(s,1.2,2.15,-3.03,2)];
 const shelf=new THREE.Group();s.add(shelf);shelf.position.set(-3.9,0,-2.3);
 for(const y of[.3,1.2,2.1]){box(shelf,.75,.09,.5,'#78583F',0,y,0);for(let i=0;i<5;i++)box(shelf,.09,.35,.30,['#5D7768','#8B5B55','#B6A172'][i%3],-.27+i*.13,y+.22,0);}
 const lamp=cylinder(s,.17,.07,'#B69661',-.95,1.10,-.8);cylinder(s,.023,.38,'#B69661',-.95,1.3,-.8);
 const shade=new THREE.Mesh(new THREE.ConeGeometry(.25,.17,20,1,true),mat('#476D5B'));shade.position.set(-.95,1.5,-.8);s.add(shade);
 const glow=new THREE.PointLight('#FFE1AE',night?5:2.5,5);glow.position.set(-.95,1.45,-.8);s.add(glow);
 return {...S,door,desk,chair,frames,window};
}
function safe(parent){
 const g=new THREE.Group();parent.add(g);const metal=mat('#526B75',{metalness:.35,roughness:.45});
 box(g,1.5,.16,1.1,metal,0,.12,0);box(g,1.5,.16,1.1,metal,0,1.68,0);
 for(const x of[-.68,.68])box(g,.14,1.5,1.1,metal,x,.9,0);
 box(g,1.3,1.42,.10,'#637A7F',0,.9,-.5);box(g,1.2,.04,.85,'#99A4A0',0,.53,0);
 const hinge=new THREE.Group();g.add(hinge);hinge.position.set(-.68,.18,.57);box(hinge,1.36,1.42,.14,metal,.68,.71,0);
 for(const x of[.12,1.24])for(const y of[.12,1.29])cylinder(hinge,.025,.02,'#B6BDAE',x,y,.085).rotation.x=Math.PI/2;
 const wheel=new THREE.Group();hinge.add(wheel);wheel.position.set(.88,.77,.14);
 const ring=new THREE.Mesh(new THREE.TorusGeometry(.15,.018,8,24),mat('#B4BEB7',{metalness:.5,roughness:.35}));wheel.add(ring);
 for(let i=0;i<3;i++){const spoke=box(wheel,.30,.018,.018,'#AEB8AC');spoke.rotation.z=i*Math.PI/3;}
 const dial=cylinder(hinge,.075,.035,'#C4C7B5',.42,.9,.11);dial.rotation.x=Math.PI/2;
 label(hinge,['SECURE'],.46,.13,.42,1.18,.083,'#B3B6A5');
 g.hinge=hinge;g.wheel=wheel;return g;
}
function car(parent,police=false){
 const g=new THREE.Group();parent.add(g);const col=police?'#3A515D':'#D8B346';
 box(g,2.05,.5,3.35,col,0,.63,0);box(g,1.92,.18,1.15,col,0,.88,1.02);box(g,1.94,.18,.8,col,0,.98,-1.22);
 box(g,2.12,.15,.14,'#B9BCB0',0,.50,1.76);box(g,2.12,.15,.14,'#B9BCB0',0,.50,-1.76);
 for(const x of[-.73,.73]){cylinder(g,.17,.06,'#E2D49B',x,.88,1.73).rotation.x=Math.PI/2;box(g,.13,.14,.05,'#B94338',x,.81,-1.70);}
 for(const x of[-.98,.98]){box(g,.05,.78,.06,'#7C8A7E',x,1.44,.58);box(g,.05,.78,.06,'#7C8A7E',x,1.44,-.72);}
 box(g,2.0,.05,.06,'#B5BEB3',0,1.83,.58);box(g,2.0,.05,.06,'#B5BEB3',0,1.83,-.72);
 for(const x of[-.52,.52]){box(g,.56,.16,.55,'#593F32',x,.88,-.1);box(g,.56,.60,.10,'#6C4D3B',x,1.1,-.4);}
 const wheel=[];for(const x of[-1.02,1.02])for(const z of[-1.06,1.06]){const w=new THREE.Group();g.add(w);w.position.set(x,.40,z);const tire=cylinder(w,.36,.17,'#30383B');tire.rotation.z=Math.PI/2;const hub=cylinder(w,.19,.18,'#AAAFA4');hub.rotation.z=Math.PI/2;wheel.push(w);}
 const steering=new THREE.Mesh(new THREE.TorusGeometry(.19,.022,8,24),mat('#3A3D38'));steering.position.set(-.5,1.02,.39);steering.rotation.x=-.6;g.add(steering);
 const door=new THREE.Group();g.add(door);door.position.set(1.03,.48,.50);box(door,.055,.65,1.14,col,0,.32,-.57);box(door,.07,.04,.18,'#B6B6A5',.04,.56,-.42);
 const red=cylinder(g,.11,.14,'#BF4A46',-.2,1.72,-.74),blue=cylinder(g,.11,.14,'#498CB9',.2,1.72,-.74);
 red.material=new THREE.MeshBasicMaterial({color:'#D34642'});blue.material=new THREE.MeshBasicMaterial({color:'#4A92DA'});
 if(!police){red.visible=blue.visible=false;label(g,['TAXI'],.50,.18,0,1.92,-.74,'#E6D391');}
 g.wheels=wheel;g.door=door;g.red=red;g.blue=blue;g.steering=steering;g.userData.moving=false;g.userData.siren=false;return g;
}
function propBook(parent,title){const g=new THREE.Group();parent.add(g);box(g,.38,.46,.05,'#E1D6B6');g.cover=new THREE.Group();g.cover.position.set(-.19,0,.04);g.add(g.cover);box(g.cover,.39,.48,.025,'#567565',.195,0,0);label(g.cover,[title],.32,.36,.195,0,.016,'#7F947A');label(g,['RECORDS','CONFIDENTIAL'],.31,.36,.01,0,.028);return g;}
function coin(parent){
 const g=new THREE.Group();parent.add(g);cylinder(g,.115,.025,'#D5B14D').rotation.x=Math.PI/2;
 function face(fake){
  return texture((c,w,h)=>{
   c.fillStyle='#D8BA61';c.fillRect(0,0,w,h);c.strokeStyle='#94792F';c.lineWidth=10;
   c.beginPath();c.arc(w/2,h/2,w*.45,0,7);c.stroke();c.fillStyle='#9C8035';c.textAlign='center';
   if(fake){
    c.beginPath();c.ellipse(w*.5,h*.45,w*.15,h*.20,0,0,7);c.fill();
    for(const y of[.36,.49]){c.beginPath();c.arc(w*.34,h*y,w*.044,0,7);c.fill();}
    c.font='bold 66px Georgia';c.fillText('NEXT THU',w*.5,h*.8);
   }else{c.font='bold 220px Georgia';c.fillText('1',w*.5,h*.66);}
  },512,512);
 }
 for(const [name,fake] of[['fakeFace',true],['realFace',false]]){
  const mesh=new THREE.Mesh(new THREE.CircleGeometry(.11,48),new THREE.MeshStandardMaterial({map:face(fake),roughness:.7}));
  mesh.position.z=.015;g.add(mesh);g[name]=mesh;
 }
 return g;
}

export async function createComedyStage(E,data,fit=frameShot){
 await loadActors();const worlds={home:room(E,'PRIVATE RESIDENCE',true),office:room(E,'TOWN OFFICE'),auction:room(E,'AUCTION ROOMS'),street:street(E),road:street(E)};
 const home=worlds.home,auction=worlds.auction,road=worlds.road;
 const heroArt=painting(home.scene,0,1.65,-2.0,0),hiddenArt=new THREE.Group();home.scene.add(hiddenArt);hiddenArt.position.set(-.3,0,-2.05);
 for(let i=0;i<5;i++)painting(hiddenArt,-1.7+i*.8,1.85,0,i);
 const curtain=new THREE.Group();home.scene.add(curtain);curtain.position.set(-.3,1.6,-1.85);
 for(let i=0;i<23;i++)box(curtain,.205,2.8,.10+(i%2)*.04,i%2?'#773F47':'#864951',(i-11)*.195);
 const actors=data.cast.map((look,i)=>{const a=new Actor(home.scene,{coat:look.coat,hat:look.hatCol||'#594E43',height:look.height||1.85});a.toon.restyle({hat:look.hat||'bowler',pattern:look.pattern||'trench',extra:look.extra||['thinmustache'],kid:!!look.kid});return a;});
 const props={art:hiddenArt,portrait:heroArt,window:home.window,chair:home.chair},loose=[];function addProp(name,obj){props[name]=obj;loose.push(obj);return obj;}
 addProp('safe',safe(auction.scene));addProp('book',propBook(home.scene,'LEDGER'));
 addProp('coin',coin(home.scene));addProp('key',key(home.scene,1.4));
 const coinPile=new THREE.Group();home.scene.add(coinPile);addProp('coinPile',coinPile);
 for(let i=0;i<5;i++)cylinder(coinPile,.083,.025,'#D5B14D',-.12+(i%3)*.11,.013+Math.floor(i/3)*.027,(i%2)*.052);
 const watch=new THREE.Group();home.scene.add(watch);cylinder(watch,.075,.022,'#C5C5B6').rotation.x=Math.PI/2;label(watch,['12','6'],.11,.11,0,0,.014,'#F0E5C9');addProp('watch',watch);
 const bag=new THREE.Group();home.scene.add(bag);const profile=[[.03,0],[.18,.04],[.22,.22],[.15,.36],[.095,.39]].map(p=>new THREE.Vector2(...p));bag.add(new THREE.Mesh(new THREE.LatheGeometry(profile,24),mat('#73513C')));const bagRim=new THREE.Mesh(new THREE.TorusGeometry(.10,.015,8,24),mat('#B49A72'));bagRim.rotation.x=Math.PI/2;bagRim.position.y=.39;bag.add(bagRim);addProp('bag',bag);
 if(data.silver){for(const x of[-.045,.045]){cylinder(bag,.023,.18,'#ADB9BC',x,.42,0);cylinder(bag,.044,.027,'#D3D9D4',x,.52,0);}}
 const paper=new THREE.Group();home.scene.add(paper);paper.unfold=new THREE.Group();paper.add(paper.unfold);label(paper.unfold,data.paper||['CITY RECORD','PLEASE SIGN'],.48,.35,0,0,0);addProp('paper',paper);
 const rejected=label(paper,['CLAIM REJECTED'],.56,.33,0,0,.016,'#D6907B');
 const sign=label(road.scene,['BRIDGE CLOSED','ROAD WORK'],1.06,.6,0,0,0,'#E1AE59');addProp('bridge',sign);
 const boxSignStand=box(road.scene,.10,1.2,.10,'#8B6444',0,.53,.02);
 const speed=label(road.scene,['SPEED','LIMIT 25'],.50,.61,0,0,0,'#F0E6C7');addProp('speed',speed);
 const receipt=label(home.scene,['PAID','RECEIPT'],.32,.40,0,0,0);addProp('receipt',receipt);
 const news=label(home.scene,data.news||['THE TOWN TIMES','UNLIKELY HERO'],.60,.73,0,0,0);addProp('news',news);
 const phone=new THREE.Group();home.scene.add(phone);box(phone,.48,.15,.34,'#333C37');const dial=cylinder(phone,.12,.025,'#BEAB78',0,.10,.02);dial.rotation.x=.2;addProp('phone',phone);
 const receiver=new THREE.Group();home.scene.add(receiver);box(receiver,.32,.035,.06,'#2B3631');for(const x of[-.15,.15]){const end=cylinder(receiver,.065,.07,'#26312D',x,-.035,0);end.rotation.z=x<0?-.3:.3;}addProp('receiver',receiver);
 const gavel=new THREE.Group();home.scene.add(gavel);box(gavel,.026,.18,.026,'#745036',0,-.055,0);box(gavel,.22,.09,.1,'#91663D',0,-.13,0);addProp('gavel',gavel);
 const paddle=new THREE.Group();home.scene.add(paddle);box(paddle,.025,.28,.025,'#9D7B4A',0,-.15,0);label(paddle,['BID'],.24,.26,0,.04,.01,'#DACDAA');addProp('paddle',paddle);
 const medal=new THREE.Group();home.scene.add(medal);cylinder(medal,.065,.014,'#D8B457').rotation.x=Math.PI/2;label(medal,['HERO'],.085,.04,0,0,.013,'#D8B457');addProp('medal',medal);
 const loaf=new THREE.Mesh(new THREE.SphereGeometry(.13,20,12),mat('#D9A15C'));loaf.scale.set(1.5,.65,1);home.scene.add(loaf);addProp('bread',loaf);
 const flowers=new THREE.Group();home.scene.add(flowers);for(let i=0;i<5;i++){cylinder(flowers,.006,.24,'#4A7955',(i-2)*.025,.1,0);const f=new THREE.Mesh(new THREE.SphereGeometry(.035,10,8),mat(i%2?'#D29A90':'#D5BF67'));f.position.set((i-2)*.025,.24+Math.sin(i)*.025,0);flowers.add(f);}addProp('flowers',flowers);
 const hammer=new THREE.Group();home.scene.add(hammer);box(hammer,.03,.35,.035,'#95704A',0,-.10,0);box(hammer,.18,.08,.07,'#83918D',0,.1,0);addProp('hammer',hammer);
 const rope=new THREE.Group();auction.scene.add(rope);for(const x of[-1,1]){cylinder(rope,.04,1.15,'#C0A365',x,.6,.7);cylinder(rope,.20,.05,'#B49A5D',x,.05,.7);}const ropeLine=new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(V(-1,1.1,.7),V(0,.8,.7),V(1,1.1,.7)),24,.025,8,false),mat('#9B3F48'));rope.add(ropeLine);props.rope=rope;
 const taxi=car(road.scene),police=car(road.scene,true);police.scale.setScalar(.85);props.taxi=taxi;props.police=police;
 const belt=new THREE.Group();taxi.add(belt);belt.position.set(.48,1.08,.25);
 const webbing=box(belt,.042,.41,.025,'#393E3E');webbing.rotation.z=-.57;
 const buckle=box(belt,.08,.065,.027,'#AAA99B',-.115,-.174,.01);
 box(buckle,.045,.024,.013,'#A8483F',0,0,.018);
 const turnLamp=box(taxi,.15,.095,.055,'#E8A54C',.93,.82,1.71);turnLamp.material=new THREE.MeshBasicMaterial({color:'#F6BA5A'});
 const crossing=new THREE.Group();road.scene.add(crossing);for(let i=0;i<7;i++)box(crossing,.42,.015,2.1,'#E2DEBC',-2.1+i*.7,.002,2.6);props.crossing=crossing;
 const signal=new THREE.Group();road.scene.add(signal);cylinder(signal,.05,2.8,'#495F59',2.7,1.4,1.5);box(signal,.35,.85,.27,'#35433D',2.7,2.75,1.5);
 const red=cylinder(signal,.10,.04,'#CE514B',2.7,3.0,1.66),green=cylinder(signal,.10,.04,'#67AD73',2.7,2.5,1.66);red.rotation.x=green.rotation.x=Math.PI/2;red.material=new THREE.MeshBasicMaterial({color:'#D6544F'});green.material=new THREE.MeshBasicMaterial({color:'#76B879'});signal.red=red;signal.green=green;props.signal=signal;
 const meter=label(road.scene,['FARE','3 BLOCKS'],.32,.24,0,0,0,'#D9D4B4');addProp('meter',meter);
 const cam=camera(36);let currentWorld=home;const S={worlds,actors,props,events:{},frameInfo:null};
 const vecLocal=(actor,p)=>{actor.group.updateWorldMatrix(true,false);return actor.group.worldToLocal(p.clone()).toArray();};
 const taxiSeatY=.22;
 const gesture=(actor,x,y,z)=>[x,y-upperBodyDrop({},actor.toon.look)*actor.toon.H/1024,z];
 function pose(a,t,options={}){a.pose(t,{mood:'neutral',...options});}
 function place(i,x,z=0,y=0){const a=actors[i];currentWorld.scene.add(a.group);a.group.visible=true;a.at(x,y,z);return a;}
 function prop(name,p=[0,1.1,.3]){const o=props[name];o.visible=true;currentWorld.scene.add(o);o.position.set(...p);return o;}
 function grip(a,name,side='l',offset=[0,0,.014]){const o=props[name];o.visible=true;a.grip(o,side);o.position.set(...offset);return o;}
 function reset(world){
  currentWorld=world;for(const a of actors){a.group.visible=false;a.group.scale.setScalar(1);}
  for(const o of loose){o.visible=false;world.scene.add(o);o.position.set(0,0,0);o.rotation.set(0,0,0);o.scale.setScalar(1);}
  for(const w of Object.values(worlds)){if(w.door){w.door.rotation.y=0;w.chair.rotation.z=0;w.frames[0].rotation.z=0;w.window.pane.rotation.y=0;}}
  props.window=world.window;props.chair=world.chair;rejected.visible=boxSignStand.visible=false;props.paper.unfold.visible=true;
  heroArt.position.set(0,1.65,-2);
  curtain.visible=heroArt.visible=hiddenArt.visible=false;curtain.position.x=-.3;
  props.safe.hinge.rotation.y=0;props.safe.wheel.rotation.z=0;props.book.cover.rotation.y=0;props.paper.unfold.scale.setScalar(1);
  rope.visible=false;taxi.visible=police.visible=crossing.visible=signal.visible=false;taxi.position.set(0,0,0);taxi.door.rotation.y=0;police.position.set(0,0,-4.5);
  for(const car of[taxi,police])car.wheels.forEach(w=>w.rotation.x=0);
  taxi.steering.rotation.z=0;
  belt.visible=turnLamp.visible=false;
  taxi.userData.moving=taxi.userData.siren=police.userData.siren=false;taxi.userData.indicator=false;
  red.visible=true;green.visible=false;props.coin.userData.received=false;S.events={};
 }
 function duo(spec,t){const cast=spec.cast||[0],n=cast.length;cast.forEach((id,i)=>{const x=n===1?-.5:n===2?(i-.5)*1.3:(i-(n-1)/2)*.95;const a=place(id,x);pose(a,t,{mood:spec.mood||'neutral',left:gesture(a,.27,1.10,.22),right:gesture(a,-.27,1.05,.18),head:.08*Math.sin(t*.7+i)});});return cast.map(i=>actors[i]);}
 function coins(spec,u,t){const giver=actors[spec.giver??spec.cast[0]],receiverA=actors[spec.receiver??spec.cast[1]],meet=V(0,giver.toon.look.kid||receiverA.toon.look.kid?.86:1.08,.3),k=motion(u,.10,.65);
  const l=V(...gesture(giver,.27,1.05,.2)).lerp(V(...vecLocal(giver,meet)),k),r=V(...gesture(receiverA,-.27,1.02,.2)).lerp(V(...vecLocal(receiverA,meet)),k);
  pose(giver,t,{left:l.toArray(),mood:'worried',head:-.1});pose(receiverA,t,{right:r.toArray(),mood:'smug',head:-.1});
  const c=props.coin;c.visible=true;if(k<1)giver.grip(c);else{receiverA.grip(c,'r');c.userData.received=true;}c.rotation.y=.12;
 }
 function inTaxi(spec,u,t,moving=false){
  taxi.visible=true;taxi.position.z=moving?-.5+motion(u)*.9:0;taxi.userData.moving=moving;
  taxi.wheels.forEach(w=>w.rotation.x=moving?-t*3:0);taxi.steering.rotation.z=moving?.04*Math.sin(t):0;
  const driver=place(1,-.48,taxi.position.z+.02,taxiSeatY),pass=place(0,.48,taxi.position.z-.12,taxiSeatY);
  pose(driver,t,{legs:'sit',left:[.17,.8,.37],right:[-.21,.8,.37],mood:'smug'});
  pose(pass,t,{legs:'sit',mood:spec.mood||'worried',left:[.25,.76,.17],right:[-.26,.73,.19]});
  belt.visible=spec.lineBelt===true;
  prop('bag',[.54,.68,taxi.position.z+.13]);
  return {driver,pass};
 }
 S.act=(spec,u,t)=>{
  reset(worlds[spec.scene||'home']);let cast=duo(spec,t),a=cast[0],b=cast[1],k=motion(u);
  const at=spec.action;
  props.coin.fakeFace.visible=!!data.fakeCoin&&!spec.realCoin;props.coin.realFace.visible=!props.coin.fakeFace.visible;
  if(spec.mess){currentWorld.chair.rotation.z=-Math.PI/2;currentWorld.frames[0].rotation.z=.35;}
  if(spec.windowOpen)currentWorld.window.pane.rotation.y=.98;
  if(at==='walk'||at==='window'){
   a.at(at==='window'?-2.45+.80*k:-1.5+1.1*k,at==='window'?.29*Math.sin(Math.PI*k):0,at==='window'?-2.75+2.15*k:0);
   pose(a,t,{walk:k>0&&k<1?.55:0,mood:spec.mood||'sly',left:gesture(a,.34,1.17,.20),head:-.12});
   if(at==='window'){currentWorld.window.pane.rotation.y=.98*motion(u,.02,.31);}
  }else if(at==='curtain'||at==='art'){
   curtain.visible=hiddenArt.visible=true;curtain.position.x=at==='curtain'?-.3-4*k:-4.3;
   pose(a,t,{mood:at==='curtain'?'shock':'worried',left:[.5,1.35,.15],head:.14});
  }else if(at==='watch-return'){
   const target=V(.25,1.11,-.5),hand=V(.27,1.4,.2).lerp(V(...vecLocal(a,target)),k);pose(a,t,{left:hand.toArray(),mood:'worried',head:-.13});
   if(k<1)grip(a,'watch');else{prop('watch',target.toArray());props.watch.userData.resting=true;}
   S.events.watchResting=k===1;
  }else if(at==='news'){
   pose(a,t,{left:[.26,.93,.27],right:[-.26,.93,.27],mood:spec.mood||'proud'});
   grip(a,'news','l',[-.26,-.04,.035]);
  }else if(at==='phone'){
   prop('phone',[-.91,1.13,-.52]);
   const cradle=V(-.91,1.26,-.51),ear=V(-.38,1.58,.095),raise=spec.onCall?1:k;
   const hand=V(...vecLocal(a,cradle)).lerp(ear,raise);
   pose(a,t,{right:hand.toArray(),left:[.25,1.04,.1],head:-.12,mood:'worried'});
   grip(a,'receiver','r');props.receiver.rotation.z=lerp(0,Math.PI*.43,raise);
  }else if(at==='book'){
   pose(a,t,{right:[-.25,1.2,.30],left:[.26,1.25,.2],mood:spec.mood||'sly',head:-.1});grip(a,'book','r');props.book.cover.rotation.y=-2.65*k;
  }else if(at==='point'||at==='reaction'){
   cast.forEach((actor,i)=>pose(actor,t,{mood:spec.mood||'shock',head:(i%2?1:-1)*.12,left:gesture(actor,.33+.10*Math.sin(Math.PI*u),1.11+.12*Math.sin(Math.PI*u),.20)}));
   if(spec.art){hiddenArt.visible=true;curtain.visible=true;curtain.position.x=-4.3;}
   if(spec.portrait){heroArt.visible=true;}
  }else if(at==='handshake'){
   const meet=V(0,1.22+.05*Math.sin(u*18)*k,.25);
   pose(a,t,{left:V(.28,1.1,.18).lerp(V(...vecLocal(a,meet)),k).toArray(),mood:'proud'});
   pose(b,t,{right:V(-.28,1.1,.18).lerp(V(...vecLocal(b,meet)),k).toArray(),mood:'happy'});
  }else if(at==='medal'){
   pose(a,t,{mood:'proud',left:[.23,1.25,.2],head:.13});const med=prop('medal',[a.group.position.x,1.12,.06]);med.visible=k===1;
   if(b)pose(b,t,{mood:'happy',right:[lerp(-.3,-.8,k),1.25,.15]});
  }else if(at==='pocket-watch'){
   pose(a,t,{left:[.28,lerp(1.3,.93,k),.20],mood:'worried',head:-.15});grip(a,'watch');props.watch.visible=k<1;
   if(b)pose(b,t,{mood:'shock',left:[.4,1.4,.2],head:-.1});
  }else if(at==='pay'||at==='refund')coins(spec,u,t);
  else if(at==='bag'){
   const bag=prop('bag',[a.group.position.x+.45,lerp(.61,.87,k),.26]);
   pose(a,t,{left:[.45,bag.position.y+.38,.26],mood:spec.mood||'proud'});
  }else if(at==='bag-return'){
   const bag=prop('bag',[.25,lerp(1.28,1.055,k),-.54]);
   pose(a,t,{left:vecLocal(a,bag.position.clone().add(V(0,.39,0))),mood:'sly'});
   S.events.bagResting=k===1;
  }else if(at==='count-coins'){
   const pile=prop('coinPile',[.16,1.055,-.47]);
   const count=Math.min(pile.children.length,Math.floor(u*6)),cycle=u*6%1;
   pile.children.forEach((piece,i)=>{piece.visible=i<count;});
   const hand=V(.25,1.35,.20).lerp(V(...vecLocal(a,pile.position.clone().add(V(0,.07,0)))),motion(cycle,.10,.9));
   pose(a,t,{left:hand.toArray(),head:-.15,mood:'worried'});
   if(count<pile.children.length){grip(a,'coin');props.coin.fakeFace.visible=false;props.coin.realFace.visible=true;}
   S.events.coinCount=count;
  }else if(at==='paper'){
   pose(a,t,{left:[.27,1.27,.25],mood:spec.mood||'worried'});grip(a,'paper');props.paper.unfold.scale.x=lerp(.05,1,k);
  }else if(at==='receipt'){
   pose(a,t,{left:[.28,1.27+.16*k,.25],mood:'proud'});grip(a,'receipt');
  }else if(at==='portrait'){
   heroArt.visible=true;heroArt.position.set(0,1.6,-.55);
   if(a)pose(a,t,{mood:'worried',head:.22,left:[.4,1.36,.15]});
  }else if(at==='coin-show'){
   pose(a,t,{left:gesture(a,.40,1.21,.22),mood:'sly'});grip(a,'coin');props.coin.rotation.y=.15*Math.sin(u*3);
  }else if(at==='coin-macro'){
   prop('coin',[0,1.2,.3]);props.coin.rotation.y=lerp(-.3,.1,k);
  }else if(at==='safe-roll'||at==='safe-handle'||at==='safe-open'||at==='safe-empty'||at==='key-tape'){
   prop('safe',[.75,0,-.5]);
   if(at==='safe-roll'){props.safe.position.x=lerp(1.25,.75,k);pose(a,t,{walk:.3,left:[.50,1.12,.15],mood:'tired'});}
   if(at==='safe-handle'){props.safe.wheel.rotation.z=2.4*k;pose(a,t,{left:[.5,1.2,.3],mood:'worried',head:-.10});}
   if(at==='safe-open'||at==='safe-empty'){props.safe.wheel.rotation.z=1.5;props.safe.hinge.rotation.y=at==='safe-empty'?-1.55:-1.55*motion(u,.30,.8);pose(a,t,{left:[.5,1.3,.3],mood:'shock',head:.12});}
   if(at==='key-tape'){const keyObj=prop('key',[.65,lerp(.20,1.25,k),.25]);pose(a,t,{left:vecLocal(a,keyObj.position.clone()),head:-.15,mood:'sly'});if(k===1)grip(a,'key');}
  }else if(at==='listen'){
   prop('safe',[.75,0,-.5]);pose(a,t,{lean:.10,head:.30,left:[.45,1.4,.2],mood:'sly'});
  }else if(at==='bid'){
   pose(a,t,{left:[lerp(.29,.47,k),lerp(1.06,1.59,k),.17],mood:'proud',head:.1});grip(a,'paddle');
   if(b){const lift=motion(u,.35,.85);pose(b,t,{right:[lerp(-.29,-.43,lift),lerp(1.05,1.50,lift),.17],mood:'angry'});}
  }else if(at==='hammer'){
   pose(a,t,{right:[-.44,1.27,.18],mood:'proud'});grip(a,'hammer','r');prop('safe',[.75,0,-.5]);
  }else if(at==='gavel'){
   const down=motion(u,.15,.35)*(1-motion(u,.62,.80)),y=lerp(1.50,1.235,down);
   a.at(.40,0,-.37);
   pose(a,t,{right:[-.48,y,-.18],mood:'proud'});grip(a,'gavel','r',[0,0,0]);
   const position=props.gavel.getWorldPosition(V());S.events.gavelContact=position.y-.175<=1.062;
  }else if(at==='rope'){
   prop('safe',[.75,0,-.5]);props.safe.hinge.rotation.y=-1.55;prop('rope',[0,0,0]);pose(a,t,{mood:'proud',left:[.35,1.35,.2]});
  }else if(at==='mess'){
   currentWorld.frames[0].rotation.z=.35*k;currentWorld.chair.rotation.z=-Math.PI/2*k;pose(a,t,{left:[.4,1.35,.25],mood:'sly'});
  }else if(at==='tug'){
   const bag=prop('bag',[.12*Math.sin(u*Math.PI*4),.81,.30]);
   for(const [actor,side] of[[a,'l'],[b,'r']]){const hand=vecLocal(actor,bag.position.clone().add(V(0,.38,0)));pose(actor,t,{[side==='l'?'left':'right']:hand,mood:'angry',lean:side==='l'?-.07:.07});}
  }else if(at==='knock'){
   a.at(1.54,0,-2.33);const reach=motion(u,.18,.34)*(1-motion(u,.49,.62));
   const contact=V(1.95,1.32,-2.86),hand=V(-.27,1.15,.06).lerp(V(...vecLocal(a,contact)),reach);
   pose(a,t,{left:hand.toArray(),mood:'tired',head:-.12});
   S.events.knockContact=reach===1;
   currentWorld.door.rotation.y=-.30*motion(u,.72,.95);
  }else if(at==='reject'){
   pose(a,t,{left:[.25,1.3,.25],mood:'tired'});grip(a,'paper');props.paper.rotation.z=.12*Math.sin(Math.PI*k);rejected.visible=k===1;props.paper.unfold.visible=!rejected.visible;
  }else if(at==='bread'){
   pose(a,t,{left:[.25,1.35,.25],mood:'happy'});grip(a,'bread');props.bread.scale.set(1.5,.65,1);
  }else if(at==='flowers'){
   pose(a,t,{left:gesture(a,.43,1.12,.24),mood:'happy'});grip(a,'flowers');
  }else if(at==='car-entry'){
   const {driver,pass}=inTaxi(spec,u,t,false);taxi.door.rotation.y=1.1*Math.sin(Math.PI*k);
   pass.at(lerp(2.0,.48,k),taxiSeatY*motion(k,.48,1)+.13*Math.sin(Math.PI*k),lerp(.5,-.12,k));
   pose(pass,t,{legs:k>.7?'sit':'walk',walk:k<.7?.4:0,mood:'worried',right:[-.28,lerp(1.04,.73,k),.15]});
   grip(pass,'bag','r',[0,-.35,.04]);
  }else if(at==='drive'||at==='redlight'||at==='greenlight'||at==='police-drive'||at==='pull-over'||at==='belt'||at==='officer-window'||at==='meter'){
   const moving=at==='drive'||at==='greenlight'||at==='police-drive',{driver,pass}=inTaxi(spec,u,t,moving);
   if(at==='redlight'||at==='greenlight'){signal.visible=true;red.visible=at==='redlight';green.visible=at==='greenlight';}
   if(at==='belt'){
    const point=V(.36,1.15,.29).lerp(V(.365,.906,.28),k);
    pose(pass,t,{legs:'sit',right:vecLocal(pass,point),mood:'tired'});
    belt.visible=k===1;S.events.beltLatched=belt.visible;
   }
   if(at==='police-drive'||at==='pull-over'||at==='officer-window'){police.visible=true;police.position.set(0,0,-3.8+1.2*k);police.userData.siren=true;police.red.visible=Math.sin(t*9)>0;police.blue.visible=!police.red.visible;}
   if(at==='pull-over'){taxi.position.x=.65*k;driver.at(-.48+taxi.position.x,taxiSeatY,.02);pass.at(.48+taxi.position.x,taxiSeatY,-.12);props.bag.position.x+=taxi.position.x;taxi.userData.indicator=true;turnLamp.visible=Math.sin(t*10)>0;}
   if(at==='officer-window'){
    const cop=place(2,1.85,.15);
    pose(cop,t,{right:[-.6-.18*Math.max(0,Math.sin(u*Math.PI*4)),1.10,.15],mood:'tired'});
    const raise=spec.surrender?k:0;
    pose(pass,t,{legs:'sit',left:[lerp(.24,.41,raise),lerp(.76,1.16,raise),.13],
     right:[lerp(-.25,-.41,raise),lerp(.75,1.16,raise),.13],mood:'shock'});
   }
   if(at==='meter'){prop('meter',[-.19,1.03,.44]);pose(driver,t,{legs:'sit',left:[.28,.79,.42],right:[-.21,.8,.37],mood:'proud'});}
  }else if(at==='crossing'){
   taxi.visible=true;taxi.position.z=-3;crossing.visible=true;const woman=a;woman.at(lerp(-1.4,spec.stop?0:1.4,k),0,2.5);
   pose(woman,t,{walk:k>0&&k<1?.40:0,mood:spec.stop?'worried':'neutral',
    left:[spec.stop?lerp(.28,.37,k):.28,spec.stop?lerp(1.10,1.49,k):1.1,.14],head:-.10});
  }else if(at==='roadblock'){
   prop('bridge',[0,1.27,.05]);boxSignStand.position.set(0,.53,.05);boxSignStand.visible=true;
  }
  if(spec.speed)prop('speed',[1.8,1.60,.5]);
  if(spec.hold){grip(a,spec.hold);}
  S.events={...S.events,coinReceived:props.coin.userData.received,doorAngle:currentWorld.door?.rotation.y||0,
   safeAngle:props.safe.hinge.rotation.y,wheelAngle:props.safe.wheel.rotation.z,bookAngle:props.book.cover.rotation.y,
   paperScale:props.paper.unfold.scale.x,paperAngle:props.paper.rotation.y,bagY:props.bag.position.y,bagX:props.bag.position.x,
   medalVisible:props.medal.visible,watchVisible:props.watch.visible,chairAngle:currentWorld.chair?.rotation.z||0,
   windowAngle:currentWorld.window?.pane.rotation.y||0,claimMarked:rejected.visible,
   carDoorAngle:taxi.door.rotation.y,carDoorOpen:Math.abs(taxi.door.rotation.y)>.005,engineMoving:taxi.visible&&taxi.userData.moving,engineIdle:taxi.visible&&!taxi.userData.moving,
   siren:police.visible&&police.userData.siren,indicator:taxi.userData.indicator};
 };
 S.render=(spec,u,t,blit)=>{
  const cast=(spec.cast||[0]).map(i=>actors[i]).filter(a=>a.group.visible);
  // Taxi modes always include both seated occupants; explicit exterior inserts
  // may isolate a pedestrian or a prop without leaving half-faces at the edges.
  if(['car-entry','drive','redlight','greenlight','police-drive','pull-over','belt','officer-window','meter'].includes(spec.action)){
   for(const i of(spec.action==='officer-window'?[0,1,2]:[0,1]))if(!cast.includes(actors[i]))cast.push(actors[i]);
  }
  for(const actor of actors)if(actor.group.visible&&!cast.includes(actor))actor.group.visible=false;
  const focus=(spec.focus||[]).map(name=>props[name]).filter(Boolean),style=spec.style||'medium';
  let target=V(0,1.3,0),from=V(.35,1.9,5.6),to=V(.1,1.8,5.0),fov=36;
  if(style==='wide'){from=V(.35,2.3,7.6);to=V(.1,2.1,7);}
  if(style==='close'){from=V(.2,1.8,3.7);to=V(.05,1.75,3.3);if(cast.length===1)target.x=cast[0].group.position.x;}
  if(style==='macro'){target=props.coin.getWorldPosition(V());from=target.clone().add(V(.05,.05,1.1));to=target.clone().add(V(0,.02,.95));}
  if(currentWorld===road){target=V(0,1.1,.2);from=V(.4,2.35,6.6);to=V(.2,2.25,6.0);if(spec.action==='crossing'){target=actors[spec.cast[0]].group.position.clone().add(V(0,1.25,0));from=target.clone().add(V(.3,.4,4.4));to=target.clone().add(V(.1,.3,4));}}
  cam.fov=fov;cam.updateProjectionMatrix();cam.position.lerpVectors(from,to,sm(u));cam.lookAt(target);
  for(const actor of cast)actor.face(cam);
  S.frameInfo=fit(cam,{actors:cast,objects:focus,hands:style!=='macro'&&spec.hands!==false});
  E.render(currentWorld.scene,cam,{aperture:0,bloom:.08,vignette:.12,grain:0,warm:.01,sat:.98,t:0});blit();
 };
 return S;
}
