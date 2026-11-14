// A single stable furnished room, with named nested assemblies and real sockets.
import * as THREE from 'three';
import {V,box,cylinder,card,words,mat,texture,makeScene} from './world.js';
import {makeRadio,makeFlashlight,makeCamera} from './equipment.js';
import {named} from './entity_registry.mjs';
export function makeContinuityRoom(E){
 const S=makeScene(E,true),scene=S.scene,root=named(new THREE.Group(),'main_room');scene.add(root);
 scene.background=new THREE.Color('#28383C');scene.fog=new THREE.Fog('#28383C',20,45);
 S.lights.key.color.set('#E8CDA7');S.lights.key.intensity=3.6;S.lights.key.position.set(3.8,4.5,3);S.lights.rim.color.set('#ABC3D3');S.lights.rim.intensity=1.8;
 for(const light of S.lights.group.children)if(light.isHemisphereLight)light.intensity=.95;
 scene.environmentIntensity=.25;
 const tile=texture((g,w,h)=>{g.fillStyle='#6C7B77';g.fillRect(0,0,w,h);for(let i=0;i<8;i++)for(let j=0;j<8;j++){g.fillStyle=(i+j)%2?'#77847B':'#899589';g.fillRect(i*w/8+2,j*h/8+2,w/8-4,h/8-4);}},512,512);tile.wrapS=tile.wrapT=THREE.RepeatWrapping;tile.repeat.set(3,3);
 named(box(root,9,.16,9,mat('white',{map:tile}),0,-.10,-1),'floor');
 named(box(root,9,3.9,.15,'#536966',0,1.95,-5),'back_wall');named(box(root,.15,3.9,9,'#4B6261',-4.5,1.95,-.55),'left_wall');
 for(const y of[.15,1.0,3.55])box(root,9,.06,.08,'#91A494',0,y,-4.90);
 const window=named(new THREE.Group(),'window');root.add(window);window.position.set(-2.35,2.18,-4.88);
 box(window,1.9,1.55,.10,'#B6B69E');box(window,1.7,1.35,.12,mat('#65858D',{emissive:'#36515B',emissiveIntensity:.25}),0,0,.04);
 for(const x of[-.42,.42])box(window,.045,1.36,.04,'#AABAA9',x,0,.13);box(window,1.72,.045,.04,'#AABAA9',0,0,.13);
 const shelf=named(new THREE.Group(),'equipment_shelf');root.add(shelf);shelf.position.set(2.9,0,-4.35);
 for(const y of[.1,.85,1.6,2.35])box(shelf,1.6,.07,.45,'#8B8470',0,y,0);for(const x of[-.73,.73])box(shelf,.055,2.5,.48,'#354F52',x,1.25,0);
 for(let i=0;i<7;i++){box(shelf,.13,.34,.27,['#886E58','#6B8A7C','#B4A67D'][i%3],-.6+i*.18,1.82,0);box(shelf,.09,.045,.015,'#C0C5AD',-.6+i*.18,1.8,.143);}
 const panel=named(new THREE.Group(),'wall_panel');root.add(panel);panel.position.set(.75,1.35,-4.82);box(panel,.6,.75,.12,'#7A8D86');box(panel,.49,.60,.05,'#314B50',0,0,.08);
 const breaker=named(box(panel,.09,.16,.06,'#B6C1A7',.11,.04,.14),'breaker');
 card(root,words(['CONTROL ROOM','NORTH WING'],{paper:'#A5B099',ink:'#2B484A'}),1.2,.45,.7,2.7,-4.88);
 const table=named(new THREE.Group(),'center_table');root.add(table);table.position.set(0,0,0);
 named(box(table,2.4,.13,1.2,'#8D8068',0,.92,0),'table_top');for(const x of[-1.02,1.02])for(const z of[-.43,.43])box(table,.07,.90,.07,'#364D50',x,.45,z);
 box(table,2.25,.045,.045,'#B7B19A',0,.91,.61);box(table,1.8,.04,.65,'#44605D',0,.26,0);
 const mug=named(new THREE.Group(),'chipped_mug');table.add(mug);mug.position.set(-.65,1.07,.02);
 cylinder(mug,.075,.17,'#D1CEAF',0,.085,0);cylinder(mug,.065,.006,'#504E3D',0,.172,0);
 const handle=new THREE.Mesh(new THREE.TorusGeometry(.05,.012,8,20),mat('#D1CEAF'));handle.position.set(.08,.09,0);mug.add(handle);box(mug,.024,.018,.009,'#7B897B',-.02,.164,.071);
 const radio=named(makeRadio(),'radio');table.add(radio);radio.position.set(-1.02,1.12,.30);radio.scale.setScalar(1.15);
 const battery=named(box(table,.075,.038,.13,'#51676B',.15,1.005,.3),'loose_battery');box(battery,.022,.008,.015,'#C7B56C',0,.023,.05);
 const flashlight=named(makeFlashlight({range:5,angle:.17,power:14}),'flashlight');table.add(flashlight);flashlight.position.set(-.12,1.015,-.17);flashlight.rotation.x=Math.PI/2;flashlight.setEnabled(false);
 const camera=named(makeCamera(),'missing_camera');table.add(camera);camera.position.set(.70,1.07,-.28);camera.rotation.y=-.28;
 const socket=named(new THREE.Object3D(),'radio_rest');socket.position.copy(radio.position);table.add(socket);
 const plug=named(new THREE.Group(),'disconnected_plug');table.add(plug);plug.position.set(.28,1.015,-.05);
 const grip=box(plug,.06,.035,.09,'#2A4248');cylinder(plug,.012,.07,'#BBC4AD',0,.0,.07).rotation.x=Math.PI/2;
 const cable=named(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(.28,1.015,-.10),V(.8,.98,-.4),V(1.05,.18,-.55),V(1.3,.02,-.9),V(1.7,.02,-3.7),V(.9,1.1,-4.8)]),80,.008,8),mat('#B4BBA4')),'power_cable');root.add(cable);
 const chair=named(new THREE.Group(),'blue_chair');root.add(chair);chair.position.set(-2.3,0,-2.45);
 const swivel=named(new THREE.Group(),'chair_seat');chair.add(swivel);swivel.rotation.y=-1.1;
 cylinder(chair,.045,.62,'#829892',0,.35,0);box(swivel,.63,.14,.60,'#426D83',0,.73,0);box(swivel,.63,.68,.11,'#426D83',0,1.10,-.25);
 for(let i=0;i<5;i++){const a=i*Math.PI*2/5,g=new THREE.Group();chair.add(g);g.rotation.y=a;box(g,.04,.04,.43,'#637B78',0,.12,.2);cylinder(g,.055,.055,'#283E44',0,.07,.39).rotation.z=Math.PI/2;}
 const light=new THREE.PointLight('#DCCAA0',4,8,2);light.position.set(-2,2.9,-3.8);root.add(light);
 return {...S,root,table,radio,flashlight,camera,mug,battery,plug,chair,swivel,panel,breaker,socket,cable};
}
