// Verify the actual immutable VideoFrame consumed by the encoder, not just its
// scene texture. Keep presentation + snapshot in one synchronous section.
export function sampledFrameIsVisible(rgba){
 let lit=0,count=0;
 for(let i=0;i<rgba.length;i+=4){count++;if(rgba[i]+rgba[i+1]+rgba[i+2]>18)lit++;}
 return count>0&&lit/count>=.02;
}

export function createFrameSampler(){
 const canvas=new OffscreenCanvas(40,30),ctx=canvas.getContext('2d',{willReadFrequently:true});
 return frame=>{
  ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,40,30);
  ctx.drawImage(frame,0,0,40,30);
  return sampledFrameIsVisible(ctx.getImageData(0,0,40,30).data);
 };
}

export async function captureCheckedFrame({time,duration,timestamp,prepare,ready,present,finish,snapshot,visible,onRetry=()=>{}}){
 for(let attempt=0;attempt<2;attempt++){
  const prepared=prepare(time);
  // Finish pending target/PBO work before touching the encoder canvas.
  await ready(time);
  present(prepared);finish();
  const frame=snapshot(timestamp);
  try{
   if(time<.3||time>duration-.5||visible(frame))return frame;
  }catch(error){frame.close();throw error;}
  frame.close();
  if(attempt===0)onRetry({time,timestamp,attempt:1});
 }
 throw Error('Captured VideoFrame is blank at '+time+' after an exact-time retry; refusing encoding');
}
