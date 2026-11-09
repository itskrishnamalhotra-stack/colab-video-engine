"""Cache the native GPU toolchain once per runtime; independent of any video."""
import ctypes.util,json,shutil,subprocess,sys,tarfile,urllib.request
from pathlib import Path
from run_colab_render import fetch,sha,run,prepare_snow

def setup(root):
 root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
 version='5.2.3';name=f'blender-{version}-linux-x64.tar.xz'
 tools=root/'tools';tools.mkdir(exist_ok=True);exe=tools/name[:-7]/'blender'
 if not exe.is_file():
  print('RUNTIME_STAGE installing_blender_once',flush=True)
  base='https://download.blender.org/release/Blender5.2/'
  sums=urllib.request.urlopen(base+f'blender-{version}.sha256',timeout=60).read().decode()
  expected=next(line.split()[0] for line in sums.splitlines() if line.strip().endswith(name))
  archive=tools/name;fetch(base+name,archive,expected)
  with tarfile.open(archive) as source:source.extractall(tools,filter='data')
 if not all(ctypes.util.find_library(n) for n in ['Xrender','Xi','xkbcommon','SM','GL','EGL']) or not all(shutil.which(n) for n in ['ffmpeg','ffprobe']):
  run(['apt-get','-qq','update'],stdout=subprocess.DEVNULL)
  run(['apt-get','-qq','install','-y','libxrender1','libxi6','libxkbcommon0','libsm6','libgl1','libegl1','ffmpeg'],stdout=subprocess.DEVNULL)
 capabilities={'blender':str(exe),'blender_version':version,'ffmpeg':shutil.which('ffmpeg'),
               'root':str(root),'projects':str(root/'projects'),'tools':['python','shell','file_transfer','build_scene','probe_frames','render_video']}
 gpu=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],capture_output=True,text=True,timeout=10)
 capabilities['gpu']=gpu.stdout.strip() if gpu.returncode==0 else 'not assigned'
 try:
  from nvidia_graphics import prepare_nvidia_graphics
  env=prepare_nvidia_graphics(exe,root)
  selected={k:env[k] for k in ['__EGL_VENDOR_LIBRARY_FILENAMES','__GLX_VENDOR_LIBRARY_NAME','LD_LIBRARY_PATH'] if k in env}
  (root/'gpu-environment.json').write_text(json.dumps(selected,indent=2))
  capabilities['eevee_graphics']='ready'
 except RuntimeError as error:capabilities['eevee_graphics']=str(error)
 recipe=root/'asset_recipe.json'
 if recipe.is_file():
  print('RUNTIME_STAGE caching_character_once',flush=True)
  prepare_snow(root,json.loads(recipe.read_text()))
  capabilities['snow_asset']='cached'
 (root/'projects').mkdir(exist_ok=True);(root/'results').mkdir(exist_ok=True)
 (root/'runtime-capabilities.json').write_text(json.dumps(capabilities,indent=2))
 print('RUNTIME_READY',json.dumps(capabilities),flush=True)
 return capabilities

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',default='/content/video_engine');a=p.parse_args();setup(a.root)
