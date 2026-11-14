"""Require an actual per-frame animation event trace, bound to visual source hashes."""
import hashlib,json,subprocess
from pathlib import Path
from render_reuse import visual_signature,digest
ENGINE=Path(__file__).resolve().parent

def trace_key(project):
 p=Path(project)
 files=[p/'action_probe.json',ENGINE/'trace_action_events.mjs',ENGINE/'action_event_trace.mjs']
 return hashlib.sha256((visual_signature(p)+''.join(digest(f) for f in files)).encode()).hexdigest()

def ensure_trace(project):
 p=Path(project);key=trace_key(p);out=p/'data/animation-events.json'
 try:
  old=json.loads(out.read_text())
  if old['source_sha256']==key:
   payload={k:v for k,v in old.items() if k!='trace_content_sha256'}
   if old.get('trace_content_sha256')==hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest():return old
 except (OSError,ValueError,KeyError):pass
 config=json.loads((ENGINE/'video_defaults.json').read_text())
 # This is still the normal sound-state pass, not an extra visual audit. Long
 # stories evaluate more output frames and need a proportionate execution bound.
 timing=json.loads((p/'data/lines.json').read_text())
 duration=float(timing.get('duration',timing.get('dur',30))) if isinstance(timing,dict) else 30
 subprocess.run([config['node'],str(ENGINE/'trace_action_events.mjs'),str(p.resolve())],check=True,timeout=max(120,min(1200,round(duration*2))))
 if trace_key(p)!=key:raise ValueError('Animation inputs changed during contact trace')
 temporary=p/'data/animation-events.unverified.json';trace=json.loads(temporary.read_text())
 trace.update(source_sha256=key,visual_inputs_sha256=visual_signature(p),method='actual-animation-state-per-output-frame')
 if trace.get('framing'):
  (p/'data/framing-audit.json').write_text(json.dumps({'frames':trace['frame_count'],'shots':trace['framing'],'visual_inputs_sha256':trace['visual_inputs_sha256']},indent=2))
 trace['trace_content_sha256']=hashlib.sha256(json.dumps(trace,sort_keys=True).encode()).hexdigest()
 out.write_text(json.dumps(trace,indent=2));temporary.unlink();return trace

def bind_events(plan,trace):
 result=[];used=set()
 materials=json.loads((ENGINE/'sound_materials.json').read_text())
 forbidden={'at','repeat_seconds','until','span','t','offset'}
 for index,binding in enumerate(plan['events']):
  if forbidden.intersection(binding):raise ValueError('Estimated/offset Foley timing is forbidden in event-bound plans')
  matches=[e for e in trace['events'] if e['shot']==binding['shot'] and e['id']==binding['event']]
  if not matches:
   spec=next((s for s in trace['observations'] if s['shot']==binding['shot'] and s['id']==binding['event']),None)
   if spec is not None and spec.get('min_events',1)==0:continue # Short shot contains no landing of this foot.
   raise ValueError('No measured animation event: '+binding['shot']+'/'+binding['event'])
  if not binding.get('reason') or not binding.get('material'):raise ValueError('Every sound needs an action/material rationale')
  for sample in binding.get('samples',[binding.get('sample')]):
   if binding['material'] not in materials.get(sample,[]):
    raise ValueError(f'Sample is not approved for this material: {sample} / {binding["material"]}')
  for variant,e in enumerate(matches):
   if binding['material']!=e['material']:raise ValueError('Sound/animation material mismatch: '+e['id'])
   item={k:v for k,v in binding.items() if k not in ('samples','event')}
   if 'samples' in binding:item['sample']=binding['samples'][variant%len(binding['samples'])]
   item.update(t=e['t'],frame=e['frame'],fps=trace['fps'],event_id=e['id'],event_index=index,
               timing_source='animation-state',evidence=e['evidence'],onset_align=True)
   if 'end_frame' in e:item.update(end_frame=e['end_frame'],duration=e['duration'])
   result.append(item);used.add((e['shot'],e['id']))
 return sorted(result,key=lambda e:e['frame'])

def verify_cues(project,cues):
 p=Path(project);plan=json.loads((p/'action_plan.json').read_text())
 if plan.get('version',1)<2:raise ValueError('Estimated Foley is not allowed for production reference cartoons')
 trace=ensure_trace(p)
 if cues.get('trace_sha256')!=trace['source_sha256'] or cues['cues']!=bind_events(plan,trace):
  raise ValueError('Sound cues differ from measured animation events; export them again')

def write_audit(project,cues,trace):
 p=Path(project);probe=json.loads((p/'action_probe.json').read_text())
 rows=['# Sound synchronization audit','',
       'Timing is measured from the existing animation state on each output frame at '+str(trace['fps'])+' fps.',
       'Frame numbers are zero-based; sound attack starts at frame / fps. Precision is one output frame, not a claim of subframe physical simulation.',
       'This is a transform/state audit of the unchanged source, not a claim that all contact geometry or sound aesthetics have been visually/listening reviewed.',
       'Source signature: `'+trace['visual_inputs_sha256']+'`','',
       '| Time (s) | Frame | Shot / action | Source | Material / reason |',
       '| --- | ---: | --- | --- | --- |']
 for e in cues['cues']:
  rows.append(f"| {e['t']:.6f} | {e['frame']} | {e['shot']} / {e['event_id']} | {e['sample']} | {e['material']}: {e['reason']} |")
 rows+=['','## Deliberately silent actions','']
 rows += ['- '+shot+': '+reason for shot,reason in probe.get('omitted_actions',{}).items()]
 (p/'data/sound-sync-audit.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
