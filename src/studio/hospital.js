import * as THREE from 'three';
import {makeScene,box,cylinder,mat,texture,card,words,V} from './world.js';
export function hospital(E){
 const set=makeScene(E,true),s=set.scene;
 s.background=new THREE.Color('#17272D');s.fog=new THREE.Fog('#17272D',16,38);
 set.lights.key.intensity=1.45;set.lights.key.position.set(1,6,5);set.lights.rim.intensity=1.0;
 const tile=texture((g,w,h)=>{g.fillStyle='#687E7B';g.fillRect(0,0,w,h);for(let r=0;r<8;r++)for(let c=0;c<8;c++){g.fillStyle=(r+c)%2?'#718783':'#91A098';g.fillRect(c*w/8+2,r*h/8+2,w/8-4,h/8-4);}},512,512);
 tile.wrapS=tile.wrapT=THREE.RepeatWrapping;tile.repeat.set(2,7);
 box(s,8,.15,17,mat('white',{map:tile}),0,-.10,-4);
 box(s,.18,5.4,17,'#496568',-4.0,2.7,-4);box(s,.18,5.4,17,'#4D6566',4.0,2.7,-4);
 box(s,8,.15,17,'#2D474F',0,5.4,-4);
 for(const side of[-1,1]){box(s,.07,.85,17,'#2B4C52',side*3.88,.45,-4);box(s,.08,.055,17,'#A2A994',side*3.84,.93,-4);}
 // A real flight of stairs and landing, with rails that rise with the treads.
 const stairX=-2.65,firstZ=-1.75,count=10,rise=.18,run=.32;
 for(let i=0;i<count;i++){
  box(s,1.75,(i+1)*rise,run,'#87968B',stairX,(i+1)*rise/2,firstZ-i*run);
  box(s,1.74,.025,.045,'#B9BCA7',stairX,(i+1)*rise+.012,firstZ-i*run+.14);
  for(const side of[-1,1])cylinder(s,.017,.85,'#91A5A0',stairX+side*.90,(i+1)*rise+.44,firstZ-i*run);
 }
 for(const side of[-1,1]){
  const a=V(stairX+side*.90,.99,firstZ+.12),b=V(stairX+side*.90,count*rise+.85,firstZ-(count-1)*run-.12);
  const rail=new THREE.Mesh(new THREE.CylinderGeometry(.025,.025,a.distanceTo(b),14),mat('#A5B7AF'));
  rail.position.copy(a).add(b).multiplyScalar(.5);rail.quaternion.setFromUnitVectors(V(0,1,0),b.clone().sub(a).normalize());s.add(rail);
 }
 box(s,2.4,.14,1.7,'#87968B',-2.65,1.73,-5.28);
 box(s,2.5,3.5,.18,'#4C6969',-2.65,3.45,-6.15);
 box(s,1.28,2.7,.08,'#9EA88F',-2.65,3.15,-6.02);box(s,1.12,2.55,.10,'#29484E',-2.65,3.07,-5.95);
 card(s,words(['LEVEL 2'],{paper:'#536D6B',ink:'#DCE0C4'}),1.15,.3,-2.65,4.8,-6.01);
 card(s,words(['NORTH WING','NO PUBLIC ACCESS'],{paper:'#9DA795',ink:'#2B464A'}),1.52,.62,2.6,2.5,-4.82);
 for(let i=0;i<4;i++){
  const z=-3.5-i*3;box(s,2.8,3.3,.18,'#527175',2.6,1.65,z-1.5);
  box(s,1.2,2.65,.08,'#899B90',2.5,1.33,z-1.38);box(s,1.05,2.5,.09,'#29494F',2.5,1.27,z-1.32);
  box(s,.55,.68,.035,'#1B343C',2.5,1.7,z-1.25);
  card(s,words([String(104+i)],{paper:'#B8B9A0',ink:'#29454B'}),.30,.19,2.5,2.19,z-1.22);
  cylinder(s,.035,.05,'#B9BDA4',2.85,1.1,z-1.23).rotation.x=Math.PI/2;
 }
 for(const [x,y,z] of[[0,4.8,-.3],[-2.7,5,-5],[2.5,4.6,-7]]){
  box(s,1.25,.045,.36,mat('#D5DFC6',{emissive:'#C3D6BE',emissiveIntensity:.5}),x,y,z);
  const glow=new THREE.PointLight('#B7D1C2',2.4,9,2);glow.position.set(x,y-.12,z);s.add(glow);
 }
 const table=new THREE.Group();s.add(table);table.position.set(1.3,0,.35);
 box(table,1.55,.10,.80,'#687B77',0,.78,0);
 for(const x of[-.63,.63])for(const z of[-.28,.28])box(table,.055,.75,.055,'#2C4148',x,.37,z);
 const cablePoints=[V(1.1,.82,.2),V(.8,.06,.1),V(.2,.035,.45),V(-1,.035,-.35),V(-2.1,.035,-1.3)];
 for(let i=0;i<10;i++)cablePoints.push(V(-2.60,(i+1)*rise+.025,firstZ-i*run+.08));
 cablePoints.push(V(-2.60,1.84,-5.15));
 const route=new THREE.CatmullRomCurve3(cablePoints),cable=new THREE.Group();s.add(cable);
 for(let i=0;i<8;i++){
  const segment=new THREE.Curve();segment.getPoint=t=>route.getPoint((i+t)/8);
  const mesh=new THREE.Mesh(new THREE.TubeGeometry(segment,24,.012,8,false),mat('#BEC4AD'));cable.add(mesh);
 }
 return {...set,table,cable,cableFocus:cable.children[1],stairs:{x:stairX,z:firstZ,count,rise,run}};
}
