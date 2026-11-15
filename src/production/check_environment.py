"""Read-only portability check; no video rendering, model downloads or software installation."""
from pathlib import Path
import json
import subprocess
import sys
from video_engine import settings, child_flags, environment

cfg=settings()
checks=[]
def check(name, ok, detail):
    checks.append({'name':name,'ok':bool(ok),'detail':str(detail)})

for name in ('python','pythonw','node','chrome'):
    check(name,Path(cfg[name]).is_file(),cfg[name])
ffbin=Path(cfg['ffmpeg_bin'])
for name in ('ffmpeg.exe','ffprobe.exe'):
    check(name,(ffbin/name).is_file(),ffbin/name)
skill=Path(cfg['skill_root'])
check('voice scripts',(skill/'scripts/voice.py').is_file() and (skill/'scripts/words.py').is_file(),skill/'scripts')
for style in ('night-file','tall-tale','deep-dive','inside-out','stick-story','paper-atlas'):
    root=skill/'styles'/style
    check(style,(root/'STYLE.md').is_file() and (root/'example/tools/capture.mjs').is_file(),root)
home=Path.home()
for name in ('kokoro-v1.0.onnx','voices-v1.0.bin'):
    p=home/'.faceless-shorts/kokoro'/name
    check(name,p.is_file(),p)
cache=home/'.cache/huggingface/hub/models--Systran--faster-whisper-small.en'
check('cached Whisper small.en',any(p.is_file() for p in cache.glob('snapshots/*/model.bin')),cache)
default=cfg.get('default_narrator')
if default:
    import hashlib
    pack=Path(default['pack_source'])
    valid=pack.is_file() and hashlib.sha256(pack.read_bytes()).hexdigest()==default['pack_sha256'] and default['voice']==cfg['voice']
else:valid=bool(cfg.get('voice')) and cfg.get('speed',0)>0
check('selected narrator',valid,f'{cfg["voice"]} at {cfg["speed"]}; saved custom pack pinned by hash' if default else cfg['voice'])
for name,command in (
    ('Node version',[cfg['node'],'--version']),
    ('Python packages',[cfg['python'],'-c','import kokoro_onnx, faster_whisper, numpy, scipy; print("Kokoro / Whisper / NumPy / SciPy ready")']),
):
    try:
        result=subprocess.run(command,env=environment(cfg),capture_output=True,text=True,timeout=30,**child_flags())
        detail=(result.stdout or result.stderr).strip()
        ok=result.returncode==0
        if name=='Node version':ok=ok and int(detail.lstrip('v').split('.')[0])>=22
        check(name,ok,detail)
    except Exception as error:
        check(name,False,error)
print(json.dumps({'ready':all(c['ok'] for c in checks),'checks':checks},indent=2))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
