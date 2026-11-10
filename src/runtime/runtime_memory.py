"""Host RAM admission and telemetry; VRAM is a separate budget."""
import os
from pathlib import Path

GIB=1024**3

def host_memory():
 values={}
 try:
  for line in Path('/proc/meminfo').read_text().splitlines():
   name,rest=line.split(':',1);values[name]=int(rest.split()[0])*1024
  total=values['MemTotal'];available=values.get('MemAvailable',values.get('MemFree',0))
 except (OSError,ValueError,KeyError):return None
 # /proc/meminfo can describe the host when a process has a smaller cgroup limit.
 try:
  limit=int(Path('/sys/fs/cgroup/memory.max').read_text())
  current=int(Path('/sys/fs/cgroup/memory.current').read_text())
  if 0<limit<total:total=limit;available=min(available,max(0,limit-current))
 except (OSError,ValueError):pass
 return {'total_bytes':total,'available_bytes':available,'used_bytes':max(0,total-available),
         'total_gib':round(total/GIB,2),'available_gib':round(available/GIB,2),'used_gib':round((total-available)/GIB,2)}

def process_memory(pid):
 try:
  values={}
  for line in Path(f'/proc/{int(pid)}/status').read_text().splitlines():
   if line.startswith(('VmRSS:','VmHWM:')):
    key,rest=line.split(':',1);values[key]=int(rest.split()[0])*1024
  return values
 except (OSError,ValueError):return {}

def worker_budget(requested,memory=None):
 memory=host_memory() if memory is None else memory
 if not memory:return requested,'Host RAM could not be measured; requested worker count retained.'
 # Measured four-copy Snow failure on a 12.7 GiB VM. Leave 2 GiB for OS,
 # notebook, driver and transient allocations; reserve 3.5 GiB per scene copy.
 affordable=int(max(0,memory['available_bytes']-2*GIB)//(3.5*GIB))
 if affordable<1:raise RuntimeError(f"Insufficient host RAM: {memory['available_gib']} GiB available; one Blender scene needs an estimated 3.5 GiB plus a 2 GiB reserve. Stop other memory-heavy jobs before retrying.")
 selected=min(requested,max(1,affordable))
 reason=f"Host RAM admission: {memory['available_gib']} GiB available, 2 GiB reserve, 3.5 GiB estimated per Blender worker; {requested} requested, {selected} admitted."
 return selected,reason
