// Deterministic NVIDIA-EGL readback. Testable without a browser or GPU.
export function createFrameReader(renderer,context,width,height){
 const pixels=new Uint8Array(width*height*4),image=context.createImageData(width,height),stride=width*4;
 return {
  blit(){
   const gl=renderer.getContext();renderer.setRenderTarget(null);gl.finish();
   if(renderer.userData?.captureTarget)renderer.readRenderTargetPixels(renderer.userData.captureTarget,0,0,width,height,pixels);
   else gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
   const error=gl.getError?.()||0;if(error)throw Error('GPU pixel readback failed: '+error);
   for(let y=0;y<height;y++)image.data.set(pixels.subarray((height-1-y)*stride,(height-y)*stride),y*stride);
   context.putImageData(image,0,0);
  },
  assertVisible(t,duration){
   if(t<.3||t>duration-.5)return;
   let lit=0,count=0;const step=Math.max(4,Math.floor(pixels.length/1200/4)*4);
   for(let i=0;i<pixels.length;i+=step){count++;if(pixels[i]+pixels[i+1]+pixels[i+2]>18)lit++;}
   if(lit/Math.max(1,count)<.02)throw Error('Blank GPU readback at '+t+'; refusing a flickering export.');
  }
 };
}
