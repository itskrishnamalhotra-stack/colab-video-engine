// World-space facing follows travel, never the camera. +Z is character forward.
export function headingBetween(from,to,fallback=0){const x=to[0]-from[0],z=to[2]-from[2];return Math.hypot(x,z)>1e-8?Math.atan2(x,z):fallback;}
export function characterView(bodyYaw,viewerYaw){const relative=Math.atan2(Math.sin(viewerYaw-bodyYaw),Math.cos(viewerYaw-bodyYaw)),front=Math.cos(relative);return {view:front<-.20?'back':front<.62?'profile':'front',profileSide:relative>0?-1:1,silhouetteScale:.58+.42*Math.abs(front)};}
export function angleMix(a,b,u){let d=(b-a+Math.PI)%(Math.PI*2);if(d<0)d+=Math.PI*2;return a+(d-Math.PI)*Math.max(0,Math.min(1,u));}
export function pathState(from,to,progress,{turnFrom=null,turnFraction=.16}={}){
 const u=Math.max(0,Math.min(1,progress)),target=headingBetween(from,to),turn=turnFrom==null?1:Math.min(1,u/turnFraction);
 const yaw=turnFrom==null?target:angleMix(turnFrom,target,turn*turn*(3-2*turn));
 const movement=turnFrom==null?u:Math.max(0,Math.min(1,(u-turnFraction)/(1-turnFraction)));
 return {position:from.map((a,i)=>a+(to[i]-a)*movement),yaw,distance:Math.hypot(to[0]-from[0],to[2]-from[2])*movement,movement};
}
