// Derive contacts from successive evaluated animation states, never shot fractions.
export function collectEvents(frames, specs, fps) {
  const previous = new Map(), result = [], moving = new Map(),intervals=new Map();
  for (const row of frames) {
    for (const spec of specs.filter(s => s.shot === row.shot)) {
      const value = row.values[spec.id], key = row.shot + '/' + spec.id;
      if (value === undefined || (typeof value === 'number' && !Number.isFinite(value)))
        throw Error('Missing/nonfinite animation observation: ' + key);
      if(spec.detect==='interval'){
        if(value){
          let active=intervals.get(key);
          if(!active){active={id:spec.id,shot:row.shot,frame:row.frame,t:row.frame/fps,material:spec.material,object:spec.object,
            evidence:{detector:'interval',property:spec.expression,first_active_frame:row.frame}};intervals.set(key,active);}
          active.end_frame=row.frame+1;active.duration=(active.end_frame-active.frame)/fps;
        }else if(intervals.has(key)){result.push(intervals.get(key));intervals.delete(key);}
        continue;
      }
      let before = previous.get(key);
      if (!before && spec.rest_value != null)
        before={value:spec.rest_value,frame:row.frame-1,baseline:true};
      let hit = false, frame = row.frame;
      if (before && before.frame !== row.frame - 1) throw Error('Non-contiguous observation: '+key);
      if (before) {
        if (spec.detect === 'rising') hit = !before.value && !!value;
        else if (spec.detect === 'falling') hit = !!before.value && !value;
        else if (spec.detect === 'motion-start') {
          const changed = Math.abs(value-before.value) > (spec.epsilon ?? 1e-9);
          hit = changed && !moving.get(key); moving.set(key, changed);
        } else if (spec.detect === 'settled') {
          const changed = Math.abs(value-before.value) > (spec.epsilon ?? 1e-9);
          hit = !changed && !!moving.get(key); moving.set(key, changed);
          // First stationary frame is the previous frame, confirmed by this one.
          if (hit) frame = before.frame;
        } else throw Error('Unsupported contact detector: '+spec.detect);
      }
      if (hit) result.push({id: spec.id, shot: row.shot, frame, t:frame/fps,
        evidence:{detector:spec.detect, property:spec.expression, previous:before.value,
          current:value, observed_frame:row.frame}, material:spec.material, object:spec.object});
      previous.set(key,{value,frame:row.frame});
    }
  }
  result.push(...intervals.values());
  for (const spec of specs) {
    const count=result.filter(e=>e.id===spec.id&&e.shot===spec.shot).length;
    if (count < (spec.min_events ?? 1) || (spec.max_events != null && count > spec.max_events))
      throw Error(`Animation event count outside authored contract: ${spec.shot}/${spec.id}: ${count}`);
  }
  return result.sort((a,b)=>a.frame-b.frame || a.id.localeCompare(b.id));
}
