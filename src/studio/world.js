import * as THREE from 'three';
import {T,facade,lamp,tree,barrel} from './world-textures.js';
import {lightRig} from './engine.js';
export const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const mats=new Map();
export function mat(color,extra={}){const key=color+JSON.stringify(extra);if(!mats.has(key))mats.set(key,new THREE.MeshStandardMaterial({color,roughness:.82,...extra}));return mats.get(key);}
export function box(parent,w,h,d,color,x=0,y=0,z=0){const o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),typeof color==='string'?mat(color):color);o.position.set(x,y,z);o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
export function cylinder(parent,r,h,color,x=0,y=0,z=0){const o=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,24),mat(color));o.position.set(x,y,z);o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
export function texture(draw,w=1024,h=768){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t;}
export function card(parent,tex,w,h,x,y,z){const o=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshStandardMaterial({map:tex,roughness:.9,side:THREE.DoubleSide}));o.position.set(x,y,z);parent.add(o);return o;}
export function words(lines,{paper='#F7EACB',ink='#273B35',font='Georgia',subtitle=''}={}){return texture((g,w,h)=>{
 g.fillStyle=paper;g.fillRect(0,0,w,h);g.strokeStyle='#8D7957';g.lineWidth=7;g.strokeRect(25,25,w-50,h-50);
 g.fillStyle=ink;g.textAlign='center';g.textBaseline='middle';g.font=`bold ${lines.length>3?72:90}px ${font}`;
 lines.forEach((s,i)=>g.fillText(s,w/2,h*(.3+i*.18),w-90));if(subtitle){g.font='30px Georgia';g.fillText(subtitle,w/2,h*.89);}
});}
export function newspaper(){return texture((g,w,h)=>{
 g.fillStyle='#EAE4D1';g.fillRect(0,0,w,h);g.fillStyle='#3F4840';g.textAlign='center';
 g.font='bold 62px Georgia';g.fillText('The Daily Courier',w/2,88);g.lineWidth=4;g.strokeStyle='#5F6559';g.strokeRect(30,115,w-60,h-145);
 g.font='24px Georgia';g.fillText('CITY EDITION  •  TUESDAY  •  TWO PENNIES',w/2,152);
 g.font='bold 69px Georgia';['THE GENTLEMAN','THIEF STRIKES AGAIN'].forEach((s,i)=>g.fillText(s,w/2,245+i*80));
 g.fillStyle='#92978B';g.fillRect(65,360,280,270);g.fillStyle='#515C51';g.beginPath();g.arc(205,440,65,0,7);g.fill();g.fillRect(125,406,160,20);g.fillRect(165,359,82,60);g.beginPath();g.ellipse(205,610,95,110,0,0,7);g.fill();
 for(let col=0;col<2;col++)for(let row=0;row<19;row++){g.fillStyle=row%6===0?'#687064':'#A0A395';g.fillRect(380+col*295,375+row*16,255-(row%5)*14,4);}
 g.fillStyle='#485246';g.font='italic 28px Georgia';g.fillText('WALLETS HOME BY POST — EVERY COIN RETURNED',w/2,700);
},1024,768);}
export function makeScene(E,night=false){const scene=new THREE.Scene();scene.background=new THREE.Color(night?'#172443':'#98BCC8');scene.fog=new THREE.Fog(night?'#172443':'#A6B9BA',18,65);scene.environment=E.envMap;scene.environmentIntensity=night?.12:.35;
 const lights=lightRig(scene,{key:night?'#B5CBFF':'#FFDEAB',keyI:night?1.6:3.0,keyPos:[-3,7,6],hemiI:night?.65:1.05,sky:night?'#536EAB':'#D3E7EA',ground:'#8A6952',shadowBox:9});
 return {scene,lights};}
