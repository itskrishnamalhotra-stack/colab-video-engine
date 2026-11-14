import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../skills/faceless-shorts/styles/tall-tale/example/vendor/three.module.js';
const vendor=new URL('../skills/faceless-shorts/styles/tall-tale/example/vendor/three.module.js',import.meta.url);
const source=fs.readFileSync(new URL('./webgl_kit/equipment.js',import.meta.url),'utf8').replace("from 'three'",`from '${vendor.href}'`);
const {makeFlashlight,makeRadio,makeCamera,makeTripod}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('beam apex starts at the lens and the cone widens only in front of it',()=>{
 const lamp=makeFlashlight({range:4});lamp.updateMatrixWorld(true);
 const apex=lamp.beam.localToWorld(new THREE.Vector3(0,.5,0));
 const rim=lamp.beam.localToWorld(new THREE.Vector3(1,-.5,0));
 const lens=lamp.lens.getWorldPosition(new THREE.Vector3());
 assert.ok(Math.abs(apex.z-lens.z)<.005);assert.ok(rim.z>apex.z+3.9);assert.ok(Math.abs(rim.x)>.5);
 assert.ok(lamp.target.getWorldPosition(new THREE.Vector3()).z>lens.z);
});
test('aiming under a rotated hand sends the real spotlight and geometry toward the same world target',()=>{
 const hand=new THREE.Group();hand.position.set(.7,1.1,-.2);hand.rotation.y=.8;
 const lamp=makeFlashlight();hand.add(lamp);const target=new THREE.Vector3(-1.8,1.4,-4);
 lamp.aimAt(target);hand.updateMatrixWorld(true);
 const from=lamp.light.getWorldPosition(new THREE.Vector3()),to=lamp.target.getWorldPosition(new THREE.Vector3());
 assert.ok(to.sub(from).normalize().dot(target.clone().sub(from).normalize())>.99999);
 const apex=lamp.beam.localToWorld(new THREE.Vector3(0,.5,0)),end=lamp.beam.localToWorld(new THREE.Vector3(0,-.5,0));
 const beamDirection=end.clone().sub(apex).normalize(),expected=target.clone().sub(from).normalize();
 assert.ok(beamDirection.dot(expected)>.99999,JSON.stringify({apex:apex.toArray(),end:end.toArray(),from:from.toArray(),target:target.toArray(),beam:beamDirection.toArray(),expected:expected.toArray()}));
 lamp.setEnabled(false);assert.equal(lamp.light.visible,false);assert.equal(lamp.beam.visible,false);
});
test('equipment state and tripod mounting use real scene graph ownership',()=>{
 const radio=makeRadio();radio.setState({power:false,rx:true});assert.equal(radio.userData.rx,false);assert.equal(radio.screenOff.visible,true);
 const tripod=makeTripod(),camera=makeCamera();tripod.socket.add(camera);camera.position.set(0,.08,0);camera.setRecording(true);
 assert.equal(camera.parent,tripod.socket);assert.equal(camera.led.visible,true);
});
