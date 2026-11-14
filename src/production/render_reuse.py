"""Reuse an unchanged, previously verified WebGL export without another GPU job."""
import hashlib,json,shutil
from pathlib import Path
ENGINE=Path(__file__).resolve().parent
def path_order(path,project):
 # Preserve the original Windows ordering on every runtime. Native Path sorts
 # differently on Linux for mixed-case names, despite identical file bytes.
 return tuple(part.casefold() for part in path.relative_to(project).parts)

def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def declared_visual_inputs(project):
 project=Path(project).resolve();script=json.loads((project/'script.json').read_text());paths=[]
 for name in script.get('visual_inputs',[]):
  path=(project/name).resolve()
  if not path.is_relative_to(project) or not path.is_file():raise ValueError('Invalid declared visual input: '+str(name))
  paths.append(path)
 return paths

def signature(project):
 project=Path(project).resolve();h=hashlib.sha256();paths=[]
 for folder in ('src','fonts','assets','vendor','audio','tools','voices'):
  paths.extend(p for p in (project/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 for name in ('script.json','narrator.json','action_plan.json','action_probe.json','prepare_cues.py','index.html','data/narration.wav','data/lines.json','data/words.json'):
  if (project/name).is_file():paths.append(project/name)
 paths.extend(declared_visual_inputs(project))
 for p in sorted(paths,key=lambda p:path_order(p,project)):h.update((p.relative_to(project).as_posix()+'\0'+digest(p)+'\n').encode())
 backend=json.loads((project/'render_backend.json').read_text())
 for key in ('workers','job_timeout_seconds','force_render'):backend.pop(key,None)
 h.update(json.dumps(backend,sort_keys=True).encode())
 for name in ('foley_mix.py','longform_mix.py','music_mix.py','music_policy.json','action_sound.py','animation_events.py','trace_action_events.mjs','action_event_trace.mjs','video_defaults.json','sound_profile.py','sound_defaults.json','sound_materials.json'):
  if (ENGINE/name).is_file():h.update((name+digest(ENGINE/name)).encode())
 return h.hexdigest()

def visual_signature(project):
 project=Path(project).resolve();h=hashlib.sha256();paths=[]
 for folder in ('src','fonts','assets','vendor'):
  paths.extend(p for p in (project/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 for name in ('index.html','data/lines.json','data/words.json','data/shot_timing.json','tools/cloud_capture.mjs','tools/capture_transport.mjs'):
  if (project/name).is_file():paths.append(project/name)
 paths.extend(declared_visual_inputs(project))
 for p in sorted(paths,key=lambda p:path_order(p,project)):h.update((p.relative_to(project).as_posix()+'\0'+digest(p)+'\n').encode())
 script=json.loads((project/'script.json').read_text())
 for key in ('music','sound_profile','sound_design'):script.pop(key,None)
 h.update(json.dumps(script,sort_keys=True).encode())
 plan=project/'action_plan.json'
 if plan.is_file():h.update(json.dumps(json.loads(plan.read_text())['shots'],sort_keys=True).encode())
 backend=json.loads((project/'render_backend.json').read_text())
 for key in ('workers','job_timeout_seconds','force_render','timing_target_seconds','preferred_target_seconds','audio_execution'):backend.pop(key,None)
 h.update(json.dumps(backend,sort_keys=True).encode());return h.hexdigest()

def restore(job):
 from video_engine import save_stage
 p=Path(job['project']);backend=json.loads((p/'render_backend.json').read_text());key=signature(p);job['render_inputs_sha256']=key
 if backend.get('force_render'):return False
 try:
  entry=json.loads((p/'data/render-cache.json').read_text());source=Path(entry['video_path']).resolve()
  if entry['inputs_sha256']!=key or not entry.get('verified') or not source.is_relative_to((p/'renders').resolve()) or not source.is_file() or digest(source)!=entry['video_sha256']:return False
 except (OSError,ValueError,KeyError):return False
 save_stage(job,'reusing_verified_render');target=Path(job['render_file']);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);job['cache_hit']=True
 return True

def remember(job):
 from video_engine import write
 if job.get('state')!='complete' or not job.get('render_inputs_sha256'):return
 project=Path(job['project']);source=Path(job['render_file']).resolve()
 if signature(project)!=job['render_inputs_sha256'] or not source.is_relative_to((project/'renders').resolve()):return
 write(project/'data/render-cache.json',{'inputs_sha256':job['render_inputs_sha256'],'visual_inputs_sha256':visual_signature(project),'video_path':str(source),'video_sha256':digest(source),'verified':True})
