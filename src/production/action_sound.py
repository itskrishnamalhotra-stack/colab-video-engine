"""Resolve narration anchors and measured animation contacts for Foley.

Version 2 plans bind sound to actual evaluated animation state transitions.
Version 1 is retained only for unprofiled historical projects.
"""
import json, math, re
from pathlib import Path
from sound_profile import validate_events

def norm(word):
 return re.sub(r"[^a-z0-9']",'',str(word).lower())

def resolve_shots(plan,timing,words):
 result=[]
 for shot in plan['shots']:
  line=timing['lines'][shot['line']]
  if 'word' in shot:
   matches=[w for w in words if w['line']==shot['line'] and norm(w['w'])==norm(shot['word'])]
   index=shot.get('occurrence',1)-1
   if index>=len(matches):raise ValueError(f"Missing shot anchor {shot['id']}: {shot['word']}")
   start=matches[index]['s']+shot.get('offset',0)
  else:start=line['start']+(line['end']-line['start'])*shot.get('fraction',0)
  result.append({**shot,'start':max(0,start)})
 result.sort(key=lambda s:s['start'])
 result[0]['start']=0
 for i,s in enumerate(result):
  s['end']=result[i+1]['start'] if i+1<len(result) else timing['duration']
  if s['end']<=s['start']:raise ValueError('Overlapping shot anchors: '+s['id'])
 return result

def export(project):
 project=Path(project);data=project/'data'
 plan=json.loads((project/'action_plan.json').read_text())
 profile=validate_events(plan['events'])
 timing=json.loads((data/'lines.json').read_text());words=json.loads((data/'words.json').read_text())
 shots=resolve_shots(plan,timing,words);lookup={s['id']:s for s in shots};events=[]
 if plan.get('version',1)>=2:
  # Write the exact shot clock before evaluating the unchanged scene functions.
  (data/'shot_timing.json').write_text(json.dumps(shots,indent=2))
  from animation_events import ensure_trace,bind_events,write_audit
  trace=ensure_trace(project);events=bind_events(plan,trace)
  output={'duration':timing['duration'],'sound_profile':profile,'shots':shots,'cues':events,
          'timing_method':'animation-state-per-output-frame','trace_sha256':trace['source_sha256']}
  (data/'cues.json').write_text(json.dumps(output,indent=2))
  write_audit(project,output,trace)
  print(f"ACTION_SOUND {len(shots)} shots / {len(events)} measured-frame Foley events / {timing['duration']:.2f}s",flush=True)
  return output
 if (project/'visual_profile.json').is_file():
  raise ValueError('Reference-cartoon production requires version 2 measured animation events; estimated Foley is disabled.')
 for index,event in enumerate(plan['events']):
  shot=lookup[event['shot']];duration=shot['end']-shot['start']
  begin=shot['start']+duration*event.get('at',0)
  if 'repeat_seconds' in event:
   interval=event['repeat_seconds'];begin=math.ceil(begin/interval)*interval
   stop=shot['start']+duration*event.get('until',1)
   positions=[begin+i*interval for i in range(max(0,math.ceil((stop-begin)/interval)))]
  else:positions=[begin]
  for variant,t in enumerate(positions):
   item={k:v for k,v in event.items() if k not in ('shot','at','repeat_seconds','until')}
   samples=item.pop('samples',None)
   if samples:item['sample']=samples[variant%len(samples)]
   item.update(t=round(t,5),shot=shot['id'],event_index=index)
   if 'span' in item:item['duration']=duration*item.pop('span')
   events.append(item)
 output={'duration':timing['duration'],'sound_profile':profile,'shots':shots,'cues':sorted(events,key=lambda e:e['t'])}
 (data/'cues.json').write_text(json.dumps(output,indent=2))
 (data/'shot_timing.json').write_text(json.dumps(shots,indent=2))
 print(f"ACTION_SOUND {len(shots)} shots / {len(events)} synchronized Foley events / {timing['duration']:.2f}s",flush=True)
 return output

if __name__=='__main__':
 import sys
 export(sys.argv[1])
