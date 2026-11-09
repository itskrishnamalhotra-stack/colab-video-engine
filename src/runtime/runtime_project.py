"""Build, inspect a few frames, or render any uploaded Blender project on the GPU."""
import argparse,fcntl,hashlib,json,os,re,shutil,subprocess,sys,time,traceback
from pathlib import Path
from run_colab_render import main as render_video
from gpu_process_monitor import monitored_run

def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def run_project(root,name,task,request_id,first=1,last=None,renderer='eevee',workers=2):
 root=Path(root).resolve()
 if not re.fullmatch(r'[A-Za-z0-9_-]+',name) or not re.fullmatch(r'[A-Za-z0-9_-]+',request_id):raise ValueError('Invalid project/request ID.')
 project=root/'projects'/name
 if not project.is_dir():raise FileNotFoundError('Upload the project before starting its job.')
 lock=(project/'.runtime-job.lock').open('a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise RuntimeError('This project already has an active runtime job.')
 try:
  caps=json.loads((root/'runtime-capabilities.json').read_text());exe=caps['blender']
  env=os.environ.copy();gpu_env=root/'gpu-environment.json'
  if gpu_env.is_file():env.update(json.loads(gpu_env.read_text()))
  work=root/'runs'/request_id/'video_engine';work.mkdir(parents=True,exist_ok=True)
  package_marker=project/'.source-package.sha256';prepared_marker=project/'.prepared-package.sha256'
  changed=package_marker.read_text() if package_marker.is_file() else 'manual-'+str(time.time_ns())
  if task=='build' or not (project/'prepared-scene.blend').is_file() or not prepared_marker.is_file() or prepared_marker.read_text()!=changed:
   print('RUNTIME_STAGE building_uploaded_scene',flush=True)
   # These are native CPU preparation steps on the cloud machine, not the laptop.
   monitored_run([exe,'--background','--factory-startup','--enable-autoexec','--python-exit-code','1','--python',str(project/'build_scene.py'),
                  '--','--project',str(project),'--frames',str(work/'build-frames'),'--prepare-only'],work/'build',env=env)
   if not (project/'prepared-scene.blend').is_file():raise RuntimeError('The source scene did not produce prepared-scene.blend.')
   prepared_marker.write_text(changed)
  result={'project':name,'task':task,'request_id':request_id,'outputs':[]}
  if task=='build':result['scene']=str(project/'prepared-scene.blend')
  elif task=='probe':
   last=first if last is None else last
   metadata=json.loads((project/'prepared-scene.json').read_text())
   if not 1<=first<=last<=metadata['frames'] or last-first>=32:raise ValueError('A probe may select at most 32 consecutive frames within the scene.')
   frames=work/'probe-frames'
   monitored_run([exe,'--background','--factory-startup','--enable-autoexec','--python-exit-code','1','--gpu-backend','opengl','--python',str(root/'render_prepared.py'),
                  '--','--project',str(project),'--frames',str(frames),'--renderer',renderer,'--frame-start',str(first),'--frame-end',str(last),'--worker-id','probe'],work/'probe',env=env)
   result['outputs']=[{'path':str(path),'sha256':digest(path),'bytes':path.stat().st_size,'kind':'image'} for path in sorted(frames.glob('frame_*.png'))]
  elif task=='render':
   (work/'projects').mkdir(exist_ok=True);(work/'projects'/name).symlink_to(project,target_is_directory=True)
   (work/'tools').symlink_to(root/'tools',target_is_directory=True)
   for source in root.glob('*.py'):
    (work/source.name).symlink_to(source)
   scene=project/'prepared-scene.blend';metadata=json.loads((project/'prepared-scene.json').read_text())
   manifest={'project':name,'files':[],'prepared_scene':{'url':scene.as_uri(),'api_url':scene.as_uri(),'sha256':digest(scene),'source_metadata':metadata}}
   (work/'manifest.json').write_text(json.dumps(manifest))
   output=render_video(work,renderer=renderer,parallel_workers=workers if renderer=='eevee' else None)
   result['outputs']=[{'path':str(output),'sha256':digest(output),'bytes':output.stat().st_size,'kind':'video'}]
  else:raise ValueError('Task must be build, probe or render.')
  target=root/'results'/(request_id+'.json');target.parent.mkdir(exist_ok=True)
  target.write_text(json.dumps(result,indent=2));print('ENGINE_RESULT',json.dumps(result),flush=True)
  return result
 finally:lock.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default='/content/video_engine');p.add_argument('--project',required=True);p.add_argument('--task',choices=['build','probe','render'],default='render')
 p.add_argument('--request-id',required=True);p.add_argument('--first',type=int,default=1);p.add_argument('--last',type=int);p.add_argument('--renderer',choices=['cycles','eevee'],default='eevee');p.add_argument('--workers',type=int,choices=[1,2],default=2)
 a=p.parse_args();run_project(a.root,a.project,a.task,a.request_id,a.first,a.last,a.renderer,a.workers)
