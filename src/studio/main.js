// Boot: fonts → script + timing → 3D engine + sets → captions → shots. draw(t) renders film time t (pure function of t):
// the shot renders its 3D frame into the hidden WebGL canvas, which is copied onto the 2D canvas, then the 2D layer
// (labels, counters) and the captions go on top. window.OP is the API tools/capture.mjs drives.
import { W, H, setCtx, ctx, clamp } from './core/lib.js';
import { T, loadTiming } from './core/timing.js';
import { buildCaptions, drawCaption, captionList } from './core/captions.js';
import { makeEngine, RES, AA } from './studio/engine.js';
import { buildShots } from './shots.js';
import {createFrameReader} from './studio/frame_reader.mjs';
import {makeGpuCompositor} from './studio/gpu_compositor.mjs';
import {captureCheckedFrame,createFrameSampler} from './studio/browser_frame.mjs';
import {FORMAT} from './core/video_format.js';

const cv = document.getElementById('cv'), GL = document.getElementById('gl');
setCtx(cv.getContext('2d',{willReadFrequently:true,alpha:false}));
const OP = (window.OP = { ready: false });
let pendingSnapshot=null;

function draw(t,deferred=false) {
  t = clamp(t, 0, T.dur - 1e-4);
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.letterSpacing = '0px';
  const S = OP._shots; let i = S.length - 1; while (i > 0 && S[i].at > t) i--;
  const sh = S[i], end = i < S.length - 1 ? S[i + 1].at : T.dur, d = end - sh.at, lt = t - sh.at;
  const blit = () => {if(deferred==='gpu')return;if(deferred)pendingSnapshot=OP._frameReader.snapshot();else OP._frameReader.blit();};
  ctx.save(); sh.draw(lt, d, t, blit); ctx.restore();
  if(deferred==='gpu')return;
  if(deferred){if(!pendingSnapshot)throw Error('Scene did not submit a frame');const pending=pendingSnapshot;pendingSnapshot=null;return pending;}
  overlay(t);
}
function overlay(t){
  ctx.globalAlpha = 1; ctx.letterSpacing = '0px';
  const fade = Math.min(clamp(t / 0.25), clamp((T.dur - t) / 0.4));
  if (fade < 1) { ctx.fillStyle = '#000'; ctx.globalAlpha = 1 - fade; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
  drawCaption(t);
}

(async () => {
  try {
    await document.fonts.load('900 100px Inter'); await document.fonts.load('800 100px Inter');
    const script = await (await fetch('script.json', { cache: 'no-store' })).json();
    await loadTiming();
    buildCaptions(script);
    cv.width=W;cv.height=H;
    GL.width = Math.round(W * RES); GL.height = Math.round(H * RES);
    const E = makeEngine(GL, { w: GL.width, h: GL.height, samples: AA });
    OP._renderer=E.renderer;OP._frameReader=createFrameReader(E.renderer,ctx,W,H);
    E.renderer.userData.cacheShadows=script.capture?.shadow_cache===true;
    OP.gpuInfo = () => {const gl=E.renderer.getContext(),ex=gl.getExtension('WEBGL_debug_renderer_info');return {renderer:ex?gl.getParameter(ex.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),resolution:[GL.width,GL.height]};};
    const { shots, cues } = await buildShots(E);
    shots.sort((a, b) => a.at - b.at);
    OP._shots = shots; OP.script = script;
    OP.duration = () => T.dur;
    OP.draw = draw;
    // The optimized route is opt-in for stories whose only 2D layer is captions.
    const fastComposition=script.capture?.scene_overlay==='none';
    const gpuCompositor=makeGpuCompositor(E),captions=captionList();
    const prepareGpuFrame=t=>{
      draw(t,'gpu');const caption=captions.find(c=>t>=c.s&&t<c.e),key=caption?(t-caption.s<.1?t:caption.s):'empty';
      gpuCompositor.paint(key,context=>{setCtx(context);try{drawCaption(t);}finally{setCtx(cv.getContext('2d'));}});
      return Math.min(clamp(t/.25),clamp((T.dur-t)/.4));
    };
    const gpuFrame=(t,target=null)=>gpuCompositor.present(prepareGpuFrame(t),target);
    OP.captureCapabilities={asyncRaw:fastComposition};
    const composed=t=>OP._frameReader.composed(fastComposition&&t>=.25&&T.dur-t>=.4?[0,FORMAT.caption.top,W,FORMAT.caption.height]:null);
    const postFrame=async(t,endpoint,sequence)=>{
      OP._frameReader.assertVisible(t,T.dur);
      const started=performance.now(),body=composed(t),composedAt=performance.now();
      const response=await fetch(endpoint+'?seq='+sequence,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body});
      const result=await response.json();if(!response.ok)throw Error(result.error||'Raw capture failed');
      if(result.frame!==sequence+1||result.bytes!==W*H*4)throw Error('Raw capture acknowledgement mismatch');
      OP.transferTiming={compose_ms:composedAt-started,upload_ms:performance.now()-composedAt};return result;
    };
    OP.frame = (t, q = 0.92) => {
      draw(t);
      OP._frameReader.assertVisible(t,T.dur);
      return cv.toDataURL('image/jpeg', q);
    };
    OP.rawFrame = async (t,endpoint,sequence) => {
      draw(t);
      // Preserve the composed captions/fades. Binary POST avoids JPEG encode,
      // base64/JSON transfer and FFmpeg JPEG decode; GPU readback still occurs.
      return postFrame(t,endpoint,sequence);
    };
    OP.rawBatch=async(times,endpoint,sequence)=>{
      if(!fastComposition||times.length>4||times.length<1)throw Error('Invalid asynchronous frame batch');
      const begin=performance.now(),timing={wait_ms:0,compose_ms:0,upload_ms:0};
      const queued=times.map(t=>({t,frame:draw(t,true)}));
      timing.draw_ms=performance.now()-begin;const payloads=[];
      for(let i=0;i<queued.length;i++){
        const item=queued[i],start=performance.now(),pixels=await item.frame;timing.wait_ms+=performance.now()-start;
        const composeStart=performance.now();OP._frameReader.present(pixels);overlay(item.t);OP._frameReader.assertVisible(item.t,T.dur);payloads.push(new Uint8Array(composed(item.t)));timing.compose_ms+=performance.now()-composeStart;
      }
      const upload=performance.now(),response=await fetch(endpoint+'?seq='+sequence+'&count='+times.length,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:new Blob(payloads)}),result=await response.json();
      if(!response.ok||result.frame!==sequence+times.length||result.bytes!==times.length*W*H*4)throw Error(result.error||'Raw frame batch acknowledgement mismatch');
      timing.upload_ms=performance.now()-upload;return {frames:times.length,timing};
    };
    OP.readbackCheck=async(times)=>{
      if(!fastComposition)throw Error('Story has not declared its overlay compatibility');
      const hash=async(bytes)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
      const expected=[];for(const t of times){draw(t);expected.push(await hash(ctx.getImageData(0,0,W,H).data));}
      const queued=times.map(t=>({t,frame:draw(t,true)})),results=[];
      for(let i=0;i<queued.length;i++){
        const item=queued[i];OP._frameReader.present(await item.frame);overlay(item.t);OP._frameReader.assertVisible(item.t,T.dur);
        const actual=await hash(composed(item.t));if(actual!==expected[i])throw Error('Asynchronous pixel mismatch at '+item.t);
        results.push({time:item.t,exact_pixels:true});
      }return results;
    };
    OP.shadowCheck=async(times)=>{
      const hash=async()=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',ctx.getImageData(0,0,W,H).data)),v=>v.toString(16).padStart(2,'0')).join('');
      const results=[];
      for(const t of times){E.renderer.userData.cacheShadows=false;draw(t);const expected=await hash();E.renderer.userData.cacheShadows=true;draw(t);if(await hash()!==expected)throw Error('Cached shadow pixel mismatch at '+t);draw(t);if(await hash()!==expected)throw Error('Reused shadow pixel mismatch at '+t);results.push({time:t,exact_pixels:true});}
      return results;
    };
    OP.gpuCompositionCheck=async(times)=>{
      const target=gpuCompositor.createCheckTarget(),pixels=new Uint8Array(W*H*4),results=[];
      try{for(const t of times){draw(t);const expected=ctx.getImageData(0,0,W,H).data;gpuFrame(t,target);E.renderer.readRenderTargetPixels(target,0,0,W,H,pixels);let squared=0,max=0;
        for(let y=0;y<H;y++)for(let x=0;x<W*4;x++){const d=expected[y*W*4+x]-pixels[(H-1-y)*W*4+x];squared+=d*d;max=Math.max(max,Math.abs(d));}
        const rmse=Math.sqrt(squared/pixels.length);if(rmse>1||max>5)throw Error('GPU composition mismatch at '+t+': RMSE='+rmse+' max='+max);await gpuCompositor.assertVisible(t,T.dur);results.push({time:t,rmse,max_delta:max});
      }}finally{target.dispose();}return results;
    };
    OP.browserVideo=async({start,count,times},endpoint)=>{
      if(!fastComposition)throw Error('Browser video requires caption-only composition');
      const config={codec:'avc1.420028',width:W,height:H,framerate:30,bitrate:20000000,latencyMode:'realtime',hardwareAcceleration:'prefer-software',avc:{format:'annexb'}};
      if(!(await VideoEncoder.isConfigSupported(config)).supported)throw Error('This browser cannot encode the required H.264 stream');
      let chunks=[],bytes=0,encoded=0,sequence=0,pendingBytes=0,fatal=null,uploads=Promise.resolve(),captureRetries=0;const begun=performance.now();
      const frameVisible=createFrameSampler(),gl=E.renderer.getContext();
      const flushBatch=()=>{
        if(!chunks.length)return;const parts=chunks,batchCount=parts.length,first=sequence,size=bytes;chunks=[];bytes=0;sequence+=batchCount;pendingBytes+=size;
        uploads=uploads.then(async()=>{const response=await fetch(endpoint+'?seq='+first+'&count='+batchCount,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:new Blob(parts)}),result=await response.json();if(!response.ok||result.frame!==first+batchCount||result.bytes!==size)throw Error(result.error||'Encoded batch acknowledgement mismatch');pendingBytes-=size;});uploads.catch(error=>{fatal=error;});
      };
      const encoder=new VideoEncoder({error:error=>{fatal=error;},output:chunk=>{
        if(Math.abs(chunk.timestamp-Math.round(encoded*1000000/30))>1){fatal=Error('Unexpected encoded frame order');return;}
        const data=new Uint8Array(chunk.byteLength);chunk.copyTo(data);chunks.push(data);bytes+=data.length;encoded++;if(chunks.length>=30||bytes>=2000000)flushBatch();
      }});encoder.configure(config);
      try{
        for(let i=0;i<count;i++){
          if(fatal)throw fatal;if(pendingBytes>8000000)await uploads;
          while(encoder.encodeQueueSize>3)await new Promise(resolve=>encoder.addEventListener('dequeue',resolve,{once:true}));
          const t=times?times[i]:start+i/30;
          const frame=await captureCheckedFrame({time:t,duration:T.dur,timestamp:Math.round(i*1000000/30),
            prepare:prepareGpuFrame,ready:time=>gpuCompositor.assertVisible(time,T.dur),
            present:fade=>gpuCompositor.present(fade),finish:()=>{gl.bindBuffer(gl.PIXEL_PACK_BUFFER,null);gl.finish();},
            snapshot:timestamp=>new VideoFrame(GL,{timestamp,duration:33333}),visible:frameVisible,
            onRetry:info=>{captureRetries++;console.warn('VIDEO_FRAME_RETRY '+JSON.stringify(info));}});
          try{encoder.encode(frame,{keyFrame:i%60===0});}finally{frame.close();}
        }
        await encoder.flush();flushBatch();await uploads;if(fatal)throw fatal;if(encoded!==count)throw Error('Browser encoder lost frames: '+encoded+'/'+count);
        return {frames:encoded,seconds:(performance.now()-begun)/1000,encoder:'browser-h264-software',bitrate:config.bitrate,capture_retries:captureRetries,actual_video_frames_checked:true};
      }finally{encoder.close();}
    };
    OP.shots = () => shots.map((s, i) => ({ id: s.id, at: +s.at.toFixed(3), end: +(i < shots.length - 1 ? shots[i + 1].at : T.dur).toFixed(3), note: s.note || '' }));
    OP.captions = () => captionList().map((c) => ({ s: +c.s.toFixed(3), e: +c.e.toFixed(3), text: c.words.map((w) => (w.hi ? '*' : '') + w.txt).join(' ') }));
    OP.cues = () => cues.slice().sort((a, b) => a.t - b.t);
    OP.ready = true;
    const q = new URLSearchParams(location.search);
    if (!q.has('capture')) {
      if (q.has('t')) draw(+q.get('t'));
      else {
        const audio = new Audio('data/mix.wav'); let t0 = null; const btn = document.getElementById('play'); btn.hidden = false;
        btn.onclick = () => { btn.hidden = true; t0 = performance.now(); audio.currentTime = 0; audio.play().catch(() => {}); };
        const loop = (now) => { const t = t0 == null ? 0 : (now - t0) / 1000; draw(t); if (t0 != null && t > T.dur) { t0 = null; btn.hidden = false; } requestAnimationFrame(loop); };
        requestAnimationFrame(loop);
      }
    }
  } catch (e) { OP.bootError = String(e && e.stack || e); console.error(e); }
})();
