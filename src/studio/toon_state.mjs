// Exact state keys: phase affects pixels only for walking/running legs.
// Do not quantize visible state; random-access frames must remain deterministic.
export function toonStateKey(state){
 const moving=state.legs==='walk'||state.legs==='run';
 return JSON.stringify({...state,phase:moving?(state.phase??0):0},(key,value)=>typeof value==='function'?(value.name||String(value).length):value);
}

// Canvas pixels relative to the standing adult pose.
export function upperBodyDrop(state,look){
 return (state.legs==='sit'?210:0)+(look.kid?190:0)+(state.bob||0)+(state.legs==='jump'?-60:0);
}
