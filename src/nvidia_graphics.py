"""Select existing NVIDIA EGL libraries and verify Blender graphics before rendering.

No packages, driver changes, network requests or system config edits. The vendor
file and probe live only under the job root; environment changes affect children.
"""
import ctypes,ctypes.util,json,os,subprocess
from pathlib import Path

def find_egl_libraries():
 candidates=['libEGL_nvidia.so.0']
 found=ctypes.util.find_library('EGL_nvidia')
 if found:candidates.append(found)
 try:
  result=subprocess.run(['ldconfig','-p'],capture_output=True,text=True,timeout=5)
  candidates += [line.split('=>',1)[1].strip() for line in result.stdout.splitlines() if 'libEGL_nvidia.so' in line and '=>' in line]
 except (OSError,subprocess.TimeoutExpired):pass
 for directory in ['/usr/lib/x86_64-linux-gnu','/usr/lib64','/usr/lib','/usr/local/nvidia/lib64','/usr/local/nvidia/lib']:
  candidates += [str(p) for p in Path(directory).glob('libEGL_nvidia.so*') if p.is_file()]
 for parent in [Path('/usr/lib/x86_64-linux-gnu'),Path('/usr/lib')]:
  candidates += [str(p) for p in parent.glob('nvidia*/libEGL_nvidia.so*') if p.is_file()]
 return list(dict.fromkeys(candidates))

def prepare_nvidia_graphics(executable,root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 report_path=root/'graphics-status.json'
 report={'state':'checking','driver_changes':False,'attempts':[],
         'driver_capabilities':os.environ.get('NVIDIA_DRIVER_CAPABILITIES','unset')}
 def save():report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
 selected=None
 for library in find_egl_libraries():
  try:
   ctypes.CDLL(library)
   selected=library;report['attempts'].append({'library':library,'loadable':True});break
  except OSError as error:report['attempts'].append({'library':library,'loadable':False,'error':str(error)})
 if selected is None:
  report.update(state='unavailable',reason='No loadable NVIDIA EGL vendor library is exposed in this runtime. CUDA access alone does not provide OpenGL graphics access.')
  save()
  raise RuntimeError(report['reason']+' See graphics-status.json. No driver was installed and no render was started.')
 vendor=root/'nvidia-egl-vendor.json'
 vendor.write_text(json.dumps({'file_format_version':'1.0.0','ICD':{'library_path':selected}}),encoding='utf-8')
 env=os.environ.copy()
 for name in ('LIBGL_ALWAYS_SOFTWARE','GALLIUM_DRIVER','MESA_LOADER_DRIVER_OVERRIDE'):env.pop(name,None)
 env['__EGL_VENDOR_LIBRARY_FILENAMES']=str(vendor.resolve())
 env['__GLX_VENDOR_LIBRARY_NAME']='nvidia'
 env.pop('DISPLAY',None);env.pop('WAYLAND_DISPLAY',None)
 if Path(selected).is_absolute():env['LD_LIBRARY_PATH']=str(Path(selected).parent)+os.pathsep+env.get('LD_LIBRARY_PATH','')
 result_path=root/'graphics-device.json';result_path.unlink(missing_ok=True)
 probe=root/'graphics_probe.py'
 probe.write_text('import gpu,json\nfrom pathlib import Path\ngpu.init()\n'+
                  'result={"vendor":gpu.platform.vendor_get(),"renderer":gpu.platform.renderer_get(),"backend":gpu.platform.backend_type_get()}\n'+
                  'Path('+repr(str(result_path.resolve()))+').write_text(json.dumps(result))\nprint("GRAPHICS_DEVICE",json.dumps(result),flush=True)\n',encoding='utf-8')
 log=root/'graphics-preflight.log'
 try:
  with log.open('w',encoding='utf-8') as output:
   result=subprocess.run([str(executable),'--background','--factory-startup','--gpu-backend','opengl',
                          '--python-exit-code','1','--python',str(probe)],env=env,stdout=output,stderr=subprocess.STDOUT,timeout=30)
  report['returncode']=result.returncode
  device=json.loads(result_path.read_text()) if result_path.is_file() else {}
  report['device']=device
  if result.returncode or 'NVIDIA' not in device.get('vendor','').upper() or any(x in device.get('renderer','').lower() for x in ('llvmpipe','software','softpipe')):
   raise RuntimeError('An NVIDIA EGL library was found, but Blender could not create an NVIDIA graphics context. See graphics-preflight.log.')
 except (OSError,ValueError,subprocess.TimeoutExpired,RuntimeError) as error:
  report.update(state='unavailable',reason=str(error));save()
  raise RuntimeError(str(error)+' The full video was not started; no software fallback or driver change was attempted.') from error
 report.update(state='ready',selected_library=selected);save()
 print('BUILD_STAGE NVIDIA graphics preflight passed '+json.dumps(device),flush=True)
 return env
