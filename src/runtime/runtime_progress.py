"""Thread-safe frame totals and measured throughput for persistent render workers."""
import collections,json,os,threading,time
from pathlib import Path
from frame_cache import valid_png
from runtime_memory import host_memory

class RenderProgress:
 def __init__(self,root,frames,first,last,clock=time.monotonic):
  self.root=Path(root);self.frames=Path(frames);self.first=first;self.last=last;self.clock=clock
  self.started=clock();self.lock=threading.RLock();self.workers={};self.history=collections.deque();self.gpu=None
  self.completed={f for f in range(first,last+1) if valid_png(self.frames/f'frame_{f:04d}.png')}
  self.cached=len(self.completed)
  context=self.root/'progress.json'
  try:self.context=json.loads(context.read_text())
  except (OSError,ValueError):self.context={}
 def register(self,label,bounds):
  with self.lock:self.workers[label]={'id':label,'first':bounds[0],'last':bounds[1],'pid':None,'status':'queued','phase':'Waiting to start','frame':None}
 def event(self,label,event):
  with self.lock:
   worker=self.workers[label]
   if event['event']=='state':
    state=event['state'];worker.update(pid=state.get('pid'),status=state['state'])
    if state.get('gpu'):self.gpu=state['gpu']
    if state.get('process_memory'):worker['memory']=state['process_memory']
    if state['state'] in ('complete','failed'):worker['phase']='Finished' if state['state']=='complete' else 'Failed'
   else:
    line=event['line']
    if line.startswith('FRAME_STARTED '):
     try:worker.update(frame=int(line.split()[1]),phase='Preparing / rendering frame')
     except (ValueError,IndexError):pass
    elif line.startswith('BUILD_STAGE packed animation'):worker['phase']='Loading scene'
    elif line.startswith('FRAME_PROGRESS '):
     try:frame=int(line.split()[1].split('/')[0])
     except (ValueError,IndexError):return
     if worker['first']<=frame<=worker['last'] and frame not in self.completed and valid_png(self.frames/f'frame_{frame:04d}.png'):
      self.completed.add(frame);self.history.append((self.clock(),len(self.completed)))
 def snapshot(self,stage='rendering'):
  with self.lock:
   now=self.clock();total=self.last-self.first+1;count=len(self.completed)
   while len(self.history)>2 and self.history[1][0]<now-60:self.history.popleft()
   fps=None;eta=None
   if len(self.history)>=2:
    elapsed=self.history[-1][0]-self.history[0][0];delta=self.history[-1][1]-self.history[0][1]
    if elapsed>=10 and delta>=2:fps=delta/elapsed;eta=(total-count)/fps
   if count==total:eta=0
   workers=[]
   for worker in self.workers.values():
    item=worker.copy();item['completed']=sum(worker['first']<=f<=worker['last'] for f in self.completed)
    item['total']=worker['last']-worker['first']+1;workers.append(item)
   return {**{k:self.context[k] for k in ('project','request_id','task','requested_worker_limit','admitted_workers','worker_budget_reason') if k in self.context},
    'stage':stage,'completed_frames':count,'total_frames':total,'percent':round(100*count/total,1),
    'cached_frames':self.cached,'active_workers':sum(w['status']=='running' for w in workers),'requested_workers':len(workers),
    'workers':workers,'elapsed_seconds':round(now-self.started,1),'frames_per_second':round(fps,3) if fps else None,
    'eta_seconds':round(eta) if eta is not None else None,'host_memory':host_memory(),'gpu':self.gpu,'updated':time.time()}
 def publish(self,stage='rendering'):
  result=self.snapshot(stage);target=self.root/'progress.json';temporary=target.with_suffix('.tmp')
  temporary.write_text(json.dumps(result,indent=2));temporary.replace(target)
  print('RENDER_PROGRESS '+json.dumps(result,separators=(',',':')),flush=True)
  return result

def emit_progress(root,stage,**values):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);target=root/'progress.json'
 try:current=json.loads(target.read_text())
 except (OSError,ValueError):current={}
 current.update(stage=stage,updated=time.time(),**values)
 temporary=target.with_suffix('.tmp');temporary.write_text(json.dumps(current,indent=2));temporary.replace(target)
 print('ENGINE_PROGRESS '+json.dumps(current,separators=(',',':')),flush=True)
 return current
