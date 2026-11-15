"""GPU Three.js capture through the same bridge, with verified output manifests."""
import argparse,collections,concurrent.futures,fcntl,hashlib,json,os,re,subprocess,time,threading
from pathlib import Path
from runtime_progress import emit_progress
from runtime_setup import setup
from runtime_memory import host_memory
from webgl_partition import partition,Progress,MAX_WEBGL_WORKERS
from webgl_graphics_environment import capture_environment

def digest(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def run(root,name,task,identifier,workers=2):
 root=Path(root).resolve()
 if not all(re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in (name,identifier)):raise ValueError('Invalid project/request ID.')
 project=root/'projects'/name
 lock=(project/'.runtime-job.lock').open('a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:lock.close();raise RuntimeError('This project has an active job.')
 work=root/'runs'/identifier/'video_engine';work.mkdir(parents=True,exist_ok=True)
 try:
  emit_progress(work,'preparing_webgl',project=name,request_id=identifier,task=task)
  tools=setup(root);selected=json.loads((root/'gpu-environment.json').read_text())
  env=capture_environment(os.environ,selected)
  backend=json.loads((project/'render_backend.json').read_text())
  env.update(CHROME=tools['chrome'],RENDER_GPU='1',REQUIRE_NVIDIA='1',FPS='30',QS=backend.get('capture_query','&res=1&aa=4&shadow=2048'))
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
   # Probe once per job, before launching browsers; all segments use one codec
   # and pixel format. Explicit NVENC requests fail rather than silently changing.
   encoder={'encoder':'browser-h264-software','pixel_format':'yuv420p','reason':'GPU composition with native browser encoding; no uncompressed HTTP transfer'} if backend.get('capture_transport')=='webcodecs' else json.loads(subprocess.check_output([tools['node'],str(project/'tools/capture_transport.mjs'),'probe',backend.get('video_encoder','auto')],cwd=project,env=env,text=True)) if (project/'tools/capture_transport.mjs').is_file() else {'encoder':'libx264','pixel_format':'yuv420p','reason':'legacy project capture'}
   (work/'encoder-status.json').write_text(json.dumps(encoder,indent=2));print('VIDEO_ENCODER '+json.dumps(encoder),flush=True)
   env.update(VIDEO_ENCODER=encoder['encoder'],VIDEO_PIXEL_FORMAT=encoder['pixel_format'],VIDEO_ENCODER_VERIFIED='1',CAPTURE_TRANSPORT=backend.get('capture_transport','auto'))
   output=work/'outputs'/(name+'-webgl.mp4');output.parent.mkdir(exist_ok=True)
   expected=json.loads((project/'data/lines.json').read_text())['duration'];total=round(expected*30)
   parts=partition(total,workers);progress=Progress(total,parts);processes={};cancel=threading.Event()
   def capture(index,bounds):
    target=output.with_name(f'worker-{index}.mp4');child_env=env.copy();child_env['VIDEO_ONLY']='1'
    proc=subprocess.Popen([tools['node'],str(script),'video',str(target),str(bounds[0]/30),str(bounds[1]/30)],cwd=project,env=child_env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    processes[index]=proc;progress.state(index,'running',proc.pid)
    recent=collections.deque(maxlen=25)
    with (work/f'webgl-worker-{index}.log').open('w',encoding='utf-8') as log:
     for line in proc.stdout:
      recent.append(line)
      log.write(line);log.flush()
      if line.startswith('RENDER_PROGRESS '):progress.update(index,json.loads(line.split(' ',1)[1]))
      elif line.startswith('RENDER_PHASE '):progress.phase(index,json.loads(line.split(' ',1)[1]))
      else:print(f'[webgl-{index}] '+line,end='',flush=True)
    code=proc.wait();progress.state(index,'complete' if code==0 else 'stopped' if cancel.is_set() else 'failed')
    if code:
     cancel.set();cause=next((line.strip() for line in recent if 'Error:' in line),f'exit code {code}')
     raise RuntimeError(f'WebGL worker {index}: {cause}; see webgl-worker-{index}.log.')
    return target
   def stop_peers():
    import psutil
    for proc in list(processes.values()):
     if proc.poll() is None:
      try:
       owned=psutil.Process(proc.pid);children=owned.children(recursive=True)
       for child in reversed(children):
        try:child.terminate()
        except psutil.Error:pass
       owned.terminate()
      except psutil.Error:pass
   with concurrent.futures.ThreadPoolExecutor(max_workers=len(parts)) as pool:
    futures=[pool.submit(capture,i,bounds) for i,bounds in enumerate(parts)];pending=set(futures)
    try:
     while pending:
      done,pending=concurrent.futures.wait(pending,timeout=3,return_when=concurrent.futures.FIRST_COMPLETED)
      for job in done:job.result()
      emit_progress(work,'rendering_webgl',**progress.snapshot())
    except BaseException:
     cancel.set();stop_peers();concurrent.futures.wait(futures);emit_progress(work,'failed',**progress.snapshot());raise
   segments=[f.result() for f in futures]
   from video_format import project_dimensions
   from webgl_finalize import finalize
   finalize(segments,project/'data/mix.wav',output,total,expected,project_dimensions(project),
            progress=lambda stage:emit_progress(work,stage,**progress.snapshot()))
   result['outputs']=[{'path':str(output),'sha256':digest(output),'bytes':output.stat().st_size,'kind':'video'}]
   result['video_encoder']=encoder;result['capture_transport']=env['CAPTURE_TRANSPORT']
  else:raise ValueError('WebGL currently supports build (functional validation) or render.')
  target=root/'results'/(identifier+'.json');target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(result,indent=2))
  emit_progress(work,'complete',active_workers=0,workers=[]);print('ENGINE_RESULT '+json.dumps(result),flush=True)
  return result
 except BaseException as error:emit_progress(work,'failed',error=str(error),active_workers=0);raise
 finally:lock.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--project',required=True);p.add_argument('--task',choices=['build','render'],default='render');p.add_argument('--request-id',required=True);p.add_argument('--workers',type=int,choices=range(1,MAX_WEBGL_WORKERS+1),default=2)
 a=p.parse_args();run(a.root,a.project,a.task,a.request_id,a.workers)
