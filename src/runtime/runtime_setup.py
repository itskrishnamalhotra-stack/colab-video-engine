"""Cache the supported WebGL toolchain once; no scene or character installation."""
import json,subprocess
from pathlib import Path
from runtime_webgl_setup import setup as webgl_setup
from webgl_partition import MAX_WEBGL_WORKERS

def setup(root):
 root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
 print('RUNTIME_STAGE preparing_webgl_tools',flush=True)
 tools=webgl_setup(root)
 gpu=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],capture_output=True,text=True,timeout=15)
 if gpu.returncode:raise RuntimeError('An NVIDIA GPU runtime is required for rendering.')
 for name in ('projects','results'):(root/name).mkdir(exist_ok=True)
 capabilities={**tools,'root':str(root),'projects':str(root/'projects'),'gpu':gpu.stdout.strip(),
  'render_backend':'webgl','character_style':'permanent illustrated cartoon family',
  'tools':['python','shell','file_transfer','build_scene','probe_frames','render_video'],
  'max_render_workers':MAX_WEBGL_WORKERS,'default_render_workers':1,'webgl_max_render_workers':MAX_WEBGL_WORKERS,
  'webgl_recommended_native_workers':1,'progress_protocol':1,'supported_video_formats':['portrait','landscape'],
  'saved_video_finalization':True,'graphics_verification':'NVIDIA renderer is enforced when a capture job starts'}
 (root/'runtime-capabilities.json').write_text(json.dumps(capabilities,indent=2))
 print('RUNTIME_READY',json.dumps(capabilities),flush=True);return capabilities

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',default='/content/video_engine');a=p.parse_args();setup(a.root)
