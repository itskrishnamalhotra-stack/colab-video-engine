// Story-independent hospital equipment, playable screens, doors and trolley.
import * as THREE from 'three';
import {V,box,cylinder,card,texture,words,makeScene,mat} from './world.js';
import {drawToon} from './toon.js';
export function makeFireDoor(parent){
 const g=new THREE.Group();parent.add(g);
 for(const x of[-.77,.77])box(g,.12,2.8,.2,'#738C86',x,1.4,0);
 box(g,1.65,.12,.2,'#738C86',0,2.8,0);
 const leaf=new THREE.Group();leaf.position.x=-.7;g.add(leaf);
 box(leaf,1.4,2.65,.12,'#6E8176',.7,1.325,0);
 box(leaf,.85,.5,.14,'#223E45',.7,1.98,0);
 for(let i=0;i<6;i++){box(leaf,.008,.46,.016,'#82988E',.32+i*.15,1.98,.08);box(leaf,.81,.008,.016,'#82988E',.7,1.78+i*.08,.08);}
 const handle=box(leaf,.12,.04,.10,'#B4BBA1',1.17,1.08,.11);
 box(leaf,.9,.075,.10,'#A3B0A3',.7,.97,.13);
 const latch=box(g,.55,.06,.09,'#C3C9AD',.56,1.4,.18);
 const stop=box(g,.15,.045,.10,'#263E3D',.48,.024,.18);
 Object.assign(g,{leaf,handle,latch,stop});return g;
}
export function makeGurney(parent){
 const g=new THREE.Group();parent.add(g);const wheels=[];
 box(g,.80,.11,1.95,'#9DAFA0',0,.75,0);box(g,.74,.10,1.89,'#687E7C',0,.84,0);
 for(const x of[-.34,.34])for(const z of[-.77,.77]){
  cylinder(g,.022,.46,'#92ABA6',x,.49,z);const pivot=new THREE.Group();pivot.position.set(x,.13,z);g.add(pivot);
  const tyre=new THREE.Group();pivot.add(tyre);const rubber=new THREE.Mesh(new THREE.CylinderGeometry(.13,.13,.07,20),mat('#273C40'));rubber.rotation.z=Math.PI/2;tyre.add(rubber);
  const contact=new THREE.Mesh(new THREE.SphereGeometry(.007,8,6),mat('#A6B8A7'));contact.position.set(.038,-.132,0);tyre.add(contact);contact.visible=wheels.length===0;wheels.push({pivot,tyre,contact});
 }
 for(const x of[-.40,.40]){box(g,.025,.025,1.83,'#ADC2B7',x,1.01,0);for(const z of[-.7,.7])cylinder(g,.015,.23,'#ADC2B7',x,.9,z);}
 const grip=new THREE.Object3D();grip.position.set(0,.98,.94);g.add(grip);
 const patient=new THREE.Group();patient.position.set(0,.90,-.67);g.add(patient);
 Object.assign(g,{wheels,grip,patient});return g;
}
export function makePhone(parent,{color='#1D3036'}={}){
 const g=new THREE.Group();parent.add(g);box(g,.155,.30,.025,color);
 const labels=new Map();
 for(const [name,lines] of Object.entries({play:['VOICE MEMO','PLAY  >'],silence:['DO NOT','ANSWER'],plan:['RECORDING','THEN LATCH'],test:['FOLLOW THE','RECORDING'],call:['EMERGENCY','CALLING...'],help:['IT MOVES WHEN','WE ANSWER']})){
  const o=card(g,words(lines,{paper:'#C1CDBB',ink:'#263E43',font:'sans-serif'}),.136,.251,0,0,.014);labels.set(name,o);
 }
 g.setMode=mode=>{for(const [name,o] of labels)o.visible=name===mode;g.userData.mode=mode;};g.setMode('play');return g;
}
export function makeMonitor(parent,{portable=false,appearance=null}={}){
 const g=new THREE.Group(),lid=new THREE.Group();parent.add(g);g.add(lid);g.lid=lid;
 box(lid,.94,.57,.09,'#263D42',0,.36,0);
 if(portable){box(g,.98,.045,.65,'#657D7B',0,.03,.25);for(let r=0;r<4;r++)for(let c=0;c<10;c++)box(g,.067,.009,.045,'#29454B',-.37+c*.082,.06,.12+r*.07);box(g,.25,.009,.10,'#90A59A',0,.06,.48);}
 else{box(g,.16,.22,.10,'#344E50',0,.04,0);box(g,.49,.04,.32,'#425C5C',0,-.06,0);}
 const modes=new Map();
 for(const mode of['ben','trolley','door','black','covered','impostor','waveform']){
  const image=texture((ctx,w,h)=>{
   ctx.fillStyle='#244247';ctx.fillRect(0,0,w,h);ctx.fillStyle='#557777';ctx.fillRect(0,h*.70,w,h*.3);
   for(let i=0;i<5;i++){ctx.strokeStyle='#395F61';ctx.lineWidth=14;ctx.strokeRect(70+i*145,110,75,370);}
   if(['ben','impostor'].includes(mode)){ctx.save();ctx.translate(w*.28,h*.05);ctx.scale(.46,.46);drawToon(ctx,{body:'#AA7956',hat:'beanie',hatCol:'#A96A42',pattern:'plain',neck:'collar',extra:[],...appearance,head:mode==='ben'?'#F3F1E8':'#BAC8B8'},{mood:mode==='ben'?'neutral':'smug',armL:[48,10],armR:[8,6],legs:'stand'});ctx.restore();}
   if(mode==='trolley'){ctx.fillStyle='#97AD9D';ctx.fillRect(w*.48,h*.52,w*.34,35);for(const x of[.5,.79]){ctx.fillStyle='#172E35';ctx.fillRect(w*x,h*.58,12,80);ctx.beginPath();ctx.arc(w*x,h*.76,17,0,7);ctx.fill();}}
   if(mode==='door'){ctx.fillStyle='#7B9388';ctx.fillRect(w*.34,h*.14,w*.32,h*.60);ctx.fillStyle='#21393D';ctx.fillRect(w*.43,h*.3,w*.14,h*.15);}
   if(mode==='black'){ctx.fillStyle='#101C21';ctx.fillRect(0,0,w,h);}
   if(mode==='covered'){ctx.fillStyle='#AA7956';ctx.fillRect(0,0,w,h);ctx.fillStyle='#C0A770';ctx.fillRect(w*.6,0,w*.12,h);}
   if(mode==='waveform'){ctx.fillStyle='#142B31';ctx.fillRect(0,0,w,h);ctx.strokeStyle='#A9CBB4';ctx.lineWidth=4;for(const offset of[.33,.65]){ctx.beginPath();for(let x=20;x<w-20;x++){const y=h*offset+Math.sin(x*.12)*Math.sin(x*.019)*39;ctx.lineTo(x,y);}ctx.stroke();}}
   ctx.fillStyle='#B8CFBC';ctx.font='bold 32px monospace';ctx.fillText('CAM 02  REC',20,48);ctx.fillText(mode==='impostor'?'04:17:08':'23:41:12',w-235,h-30);
  },1024,576);
  const screen=card(lid,image,.86,.48,0,.36,.052);modes.set(mode,screen);
 }
 g.setMode=mode=>{for(const [name,o] of modes)o.visible=name===mode;g.userData.mode=mode;};g.setMode('ben');
 const playhead=box(lid,.018,.065,.012,'#CEBE86',-.3,.13,.065);g.playhead=playhead;return g;
}
export function hospitalSideSets(E){
 const service=makeScene(E,true),out=makeScene(E,false),ward=makeScene(E,true),edit=makeScene(E,true);
 edit.scene.background=new THREE.Color('#314C51');edit.lights.key.color.set('#E5C69C');edit.lights.key.intensity=2.5;
 box(edit.scene,7,.12,7,'#748B80',0,-.08,-1);box(edit.scene,7,3.4,.15,'#557270',0,1.7,-2.8);
 box(edit.scene,2.3,1.3,.08,'#AABAA7',-1.8,2,-2.7);box(edit.scene,2.1,1.1,.09,'#284F60',-1.8,2,-2.64);
 box(edit.scene,2.3,.10,.9,'#6E877E',.9,.8,0);for(const x of[0,1.8])for(const z of[-.3,.3])box(edit.scene,.06,.8,.06,'#2B4649',x,.4,z);
 for(let i=0;i<3;i++)box(edit.scene,.43,.04,.30,['#C1B599','#506C69','#A37D68'][i],1.65,.87+i*.045,-.12);
 for(const S of[service,ward]){
  const s=S.scene;s.background=new THREE.Color('#20383B');s.fog=new THREE.Fog('#20383B',14,34);S.lights.key.intensity=1.7;
  box(s,8,.12,16,'#71857E',0,-.08,-4);box(s,.15,3.9,16,'#496668',-4,1.9,-4);box(s,.15,3.9,16,'#496668',4,1.9,-4);box(s,8,.12,16,'#2B474B',0,3.9,-4);
  for(let z=-2;z>-13;z-=3){box(s,1.8,2.8,.12,'#748B7F',2.6,1.4,z);box(s,.7,.5,.14,'#244147',2.6,1.85,z+.03);box(s,1.3,.04,.24,mat('#D5DEC7',{emissive:'#B8CCB6',emissiveIntensity:.4}),0,3.65,z);}
 }
 const fireDoor=makeFireDoor(service.scene);fireDoor.position.set(-1.8,0,-2.3);
 card(service.scene,words(['LAUNDRY','SERVICE EXIT'],{paper:'#AEC0A9',ink:'#294648'}),1.4,.5,1.3,2.8,-2.6);
 const ramp=new THREE.Group();service.scene.add(ramp);box(ramp,1.2,.045,2.4,'#A7B9AE');for(let i=0;i<16;i++)box(ramp,1.1,.009,.023,'#698580',0,.027,-1.1+i*.145);
 ramp.position.set(1.5,.18,-3.4);ramp.rotation.x=-.15;
 for(let i=0;i<3;i++)box(service.scene,1.5,(i+1)*.12,.35,'#748E82',1.5,(i+1)*.06,-2.6-i*.35);
 const exit=makeFireDoor(service.scene);exit.position.set(1.5,0,-5.0);
 card(service.scene,words(['EXIT'],{paper:'#33735C',ink:'#DFE7C4'}),.85,.29,1.5,3,-4.99);
 const s=out.scene;s.background=new THREE.Color('#879F9C');s.fog=new THREE.Fog('#879F9C',22,65);out.lights.key.intensity=2.3;
 box(s,20,.15,18,'#687C77',0,-.1,-1);box(s,14,7,.4,'#677D78',0,3.5,-3);
 for(let i=0;i<5;i++){box(s,1.25,1.4,.10,'#2E4E51',-5+i*2.5,4.8,-2.76);box(s,1.3,.08,.13,'#A5AF99',-5+i*2.5,4.06,-2.7);}
 const outerDoor=makeFireDoor(s);outerDoor.position.set(0,0,-2.7);
 card(s,words(['NORTH WING','SERVICE ENTRANCE'],{paper:'#B5B9A1',ink:'#304E51'}),2.3,.65,0,3.5,-2.76);
 const ambulance=new THREE.Group();s.add(ambulance);box(ambulance,2.5,1.8,4.5,'#BBC7B7',5,1.1,1);box(ambulance,2.35,.50,.10,'#406268',5,1.57,3.30);box(ambulance,.60,.12,.28,'#9E5552',5,2.08,1);ambulance.visible=false;
 return {service,ward,out,edit,fireDoor,exit,outerDoor,ramp,ambulance};
}