export function street(E){const S=makeScene(E);const scene=S.scene;
 box(scene,16,.12,40,mat('white',{map:T.brick('#A5A29A',[10,20])}),0,-.09,-10);
 for(const side of[-1,1]){
  box(scene,2,.18,32,'#B8B0A2',side*4,-.01,-10);
  for(let i=0;i<6;i++){
   const color=['#A84736','#608B7C','#D3B27C','#657D8E','#A55F56','#95875F'][i],height=5.8+i%2;
   const paint=facade(['POST OFFICE','THE DAILY COURIER','BAKERY','TAILOR','CAFE','HARDWARE'][i],{wall:color,w:4.2,h:height,awning:i%2?'#244E42':'#963A32',kind:'brick',seed:i+side+8});
   const sideMat=mat(color),front=new THREE.MeshStandardMaterial({map:paint,roughness:.9});
   const f=new THREE.Mesh(new THREE.BoxGeometry(4.2,height,2),[sideMat,sideMat,sideMat,sideMat,front,sideMat]);
   f.position.set(side*5.0,height/2,-i*4.5);f.rotation.y=-side*Math.PI/2;f.castShadow=f.receiveShadow=true;scene.add(f);
  }
  for(let i=0;i<3;i++){const l=lamp();l.position.set(side*3.2,0,-i*8);scene.add(l);}
 }
 for(let i=0;i<3;i++){const t=tree(.9);t.position.set(-3,0,-5-i*8);scene.add(t);}
 const post=new THREE.Group();cylinder(post,.33,1.4,'#A92B2A',0,.7,0);cylinder(post,.37,.1,'#79201F',0,1.44,0);box(post,.41,.09,.03,'#251E22',0,1.15,.33);card(post,words(['CITY','POST'],{paper:'#D9B36D'}),.28,.24,0,.8,.342);post.position.set(1.15,0,-.8);scene.add(post);
 const barrelObj=barrel();barrelObj.position.set(-2.4,0,-1);scene.add(barrelObj);
 return {...S,post};}
export function room(E,{police=false,night=false}={}){const S=makeScene(E,night),s=S.scene;
 box(s,7,.12,7,mat('white',{map:T.planks('#805A3B',[4,4])}),0,-.08,-1);
 box(s,7,3.4,.12,mat('white',{map:T.wallpaper(police?'#7D9D8B':'#47675D',police?'#90AA96':'#607D6B',[5,2])}),0,1.7,-3);
 box(s,.12,3.4,7,mat('white',{map:T.brick('#906B55',[3,2])}),-3.5,1.7,-1);
 for(const y of[.1,.85,3.15])box(s,7,.065,.09,'#B59B73',0,y,-2.9);
 const win=box(s,1.8,1.7,.05,'#DFD4AE',-1.9,2,-2.89);box(s,1.61,1.48,.06,night?'#192B56':'#A7D3DD',-1.9,2,-2.84);
 box(s,.055,1.55,.06,'#DCD3B0',-1.9,2,-2.79);box(s,1.7,.06,.06,'#DCD3B0',-1.9,2,-2.79);
 for(let i=0;i<3;i++){const tx=words(police?['CASE FILE',String(107+i)]:['RETURNED','BY POST'],{paper:police?'#C7BD9A':'#CFBA91'});card(s,tx,.6,.45,.3+i*.8,2.5,-2.9);}
 const clock=new THREE.Group();cylinder(clock,.24,.055,'#3D2F2C');clock.rotation.x=Math.PI/2;clock.position.set(1.9,2.8,-2.8);s.add(clock);
 const face=card(s,words(['12','6'],{paper:'#F3E8CE'}),.38,.38,1.9,2.8,-2.75);
 const desk=new THREE.Group();s.add(desk);
 box(desk,2.6,.13,1.35,mat('white',{map:T.planks('#98704A',[2,1])}),0,.95,.15);
 box(desk,2.3,.025,1.12,'#315F4E',0,1.03,.15);
 for(const x of[-1.1,1.1])for(const z of[-.35,.65])box(desk,.12,.92,.12,'#69462D',x,.46,z);
 for(let i=0;i<3;i++){box(s,.9,.22,.6,'#624C38',2.3,.15+i*.28,-2.1);box(s,.13,.045,.04,'#C7AE65',2.3,.15+i*.28,-1.78);}
 // lamp, inkwell, correspondence, books and pinned evidence furnish the set.
 cylinder(desk,.15,.035,'#C2A259',-.9,1.06,-.2);cylinder(desk,.025,.38,'#BA9B58',-.9,1.25,-.2);
 const shade=new THREE.Mesh(new THREE.ConeGeometry(.25,.15,24,1,true),mat('#305F46'));shade.position.set(-.9,1.48,-.2);desk.add(shade);
 cylinder(desk,.055,.075,'#17282B',.8,1.08,0);
 for(let i=0;i<3;i++)box(desk,.32,.035,.45,['#715653','#4D6556','#D3B789'][i],.9,1.05+i*.04,.5);
 const lampLight=new THREE.PointLight('#FFD593',night?7:3,5,2);lampLight.position.set(-.9,1.4,-.2);s.add(lampLight);
 furnish(S,police,night);
 return {...S,desk};}
