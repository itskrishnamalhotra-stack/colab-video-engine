"""Portable notebook/bridge GPU render runner. No Chrome, tunnel or credentials required.
The notebook route runs interactively. An optional external bridge requires an
eligible paid Colab runtime with positive compute units under Colab's rules.
"""
import argparse,ctypes.util,hashlib,json,os,shutil,subprocess,sys,tarfile,time,traceback,urllib.request,zipfile
from pathlib import Path

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def fetch(url,path,expected_sha256=None):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.is_file() and (expected_sha256 is None or sha(path)==expected_sha256):return
 temporary=path.with_suffix(path.suffix+'.part')
 req=urllib.request.Request(url,headers={'User-Agent':'VideoEngine/1.0','Accept':'application/octet-stream'})
 with urllib.request.urlopen(req,timeout=180) as r,temporary.open('wb') as f:shutil.copyfileobj(r,f)
 if expected_sha256 is not None and sha(temporary)!=expected_sha256:raise ValueError('Downloaded asset failed SHA-256 verification.')
 temporary.replace(path)

def unpack_zip(archive,destination):
 destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  for n in z.namelist():
   if not (destination/n).resolve().is_relative_to(destination):raise ValueError('Unsafe ZIP member')
  z.extractall(destination)

def run(command,**kw):
 print('RUN',command[0],flush=True)
 return subprocess.run(command,check=True,**kw)

def prepare_snow(root,manifest):
 root=Path(root);asset=root/'assets/blender-studio/snow-v2'
 if (asset/'snow_v02.blend').is_file():return asset
 urls=manifest.get('snow_archive_urls',[])
 if not urls:raise RuntimeError('This project has no direct Snow asset URL. Reopen the updated notebook.')
 snow=root/'assets/blender-studio/snow-v2.zip';errors=[]
 for url in urls:
  try:
   fetch(url,snow,manifest['snow_archive_sha256'])
   unpack_zip(snow,asset)
   if not (asset/'snow_v02.blend').is_file():raise ValueError('Verified Snow archive did not contain its rig.')
   print('SNOW_ASSET_VERIFIED',manifest['snow_archive_sha256'],flush=True)
   return asset
  except Exception as error:
   detail=f'HTTP {error.code}' if hasattr(error,'code') else str(error)
   errors.append(detail)
 raise RuntimeError('Snow rig download failed at the configured mirrors: '+'; '.join(errors))

def main(root):
 root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
 status=root/'gpu-status.json'
 def stage(name,**kw):
  status.write_text(json.dumps({'stage':name,'updated':time.time(),**kw},indent=2),encoding='utf-8')
  print('GPU_STAGE',name,flush=True)
 manifest=json.loads((root/'manifest.json').read_text())
 for item in manifest['files']:
  if sha(root/item['path'])!=item['sha256']:raise ValueError('Bundle verification failed: '+item['path'])
 project=root/'projects'/manifest['project']
 stage('checking_gpu')
 run(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'])
 stage('preparing_blender')
 version='5.2.3';name=f'blender-{version}-linux-x64.tar.xz'
 base='https://download.blender.org/release/Blender5.2/'
 tools=root/'tools';tools.mkdir(exist_ok=True)
 sums=urllib.request.urlopen(base+f'blender-{version}.sha256',timeout=60).read().decode()
 expected=next(line.split()[0] for line in sums.splitlines() if line.strip().endswith(name))
 archive=tools/name;exe=tools/name[:-7]/'blender'
 if not exe.is_file():
  fetch(base+name,archive,expected)
  if sha(archive)!=expected:raise ValueError('Blender does not match the publisher SHA-256.')
  with tarfile.open(archive) as tar:tar.extractall(tools,filter='data')
 if not exe.is_file():raise FileNotFoundError('Blender extraction did not produce the executable.')
 # Shared libraries only. Never replace Google's NVIDIA driver or kernel stack.
 if not all(ctypes.util.find_library(n) for n in ['Xrender','Xi','xkbcommon','SM','GL','EGL']) or not all(shutil.which(n) for n in ['ffmpeg','ffprobe']):
  run(['apt-get','-qq','update'],stdout=subprocess.DEVNULL)
  run(['apt-get','-qq','install','-y','libxrender1','libxi6','libxkbcommon0','libsm6','libgl1','libegl1','ffmpeg'],stdout=subprocess.DEVNULL)
 stage('preparing_snow_rig')
 prepare_snow(root,manifest)
 frames=project/'renders/gpu-frames';frames.mkdir(parents=True,exist_ok=True)
 stage('rendering_cuda',note='The scene checks CUDA devices and stops if GPU selection fails.')
 render_start=time.monotonic()
 run([str(exe),'--background','--factory-startup','--enable-autoexec','--python-exit-code','1',
      '--threads','4','--python',str(project/'build_scene.py'),'--','--project',str(project),'--frames',str(frames),'--device','CUDA'])
 stage('encoding_mp4')
 outputs=root/'outputs';outputs.mkdir(exist_ok=True);output=outputs/(manifest['project']+'.mp4')
 run(['ffmpeg','-v','error','-y','-framerate','30','-start_number','1','-i',str(frames/'frame_%04d.png'),
      '-i',str(project/'data/mix.wav'),'-vf','ass=filename=data/captions.ass:fontsdir=fonts',
      '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
      '-shortest','-movflags','+faststart',str(output)],cwd=project)
 result=subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)],text=True)
 info=json.loads(result);video=next(s for s in info['streams'] if s['codec_type']=='video')
 if (video['width'],video['height'])!=(1080,1920) or not any(s['codec_type']=='audio' for s in info['streams']):raise ValueError('Output stream validation failed.')
 expected_duration=json.loads((project/'data/lines.json').read_text())['duration']
 if abs(float(info['format']['duration'])-expected_duration)>.25:raise ValueError('Output duration is incorrect.')
 output.with_suffix('.verification.json').write_text(result)
 device=json.loads((project/'data/render-device.json').read_text())
 if device.get('requested_device')!='CUDA' or device.get('engine')!='CYCLES':raise ValueError('CUDA renderer verification failed.')
 stage('complete',output=str(output),bytes=output.stat().st_size,sha256=sha(output),render_and_encode_seconds=round(time.monotonic()-render_start,2),renderer=device)
 print('GPU_VIDEO_READY',str(output),flush=True)
 return output

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--root',default='/content/video_engine');args=parser.parse_args()
 try:main(args.root)
 except BaseException as e:
  root=Path(args.root);root.mkdir(parents=True,exist_ok=True)
  (root/'GPU_ERROR.txt').write_text('GPU RENDER FAILED\n\n'+str(e)+'\n\n'+traceback.format_exc(),encoding='utf-8')
  print('GPU_ERROR',str(e),flush=True);raise
