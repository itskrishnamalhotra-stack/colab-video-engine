"""Cache official Node and Chrome on a Linux GPU runtime, without changing drivers."""
import ctypes.util,hashlib,json,os,shutil,subprocess,tarfile,urllib.request
from pathlib import Path

def setup(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);tools=root/'tools';tools.mkdir(exist_ok=True)
 if not all(shutil.which(n) for n in ('ffmpeg','ffprobe')) or not all(ctypes.util.find_library(n) for n in ('EGL','GL')):
  subprocess.run(['apt-get','-qq','update'],check=True)
  subprocess.run(['apt-get','-qq','install','-y','ffmpeg','libegl1','libgl1','libxrender1','libxi6','libxkbcommon0','libsm6'],check=True)
 from webgl_graphics_environment import select_nvidia
 selected=select_nvidia(root)
 os.environ.update(selected);(root/'gpu-environment.json').write_text(json.dumps(selected,indent=2))
 nodes=sorted(tools.glob('node-v22.*-linux-x64/bin/node'))
 if nodes:node=nodes[-1]
 else:
  base='https://nodejs.org/dist/latest-v22.x/'
  sums=urllib.request.urlopen(base+'SHASUMS256.txt',timeout=60).read().decode()
  expected,name=next(line.split() for line in sums.splitlines() if line.endswith('-linux-x64.tar.xz'))
  archive=tools/name;urllib.request.urlretrieve(base+name,archive)
  with archive.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
  if actual!=expected:raise ValueError('Node publisher SHA-256 mismatch.')
  with tarfile.open(archive) as source:source.extractall(tools,filter='data')
  node=tools/name.removesuffix('.tar.xz')/'bin/node'
 chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable')
 if not chrome:
  deb=tools/'google-chrome-stable_current_amd64.deb'
  urllib.request.urlretrieve('https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb',deb)
  subprocess.run(['apt-get','-qq','update'],check=True)
  subprocess.run(['apt-get','-qq','install','-y',str(deb)],check=True)
  chrome=shutil.which('google-chrome')
 result={'node':str(node),'chrome':chrome,'ffmpeg':shutil.which('ffmpeg')}
 (root/'webgl-tools.json').write_text(json.dumps(result,indent=2));return result
