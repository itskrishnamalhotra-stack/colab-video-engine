import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../skills/faceless-shorts/styles/tall-tale/example/vendor/three.module.js';
import {frameShot} from './webgl_kit/camera_framing.mjs';
const vendor=new URL('../skills/faceless-shorts/styles/tall-tale/example/vendor/three.module.js',import.meta.url);
let source=fs.readFileSync(new URL('./webgl_kit/hospital_coverage.js',import.meta.url),'utf8')
 .replace("from 'three'",`from '${vendor.href}'`)
 .replace("import {V} from './world.js';",'const V=(...args)=>new THREE.Vector3(...args);')
 .replace("from './camera_framing.mjs'",`from '${new URL('./webgl_kit/camera_framing.mjs',import.meta.url).href}'`);
const {hospitalCoverage}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
function actor(x,z){
 const group=new THREE.Group(),pivot=new THREE.Group();group.add(pivot);group.position.set(x,0,z);
 const arms={l:{hand:new THREE.Group()},r:{hand:new THREE.Group()}};
 for(const [side,a] of Object.entries(arms)){a.hand.position.set(side==='l'?.25:-.25,1.05,.2);group.add(a.hand);}
 return {group,toon:{H:1.85,st:{},look:{pattern:'trench'},pivot},arms,face(){},handPoint(side){return arms[side].hand.getWorldPosition(new THREE.Vector3());}};
}
function state(){const a=actor(-1.05,.25),b=actor(1.10,-.10);return {cast:[a,b],focus:a,detail:a,important:[],props:{cart:new THREE.Group()}};}
test('the same authored shot has motivated camera travel without changing cast visibility',()=>{
 const s=state(),cam=new THREE.PerspectiveCamera(42,16/9,.05,100);s.props.cart.visible=false;
 const first=hospitalCoverage(cam,s,{action:'reaction'},'main',0,20);const p=cam.position.clone();
 frameShot(cam,first);hospitalCoverage(cam,s,{action:'reaction'},'main',1,20);
 assert.ok(cam.position.distanceTo(p)>.2);assert.ok(s.cast.every(a=>a.group.visible));
});
test('a held-equipment close-up includes its connected owner and fits the focus',()=>{
 const s=state(),radio=new THREE.Mesh(new THREE.BoxGeometry(.12,.2,.05));s.cast[0].arms.r.hand.add(radio);s.detail=radio;
 const cam=new THREE.PerspectiveCamera(42,16/9,.05,100),contract=hospitalCoverage(cam,s,{action:'radio'},'detail',.5,32);
 assert.deepEqual(contract.actors,[s.cast[0]]);assert.ok(contract.objects.includes(radio));assert.equal(contract.hands,true);
 const fitted=frameShot(cam,contract);assert.equal(fitted.after.behind,0);assert.ok(s.cast[0].group.visible);
});
test('group evidence coverage protects separated faces without hiding the duplicate',()=>{
 const s=state();s.cast.push(actor(3.45,-2.2));s.focus=s.cast[2];s.detail=s.cast[2];
 const cam=new THREE.PerspectiveCamera(42,16/9,.05,100),contract=hospitalCoverage(cam,s,{action:'bodywide'},'main',.5,35);
 const fitted=frameShot(cam,contract);assert.equal(fitted.face_overlaps.length,0);assert.equal(contract.actors.length,3);
});
