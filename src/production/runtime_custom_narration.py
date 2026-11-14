"""GPU narration with a saved voice pack and synthesis-native word durations."""
import argparse,hashlib,json,re,time
from pathlib import Path
import numpy as np
import soundfile as sf
SR=24000
def norm(word):return re.sub('[^a-z0-9]','',word.lower())
def fit_outro(total,target,outro,minimum=.15):
 excess=max(0,total-target)
 if excess<=max(0,outro-minimum)+1e-8:return outro-excess,excess
 return outro,0.0
def map_native_words(text,tokens,line,start,end):
 script=[w for w in text.split() if norm(w)];native=[t for t in tokens if norm(t['text'])]
 if ''.join(norm(w) for w in script)!=''.join(norm(t['text']) for t in native):raise ValueError('Native synthesis tokens differ from narration text; refusing estimated word timings')
 rows=[];offset=0;j=0;cursor=0
 for word in script:
  stop=offset+len(norm(word));selected=[]
  while j<len(native) and cursor<stop:
   t=native[j];selected.append(t);cursor+=len(norm(t['text']));j+=1
  if cursor!=stop or not selected:raise ValueError('A native token crosses a word boundary; exact timing adapter needed')
  if any(t.get('s') is None or t.get('e') is None for t in selected):raise ValueError('Missing synthesis word durations')
  s=max(start,start+min(t['s'] for t in selected));e=min(end,start+max(t['e'] for t in selected))
  if e<=s:raise ValueError('Invalid synthesis word duration')
  rows.append(dict(w=word,line=line,s=round(s,3),e=round(e,3)));offset=stop
 return rows

def generate(project):
 import torch
 from kokoro import KPipeline
 p=Path(project).resolve();script=json.loads((p/'script.json').read_text());spec=json.loads((p/'narrator.json').read_text());pack_path=p/spec['pack']
 if hashlib.sha256(pack_path.read_bytes()).hexdigest()!=spec['pack_sha256']:raise ValueError('Voice pack hash mismatch')
 if not torch.cuda.is_available():raise RuntimeError('Custom narration explicitly requires the Colab GPU')
 torch.set_num_threads(2);torch.manual_seed(42);started=time.monotonic()
 pack=np.load(pack_path,allow_pickle=False)
 if pack.shape!=(510,1,256) or pack.dtype!=np.float32 or not np.isfinite(pack).all():raise ValueError('Invalid custom voice pack')
 pipe=KPipeline(lang_code='a',repo_id='hexgrad/Kokoro-82M',device='cuda');voice=torch.from_numpy(pack)
 target=float(script['target_duration']);lead=float(script.get('lead',.2));outro=float(script.get('outro',.5));speed=float(spec.get('speed',1));maximum=float(spec.get('maximum_speed',speed));attempts=[]
 for attempt in range(3):
  chunks=[np.zeros(round(lead*SR),np.float32)];clock=lead;lines=[];words=[];speech=0;gaps=0
  with torch.inference_mode():
   for i,line in enumerate(script['lines']):
    pieces=[];native=[];offset=0
    for result in pipe(line['text'],voice=voice,speed=speed):
     audio=result.audio.detach().cpu().numpy().astype(np.float32);pieces.append(audio)
     for token in result.tokens or []:
      native.append(dict(text=token.text,s=None if token.start_ts is None else offset+token.start_ts,e=None if token.end_ts is None else offset+token.end_ts))
     offset+=len(audio)/SR
    audio=np.concatenate(pieces);start=clock;end=start+len(audio)/SR
    words+=map_native_words(line['text'],native,i,start,end);lines.append(dict(i=i,text=line['text'],start=round(start,3),end=round(end,3)))
    chunks.append(audio);gap=float(line.get('gap',script.get('gap',.12)));chunks.append(np.zeros(round(gap*SR),np.float32));clock=end+gap;speech+=len(audio)/SR;gaps+=gap
  total=clock+outro;attempts.append(dict(speed=speed,untrimmed_duration=round(total,3)))
  outro,trimmed=fit_outro(total,target,outro)
  if trimmed:attempts[-1]['silent_outro_removed_seconds']=round(trimmed,6);total-=trimmed
  print('NARRATION_DURATION '+json.dumps(attempts[-1]),flush=True)
  if total<=target:break
  needed=speed*speech/max(.1,target-lead-outro-gaps)+.005
  if needed>maximum:raise ValueError(f'Narration needs speed {needed:.3f} to fit {target}s, exceeding selected bound {maximum}')
  speed=round(needed,4)
 else:raise ValueError('Narration could not fit its requested duration within bounded native synthesis attempts')
 chunks.append(np.zeros(round(outro*SR),np.float32));audio=np.concatenate(chunks);target_samples=round(target*SR)
 if len(audio)>target_samples:
  excess=len(audio)-target_samples
  if excess>2 or np.any(audio[-excess:]!=0):raise ValueError('Narration overflow would cut speech; refusing truncation')
  audio=audio[:target_samples]
 audio=np.pad(audio,(0,target_samples-len(audio)));audio*=.9/max(np.max(np.abs(audio)),1e-7)
 data=p/'data';data.mkdir(exist_ok=True);sf.write(data/'narration.wav',audio,SR,subtype='PCM_16')
 script.update(voice=spec['voice'],speed=speed);(p/'script.json').write_text(json.dumps(script,indent=2))
 (data/'lines.json').write_text(json.dumps(dict(duration=target,voice=spec['voice'],speed=speed,lines=lines),indent=2))
 (data/'words.json').write_text(json.dumps(words,indent=2));(data/'words.txt').write_text('\n'.join(f"{w['s']:7.3f} {w['e']:7.3f} L{w['line']} {w['w']}" for w in words))
 report=dict(voice=spec['voice'],pack_sha256=spec['pack_sha256'],gpu=torch.cuda.get_device_name(0),device='cuda',word_timing='native Kokoro synthesis-duration tokens; no estimated fallback',words=len(words),duration=target,speed=speed,attempts=attempts,total_seconds=round(time.monotonic()-started,2))
 (data/'narration-report.json').write_text(json.dumps(report,indent=2));print('CUSTOM_NARRATION_READY '+json.dumps(report),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('project');a=p.parse_args();generate(a.project)
