// Directional views of the existing illustrated character family. The body has
// a world-space heading; the card displays the corresponding front/side/back art.
import * as THREE from 'three';
import {Actor,loadActors} from './actor.js';
import {characterView} from './directional_motion.mjs';
export {loadActors};
export {characterView};
export class DirectionalActor extends Actor{
 constructor(scene,options={}){super(scene,options);this.root=this.group;this.group.name=options.id||'mc';this.toon.mesh.name='character_body';this.toon.pivot.name='wardrobe_and_face';this.toon.blob.name='ground_shadow';
  if(options.look)this.toon.restyle(options.look);
  this.appearance=JSON.stringify(this.toon.look);this.contacts={left:true,right:true};this.lastView={view:'front',silhouetteScale:1};
  this.sockets={};for(const [side,arm] of Object.entries(this.arms)){arm.hand.name=this.group.name+'.'+side+'_grip';this.sockets[side]=arm.hand;}
  this.pose(0);
 }
 pose(t,options={}){
  if('walking' in options||'expression' in options){
   const walking=options.walking||false,weight=options.walkWeight??1,phase=(options.distance||0)/.35*Math.PI,swing=walking?Math.sin(phase)*.12*weight:0;
   options={...options,walk:walking?.65*weight:0,phase,
    right:options.right||[-.25,1.02,.11-swing],left:options.left||[.25,1.02,.11+swing],
    mood:({concern:'worried',smile:'happy',shock:'shock',neutral:'neutral'})[options.expression]||'neutral',
    head:(options.headYaw||0)*.3,look:[Math.max(-1,Math.min(1,(options.headYaw||0)*2)),(options.headPitch||0)*2]};
  }
  super.pose(t,options);
  if(this.lastView){this.toon.set({...this.toon.st,...this.lastView});this.updateArms();}
  const S=this.toon.st;this.contacts??={left:true,right:true};
  for(const [side,offset] of[['left',0],['right',Math.PI]])this.contacts[side]=!['walk','run'].includes(S.legs)||Math.max(0,-Math.cos(S.phase+offset))<1e-8;
  return this;
 }
 face(camera){
  if(this.group.userData.downed){super.face(camera);return;}
  const p=this.group.getWorldPosition(new THREE.Vector3());this.lastView=characterView(this.group.rotation.y,Math.atan2(camera.position.x-p.x,camera.position.z-p.z));
  this.toon.set({...this.toon.st,...this.lastView});super.face(camera);
 }
 grip(object,side='r'){super.grip(object,side);object.userData.allowSocketTransfer=true;object.userData.socket=this.arms[side].hand.name;return object;}
 assertIntact(){
  if(!this.toon.mesh.visible||this.toon.mesh.parent!==this.toon.pivot||this.toon.pivot.parent!==this.group)throw Error('Complete cartoon body was hidden or detached');
  for(const arm of Object.values(this.arms))if(arm.hand.parent!==this.group||arm.segments.some(o=>o.parent!==this.group||!o.visible))throw Error('Character limbs were hidden or detached');
  if(this.appearance!==JSON.stringify(this.toon.look))throw Error('Unregistered character wardrobe/identity change');
  return true;
 }
}
