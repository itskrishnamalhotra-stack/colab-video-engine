"""Sample-based action Foley, music ducking and a measured, limited master.

Uses project-local, licensed source audio. Missing samples fail loudly; there is
no fallback to generic pops. Deterministic variations avoid machine-gun repeats.
"""
import hashlib,json, math, os, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile
from sound_profile import validate_events,PROFILE
import music_mix
SR=48000

def db(value):return 10**(value/20)
def rms(x):return float(np.sqrt(np.mean(np.square(x,dtype=np.float64))+1e-15))
def parse_loudness(stderr):
 # FFmpeg can append progress/encoder messages after loudnorm's JSON. Decode
 # the object itself, not the remainder of stderr, and require measured fields.
 decoder=json.JSONDecoder();reports=[]
 for index,char in enumerate(stderr):
  if char!='{':continue
  try:value,_=decoder.raw_decode(stderr,index)
  except json.JSONDecodeError:continue
  if isinstance(value,dict) and {'input_i','output_i','output_tp','normalization_type'}<=value.keys():
   if all(math.isfinite(float(value[key])) for key in ('input_i','output_i','output_tp')):reports.append(value)
 if not reports:raise ValueError('FFmpeg returned no valid loudness report; see data/sound-normalization.log.')
 return reports[-1]

def binary(name):
 path=shutil.which(name)
 if path:return path
 cfg=json.loads((Path(__file__).parent/'video_defaults.json').read_text())
 return str(Path(cfg['ffmpeg_bin'])/(name+'.exe'))

def decode(path):
 result=subprocess.run([binary('ffmpeg'),'-v','error','-i',str(path),'-f','f32le','-ar',str(SR),'-ac','2','pipe:1'],capture_output=True,check=True)
 return np.frombuffer(result.stdout,dtype='<f4').reshape(-1,2).copy()

