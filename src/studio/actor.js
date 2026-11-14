// The reference's cartoon visual language: a drawn puppet face/body, not a human mannequin.
import * as THREE from 'three';
import {Toon} from './toon.js';
import {upperBodyDrop} from './toon_state.mjs';
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z),UP=V(0,1,0);
const ink=new THREE.MeshStandardMaterial({color:'#25272B',roughness:.9});
const rod=new THREE.CylinderGeometry(.012,.012,1,8),mitten=new THREE.SphereGeometry(.039,16,12);
let nextId=0;
export async function loadActors(){}
export class Actor{
 constructor(scene,{coat='#BD9D65',hat='#605D60',police=false,extra=[],height=1.85}={}){
  this.id=nextId++;this.police=police;
  this.toon=new Toon({body:coat,head:'#F3F1E8',hat:police?'mailcap':'bowler',hatCol:hat,band:police?'#C9B263':'#454047',pattern:police?'police':'trench',neck:'collar',extra:police?['mustache',...extra]:['thinmustache',...extra],mustacheCol:'#77766C'},{height,res:this.id<5?2:1.25,castShadow:false});
  this.group=this.toon.group;scene.add(this.group);this.group.userData.actor=this;
  this.arms={};
  this.stepLegs={};
  for(const side of['left','right']){
   const segments=Array.from({length:8},()=>{const mesh=new THREE.Mesh(rod,ink);this.group.add(mesh);return mesh;});
   const shoe=new THREE.Mesh(new THREE.SphereGeometry(1,16,10),ink);shoe.scale.set(.052,.025,.082);this.group.add(shoe);
   this.stepLegs[side]={segments,shoe};
  }
  for(const side of['l','r']){
   const segments=Array.from({length:10},()=>{const o=new THREE.Mesh(rod,ink);this.group.add(o);return o;});
   const hand=new THREE.Group(),glove=new THREE.Mesh(mitten,ink);glove.scale.set(.9,1.05,.7);glove.position.z=.035;hand.add(glove);this.group.add(hand);this.arms[side]={segments,hand};
  }
  this.pose(0);
 }
 at(x,y,z,rotation=0){this.group.position.set(x,y,z);this.group.rotation.set(0,rotation,0);this.group.userData.downed=false;return this;}
 pose(t,{left,right,walk=0,legs=walk>.05?'walk':'stand',talk=0,mood='smug',lean=0,head=0,look=null,blink=null,headTilt=0,feet=null,phase=null}={}){
  const bob=walk*Math.abs(Math.sin(phase??t*7))*6,cycle=(t+this.id*.71)%3.7;
  const eyelid=blink??(cycle<.16?Math.sin(cycle/.16*Math.PI):0);
  // Narration is off-screen. Mouth changes convey acting, not random pseudo speech.
  const reaction=this.police&&mood==='happy'?'laugh':mood;
  this.toon.set({hideArms:true,mood:reaction,look:look||[THREE.MathUtils.clamp(head*2.5,-1,1),lean>.05?.45:0],blink:eyelid,talk:reaction==='shock'?.25:0,headTilt:headTilt+head*8,
   legs,hideLegs:!!feet,phase:phase??t*7+this.id*.7,bob,lean:THREE.MathUtils.radToDeg(lean)*.4,squash:reaction==='laugh'?Math.sin(t*8)*.015:0});
  this.footPose=feet;
  this.targets={l:left??[.27,.92,.07],r:right??[-.27,.92,.07]};
  this.restHands={l:left==null,r:right==null};
  this.updateArms();
 }
 face(camera){if(!this.group.userData.downed)this.toon.face(camera);this.updateArms();}
 lieDown(t,{pitch=-Math.PI/2,roll=0}={}){
  this.group.userData.downed=true;this.group.rotation.set(pitch,0,roll);this.toon.pivot.rotation.set(0,0,0);
  this.pose(t,{mood:'tired',blink:1,left:[.26,.8,.03],right:[-.26,.8,.03]});
  this.toon.blob.visible=false;return this;
 }
 updateArms(){
  this.group.updateMatrixWorld(true);
  const {H,st,look,pivot}=this.toon,units=H/1024,drop=upperBodyDrop(st,look);
  for(const [name,leg] of Object.entries(this.stepLegs)){
   const foot=this.footPose?.[name],visible=!!foot;
   leg.shoe.visible=visible;leg.segments.forEach(o=>o.visible=visible);
   if(!foot)continue;
   const sign=name==='left'?-1:1,hipPx=(look.pattern==='trench'||look.pattern==='police')?774:574;
   const start=V(sign*42*units,(1000-hipPx-drop)*units,.01).applyMatrix4(pivot.matrix);
   const end=V(foot.x,foot.y+.025,foot.z),mid=start.clone().lerp(end,.5);mid.z+=.13;mid.y+=.045;
   const curve=new THREE.QuadraticBezierCurve3(start,mid,end);
   leg.segments.forEach((o,i)=>{const a=curve.getPoint(i/8),b=curve.getPoint((i+1)/8);o.position.copy(a).add(b).multiplyScalar(.5);o.scale.y=a.distanceTo(b)*1.05;o.quaternion.setFromUnitVectors(UP,b.sub(a).normalize());});
   leg.shoe.position.copy(end);leg.shoe.rotation.y=pivot.rotation.y;
  }
  const lean=THREE.MathUtils.degToRad(st.lean||0);
  for(const side of['l','r']){
   const sign=side==='l'?1:-1;
   // These are the same shoulder pixels as the drawn arms in drawToon.
   const start=V(sign*66*units*(st.silhouetteScale||1),(1000-376-drop)*units,.014).applyAxisAngle(V(0,0,1),-lean).applyMatrix4(pivot.matrix);
   const end=V(...this.targets[side]);
   if(this.restHands[side])end.y-=drop*units;
   const mid=start.clone().lerp(end,.55);mid.x+=sign*.045;mid.y-=.06;
   const curve=new THREE.QuadraticBezierCurve3(start,mid,end),{segments,hand}=this.arms[side];
   segments.forEach((o,i)=>{const a=curve.getPoint(i/segments.length),b=curve.getPoint((i+1)/segments.length);o.position.copy(a).add(b).multiplyScalar(.5);o.scale.y=a.distanceTo(b)*1.08;o.quaternion.setFromUnitVectors(UP,b.sub(a).normalize());});
   hand.position.copy(end);
  }
  this.group.updateMatrixWorld(true);
 }
 grip(object,side='l'){
  const hand=this.arms[side].hand;if(object.parent!==hand)hand.add(object);
  object.position.set(0,0,.014);object.rotation.set(0,0,0);
 }
 handPoint(side='l'){return this.arms[side].hand.getWorldPosition(V());}
}
