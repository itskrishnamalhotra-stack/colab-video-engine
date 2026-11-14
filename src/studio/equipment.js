// Reusable physical equipment. The lamp lens, widening beam and real light all
// share +Z as their forward axis; hand attachment never reverses that convention.
import * as THREE from 'three';
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z),UP=V(0,1,0),FORWARD=V(0,0,1);
const material=(color,extra={})=>new THREE.MeshStandardMaterial({color,roughness:.62,...extra});
function cube(parent,w,h,d,color,x=0,y=0,z=0){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),typeof color==='string'?material(color):color);m.position.set(x,y,z);m.castShadow=m.receiveShadow=true;parent.add(m);return m;}
function tube(parent,a,b,r,color){const m=new THREE.Mesh(new THREE.CylinderGeometry(r,r,a.distanceTo(b),12),material(color));m.position.copy(a).add(b).multiplyScalar(.5);m.quaternion.setFromUnitVectors(UP,b.clone().sub(a).normalize());parent.add(m);return m;}
function label(text,{w=.12,h=.06,bg='#172628',fg='#B3DABD'}={}){
 if(typeof document==='undefined')return new THREE.Mesh(new THREE.PlaneGeometry(w,h),material(bg));
 const c=document.createElement('canvas');c.width=512;c.height=256;const g=c.getContext('2d');
 g.fillStyle=bg;g.fillRect(0,0,512,256);g.fillStyle=fg;g.font='bold 108px monospace';g.textAlign='center';g.textBaseline='middle';g.fillText(text,256,128,480);
 const map=new THREE.CanvasTexture(c);map.colorSpace=THREE.SRGBColorSpace;
 return new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map,side:THREE.DoubleSide}));
}

export function makeFlashlight({range=5,angle=.19,power=12}={}){
 const root=new THREE.Group(),shell=new THREE.Group();root.add(shell);
 const body=new THREE.Mesh(new THREE.CylinderGeometry(.044,.040,.23,24),material('#33474A'));
 body.rotation.x=Math.PI/2;body.position.z=-.015;shell.add(body);
 for(const z of[-.10,-.075,-.05,-.025]){const ring=new THREE.Mesh(new THREE.TorusGeometry(.044,.003,6,24),material('#202F32'));ring.position.z=z;shell.add(ring);}
 const head=new THREE.Mesh(new THREE.CylinderGeometry(.073,.046,.075,24),material('#718A8A',{metalness:.5}));head.rotation.x=-Math.PI/2;head.position.z=.13;shell.add(head);
 const lens=new THREE.Mesh(new THREE.CircleGeometry(.061,24),new THREE.MeshBasicMaterial({color:'#E5EDD6'}));lens.position.z=.169;shell.add(lens);
 cube(shell,.027,.013,.045,'#131F26',0,.046,.015);
 const beam=new THREE.Mesh(new THREE.ConeGeometry(1,1,32,1,true),new THREE.MeshBasicMaterial({
  color:'#CEE7C9',transparent:true,opacity:.045,side:THREE.DoubleSide,depthWrite:false,blending:THREE.AdditiveBlending}));
 beam.rotation.x=-Math.PI/2;root.add(beam);
 const light=new THREE.SpotLight('#DAE8CE',power,range,angle,.65,1.5);light.position.set(0,0,.172);
 const target=new THREE.Object3D();target.position.z=range;root.add(light,target);light.target=target;
 function distance(d){const length=Math.max(.1,Math.min(range,d));beam.scale.set(Math.tan(angle)*length,length,Math.tan(angle)*length);beam.position.set(0,0,.172+length/2);target.position.z=.172+length;light.distance=length+.2;}
 function enabled(on=true){beam.visible=on;light.visible=on;lens.material.color.set(on?'#E5EDD6':'#34464D');root.userData.on=on;}
 function aimAt(worldTarget){
  root.updateWorldMatrix(true,false);const origin=root.getWorldPosition(V()),direction=worldTarget.clone().sub(origin);
  const length=direction.length();if(length<.01)throw Error('Flashlight target is at its grip');
  const rotation=new THREE.Quaternion().setFromUnitVectors(FORWARD,direction.normalize());
  if(root.parent)rotation.premultiply(root.parent.getWorldQuaternion(new THREE.Quaternion()).invert());
  root.quaternion.copy(rotation);distance(Math.max(.1,length-.172));root.updateWorldMatrix(true,true);
 }
 Object.assign(root,{shell,lens,beam,light,target,aimAt,setEnabled:enabled,setDistance:distance});
 distance(range);enabled();return root;
}

