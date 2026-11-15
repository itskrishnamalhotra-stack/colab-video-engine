// Reusable furnished hospital locations. Built once; no per-cut layout changes.
import * as THREE from 'three';
import {box,cylinder,card,words,mat} from './world.js';
export function furnishHospital(lobby,side){
 const s=lobby.scene;
 const clock=new THREE.Group();clock.name='reception_clock';s.add(clock);clock.position.set(2.55,3.45,-4.68);
 const rim=cylinder(clock,.23,.045,'#A6B5A4',0,0,0);rim.rotation.x=Math.PI/2;
 const face=cylinder(clock,.205,.05,'#D7D5B7',0,0,.02);face.rotation.x=Math.PI/2;
 box(clock,.012,.14,.012,'#374E50',.03,.06,.06).rotation.z=-.48;
 box(clock,.12,.012,.012,'#374E50',-.045,.01,.065).rotation.z=.12;
 card(s,words(['RECEPTION','NORTH WING'],{paper:'#405D5B',ink:'#CAD2B5'}),1.4,.48,1.45,2.72,-1.8);
 for(let i=0;i<3;i++){
  const seat=new THREE.Group();s.add(seat);seat.position.set(3.4,0,1.5-i*.65);seat.rotation.y=-Math.PI/2;
  box(seat,.46,.08,.44,'#617F7C',0,.45,0);box(seat,.46,.5,.08,'#617F7C',0,.72,-.20);
  for(const x of[-.18,.18])for(const z of[-.16,.16])box(seat,.025,.45,.025,'#324E53',x,.225,z);
 }
 const clipboard=new THREE.Group();lobby.table.add(clipboard);clipboard.position.set(.36,.85,-.19);clipboard.rotation.x=-Math.PI/2;
 box(clipboard,.24,.33,.015,'#A89572');card(clipboard,words(['ADMISSIONS','NORTH WING'],{paper:'#C7CCB4',ink:'#4E635C'}),.21,.28,0,0,.012);
 for(const [name,set] of [['service',side.service],['ward',side.ward]]){
  for(let z=-1;z>=-10;z-=3){
   for(const y of[2.65,2.78]){const pipe=cylinder(set.scene,.025,2.8,'#80988E',-3.82,y,z);pipe.rotation.x=Math.PI/2;}
   box(set.scene,.08,.12,.22,'#B9B9A1',-3.78,1.12,z);
  }
  const notice=card(set.scene,words([name==='service'?'LAUNDRY ROUTE':'WARD B','KEEP PASSAGE CLEAR'],{paper:'#A5B3A0',ink:'#345455'}),.9,.45,-3.78,2.05,-2.8);notice.rotation.y=Math.PI/2;
 }
 for(let z=-1.4;z>-5;z-=.5)box(side.service.scene,.10,.008,.28,mat('#A1B2A0'),1.45,.002,z);
 const shelf=new THREE.Group();side.service.scene.add(shelf);shelf.position.set(3.45,0,-.3);shelf.name='laundry_shelves';
 for(const y of[.25,.85,1.45]){
  box(shelf,.65,.06,.75,'#5F7978',0,y,0);
  for(let i=0;i<3;i++)box(shelf,.45,.09,.38,['#9BAF9D','#829B94','#ADB8A5'][i],0,y+.08+i*.095,.05);
 }
 for(const x of[-.29,.29])for(const z of[-.34,.34])box(shelf,.035,1.8,.035,'#405D60',x,.9,z);
 const mug=new THREE.Group();side.edit.scene.add(mug);mug.position.set(1.65,.89,.27);cylinder(mug,.075,.14,'#9DAF9A',0,.07,0);
 const handle=new THREE.Mesh(new THREE.TorusGeometry(.045,.012,8,20),mat('#9DAF9A'));handle.position.set(.08,.07,0);mug.add(handle);
 return {clock,clipboard,shelf,mug};
}
