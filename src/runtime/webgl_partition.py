"""Exact frame ownership and aggregate progress for persistent browser workers."""
import threading,time
from runtime_memory import host_memory
MAX_WEBGL_WORKERS=8

def partition(total,workers):
 if total<1 or workers not in range(1,MAX_WEBGL_WORKERS+1):raise ValueError(f'WebGL uses one to {MAX_WEBGL_WORKERS} workers and a positive frame count.')
 workers=min(total,workers);size,extra=divmod(total,workers);start=0;parts=[]
 for index in range(workers):
  end=start+size+(index<extra);parts.append((start,end));start=end
 return parts

class Progress:
 def __init__(self,total,parts,clock=time.monotonic):
  self.total=total;self.clock=clock;self.started=clock();self.lock=threading.RLock()
  self.workers=[{'id':f'webgl-{i}','first':a+1,'last':b,'completed':0,'total':b-a,'status':'queued','phase':'Loading browser and scene','pid':None} for i,(a,b) in enumerate(parts)]
 def state(self,index,status,pid=None):
  with self.lock:
   self.workers[index]['status']=status
   if pid:self.workers[index]['pid']=pid
   if status=='complete':self.workers[index]['phase']='Frames encoded'
   elif status in ('failed','stopped'):self.workers[index]['phase']='Stopped'
 def update(self,index,item):
  with self.lock:
   worker=self.workers[index];worker['completed']=min(worker['total'],max(worker['completed'],int(item['completed_frames'])))
   worker['frame']=worker['first']+worker['completed']-1;worker['phase']='GPU WebGL capture'
 def phase(self,index,item):
  with self.lock:
   worker=self.workers[index];worker['frame']=worker['first']+int(item['frame'])-1
   worker['phase']=item.get('phase','Rendering / GPU readback');worker['frame_started']=self.clock()
 def snapshot(self):
  with self.lock:
   completed=sum(w['completed'] for w in self.workers);elapsed=self.clock()-self.started
   rate=completed/elapsed if elapsed>=5 and completed>=20 else None
   rows=[]
   for worker in self.workers:
    row=worker.copy()
    if row['status']=='running' and row.get('frame_started') is not None:row['phase']+=f" ({self.clock()-row['frame_started']:.1f}s)"
    rows.append(row)
   failed=any(w['status'] in ('failed','stopped') for w in self.workers)
   return {'completed_frames':completed,'total_frames':self.total,'percent':round(completed/self.total*100,1),
    'active_workers':sum(w['status']=='running' for w in self.workers),'requested_workers':len(self.workers),'workers':rows,
    'elapsed_seconds':round(elapsed,1),'frames_per_second':round(rate,2) if rate else None,'eta_seconds':None if failed else round((self.total-completed)/rate) if rate else None,'host_memory':host_memory()}
