import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from '../skills/faceless-shorts/styles/tall-tale/example/vendor/three.module.js';
import {fitCamera,projectedBounds,fitsSafeFrame,frameShot,objectFramePoints,faceOverlapPairs} from './webgl_kit/camera_framing.mjs';
const vec=(x,y,z=0)=>new THREE.Vector3(x,y,z);
function camera(){const c=new THREE.PerspectiveCamera(35,1080/1920,.05,100);c.position.set(.5,1.6,3);c.lookAt(0,1.4,0);c.updateMatrixWorld(true);return c;}
function person(x){return [-.36,.36].flatMap(dx=>[1,2.03].map(y=>vec(x+dx,y)));}
test('two heads that crop in a portrait frame fit after minimum camera correction',()=>{
 const c=camera(),p=[...person(-.65),...person(.65)];
 assert.equal(fitsSafeFrame(projectedBounds(c,p)),false);
 const fixed=fitCamera(c,p);
 assert.equal(fixed.adjusted,true);assert.ok(fixed.dolly>0);assert.ok(fitsSafeFrame(fixed.after));
});
test('a moving five-person group stays safe across the full authored camera move',()=>{
 for(let i=0;i<=30;i++){
  const c=camera();c.position.set(2.9-i/30*.7,2.1-i/30*.15,5.8-i/30*.8);c.lookAt(0,1.25,-.4);
  const p=[-1.8+i/30*.4,-.6,.05,.62,1.8-i/30*.3].flatMap(person);
  assert.ok(fitsSafeFrame(fitCamera(c,p).after));
 }
});
test('already safe camera remains unchanged and preserves its orientation',()=>{
 const c=camera();c.position.z=7;c.lookAt(0,1.5,0);const start=c.position.clone(),orientation=c.quaternion.clone();
 const fixed=fitCamera(c,person(0));assert.equal(fixed.adjusted,false);
 assert.ok(start.equals(c.position));assert.ok(orientation.equals(c.quaternion));
});
test('focus object includes its rotating cover rather than just its origin',()=>{
 const group=new THREE.Group(),cover=new THREE.Mesh(new THREE.BoxGeometry(.5,.5,.03));group.add(cover);cover.position.set(.25,1.2,0);cover.rotation.y=-2;
 const points=objectFramePoints(group);assert.equal(points.length,8);
 const c=camera();assert.ok(fitsSafeFrame(fitCamera(c,points).after));
});
test('geometry behind the starting camera is recovered without clipping the near plane',()=>{
 const c=camera(),p=[vec(-1,1,4),vec(1,2,4)];assert.ok(fitsSafeFrame(fitCamera(c,p).after));
});
test('missing framing subjects fail instead of silently retaining a cropped shot',()=>{
 assert.throws(()=>frameShot(camera(),{}),/must name visible subjects/);
});
test('fitting within the borders does not excuse one required face hiding another',()=>{
 function actor(z){const group=new THREE.Group(),pivot=new THREE.Group();group.add(pivot);group.position.z=z;return {group,toon:{pivot,H:1.92,st:{},look:{}},face(){}};}
 const c=camera(),a=actor(0),b=actor(-.1);
 assert.equal(faceOverlapPairs(c,[a,b]).length,1);
 assert.throws(()=>frameShot(c,{actors:[a,b],hands:false}),/Required faces overlap/);
});
