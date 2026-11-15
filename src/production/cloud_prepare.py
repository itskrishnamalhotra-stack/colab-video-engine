"""Prepare measured action sound and the soundtrack on the connected runtime."""
import json,hashlib
from pathlib import Path
from gpu_runtime import Client,project_bundle,digest

def preparation_key(project):
 from render_reuse import signature
 engine=Path(__file__).parent
 return hashlib.sha256((signature(project)+digest(engine/'cloud_prepare.py')+digest(engine/'story_score.py')).encode()).hexdigest()

def prepared(project):
 p=Path(project)
 try:
  receipt=json.loads((p/'data/cloud-sound-prepared.json').read_text())
  if receipt['inputs_sha256']!=preparation_key(p) or receipt['mix_sha256']!=digest(p/'data/mix.wav') or receipt['report_sha256']!=digest(p/'data/sound-report.json'):return None
  from animation_events import verify_cues
  verify_cues(p,json.loads((p/'data/cues.json').read_text()))
  return receipt
 except (OSError,ValueError,KeyError):return None

def prepare(job,cfg):
 from video_engine import save_stage,write
 p=Path(job['project']);engine=Path(__file__).parent
 from install_foley import install
 install(p)
 cached=prepared(p)
 if cached:
  save_stage(job,'reusing_verified_cloud_soundtrack');return cached
 client=Client();root=client.api('GET','/engine/capabilities')['root']
 archive,_=project_bundle(p);remote=root+'/projects/'+p.name;bundle=root+'/uploads/'+job['id']+'-sound.zip'
 save_stage(job,'uploading_action_sound_project');client.upload(archive,bundle)
 modules=('action_sound.py','animation_events.py','trace_action_events.mjs','action_event_trace.mjs','foley_mix.py','longform_mix.py','music_mix.py','music_policy.json','sound_profile.py','sound_defaults.json','sound_materials.json','render_reuse.py','story_score.py')
 for name in modules:client.upload(engine/name,root+'/'+name)
 client.upload(p/'data/narration.wav',remote+'/data/narration.wav')
 plan=json.loads((p/'action_plan.json').read_text());samples={name for e in plan['events'] for name in e.get('samples',[e.get('sample')]) if name}
 for name in sorted(samples):client.upload(p/'audio/foley'/name,remote+'/audio/foley/'+name)
 result_path=root+'/results/'+job['id']+'-sound.json'
 code=f'''from pathlib import Path
import sys,os,json,zipfile,hashlib,fcntl
root=Path({root!r});sys.path.insert(0,str(root));project=Path({remote!r});project.mkdir(parents=True,exist_ok=True)
lock=(project/'.runtime-job.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
try:
 with zipfile.ZipFile({bundle!r}) as archive:
  if any(not (root/name).resolve().is_relative_to(project.resolve()) for name in archive.namelist()):raise ValueError('Unsafe action package')
  archive.extractall(root)
 tools=json.loads((root/'webgl-tools.json').read_text());os.environ['CHROME']=tools['chrome']
 (root/'video_defaults.json').write_text(json.dumps(dict(node=tools['node'],chrome=tools['chrome'],ffmpeg_bin='/usr/bin')))
 from story_score import author
 from action_sound import export
 from foley_mix import mix
 script=json.loads((project/'script.json').read_text())
 if script.get('original_score'):author(project,60,semitones=-2,motif_period=4.8)
 print('PREPARE_STAGE measuring_action_contacts',flush=True);export(project)
 print('PREPARE_STAGE mixing_soundtrack',flush=True);report=mix(project)
 Path({result_path!r}).write_text(json.dumps(dict(duration=report['duration'],events=report['sample_events'],mix_sha256=report['mix_sha256'])))
 print('PREPARE_READY '+json.dumps(dict(duration=report['duration'],events=report['sample_events'])),flush=True)
finally:lock.close()
'''
 remote_job=client.python(code,timeout=3600);job['colab_prepare_job_id']=remote_job['job_id'];write(job['status_file'],job);save_stage(job,'preparing_action_sound_on_colab')
 client.wait(remote_job['job_id'],job['log_file'])
 result=client.read_json(result_path)
 names=['data/mix.wav','data/sound-report.json','data/shot_timing.json','data/cues.json','data/animation-events.json','data/sound-sync-audit.md']
 if json.loads((p/'script.json').read_text()).get('original_score'):names.append('audio/music/suspense-phone-v2.wav')
 for name in names:client.download(remote+'/'+name,p/name)
 if digest(p/'data/mix.wav')!=result['mix_sha256']:raise ValueError('Cloud sound master differs from prepared result')
 result.update(inputs_sha256=preparation_key(p),report_sha256=digest(p/'data/sound-report.json'))
 (p/'data/cloud-sound-prepared.json').write_text(json.dumps(result,indent=2))
 return result
