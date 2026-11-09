"""Bounded two-worker throughput trial, then render remaining frames automatically."""
import concurrent.futures,json,os,statistics,struct,threading,time
from pathlib import Path
from gpu_process_monitor import monitored_run

def valid_png(path):
 try:
  with path.open('rb') as stream:
   header=stream.read(24);stream.seek(-12,2);end=stream.read(12)
  return header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(1080,1920) and end==b'\x00\x00\x00\x00IEND\xaeB`\x82'
 except (OSError,ValueError,struct.error):return False

def measured_baseline(root):
 path=Path(root)/'renderer.log'
 if not path.is_file():return None
 timings=[]
 for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
  if not line.startswith('FRAME_TIMING '):continue
  try:
   item=json.loads(line.removeprefix('FRAME_TIMING '));seconds=float(item['wall_interval_seconds'])
   if item['frame']>1 and 0<seconds<3600:timings.append(seconds)
  except (ValueError,KeyError,TypeError):pass
 return statistics.median(timings[-9:]) if len(timings)>=2 else None

def render_auto_parallel(command,root,frames,first,last,env=None,baseline_seconds=None,heartbeat_seconds=15):
 root=Path(root);frames=Path(frames)
 work=root/('parallel-'+str(time.time_ns()));work.mkdir(parents=True)
 status=root/'process-status.json';report_path=root/'parallel-status.json'
 report={'state':'running','max_workers':2,'same_render_settings':True,'work_directory':str(work)}
 def save():
  temporary=report_path.with_suffix('.tmp');temporary.write_text(json.dumps(report,indent=2));temporary.replace(report_path)
 def missing():return [f for f in range(first,last+1) if not valid_png(frames/f'frame_{f:04d}.png')]
 def ranges(items,count):
  split=(len(items)+count-1)//count
  return [(part[0],part[-1]) for offset in range(0,len(items),split) if (part:=items[offset:offset+split])]
 def pool(assignments,tag):
  cancelled=threading.Event()
  def worker(index,bounds):
   label=f'{tag}-{index}';directory=work/label
   args=command+['--frame-start',str(bounds[0]),'--frame-end',str(bounds[1]),'--worker-id',label]
   try:return monitored_run(args,directory,heartbeat_seconds,env,cancel_event=cancelled,label=label)
   except BaseException:
    cancelled.set();raise
  started=time.monotonic()
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
   jobs=[executor.submit(worker,i,bounds) for i,bounds in enumerate(assignments)]
   for job in concurrent.futures.as_completed(jobs):job.result()
  return time.monotonic()-started
 def timed_values(directory):
  values=[]
  for line in (directory/'blender-native.log').read_text(encoding='utf-8',errors='replace').splitlines():
   if line.startswith('FRAME_TIMING '):
    try:values.append(json.loads(line.removeprefix('FRAME_TIMING '))['wall_interval_seconds'])
    except (ValueError,KeyError):pass
  return values
 status.write_text(json.dumps({'state':'running','pid':os.getpid(),'kind':'parallel_controller','started':time.time()}))
 save()
 try:
  todo=missing()
  if len(todo)<4:
   if todo:pool(ranges(todo,1),'finish')
   report.update(state='complete',selected_workers=1,reason='Fewer than four frames remain.');save();return report
  baseline=baseline_seconds
  if baseline is None:
   print('BUILD_STAGE measuring serial throughput on four remaining frames; completed frames are retained.',flush=True)
   pool([(todo[0],todo[3])],'serial')
   times=timed_values(work/'serial-0')
   baseline=statistics.median(times[1:]) if len(times)>1 else None
   todo=missing()
  if baseline is None or len(todo)<4:
   if todo:pool(ranges(todo,1),'finish')
   report.update(state='complete',selected_workers=1,reason='Insufficient timing data for a parallel decision.');save();return report
  trial=todo[:4];report.update(baseline_seconds_per_frame=baseline,trial_frames=trial)
  print('BUILD_STAGE testing two workers on four unfinished frames; these frames count toward the final video.',flush=True)
  try:
   elapsed=pool(ranges(trial,2),'trial')
   if not all(valid_png(frames/f'frame_{f:04d}.png') for f in trial):raise RuntimeError('A parallel worker exited without producing its assigned frames.')
   ratio=baseline*len(trial)/elapsed
   report.update(trial_wall_seconds=round(elapsed,3),observed_throughput_ratio=round(ratio,3))
   chosen=2 if ratio>=1.15 else 1
   report['reason']='Two workers improve measured aggregate throughput by at least 15%.' if chosen==2 else 'Two workers do not improve aggregate throughput by at least 15%.'
  except Exception as error:
   chosen=1;report.update(trial_error=str(error),reason='Parallel trial failed; retain valid frames and continue with one worker.')
  report.update(selected_workers=chosen);save()
  print('BUILD_STAGE parallel selection '+json.dumps(report),flush=True)
  todo=missing()
  if todo:pool(ranges(todo,chosen),'render')
  if missing():raise RuntimeError('Missing or incomplete frames remain after the render workers finished.')
  report.update(state='complete',completed_frames=last-first+1);save();return report
 except BaseException as error:
  report.update(state='failed',error=str(error));save();raise
 finally:
  status.write_text(json.dumps({'state':report['state'],'pid':os.getpid(),'kind':'parallel_controller','updated':time.time()}))
