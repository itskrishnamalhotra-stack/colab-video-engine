"""GPU Three.js capture through the same bridge, with verified output manifests."""
import argparse,fcntl,hashlib,json,os,re,subprocess,time
from pathlib import Path
from runtime_progress import emit_progress
from runtime_webgl_setup import setup
from runtime_memory import host_memory

def digest(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def run(root,name,task,identifier):
 root=Path(root).resolve()
 if not all(re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in (name,identifier)):raise ValueError('Invalid project/request ID.')
 project=root/'projects'/name
 lock=(project/'.runtime-job.lock').open('a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:lock.close();raise RuntimeError('This project has an active job.')
 work=root/'runs'/identifier/'video_engine';work.mkdir(parents=True,exist_ok=True)
 try:
  emit_progress(work,'preparing_webgl',project=name,request_id=identifier,task=task)
  tools=setup(root);env=os.environ.copy()
  if (root/'gpu-environment.json').is_file():env.update(json.loads((root/'gpu-environment.json').read_text()))
  env.update(CHROME=tools['chrome'],RENDER_GPU='1',REQUIRE_NVIDIA='1',FPS='30',QS='&res=1&aa=0&shadow=1024')
  script=project/'tools/cloud_capture.mjs'
  def command(mode,*args):
   proc=subprocess.Popen([tools['node'],str(script),mode,*map(str,args)],cwd=project,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
   for line in proc.stdout:
    if line.startswith('RENDER_PROGRESS '):
     values=json.loads(line.split(' ',1)[1]);stage=values.pop('stage');values.pop('updated',None);emit_progress(work,stage,**values,request_id=identifier,task=task,host_memory=host_memory())
    else:print(line,end='',flush=True)
   code=proc.wait()
   if code:raise RuntimeError(f'WebGL {mode} exited with code {code}; see the preceding browser/encoder error.')
  result={'project':name,'task':task,'request_id':identifier,'outputs':[]}
  if task=='build':
   command('validate')
  elif task=='render':
   output=work/'outputs'/(name+'-webgl.mp4');output.parent.mkdir(exist_ok=True)
   command('video',output)
   emit_progress(work,'checking_mp4',active_workers=0,workers=[])
   raw=subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)],text=True)
   info=json.loads(raw);video=next(s for s in info['streams'] if s['codec_type']=='video')
   expected=json.loads((project/'data/lines.json').read_text())['duration']
   if (video['width'],video['height'])!=(1080,1920) or not any(s['codec_type']=='audio' for s in info['streams']):raise ValueError('Output needs full-resolution video and narration audio.')
   if abs(float(info['format']['duration'])-expected)>.25:raise ValueError('Incorrect rendered duration.')
   output.with_suffix('.verification.json').write_text(raw)
   result['outputs']=[{'path':str(output),'sha256':digest(output),'bytes':output.stat().st_size,'kind':'video'}]
  else:raise ValueError('WebGL currently supports build (functional validation) or render.')
  target=root/'results'/(identifier+'.json');target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(result,indent=2))
  emit_progress(work,'complete',active_workers=0,workers=[]);print('ENGINE_RESULT '+json.dumps(result),flush=True)
  return result
 except BaseException as error:emit_progress(work,'failed',error=str(error),active_workers=0);raise
 finally:lock.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--project',required=True);p.add_argument('--task',choices=['build','render'],default='render');p.add_argument('--request-id',required=True)
 a=p.parse_args();run(a.root,a.project,a.task,a.request_id)
