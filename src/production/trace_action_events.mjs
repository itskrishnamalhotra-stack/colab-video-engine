// CPU-only scene-state evaluation. No WebGL context, images or video are rendered.
// Original production files are served unchanged except an in-memory observation hook.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import {spawn} from 'node:child_process';
import {collectEvents} from './action_event_trace.mjs';

const root=path.resolve(process.argv[2]);
const probe=JSON.parse(fs.readFileSync(path.join(root,'action_probe.json'),'utf8'));
const story=path.resolve(root,probe.story_module);
if(!story.startsWith(root+path.sep))throw Error('Invalid story path');
let source=fs.readFileSync(story,'utf8');
if(source.split(probe.hook).length!==2)throw Error('Observation hook must match exactly once');
const byShot=new Map();
for(const spec of probe.observations){
  const list=byShot.get(spec.shot)||[];list.push(spec);byShot.set(spec.shot,list);
}
const cases=[...byShot].map(([shot,specs])=>`case ${JSON.stringify(shot)}:return {${specs.map(s=>JSON.stringify(s.id)+':('+s.expression+')').join(',')}};`).join('\n');
const invariants=(probe.invariants||[]).map(s=>`if(!(${s.expression}))throw Error(${JSON.stringify('Scene invariant: '+s.reason)});`).join('\n');
source=source.replace(probe.hook,probe.hook+`;${invariants};E.observe(id,(()=>{switch(id){${cases}default:return {};}})());`);
// Read the leg lift expression from the actual pinned drawing code: no separate cadence.
const legacy=(probe.adapter||'toon')==='toon';
const toonPath=legacy?path.resolve(root,probe.toon_module):null;
let toon=legacy?fs.readFileSync(toonPath,'utf8'):null;
const lift=legacy?toon.match(/const lift = ([^;]+);/):null;
let footAdapter="throw Error('Observe physical rigged feet directly; the flat-toon adapter is unavailable')";
if(legacy){
if(!lift)throw Error('Pinned toon leg implementation changed; update the probe adapter');
if(!toon.includes('this.st = st;'))throw Error('Unsupported actor state implementation');
const begin=toon.indexOf('  set(st = {}) {'),end=toon.indexOf('  /** turn the cut-out',begin);
if(begin<0||end<0)throw Error('Unsupported Toon.set adapter');
// Pixel painting is omitted, state/matrices/arms and all story action logic still execute.
toon=toon.slice(0,begin)+'  set(st = {}) { this.st=st;return this; }\n'+toon.slice(end);
footAdapter=`if(!['walk','run'].includes(S.legs))return 0;return ${lift[1]};`;
}
const page=`<!doctype html><meta charset="utf-8"><script type="importmap">{"imports":{"three":"/vendor/three.module.js","three/addons/":"/vendor/addons/"}}</script>
<script type="module">
import {loadTiming,T} from '/src/core/timing.js';
import {buildShots} from ${JSON.stringify('/'+probe.story_module)};
window.runProbe=async()=>{
 await loadTiming(); let rows=[],current=null;const framing=new Map();
 const E={envMap:null,render(){},footLift(S,side){${footAdapter}},observe(shot,values){current={shot,values};}};
 const {shots}=await buildShots(E);shots.sort((a,b)=>a.at-b.at);
 // Match cloud_capture.mjs exactly, including its rounded final frame count.
 const fps=${probe.fps},count=Math.round(T.dur*fps);
 for(let frame=0;frame<count;frame++){
  const t=Math.min(frame/fps,T.dur-1e-4);let i=shots.length-1;while(i>0&&shots[i].at>t)i--;
  const sh=shots[i],end=i+1<shots.length?shots[i+1].at:T.dur;
  current=null;sh.draw(t-sh.at,end-sh.at,t,()=>{});
  if(!current)throw Error('No contact observation for '+sh.id);
  const checked=sh.framing?.();
  if(checked){
   let record=framing.get(sh.id);
   if(!record){record={shot:sh.id,frames:0,adjusted_frames:0,original_cropped_frames:0,face_overlap_frames:0,max_dolly:0,
    corrected_bounds:{left:Infinity,right:-Infinity,bottom:Infinity,top:-Infinity},safe:checked.safe};framing.set(sh.id,record);}
   record.frames++;record.adjusted_frames+=+checked.adjusted;record.max_dolly=Math.max(record.max_dolly,checked.dolly);record.face_overlap_frames+=+(checked.face_overlaps?.length>0);
   const b=checked.before,s=checked.safe;
   if(b.behind||b.left<s.left-1e-5||b.right>s.right+1e-5||b.bottom<s.bottom-1e-5||b.top>s.top+1e-5)record.original_cropped_frames++;
   const a=checked.after;record.corrected_bounds.left=Math.min(record.corrected_bounds.left,a.left);record.corrected_bounds.right=Math.max(record.corrected_bounds.right,a.right);
   record.corrected_bounds.bottom=Math.min(record.corrected_bounds.bottom,a.bottom);record.corrected_bounds.top=Math.max(record.corrected_bounds.top,a.top);
  }
  rows.push({frame,...current});
 }
 return {fps,frame_count:count,duration:T.dur,rows,framing:[...framing.values()]};
};window.probeReady=true;
</script>`;
const mime={'.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.otf':'font/otf','.ttf':'font/ttf'};
const server=http.createServer((req,res)=>{
 try{
  const url=new URL(req.url,'http://127.0.0.1');
  if(url.pathname==='/__action_probe__'){res.setHeader('Content-Type','text/html');res.end(page);return;}
  const file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
  if(!file.startsWith(root+path.sep)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
  res.end(file===story?source:file===toonPath?toon:fs.readFileSync(file));
 }catch{res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const chrome=process.env.CHROME||'C:/Program Files/Google/Chrome/Application/chrome.exe';
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'action-trace-'));
let browser,ws;
try{
 browser=spawn(chrome,['--headless=new','--disable-gpu','--remote-debugging-port=0',`--user-data-dir=${profile}`,'--no-first-run','--no-default-browser-check',...(process.getuid?.()===0?['--no-sandbox']:[]),'about:blank'],{stdio:'ignore',windowsHide:true});
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));let port;
 for(let i=0;i<100&&!port;i++){try{port=fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0].trim();}catch{await sleep(100);}}
 if(!port)throw Error('Contact-trace browser did not start');
 const target=await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(`http://127.0.0.1:${server.address().port}/__action_probe__`)}`,{method:'PUT'})).json();
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 let seq=0;const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}};
 const evaluate=expr=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method:'Runtime.evaluate',params:{expression:expr,returnByValue:true,awaitPromise:true}}));});
 for(let i=0;;i++){const value=await evaluate('window.probeReady');if(value.result?.value)break;if(i>150)throw Error('Contact probe load failed');await sleep(100);}
 const response=await evaluate('runProbe()');
 if(response.exceptionDetails)throw Error(response.exceptionDetails.exception?.description||response.exceptionDetails.text);
 const trace=response.result.value;
 trace.events=collectEvents(trace.rows,probe.observations,trace.fps);
 for(const requirement of probe.event_requirements||[]){
  const count=trace.events.filter(e=>e.id.startsWith(requirement.prefix)).length;
  if(count<requirement.min_events)throw Error('Missing required action contacts: '+requirement.prefix+' '+count+'/'+requirement.min_events+' '+requirement.reason);
 }
 trace.observations=probe.observations;delete trace.rows;
 fs.writeFileSync(path.join(root,'data/animation-events.unverified.json'),JSON.stringify(trace,null,2));
 console.log(`ANIMATION_CONTACTS ${trace.frame_count} frames / ${trace.events.length} measured events; no image render`);
}finally{
 ws?.close();browser?.kill();server.close();
 // Remove only the exact temporary profile we created, after Chrome exits.
 if(browser)await new Promise(r=>{if(browser.exitCode!==null)r();else{browser.once('exit',r);setTimeout(r,3000);}});
 try{fs.rmSync(profile,{recursive:true,force:true});}catch{}
}
