"""Small notebook dashboard. Job data is escaped; credentials are never included."""
import html,time

def duration(value):
 if value is None:return 'estimating'
 seconds=max(0,int(value));minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
 return f'{hours}h {minutes:02d}m {seconds:02d}s' if hours else f'{minutes}m {seconds:02d}s'

def render_dashboard(jobs):
 escape=lambda value:html.escape(str(value))
 cards=[]
 for job in reversed(jobs[-8:]):
  p=job.get('progress') or {};status=job.get('status','unknown')
  if not p and status!='running':continue
  stage=p.get('stage','starting job') if status=='running' else status
  workers=p.get('workers',[]);count=p.get('completed_frames',0);total=p.get('total_frames',0)
  percent=max(0,min(100,float(p.get('percent',0))))
  age=max(0,time.time()-p['updated']) if p.get('updated') else None
  rows=''.join('<tr>'+''.join(f'<td style="padding:4px 12px">{escape(v)}</td>' for v in
    (w['id'],w.get('status'),w.get('phase'),w.get('frame') or '—',f"{w.get('completed',0)}/{w.get('total',0)}",w.get('pid') or '—'))+'</tr>' for w in workers)
  detail=f'{count}/{total} frames · {percent:.1f}% · {p.get("active_workers",0)}/{p.get("requested_workers",0)} active workers' if total else 'Preparing tools / scene; frame rendering has not started.'
  timing=f'Elapsed {duration(p.get("elapsed_seconds"))} · {p.get("frames_per_second") or "estimating"} frames/s · Remaining render time {duration(p.get("eta_seconds"))}'
  if stage in ('encoding_mp4','complete','succeeded'):timing='Frames finished. '+('Encoding and checking the MP4.' if stage=='encoding_mp4' else 'Job finished; output is available through the bridge.')
  stale=f' · Last render update {int(age)}s ago' if age is not None and age>15 and status=='running' else ''
  memory=p.get('host_memory') or {}
  memory_text=f"System RAM: {memory.get('used_gib')} / {memory.get('total_gib')} GiB used; {memory.get('available_gib')} GiB available." if memory else 'System RAM telemetry pending.'
  error=p.get('error')
  if error:timing='Failure: '+str(error)
  timing+=' '+memory_text
  if p.get('worker_budget_reason'):timing+=' '+p['worker_budget_reason']
  cards.append(f'<div style="padding:14px;border:1px solid #888;border-radius:8px;margin:10px 0"><b>{escape(p.get("project",job["job_id"][:12]))} — {escape(stage)}</b><p>{escape(detail)}</p><progress value="{percent}" max="100" style="width:100%"></progress><p>{escape(timing+stale)}</p><table><tr><th>Worker</th><th>Status</th><th>Phase</th><th>Frame</th><th>Done</th><th>PID</th></tr>{rows}</table></div>')
 return '<div><h3>Live runtime jobs</h3><small>Refreshes every 3 seconds. ETA is measured after frames finish; it excludes final encoding/download.</small>'+(''.join(cards) or '<p>Ready — waiting for a job.</p>')+'</div>'
