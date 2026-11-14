"""Isolated GPU voice-pack experiment. Never changes production narrator defaults."""
import argparse,hashlib,json,time,re
from pathlib import Path
import numpy as np
import soundfile as sf

TEXT="The radio spoke in his voice. But the battery was on the table. Then someone whispered, don't turn around."

def load_references(root,manifest=None):
 root=Path(root)
 if manifest:
  path=(root/manifest).resolve()
  if not path.is_relative_to(root.resolve()) or not path.is_file():raise ValueError('Explicit reference manifest is missing or outside the experiment')
  refs=json.loads(path.read_text())
 else:
  approved=root/'approved-references.json'
  refs=json.loads(approved.read_text()) if approved.is_file() else [r for r in json.loads((root/'references.json').read_text()) if r.get('name')=='official-liam']
 if not refs:raise ValueError('No explicitly approved normal-delivery references; do not silently reuse dramatic dataset audio')
 return refs[:2]

def run(root,manifest=None,output='outputs',prefix='am_liam_trial',text=TEXT):
 import torch
 from inno_kokoro.enroll import Tuner,enroll,read
 from kokoro import KPipeline
 root=Path(root).resolve()
 if not re.fullmatch(r'[a-z0-9_-]+',output) or not re.fullmatch(r'[a-z0-9_]+',prefix):raise ValueError('Use simple output and voice-pack names')
 out=root/output;out.mkdir(exist_ok=True)
 if not torch.cuda.is_available():raise RuntimeError('This experiment explicitly requires the Colab GPU')
 torch.set_num_threads(2);torch.manual_seed(42);np.random.seed(42)
 started=time.monotonic();print('VOICE_STAGE loading_gpu_tuner',flush=True)
 tuner=Tuner(backend='torch',device='cuda',check_update=False)
 if next(tuner.encoder.parameters()).device.type!='cuda':raise RuntimeError('Encoder was not placed on the GPU')
 refs=load_references(root,manifest);packs=[]
 with torch.inference_mode():
  for index,ref in enumerate(refs,1):
   print('VOICE_STAGE extracting_reference',index,flush=True);wav,sr=read(ref['path']);t=time.monotonic();pack,blend=enroll(wav,sr,tuner);torch.cuda.synchronize()
   if pack.shape!=(510,1,256) or pack.dtype!=np.float32 or not np.isfinite(pack).all():raise ValueError('Invalid Kokoro voice pack')
   name=prefix+'_'+str(index);npy=out/(name+'.npy');pt=out/(name+'.pt');np.save(npy,pack);torch.save(torch.from_numpy(pack),pt)
   packs.append(dict(name=name,npy=str(npy),pt=str(pt),reference=ref,reference_seconds=len(wav)/sr,enrollment_seconds=round(time.monotonic()-t,3),blend=blend,shape=list(pack.shape),tensor=torch.from_numpy(pack)))
 print('VOICE_STAGE loading_gpu_kokoro',flush=True);pipe=KPipeline(lang_code='a',repo_id='hexgrad/Kokoro-82M',device='cuda')
 if next(pipe.model.parameters()).device.type!='cuda':raise RuntimeError('Kokoro was not placed on the GPU')
 results=[]
 with torch.inference_mode():
  for item in packs:
   t=time.monotonic();chunks=[result.audio.detach().cpu().numpy() for result in pipe(text,voice=item.pop('tensor'),speed=1.0)]
   audio=np.concatenate(chunks)
   if not len(audio) or not np.isfinite(audio).all() or np.max(np.abs(audio))<1e-5:raise ValueError('Invalid voice test audio')
   audio*=.85/max(float(np.abs(audio).max()),1e-7);path=out/(item['name']+'.wav');sf.write(path,audio,24000,subtype='PCM_16');item.update(audio=str(path),audio_seconds=round(len(audio)/24000,3),generation_seconds=round(time.monotonic()-t,3));results.append(item);print('VOICE_SAMPLE_READY',path,flush=True)
 report=dict(state='complete',experimental=True,production_voice_changed=False,gpu=torch.cuda.get_device_name(0),tuner_device='cuda',tts_device='cuda',text=text,speed=1.0,total_seconds=round(time.monotonic()-started,3),items=results,notes='Kokoro-compatible approximation, not a claim of exact voice identity. Reference provenance is retained; no production/publishing activation.')
 for item in results:
  for name in ('npy','pt','audio'):item[name+'_sha256']=hashlib.sha256(Path(item[name]).read_bytes()).hexdigest()
 (out/'result.json').write_text(json.dumps(report,indent=2));print('VOICE_EXPERIMENT_COMPLETE '+json.dumps({k:v for k,v in report.items() if k!='items'}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default='/content/video_engine/voice-lab');p.add_argument('--refs');p.add_argument('--output',default='outputs');p.add_argument('--prefix',default='am_liam_trial');p.add_argument('--text',default=TEXT);a=p.parse_args();run(a.root,a.refs,a.output,a.prefix,a.text)
