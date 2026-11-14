import test from 'node:test';import assert from 'node:assert/strict';
import * as THREE from '../skills/faceless-shorts/styles/tall-tale/example/vendor/three.module.js';
import {EntityRegistry,named,transferToSocket} from './webgl_kit/entity_registry.mjs';
import {pathState,characterView} from './webgl_kit/directional_motion.mjs';
test('the same character shows front, profile and back art from its body heading',()=>{
 assert.equal(characterView(0,0).view,'front');assert.equal(characterView(Math.PI,0).view,'back');
 assert.equal(characterView(Math.PI/2,0).view,'profile');assert.equal(characterView(-Math.PI/2,0).view,'profile');
 assert.notEqual(characterView(Math.PI/2,0).profileSide,characterView(-Math.PI/2,0).profileSide);
 assert.equal(characterView(Math.PI,Math.PI).view,'front');
});
test('table contents move as one persistent assembly and survive repeated lookup',async()=>{
 const r=new EntityRegistry(),scene=new THREE.Scene();r.define('table',{factory:()=>{const root=named(new THREE.Group(),'table');root.add(named(new THREE.Mesh(new THREE.BoxGeometry(.1,.1,.1)),'mug'));return root;},required:['mug']});
 const table=await r.spawn('table',{parent:scene}),mug=r.get('table','mug'),identity=mug.uuid;
 table.position.set(2,1,3);table.rotation.y=.8;table.updateMatrixWorld(true);
 for(let i=0;i<100;i++){assert.equal(r.get('table','mug').uuid,identity);assert.equal(r.assertContinuity(),true);}
 assert.equal(mug.getWorldPosition(new THREE.Vector3()).y,1);
});
test('missing/hidden/detached required objects are caught, not silently rebuilt',async()=>{
 const r=new EntityRegistry(),root=new THREE.Group(),part=named(new THREE.Group(),'head');root.add(part);r.define('mc',{factory:()=>root,required:['head']});await r.spawn('mc');
 part.visible=false;assert.throws(()=>r.assertContinuity(),/Hidden required/);part.visible=true;root.remove(part);assert.throws(()=>r.assertContinuity(),/Detached required/);
});
test('explicit hand socket transfer preserves object identity and scene ownership',async()=>{
 const r=new EntityRegistry(),scene=new THREE.Scene(),table=named(new THREE.Group(),'table'),radio=named(new THREE.Group(),'radio'),actor=new THREE.Group(),hand=named(new THREE.Group(),'mc.r_grip');scene.add(table,actor);table.add(radio);actor.add(hand);
 r.define('table',{factory:()=>table,required:['radio']});await r.spawn('table');const uuid=radio.uuid;transferToSocket(radio,hand);assert.equal(r.assertContinuity(),true);assert.equal(radio.uuid,uuid);
 hand.remove(radio);assert.throws(()=>r.assertContinuity(),/Detached required/);
});
test('walking away and sideways faces travel, independent of camera position',()=>{
 for(const end of[[0,0,-4],[4,0,0],[-3,0,2]])for(let i=1;i<=20;i++){
  const state=pathState([0,0,0],end,i/20,{turnFrom:0});
  if(state.movement>0){const delta=new THREE.Vector3(...end).normalize(),forward=new THREE.Vector3(Math.sin(state.yaw),0,Math.cos(state.yaw));assert.ok(forward.dot(delta)>.999999);}
 }
});
