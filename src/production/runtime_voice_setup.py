"""Prepare cached CUDA Kokoro inference in an isolated runtime environment."""
import fcntl,json,os,shutil,subprocess,sys
from pathlib import Path

def run(args):
 print('VOICE_SETUP '+str(args[0])+' '+str(args[1]),flush=True)
 subprocess.run([str(x) for x in args],check=True)

def ensure(root):
 lab=Path(root)/'voice-lab';lab.mkdir(parents=True,exist_ok=True)
 with (lab/'setup.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  python=lab/'venv/bin/python';setup=lab/'setup.json'
  probe='import torch, kokoro, spacy; assert torch.cuda.is_available(); spacy.load("en_core_web_sm"); print("CUDA_KOKORO_READY")'
  if python.is_file() and shutil.which('espeak-ng') and subprocess.run([str(python),'-c',probe],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
   setup.write_text(json.dumps({'python':str(python),'device':'cuda','purpose':'saved custom voice inference'}));return str(python)
  if not shutil.which('espeak-ng'):
   run(['apt-get','update','-qq']);run(['apt-get','install','-y','-qq','espeak-ng'])
  if not shutil.which('uv'):run([sys.executable,'-m','pip','install','uv==0.9.5'])
  uv=shutil.which('uv')
  if not uv:raise RuntimeError('uv was installed but is not on PATH')
  if not python.is_file():run([uv,'venv','--python','3.12',str(lab/'venv')])
  # Explicit interpreter selection prevents installation into notebook Python 3.13.
  run([uv,'pip','install','--python',python,'torch==2.8.0','--index-url','https://download.pytorch.org/whl/cu128'])
  run([uv,'pip','install','--python',python,'kokoro==0.9.4','soundfile==0.13.1','spacy==3.8.7','numpy==2.2.6'])
  run([uv,'pip','install','--python',python,'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl'])
  run([python,'-c',probe])
  setup.write_text(json.dumps({'python':str(python),'device':'cuda','purpose':'saved custom voice inference'}));return str(python)

if __name__=='__main__':print(ensure(sys.argv[1]),flush=True)
