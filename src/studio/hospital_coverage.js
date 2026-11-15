// Motived hospital coverage, shared by stories using hospitalPerformance.
import * as THREE from 'three';
import {V} from './world.js';
import {objectFramePoints} from './camera_framing.mjs';
const centre=o=>{const points=objectFramePoints(o),b=new THREE.Box3();points.forEach(p=>b.expandByPoint(p));return points.length?b.getCenter(V()):o.getWorldPosition(V());};
const sm=u=>{u=Math.max(0,Math.min(1,u));return u*u*(3-2*u);};
export function hospitalCoverage(cam,state,row,view,u,index){
 const action=row.action,detail=state.detail,actor=state.focus?.toon?state.focus:null;
 let actors=state.cast.slice(),objects=state.important.slice(),target=V(0,1.15,-.35),distance=5.6,side=.65,height=.65;
 const close=view==='detail',follow=view==='follow',reverse=view==='reverse';
 const stand=actors.filter(a=>!a.group.userData.downed);
 // A patient is framed as part of the complete trolley/evidence object. Radio
 // and reaction coverage names the speaking/listening subjects, not every
 // background silhouette; the body and duplicate remain physically present.
 if(!['body','bodywide','offradio'].includes(action))actors=stand.slice();
 if(!['reveal','bodywide'].includes(action)){
  const relevant=actors.filter(a=>a.group.name!=='impostor'||a===actor);
  if(relevant.length)actors=relevant;
 }
 const framed=actors.filter(a=>!a.group.userData.downed);
 if(framed.length){target=framed.reduce((p,a)=>p.add(a.group.getWorldPosition(V())),V()).multiplyScalar(1/framed.length);target.y+=1.13;}
 if(['stairs','stairdetail'].includes(action)){
  target=state.focus.group.getWorldPosition(V()).add(V(0,.85,0));distance=4.5;side=2.15;height=1.25;
 }
 if(['gurney','wheel','transfer'].includes(action)&&state.props.cart.visible){target=centre(state.props.cart);target.y+=.25;objects.push(state.props.cart);side=-1.65;distance=5.0;height=1.2;}
 if(['body','bodywide','offradio'].includes(action)){target=V(-.75,1.0,-.7);distance=6.0;side=1.15;height=1.1;}
 if(close){
  if(detail&&!detail.toon){
   target=centre(detail);objects=[detail];
   const owners=state.cast.filter(a=>!a.group.userData.downed).map(a=>({a,d:Math.min(a.handPoint('l').distanceTo(target),a.handPoint('r').distanceTo(target))})).sort((a,b)=>a.d-b.d);
   const owner=owners[0]?.d<.90?owners[0].a:null;
   actors=owner?[owner]:[];
   if(owner){target.lerp(owner.group.localToWorld(V(0,1.35,.02)),.38);distance=2.7;side=owner.group.position.x>0?-1.0:1.0;height=.4;}
   else{distance=action==='offradio'?2.1:1.8;side=.35;height=.65;}
   if(['door','exit','latch','ramp'].includes(action)){actors=actor?[actor]:actors;distance=3.9;side=1.25;height=.55;}
   if(action==='stairdetail'){actors=[state.focus];objects=Object.values(state.focus.stepLegs).map(l=>l.shoe);target=state.focus.group.getWorldPosition(V()).add(V(0,.7,0));distance=3;side=1.65;height=.6;}
  }else{
   const who=detail?.toon?detail:actor||stand[0];actors=who?[who]:[];objects=[];
   if(who){target=who.group.localToWorld(V(0,1.45,.04));side=who.group.position.x>0?-.55:.55;distance=2.35;height=.12;
    if(who.group.userData.downed){target=centre(who.group);objects=[who.group];distance=3.3;height=1.55;}}
  }
 }
 if(follow){distance=3.9;side=-2.2;height=.65;}
 if(reverse&&index===42){const watcher=state.cast.find(a=>a.group.name==='impostor');if(watcher){actors=[watcher];objects=[];target=watcher.group.localToWorld(V(0,1.45,.04));distance=2.6;side=-.25;height=.1;}}
 const q=sm(u),travel=.40*(q-.5),push=(index%3===0?-.45:.25)*(q-.5);
 cam.fov=close?36:42;cam.updateProjectionMatrix();
 const offset=V(side+travel,height,distance+push);
 if(reverse)offset.applyAxisAngle(V(0,1,0),-.48);
 cam.position.copy(target).add(offset);cam.lookAt(target);
 for(const a of state.cast)a.face(cam);
 // An off-radio insert also keeps the complete, connected owner in its framing.
 if(action==='offradio'&&close){const body=state.cast.find(a=>a.group.userData.downed);if(body){actors=[body];objects=[state.props.offRadio,body.group];}}
 const contract={actors,objects:objects.filter(o=>o.visible),hands:true,safe:{left:-.90,right:.90,bottom:-.61,top:.88}};
 return contract;
}
