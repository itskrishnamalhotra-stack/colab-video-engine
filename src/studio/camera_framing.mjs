// Frame-aware camera safety for portrait stories. Pure geometry; no GPU reads.
import {upperBodyDrop} from './toon_state.mjs';

const DEFAULT_SAFE={left:-.84,right:.84,bottom:-.26,top:.87};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));

export function projectedBounds(camera,points){
 camera.updateMatrixWorld(true);
 const out={left:Infinity,right:-Infinity,bottom:Infinity,top:-Infinity,behind:0};
 for(const p of points){
  const local=p.clone().applyMatrix4(camera.matrixWorldInverse);
  if(local.z>=-camera.near)out.behind++;
  const q=p.clone().project(camera);
  out.left=Math.min(out.left,q.x);out.right=Math.max(out.right,q.x);
  out.bottom=Math.min(out.bottom,q.y);out.top=Math.max(out.top,q.y);
 }
 return out;
}

export function fitsSafeFrame(bounds,safe=DEFAULT_SAFE,tolerance=1e-5){
 return !bounds.behind&&bounds.left>=safe.left-tolerance&&bounds.right<=safe.right+tolerance&&
  bounds.bottom>=safe.bottom-tolerance&&bounds.top<=safe.top+tolerance;
}

export function fitCamera(camera,points,{safe=DEFAULT_SAFE}={}){
 if(!points.length)throw Error('A framing contract must name visible subjects');
 camera.updateMatrixWorld(true);
 const before=projectedBounds(camera,points);
 if(fitsSafeFrame(before,safe))return {before,after:before,adjusted:false,dolly:0};
 const local=points.map(p=>p.clone().applyMatrix4(camera.matrixWorldInverse));
 const tanV=Math.tan(camera.fov*Math.PI/360)/camera.zoom,tanH=tanV*camera.aspect;
 function intervals(back){
  let x0=-Infinity,x1=Infinity,y0=-Infinity,y1=Infinity;
  for(const p of local){
   const depth=-p.z+back;
   if(depth<=camera.near*1.1)return null;
   x0=Math.max(x0,p.x-safe.right*tanH*depth);x1=Math.min(x1,p.x-safe.left*tanH*depth);
   y0=Math.max(y0,p.y-safe.top*tanV*depth);y1=Math.min(y1,p.y-safe.bottom*tanV*depth);
  }
  return x0<=x1&&y0<=y1?{x0,x1,y0,y1}:null;
 }
 let back=0,range=intervals(0);
 if(!range){
  let high=1;while(!intervals(high)&&high<1024)high*=2;
  if(!intervals(high))throw Error('Framing subjects cannot fit the camera');
  let low=0;for(let i=0;i<40;i++){const mid=(low+high)/2;if(intervals(mid))high=mid;else low=mid;}
  back=high+.02;range=intervals(back);
 }
 const dx=clamp(0,range.x0,range.x1),dy=clamp(0,range.y0,range.y1);
 const right=camera.position.clone().set(1,0,0).applyQuaternion(camera.quaternion);
 const up=camera.position.clone().set(0,1,0).applyQuaternion(camera.quaternion);
 const backward=camera.position.clone().set(0,0,1).applyQuaternion(camera.quaternion);
 camera.position.addScaledVector(right,dx).addScaledVector(up,dy).addScaledVector(backward,back);
 camera.updateMatrixWorld(true);
 return {before,after:projectedBounds(camera,points),adjusted:true,dolly:back,pan:[dx,dy]};
}

export function objectFramePoints(object){
 if(!object.visible)return [];
 object.updateWorldMatrix(true,true);const points=[];
 object.traverseVisible(o=>{
  if(!o.geometry)return;
  if(!o.geometry.boundingBox)o.geometry.computeBoundingBox();
  const b=o.geometry.boundingBox;if(!b||b.isEmpty())return;
  for(const x of[b.min.x,b.max.x])for(const y of[b.min.y,b.max.y])for(const z of[b.min.z,b.max.z])
   points.push(object.position.clone().set(x,y,z).applyMatrix4(o.matrixWorld));
 });
 return points;
}

