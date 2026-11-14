// Random-access, planted-foot stair gait. The exact same feet drive geometry
// and contact observations. No independent sound cadence or per-shot timers.
const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x);};
export function stairGait(progress,stairs,{descending=false,lift=.13}={}){
 const {x,z,count,rise,run}=stairs;
 if(!Number.isInteger(count)||count<1||rise<=0||run<=0)throw Error('Invalid stair geometry');
 const q=clamp(progress)*count,cycle=Math.min(count-1,Math.floor(q)),phase=q-cycle;
 const point=step=>({y:Math.max(0,step)*rise,z:step<=0?z+run:z-(step-1)*run});
 const feet={};
 for(const [name,parity,side] of[['left',0,-1],['right',1,1]]){
  const turn=cycle%2===parity;
  const previous=cycle===0?0:(cycle%2===parity?Math.max(0,cycle-1):cycle);
  const from=descending?count-previous:previous,to=descending?count-(cycle+1):cycle+1;
  const a=point(from),b=point(to),s=turn?smooth(phase/.72):0;
  const contact=!turn||phase>=.72||progress>=1;
  feet[name]={x:x+side*.105,y:a.y+(b.y-a.y)*s+(contact?0:Math.sin(Math.PI*s)*lift),z:a.z+(b.z-a.z)*s,contact};
 }
 return {root:{x,y:(feet.left.y+feet.right.y)/2,z:(feet.left.z+feet.right.z)/2},feet};
}