export function makeRadio(){
 const root=new THREE.Group(),body=cube(root,.115,.205,.055,'#293E42',0,.02,0);
 cube(root,.10,.025,.057,'#1B2B2D',0,-.095,0);
 for(let i=0;i<5;i++)cube(root,.075,.006,.008,'#101C20',0,-.045+i*.012,.032);
 const antenna=new THREE.Mesh(new THREE.CylinderGeometry(.004,.006,.16,10),material('#1B2B31'));antenna.position.set(-.032,.19,0);root.add(antenna);
 const dial=new THREE.Mesh(new THREE.CylinderGeometry(.013,.013,.024,14),material('#75918B'));dial.position.set(.030,.135,0);root.add(dial);
 const screenOn=label('CH 3',{w:.084,h:.044}),screenOff=label('OFF',{w:.084,h:.044,bg:'#263638',fg:'#C2CAC1'});
 for(const screen of[screenOn,screenOff]){screen.position.set(0,.055,.029);root.add(screen);}
 const led=new THREE.Mesh(new THREE.SphereGeometry(.008,12,8),new THREE.MeshBasicMaterial({color:'#DDA454'}));led.position.set(.039,.100,.032);root.add(led);
 const cavity=cube(root,.077,.11,.014,'#101F24',0,-.024,-.032);
 const batteryCover=cube(root,.082,.119,.009,'#405B5C',0,-.024,-.043);batteryCover.name='battery_cover';
 function setState({power=true,rx=false}={}){screenOn.visible=power;screenOff.visible=!power;led.visible=power;led.material.color.set(rx?'#E85A4D':'#74B991');dial.rotation.y=power?.6:0;root.userData.power=power;root.userData.rx=power&&rx;}
 setState();Object.assign(root,{body,led,dial,screenOn,screenOff,setState,batteryCover,cavity});return root;
}

export function makeCamera(){
 const root=new THREE.Group(),body=cube(root,.235,.135,.125,'#35484F');
 cube(root,.08,.15,.12,'#213139',.105,-.005,.005);
 const lens=new THREE.Mesh(new THREE.CylinderGeometry(.050,.045,.12,24),material('#657D81',{metalness:.45}));lens.rotation.x=Math.PI/2;lens.position.z=.11;root.add(lens);
 const glass=new THREE.Mesh(new THREE.CircleGeometry(.044,24),material('#1D344A',{metalness:.4,roughness:.16}));glass.position.z=.172;root.add(glass);
 const tape=new THREE.Mesh(new THREE.TorusGeometry(.050,.004,8,24),material('#D0C264'));tape.position.z=.145;root.add(tape);
 cube(root,.065,.025,.055,'#53666B',0,.085,0);
 const led=new THREE.Mesh(new THREE.SphereGeometry(.006,10,8),new THREE.MeshBasicMaterial({color:'#EC6C55'}));led.position.set(-.083,.039,.069);root.add(led);
 function recording(on){led.visible=on;root.userData.recording=on;}
 recording(false);Object.assign(root,{body,led,setRecording:recording});return root;
}

export function makeCameraBag(){
 const root=new THREE.Group();cube(root,.24,.21,.12,'#3D514E');cube(root,.25,.055,.13,'#63736A',0,.10,.005);
 cube(root,.046,.08,.008,'#D1C469',.065,.02,.069);
 for(const x of[-.10,.10])tube(root,V(x,.10,0),V(x,.30,0),.009,'#263D3E');
 tube(root,V(-.10,.30,0),V(.10,.30,0),.009,'#263D3E');return root;
}

export function makeTripod(){
 const root=new THREE.Group();
 for(let i=0;i<3;i++){const a=i*2*Math.PI/3+Math.PI/6,foot=V(Math.cos(a)*.38,.025,Math.sin(a)*.38);
  tube(root,V(0,.92,0),foot,.015,'#667D80');cube(root,.065,.035,.065,'#1E3237',foot.x,.018,foot.z);}
 tube(root,V(0,.65,0),V(0,1.04,0),.018,'#A6B7B0');
 const socket=new THREE.Group();socket.position.y=1.08;root.add(socket);cube(socket,.13,.045,.11,'#31494A');
 tube(root,V(.04,1.02,0),V(.28,1.01,-.15),.011,'#24363C');
 Object.assign(root,{socket});return root;
}

export function makeEquipmentCase(){
 const root=new THREE.Group();cube(root,.58,.20,.34,'#33494C',0,.12,0);
 for(const x of[-.26,.26])cube(root,.025,.22,.36,'#1B3035',x,.12,0);
 const lid=new THREE.Group();lid.position.set(0,.23,-.17);root.add(lid);cube(lid,.58,.045,.34,'#526B69',0,0,.17);
 const latches=[];
 for(const x of[-.18,.18]){const latch=new THREE.Group();latch.position.set(x,.19,.185);root.add(latch);
  cube(latch,.055,.07,.025,'#A6AAA0',0,-.015,0);latches.push(latch);}
 Object.assign(root,{lid,latches});return root;
}