export function actorFramePoints(actor,{hands=true,body=false,faceOnly=false}={}){
 if(typeof actor.framePoints==='function')return actor.framePoints({hands,body,faceOnly});
 const toon=actor.toon,S=toon.st||{},L=toon.look||{},H=toon.H;
 actor.group.updateWorldMatrix(true,true);
 const by=upperBodyDrop(S,L);
 const hy=178+by*.99,headAngle=(S.headTilt||0)*Math.PI/180,lean=(S.lean||0)*Math.PI/180;
 const points=[];
 // Conservative head + hat silhouette bounds, transformed by the same canvas
 // head tilt/squash, body lean and billboard pivot as the actual puppet.
 for(const px of(faceOnly?[115,397]:[65,447]))for(const py of(faceOnly?[40+by,318+by]:[-40+by,335+by])){
  const sx=(px-256)*(1+(S.squash||0)*-.3),sy=(py-hy)*(1+(S.squash||0));
  const hx=sx*Math.cos(headAngle)-sy*Math.sin(headAngle),y=hy+sx*Math.sin(headAngle)+sy*Math.cos(headAngle);
  const rx=hx*Math.cos(lean)-(y-1000)*Math.sin(lean),ry=hx*Math.sin(lean)+(y-1000)*Math.cos(lean);
  points.push(actor.group.position.clone().set(rx*H/1024,-ry*H/1024,0).applyMatrix4(toon.pivot.matrixWorld));
 }
 if(hands)for(const side of(Array.isArray(hands)?hands:Object.keys(actor.arms))){const arm=actor.arms[side];
  const p=arm.hand.getWorldPosition(actor.group.position.clone());
  for(const x of[-.065,.065])for(const y of[-.065,.065])for(const z of[-.065,.065])
   points.push(p.clone().add(actor.group.position.clone().set(x,y,z)));
 }
 if(body)for(const x of[-.28,.28])for(const y of[-.05,.85])for(const z of[-.05,.05])
  points.push(actor.group.position.clone().set(x,y,z).applyMatrix4(actor.group.matrixWorld));
 return points;
}

export function faceOverlapPairs(camera,actors){
 const boxes=actors.filter(a=>a.group.visible).map(a=>projectedBounds(camera,actorFramePoints(a,{hands:false,faceOnly:true})));
 const pairs=[];
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
  const a=boxes[i],b=boxes[j],w=Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left)),
   h=Math.max(0,Math.min(a.top,b.top)-Math.max(a.bottom,b.bottom));
  const ratio=w*h/Math.min((a.right-a.left)*(a.top-a.bottom),(b.right-b.left)*(b.top-b.bottom));
  if(ratio>.20)pairs.push({actors:[i,j],ratio});
 }
 return pairs;
}

export function frameShot(camera,{actors=[],objects=[],hands=true,safe=DEFAULT_SAFE,allowFaceOverlap=false}={}){
 const points=()=>[...actors.filter(a=>a.group.visible).flatMap(a=>actorFramePoints(a,{hands})),
                      ...objects.flatMap(objectFramePoints)];
 const before=projectedBounds(camera,points());let dolly=0,adjusted=false;
 // Billboards and held badge/tag surfaces turn toward the final camera position.
 for(let i=0;i<4;i++){
  const fit=fitCamera(camera,points(),{safe});dolly+=fit.dolly;adjusted ||= fit.adjusted;
  for(const actor of actors)if(actor.group.visible)actor.face(camera);
 }
 const after=projectedBounds(camera,points());
 if(!fitsSafeFrame(after,safe,.002))throw Error('Framing safety contract remains cropped after fitting');
 const overlaps=faceOverlapPairs(camera,actors);
 if(overlaps.length&&!allowFaceOverlap)throw Error('Required faces overlap: adjust shot camera angle or actor spacing');
 return {before,after,safe,adjusted,dolly,subjects:actors.length,objects:objects.length,face_overlaps:overlaps};
}