function furnish(S,police,night){const s=S.scene;
 // Layered furnishings at the actual camera-facing edge, not empty background planes.
 const shelf=box(s,1.3,.12,.5,'#725136',2.3,1.5,-2.5);
 for(let i=0;i<9;i++){box(s,.09,.35+(i%3)*.05,.25,['#516F66','#806553','#6F4E50','#C2AC7A'][i%4],1.78+i*.12,1.72,-2.47);}
 const cork=box(s,1.25,.82,.07,'#70553B',.5,2.05,-2.83);box(s,1.14,.72,.03,'#A58D60',.5,2.05,-2.78);
 for(let i=0;i<5;i++){const o=card(s,words([police?'CASE '+(14+i):'RETURN TO','OWNER'],{paper:'#E6DDC0'}),.27,.29,.1+(i%3)*.37,1.9+Math.floor(i/3)*.31,-2.75);o.rotation.z=(i%3-1)*.09;cylinder(s,.012,.015,'#9F4439',o.position.x,o.position.y+.12,-2.72).rotation.x=Math.PI/2;}
 const chair=new THREE.Group();s.add(chair);box(chair,.55,.1,.6,'#73553C',0,.52,-.55);box(chair,.52,.72,.12,'#8D6845',0,.95,-.83);for(const x of[-.2,.2])for(const z of[-.75,-.35])box(chair,.055,.5,.055,'#4C3B2E',x,.25,z);
 const telephone=new THREE.Group();s.add(telephone);telephone.position.set(-.86,1.04,.9);box(telephone,.36,.11,.28,'#2F5148');const dial=cylinder(telephone,.10,.02,'#C8B57D',0,.07,.03);dial.rotation.x=.23;
 const grip=new THREE.Mesh(new THREE.TorusGeometry(.14,.025,8,20,Math.PI),mat('#2D443E'));grip.rotation.z=.25;grip.position.set(0,.22,-.04);telephone.add(grip);
 for(const x of[-.135,.135])cylinder(telephone,.055,.09,'#345249',x,.15,-.04);
 const mug=new THREE.Group();s.add(mug);mug.position.set(.74,1.055,1);cylinder(mug,.075,.15,'#DDD7BA',0,.075,0);cylinder(mug,.062,.009,'#644735',0,.152,0);const handle=new THREE.Mesh(new THREE.TorusGeometry(.047,.013,8,20),mat('#DDD7BA'));handle.position.set(.082,.09,0);mug.add(handle);
 const penCup=cylinder(s,.055,.11,'#698E8B',.95,1.115,.6);for(let i=0;i<4;i++){const pen=box(s,.01,.22,.01,['#BD5E49','#DFBD6B','#486C72','#3D4039'][i],.92+i*.016,1.22,.6);pen.rotation.z=(i-1.5)*.13;}
 for(let i=0;i<3;i++){const env=card(s,words(['CITY POST','RETURN SERVICE'],{paper:'#D7C99F'}),.3,.19,-.5,1.06+i*.008,1.0);env.rotation.x=-Math.PI/2;env.rotation.z=i*.07;}
 const calendar=card(s,words(['NOVEMBER','SUNDAY'],{paper:'#DED7BF'}),.52,.6,2.45,2.35,-2.88);
 for(const x of[-2.8,-1.0]){box(s,.28,1.8,.16,'#8A6A4D',x,2,-2.65);for(let i=0;i<5;i++)box(s,.035,1.7,.035,'#A18162',x-.10+i*.05,2,-2.54);}
 if(police){const badge=card(s,words(['INSPECTOR','GRUBB'],{paper:'#59472E',ink:'#D6C18A'}),.5,.17,.2,1.13,1.25);}
}
export function wallet(parent){const g=new THREE.Group();parent.add(g);
 const leather=texture((c,w,h)=>{c.fillStyle='#674632';c.fillRect(0,0,w,h);c.strokeStyle='#A0825D';c.lineWidth=6;c.setLineDash([13,9]);c.strokeRect(24,24,w-48,h-48);c.setLineDash([]);c.fillStyle='#3E2D24';c.font='bold 44px Georgia';c.textAlign='center';c.fillText('C O U R I E R',w/2,h*.67);});
 box(g,.28,.19,.022,'#4F3728');card(g,leather,.277,.187,0,0,.012);
 const identity=texture((c,w,h)=>{c.fillStyle='#EEE8D2';c.fillRect(0,0,w,h);c.fillStyle='#79939B';c.fillRect(0,0,w,110);c.fillStyle='#F6EFDC';c.font='bold 52px Georgia';c.fillText('CITY IDENTITY CARD',40,76);c.fillStyle='#B9B9A7';c.fillRect(40,155,230,245);c.fillStyle='#717A71';c.beginPath();c.arc(155,225,50,0,7);c.fill();c.beginPath();c.ellipse(155,365,85,100,0,0,7);c.fill();c.fillStyle='#3F4B43';c.font='bold 65px Georgia';c.fillText('14 ELM STREET',300,235);c.font='40px Georgia';c.fillText('WEST QUARTER',300,310);c.fillText('REGISTERED RESIDENT',300,380);c.fillStyle='#A19273';for(let i=0;i<5;i++)c.fillRect(45,475+i*36,850-i%2*180,9);});
 card(g,identity,.246,.162,0,.005,.016);
 const flap=new THREE.Group();g.add(flap);card(flap,leather,.282,.192,0,0,.022);g.flap=flap;
 const snap=cylinder(flap,.009,.006,'#C9A35F',.102,0,.027);snap.rotation.x=Math.PI/2;
 return g;}
