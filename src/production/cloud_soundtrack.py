"""Mix a new soundtrack on Colab and stream-copy the saved verified pictures."""
import json
from pathlib import Path
from gpu_runtime import Client,digest
from render_reuse import signature
def soundtrack_inputs(project):
 p=Path(project).resolve();script=json.loads((p/'script.json').read_text());cues=json.loads((p/'data/cues.json').read_text())
 names=['script.json','action_plan.json','action_probe.json','data/narration.wav','data/lines.json','data/words.json','data/cues.json','data/animation-events.json',script['music']]
 names+=['audio/foley/'+name for name in sorted({event['sample'] for event in cues['cues']})]
 for name in names:
  path=(p/name).resolve()
  if not path.is_relative_to(p) or not path.is_file():raise ValueError('Missing/invalid soundtrack input: '+name)
 return names

def remux_remote(job,cfg,source,cache):
 from video_engine import save_stage,write,JOBS
 p=Path(job['project']);engine=Path(__file__).parent;client=Client();root=client.api('GET','/engine/capabilities')['root']
 modules=('foley_mix.py','longform_mix.py','music_mix.py','music_policy.json','sound_profile.py','sound_defaults.json','sound_materials.json','animation_events.py','render_reuse.py','trace_action_events.mjs','action_event_trace.mjs','webgl_finalize.py','video_format.py')
 save_stage(job,'uploading_soundtrack_revision')
 for name in modules:client.upload(engine/name,root+'/'+name)
 remote_project=root+'/projects/'+p.name;script=json.loads((p/'script.json').read_text())
 for name in soundtrack_inputs(p):client.upload(p/name,remote_project+'/'+name)
 remote_source=None
 try:
  prior=json.loads((JOBS/source.stem/'status.json').read_text());result=client.read_json(prior['runtime_result_path'])
  item=next(item for item in result['outputs'] if item['kind']=='video')
  if client.api('GET','/files/stat',params={'path':item['path']})['sha256']==digest(source):remote_source=item['path']
 except (OSError,KeyError,RuntimeError,StopIteration):pass
 if not remote_source:
  remote_source=root+'/audio-updates/'+job['id']+'/source.mp4';client.upload(source,remote_source)
 expected=json.loads((p/'data/lines.json').read_text())['duration'];result_path=root+'/results/'+job['id']+'.json'
 code=f'''from pathlib import Path
import sys,json,hashlib,fcntl,os
root=Path({root!r});sys.path.insert(0,str(root))
from foley_mix import mix
from webgl_finalize import finalize
from video_format import project_dimensions
from render_reuse import visual_signature
from runtime_progress import emit_progress
project=Path({remote_project!r});work=root/'runs'/{job['id']!r}/'video_engine'
lock=(project/'.runtime-job.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
context=dict(project={p.name!r},request_id={job['id']!r},task='soundtrack',active_workers=0,workers=[],rendered_new_frames=0)
try:
 tools=json.loads((root/'webgl-tools.json').read_text());os.environ['CHROME']=tools['chrome'];(root/'video_defaults.json').write_text(json.dumps(dict(node=tools['node'],chrome=tools['chrome'],ffmpeg_bin='/usr/bin')))
 if visual_signature(project)!={cache['visual_inputs_sha256']!r}:raise ValueError('Cloud scene/timing differs from the verified pictures; refusing soundtrack update')
 emit_progress(work,'mixing_soundtrack',**context);report=mix(project)
 output=work/'outputs'/({p.name!r}+'-music-revised.mp4')
 info,evidence=finalize([Path({remote_source!r})],project/'data/mix.wav',output,round({expected!r}*30),{expected!r},project_dimensions(project),progress=lambda stage:emit_progress(work,stage,**context))
 with output.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
 result=dict(sound_report=report,finalization=evidence,outputs=[dict(path=str(output),kind='video',sha256=sha)])
 Path({result_path!r}).write_text(json.dumps(result,indent=2));emit_progress(work,'complete',**context)
except BaseException as error:
 emit_progress(work,'failed',error=str(error),**context);raise
finally:lock.close()
'''
 remote=client.python(code,timeout=1800);job.update(colab_job_id=remote['job_id'],runtime_result_path=result_path,rendered_new_frames=0)
 write(job['status_file'],job);save_stage(job,'mixing_soundtrack_on_colab')
 def progress(value):job['progress']=value;write(job['status_file'],job)
 client.wait(remote['job_id'],job['log_file'],on_progress=progress);result=client.read_json(result_path)
 output=result['outputs'][0];client.download(output['path'],job['render_file'],on_progress=progress)
 if digest(job['render_file'])!=output['sha256']:raise ValueError('Soundtrack revision download hash mismatch')
 client.download(remote_project+'/data/mix.wav',p/'data/mix.wav')
 (p/'data/sound-report.json').write_text(json.dumps(result['sound_report'],indent=2))
 job.update(render_inputs_sha256=signature(p),cloud_soundtrack=True,finalization_evidence=result['finalization'])
