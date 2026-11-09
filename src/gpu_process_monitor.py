"""Flush native logs and record child exit/memory counters while Python owns the wait."""
import collections,json,os,subprocess,time
from pathlib import Path

def memory_state():
 result={}
 for name in ['memory.current','memory.peak','memory.max','memory.events']:
  path=Path('/sys/fs/cgroup')/name
  if path.is_file():
   text=path.read_text().strip()
   result[name]=dict(line.split() for line in text.splitlines()) if name=='memory.events' else text
 return result

def monitored_run(command,root,heartbeat_seconds=15):
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 state_path=root/'process-status.json';log=root/'blender-native.log'
 before=memory_state();started=time.time()
 def write(state):
  temp=state_path.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2));temp.replace(state_path)
 with log.open('w',encoding='utf-8',buffering=1) as output:
  proc=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT)
  state={'state':'running','pid':proc.pid,'started':started,'memory_before':before,'native_log':str(log)}
  write(state)
  offset=0
  while True:
   with log.open('rb') as reader:
    reader.seek(offset)
    for line in reader:
     text=line.decode('utf-8',errors='replace').rstrip()
     if text.startswith(('BUILD_STAGE','FRAME_PROGRESS','BLENDER_FRAMES_COMPLETE')):print(text,flush=True)
    offset=reader.tell()
   code=proc.poll();state.update(updated=time.time(),elapsed_seconds=round(time.time()-started,1),memory=memory_state())
   if code is not None:
    state.update(state='complete' if code==0 else 'failed',returncode=code);write(state);break
   write(state)
   print('JOB_HEARTBEAT',json.dumps({'child_pid':proc.pid,'alive':True,'elapsed_seconds':state['elapsed_seconds'],'memory':state['memory']}),flush=True)
   try:proc.wait(timeout=heartbeat_seconds)
   except subprocess.TimeoutExpired:pass
 if code:
  with log.open(encoding='utf-8',errors='replace') as f:recent=''.join(collections.deque(f,maxlen=80))
  print('NATIVE_FAILURE_TAIL\n'+recent,flush=True)
  raise RuntimeError(f'Blender exited with code {code}. See blender-native.log and process-status.json; a signal alone does not prove an OOM.')
 return state