def fit_sample(x,duration=None,rate=1,loop=False):
 if rate!=1:x=signal.resample_poly(x,1000,max(1,round(1000*rate)),axis=0).astype(np.float32)
 if duration is not None:
  n=max(1,round(duration*SR))
  if loop and len(x)<n:
   # Overlap the tails so repeated rasp/cloth beds have no hard boundaries.
   overlap=min(round(.035*SR),len(x)//4);step=len(x)-overlap
   out=np.zeros((n+len(x),2),np.float32)
   edge=np.ones(len(x),np.float32)
   if overlap:edge[:overlap]=np.linspace(0,1,overlap);edge[-overlap:]=np.linspace(1,0,overlap)
   for i in range(0,n,step):out[i:i+len(x)]+=x*edge[:,None]
   x=out[:n]
  else:x=x[:n]
 fade=min(round(.008*SR),len(x)//3)
 if fade:x[:fade]*=np.linspace(0,1,fade)[:,None];x[-fade:]*=np.linspace(1,0,fade)[:,None]
 return x

def trim_to_onset(x):
 # Align the first detectable attack, not the start of a file containing silence.
 # -40 dB relative to that sample's peak; report the exact removed sample count.
 envelope=np.max(np.abs(x),axis=1);peak=float(envelope.max())
 if peak<1e-7:raise ValueError('Silent Foley cannot represent an action contact')
 hits=np.flatnonzero(envelope>=peak*.01)
 start=int(hits[0]);return x[start:].copy(),start

def place(bus,x,start):
 index=round(start*SR);offset=max(0,-index);index=max(0,index);count=min(len(x)-offset,len(bus)-index)
 if count>0:bus[index:index+count]+=x[offset:offset+count]

def mix(project):
 p=Path(project);cues=json.loads((p/'data/cues.json').read_text());script=json.loads((p/'script.json').read_text())
 profile=validate_events(cues['cues'])
 if (p/'visual_profile.json').is_file():
  from animation_events import verify_cues
  verify_cues(p,cues)
 def digest(path):
  with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
 inputs=[p/'data/cues.json',p/'data/narration.wav',p/script['music'],Path(__file__),PROFILE,Path(__file__).parent/'sound_materials.json',Path(music_mix.__file__),music_mix.POLICY]
 if cues['duration']>180:inputs.append(Path(__file__).parent/'longform_mix.py')
 inputs.extend(p/'audio/foley'/name for name in sorted({event['sample'] for event in cues['cues']}))
 key=hashlib.sha256((''.join(digest(path) for path in inputs)+json.dumps({k:script.get(k) for k in ('sound_design','soundscape')},sort_keys=True)).encode()).hexdigest()
 try:
  previous=json.loads((p/'data/sound-report.json').read_text())
  if previous.get('inputs_sha256')==key and digest(p/'data/mix.wav')==previous.get('mix_sha256'):
   print('SOUND_MASTER_REUSED verified unchanged mix',flush=True);return previous
 except (OSError,ValueError,KeyError):pass
 if cues['duration']>180:
  from longform_mix import mix_longform
  return mix_longform(p,cues,script,key)
 n=round(cues['duration']*SR);voice=np.zeros((n,2),np.float32);foley=voice.copy();music=voice.copy();ambience=voice.copy()
 narration=decode(p/'data/narration.wav');narration*=db(-19)/max(rms(narration),1e-7);place(voice,narration,0)
 cache={};event_log=[]
 for i,event in enumerate(cues['cues']):
  name=event.get('sample')
  if not name:raise ValueError(f"Foley event has no sample: {event}")
  path=(p/'audio/foley'/name).resolve()
  if not path.is_relative_to((p/'audio/foley').resolve()) or not path.is_file():raise FileNotFoundError(path)
  if name not in cache:cache[name]=decode(path)
  sample=cache[name].copy();trimmed=0
  if event.get('onset_align'):sample,trimmed=trim_to_onset(sample)
  x=fit_sample(sample,event.get('duration'),event.get('rate',1),event.get('loop',False))
  if not len(x):raise ValueError('Empty sound: '+name)
  # Raw Foley has large isolated spikes. Peak-only normalization makes the body
  # almost inaudible. Control that crest, then set an audible event RMS.
  mono=x.mean(axis=1)
  mono=signal.sosfilt(signal.butter(2,65,btype='highpass',fs=SR,output='sos'),mono).astype(np.float32)
  if event.get('lowpass_hz'):
   cutoff=float(event['lowpass_hz'])
   if not 200<=cutoff<SR/2:raise ValueError('Invalid Foley lowpass cutoff')
   mono=signal.sosfilt(signal.butter(2,cutoff,btype='lowpass',fs=SR,output='sos'),mono).astype(np.float32)
  mono=np.tanh(mono/max(rms(mono)*3.5,1e-7))
  mono*=db(event.get('db',-14)-8)/max(rms(mono),1e-7)
  mono*=min(1,db(-4)/max(float(np.max(np.abs(mono))),1e-7))
  # Equal-power stereo placement; preserve texture rather than a global lowpass.
  pan=max(-1,min(1,event.get('pan',0)))
  x=np.column_stack((mono*math.cos((pan+1)*math.pi/4),mono*math.sin((pan+1)*math.pi/4))).astype(np.float32)
  # With measured contacts, require integer frame -> audio sample correspondence.
  if event.get('timing_source')=='animation-state':
   if abs(event['t']-event['frame']/event['fps'])>1e-10:raise ValueError('Contact frame/time mismatch')
  place(foley,x,event['t']);event_log.append({**event,'audio_sample':round(event['t']*SR),
    'source_leading_samples_removed':trimmed,'played_seconds':round(len(x)/SR,3),'event_rms_db':round(20*math.log10(rms(x)),2)})
 # Room air remains low; every scene's audible identity comes from its action Foley.
 rng=np.random.default_rng(20261110)
 air=rng.standard_normal((n,2)).astype(np.float32)
 air=signal.sosfilt(signal.butter(2,[100,1900],btype='bandpass',fs=SR,output='sos'),air,axis=0).astype(np.float32)
 air*=db(-53)/rms(air);ambience+=air
 music_path=p/script['music']
 policy=music_mix.settings(script);score,music_report=music_mix.prepare(decode(music_path),policy)
 music,_=music_mix.block(score,voice,0,n,policy)
 pre=voice+foley+music+ambience
 temporary=p/'data/mix-premaster.wav';wavfile.write(temporary,SR,pre.astype(np.float32))
 result=subprocess.run([binary('ffmpeg'),'-y','-hide_banner','-nostats','-i',str(temporary),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-ar',str(SR),'-c:a','pcm_s16le',str(p/'data/mix.wav')],capture_output=True,text=True,check=True)
 (p/'data/sound-normalization.log').write_text(result.stderr,encoding='utf-8')
 temporary.unlink()
 loudness=parse_loudness(result.stderr)
 report={'inputs_sha256':key,'mix_sha256':digest(p/'data/mix.wav'),'duration':cues['duration'],'sample_events':len(event_log),'unique_samples':len(cache),'narrator':'af_heart','speed':1.0,'voice_rms_db':round(20*math.log10(rms(voice)),2),'foley_rms_db':round(20*math.log10(rms(foley)),2),'music_rms_db':round(20*math.log10(rms(music)),2),'loudness':loudness,'events':event_log}
 report['music_policy']={**policy,**music_report}
 (p/'data/sound-report.json').write_text(json.dumps(report,indent=2));print('SOUND_MASTER',json.dumps({k:v for k,v in report.items() if k!='events'}),flush=True)
 return report

if __name__=='__main__':mix(sys.argv[1])
