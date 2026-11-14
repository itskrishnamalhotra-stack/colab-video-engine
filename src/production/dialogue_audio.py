"""Optional radio EQ on authored dialogue, bound to actual aligned words.

Preserves narrator identity, sample count and the word/animation clock.
"""
import hashlib,json,re,sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(word):return re.sub(r"[^a-z0-9']",'',word.lower())

def apply(project):
    p=Path(project);script=json.loads((p/'script.json').read_text())
    specs=script.get('radio_dialogue',[])
    if not specs:return
    data=p/'data';main=data/'narration.wav';clean=data/'narration-clean.wav';report=data/'radio-dialogue.json'
    words=json.loads((data/'words.json').read_text())
    signature=hashlib.sha256((json.dumps(specs,sort_keys=True)+digest(data/'words.json')+digest(__file__)).encode()).hexdigest()
    old=json.loads(report.read_text()) if report.is_file() else {}
    current=digest(main)
    if old.get('processed_sha256')==current and old.get('signature')==signature:return
    if old.get('processed_sha256')==current:
        if not clean.is_file() or digest(clean)!=old.get('clean_sha256'):raise ValueError('Missing original dialogue source.')
    else:clean.write_bytes(main.read_bytes())
    sr,raw=wavfile.read(clean)
    if raw.dtype!=np.int16:raise ValueError('Expected the original PCM16 narration recording.')
    audio=raw.astype(np.float64)/32768;windows=[]
    for spec in specs:
        line=[w for w in words if w['line']==spec['line']]
        starts=[i for i,w in enumerate(line) if norm(w['w'])==norm(spec['first'])]
        if not starts:raise ValueError('Missing radio dialogue opening word.')
        first=starts[spec.get('occurrence',1)-1]
        ends=[w for w in line[first:] if norm(w['w'])==norm(spec['last'])]
        if not ends:raise ValueError('Missing radio dialogue ending word.')
        start,end=float(line[first]['s']),float(ends[0]['e']);a,b=round(start*sr),round(end*sr)
        x=audio[a:b].copy();wet=signal.sosfilt(signal.butter(3,[380,2900],btype='bandpass',fs=sr,output='sos'),x,axis=0)
        wet=np.tanh(wet*2.5);wet*=np.sqrt(np.mean(x*x)+1e-12)/np.sqrt(np.mean(wet*wet)+1e-12)
        fade=min(round(.008*sr),len(x)//3);blend=np.ones(len(x))*.88
        blend[:fade]*=np.linspace(0,1,fade);blend[-fade:]*=np.linspace(1,0,fade)
        audio[a:b]=x*(1-blend)+wet*blend
        windows.append({'line':spec['line'],'start':start,'end':end,'first':spec['first'],'last':spec['last']})
    wavfile.write(main,sr,np.clip(audio*32768,-32767,32767).astype(np.int16))
    (data/'radio_spans.json').write_text(json.dumps(windows,indent=2))
    report.write_text(json.dumps({'signature':signature,'clean_sha256':digest(clean),'processed_sha256':digest(main),
        'samples':len(audio),'sample_rate':sr,'windows':windows},indent=2))
    print(f'RADIO_DIALOGUE {len(windows)} exact word-bound spans; narrator {script.get("voice","af_heart")}; {len(audio)/sr:.2f}s unchanged.')

if __name__=='__main__':apply(sys.argv[1])
