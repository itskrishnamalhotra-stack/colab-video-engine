"""Select installed NVIDIA EGL for Chrome without installing/changing drivers."""
import ctypes,ctypes.util,json,os,subprocess
from pathlib import Path

SOFTWARE_FLAGS=('LIBGL_ALWAYS_SOFTWARE','SOFTWARE_GL','MESA_LOADER_DRIVER_OVERRIDE','GALLIUM_DRIVER','LIBGL_DRIVERS_PATH')

def driver_candidates():
 paths=[]
 for directory in ['/usr/lib64-nvidia','/usr/lib/x86_64-linux-gnu','/usr/lib64','/usr/local/nvidia/lib64']:
  paths.extend(sorted(Path(directory).glob('libEGL_nvidia.so*')))
 for directory in Path('/usr/lib/x86_64-linux-gnu').glob('nvidia*'):
  paths.extend(sorted(directory.glob('libEGL_nvidia.so*')))
 try:
  result=subprocess.run(['ldconfig','-p'],capture_output=True,text=True,timeout=10)
  paths.extend(Path(line.split('=>',1)[1].strip()) for line in result.stdout.splitlines() if 'libEGL_nvidia.so' in line and '=>' in line)
 except (OSError,subprocess.TimeoutExpired):pass
 found=ctypes.util.find_library('EGL_nvidia')
 if found:paths.append(Path(found))
 return list(dict.fromkeys(paths))

def select_nvidia(root,inherited=None):
 base=dict(os.environ if inherited is None else inherited);selected=None;errors=[]
 for candidate in driver_candidates():
  if candidate.is_absolute() and not candidate.is_file():continue
  try:ctypes.CDLL(str(candidate));selected=candidate.resolve() if candidate.is_absolute() else candidate;break
  except OSError:errors.append(str(candidate))
 if selected is None:raise RuntimeError('No loadable NVIDIA EGL graphics library is exposed. CUDA availability alone is insufficient for WebGL; software rendering remains disabled.')
 folder=Path(root)/'tools';folder.mkdir(parents=True,exist_ok=True)
 vendor=folder/'nvidia-egl.json'
 vendor.write_text(json.dumps({'file_format_version':'1.0.0','ICD':{'library_path':str(selected)}},indent=2))
 libraries=([str(selected.parent)] if selected.is_absolute() else [])+base.get('LD_LIBRARY_PATH','').split(os.pathsep)
 env={'__EGL_VENDOR_LIBRARY_FILENAMES':str(vendor.resolve()),'__GLX_VENDOR_LIBRARY_NAME':'nvidia','LD_LIBRARY_PATH':os.pathsep.join(dict.fromkeys(p for p in libraries if p))}
 (Path(root)/'gpu-environment.json').write_text(json.dumps(env,indent=2))
 return env

def capture_environment(base,selected):
 result=dict(base)
 for name in SOFTWARE_FLAGS:result.pop(name,None)
 result.update(selected);return result