export function key(parent,scale=1){const g=new THREE.Group();parent.add(g);const brass=mat('#D7B552',{metalness:.55,roughness:.35});
 const ring=new THREE.Mesh(new THREE.TorusGeometry(.025,.007,8,24),brass);g.add(ring);box(g,.009,.088,.009,brass,0,-.057,0);box(g,.032,.011,.009,brass,.01,-.089,0);box(g,.025,.01,.009,brass,.008,-.069,0);g.scale.setScalar(scale);return g;}
export function note(parent,text=['Be more','careful.']){const p=card(parent,words(text,{font:'Georgia',paper:'#F4EDCF'}),.5,.35,0,0,0);return p;}
export function door(E){const S=makeScene(E,true),s=S.scene;box(s,4,3.6,.2,mat('white',{map:T.brick('#68758E',[2,2])}),0,1.8,-.15);
 box(s,1.35,2.6,.1,'#D1C29D',0,1.3,0);box(s,1.12,2.4,.12,'#131F30',0,1.22,.08);
 const hinge=new THREE.Group();hinge.position.set(-.55,.04,.16);s.add(hinge);box(hinge,1.1,2.35,.1,'#705038',.55,1.175,0);
 for(const y of[.55,1.7])box(hinge,.8,.65,.035,'#826044',.55,y,.065);
 const lock=box(hinge,.16,.27,.035,'#C6A251',.92,1.12,.08);box(hinge,.02,.065,.01,'#302722',.92,1.12,.102);cylinder(hinge,.04,.065,'#D3B66C',.92,.88,.1).rotation.x=Math.PI/2;
 const k=key(hinge,1.25);k.position.set(.92,1.13,.28);k.rotation.x=Math.PI/2;
 return {...S,hinge,key:k};}
