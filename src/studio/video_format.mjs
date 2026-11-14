// Full-HD format and caption layout. Portrait values preserve the approved kit.
export function resolveVideoFormat(name='portrait') {
  if(name==='portrait')return {width:1080,height:1920,caption:{top:1280,height:360,y:1340,size:88,maxW:960}};
  if(name==='landscape')return {width:1920,height:1080,caption:{top:880,height:200,y:948,size:58,maxW:1680}};
  throw Error('Unsupported video format: '+name);
}
