import * as THREE from 'three';
import {FORMAT} from '../core/video_format.js';
// Compose the existing caption artwork over the owned scene texture on the GPU.
export function makeGpuCompositor(engine){
 const {width:W,height:H,caption:band}=FORMAT;
 const renderer=engine.renderer,caption=document.createElement('canvas');caption.width=W;caption.height=band.height;
 const context=caption.getContext('2d',{willReadFrequently:true}),texture=new THREE.CanvasTexture(caption);texture.generateMipmaps=false;texture.minFilter=texture.magFilter=THREE.NearestFilter;texture.colorSpace=THREE.NoColorSpace;
 const uniforms={sceneImage:{value:renderer.userData.captureTarget.texture},captionImage:{value:texture},fade:{value:1},frameHeight:{value:H},bandTop:{value:band.top},bandHeight:{value:band.height}};
 const vertexShader='varying vec2 uvOut;void main(){uvOut=uv;gl_Position=vec4(position.xy,0.0,1.0);}';
 const material=new THREE.ShaderMaterial({uniforms,vertexShader,depthTest:false,depthWrite:false,toneMapped:false,fragmentShader:`varying vec2 uvOut;uniform sampler2D sceneImage,captionImage;uniform float fade,frameHeight,bandTop,bandHeight;
 void main(){vec3 bg=texture2D(sceneImage,uvOut).rgb*fade;float top=(1.0-uvOut.y)*frameHeight;vec4 cap=vec4(0.0);if(top>=bandTop&&top<bandTop+bandHeight)cap=texture2D(captionImage,vec2(uvOut.x,1.0-(top-bandTop)/bandHeight));gl_FragColor=vec4(mix(bg,cap.rgb,cap.a),1.0);}`});
 const scene=new THREE.Scene(),camera=new THREE.Camera();scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),material));
 const guardTarget=new THREE.WebGLRenderTarget(1,1,{depthBuffer:false,stencilBuffer:false});
 const guardMaterial=new THREE.ShaderMaterial({uniforms:{sceneImage:uniforms.sceneImage},vertexShader,depthTest:false,depthWrite:false,toneMapped:false,fragmentShader:`uniform sampler2D sceneImage;void main(){float lit=0.0;for(int y=0;y<30;y++){for(int x=0;x<40;x++){vec3 c=texture2D(sceneImage,(vec2(float(x),float(y))+.5)/vec2(40.0,30.0)).rgb;if(c.r+c.g+c.b>18.0/255.0)lit+=1.0;}}gl_FragColor=vec4(lit/1200.0,0.0,0.0,1.0);}`});
 const guardScene=new THREE.Scene();guardScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),guardMaterial));let captionKey=null;
 return {
  context,
  paint(key,draw){if(key===captionKey)return;context.setTransform(1,0,0,1,0,0);context.clearRect(0,0,W,band.height);context.save();context.translate(0,-band.top);draw(context);context.restore();texture.needsUpdate=true;captionKey=key;},
  present(fade,target=null){uniforms.fade.value=fade;renderer.setRenderTarget(target);renderer.clear();renderer.render(scene,camera);renderer.setRenderTarget(null);},
  async assertVisible(t,duration){
   if(t<.3||t>duration-.5)return;
   renderer.setRenderTarget(guardTarget);renderer.render(guardScene,camera);renderer.setRenderTarget(null);
   const pixel=new Uint8Array(4);await renderer.readRenderTargetPixelsAsync(guardTarget,0,0,1,1,pixel);
   if(pixel[0]<5)throw Error('Blank GPU-composed frame at '+t+'; refusing delivery');
  },
  createCheckTarget(){return new THREE.WebGLRenderTarget(W,H,{depthBuffer:false,stencilBuffer:false});}
 };
}