export function town(E){const S=makeScene(E,true),s=S.scene,doors=[];box(s,65,.1,65,mat('white',{map:T.brick('#354154',[16,16])}),0,-.15,-16);
 const roof=mat('#3D405E'),walls=['#A7A7A0','#9E9184','#818A96','#B4A091'];
 for(let row=0;row<6;row++)for(let col=0;col<6;col++){
  const g=new THREE.Group();g.position.set((col-2.5)*4.5,0,-row*4.7);s.add(g);const h=2.3+(row+col)%3*.45;
  box(g,3,h,3,walls[(row+col)%4],0,h/2,0);
  const sh=new THREE.Shape();sh.moveTo(-1.7,0);sh.lineTo(0,1.3);sh.lineTo(1.7,0);sh.closePath();const r=new THREE.Mesh(new THREE.ExtrudeGeometry(sh,{depth:3.5,bevelEnabled:false}),roof);r.position.set(0,h,-1.75);g.add(r);
  for(const x of[-.8,.8])for(const y of[.7,1.6]){
   box(g,.59,.64,.05,'#D2C6AC',x,y,1.52);box(g,.48,.53,.03,mat('#F5D48C',{emissive:'#C58C36',emissiveIntensity:.4}),x,y,1.56);
   box(g,.025,.54,.03,'#D9D1B8',x,y,1.585);box(g,.49,.025,.03,'#D9D1B8',x,y,1.59);box(g,.67,.055,.13,'#9F9B91',x,y-.34,1.58);
  }
  box(g,3.15,.11,3.1,'#B2AEA3',0,h,0);box(g,.34,.8,.38,mat('white',{map:T.brick('#775D57')}),.9,h+.8,-.35);box(g,.44,.09,.48,'#62564F',.9,h+1.2,-.35);
  box(g,.68,1.28,.06,'#C5B9A3',0,.64,1.53);box(g,.54,1.18,.04,'#171D2D',0,.59,1.57);
  const hinge=new THREE.Group();hinge.position.set(-.27,0,1.61);g.add(hinge);box(hinge,.54,1.18,.055,'#625043',.27,.59,0);box(hinge,.035,.035,.035,'#D3B66D',.46,.58,.045);doors.push(hinge);
  box(g,.82,.08,.35,'#7A7E82',0,.025,1.73);
 }
 const moon=new THREE.Mesh(new THREE.SphereGeometry(1.4,24,16),new THREE.MeshBasicMaterial({color:'#FAE8BE'}));moon.position.set(8,13,-18);s.add(moon);
 const tower=new THREE.Group();tower.position.set(-4,0,-9);s.add(tower);box(tower,2.1,7,2.1,mat('white',{map:T.brick('#676D72',[2,5])}),0,3.5,0);
 for(const y of[.2,4.9,6.8])box(tower,2.35,.18,2.35,'#AAA68C',0,y,0);
 const spire=new THREE.Mesh(new THREE.ConeGeometry(1.8,3.2,4),mat('#314E50'));spire.rotation.y=Math.PI/4;spire.position.y=8.5;tower.add(spire);
 const clock=texture((c,w,h)=>{c.fillStyle='#D7CFB2';c.fillRect(0,0,w,h);c.strokeStyle='#34413D';c.lineWidth=20;c.beginPath();c.arc(w/2,h/2,w*.44,0,7);c.stroke();for(let i=0;i<12;i++){const a=i*Math.PI/6;c.beginPath();c.moveTo(w/2+Math.cos(a)*w*.34,h/2+Math.sin(a)*h*.34);c.lineTo(w/2+Math.cos(a)*w*.40,h/2+Math.sin(a)*h*.40);c.stroke();}c.lineWidth=24;c.beginPath();c.moveTo(w*.5,h*.5);c.lineTo(w*.5,h*.2);c.moveTo(w*.5,h*.5);c.lineTo(w*.27,h*.5);c.stroke();},256,256);
 card(tower,clock,1.5,1.5,0,5.9,1.065);
 return {...S,doors};}
