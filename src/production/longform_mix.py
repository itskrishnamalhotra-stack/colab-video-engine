"""Bounded-memory version of the approved sample mixer for long-form stories.

Disk-backed narration/contact buses and two-second blocks avoid allocating six
whole-film stereo arrays. Uses the same source checks, exact frame clock and
normalization as Shorts. No generated substitute for a missing physical sound.
"""
import hashlib,json,math,subprocess
from pathlib import Path
import numpy as np
from scipy import signal
import music_mix

def mix_longform(p,cues,script,key):
 from foley_mix import SR,db,rms,binary,decode,fit_sample,trim_to_onset,parse_loudness
 folder=p/'data';n=round(cues['duration']*SR);block=SR*2;temps=[]
 def raw_file(name):
  path=folder/name;temps.append(path);return path
 voice_path=raw_file('longform-voice.f32')
 subprocess.run([binary('ffmpeg'),'-v','error','-y','-i',str(folder/'narration.wav'),'-f','f32le','-ar',str(SR),'-ac','2',str(voice_path)],check=True)
 voice=np.memmap(voice_path,dtype='<f4',mode='r',shape=(voice_path.stat().st_size//8,2))
 def energy(data):
  total=0;count=0
  for at in range(0,len(data),block):
   x=data[at:at+block];total+=float(np.sum(np.square(x,dtype=np.float64)));count+=x.size
  return total/max(1,count)
 voice_gain=db(-19)/max(math.sqrt(energy(voice)),1e-7)
 contacts_path=raw_file('longform-contacts.f32')
 contacts=np.memmap(contacts_path,dtype='<f4',mode='w+',shape=(n,2));contacts[:]=0
 cache={};events=[]
 for event in cues['cues']:
  name=event['sample'];path=(p/'audio/foley'/name).resolve()
  if not path.is_relative_to((p/'audio/foley').resolve()) or not path.is_file():raise FileNotFoundError(path)
  if name not in cache:cache[name]=decode(path)
  sample=cache[name].copy();trimmed=0
  if event.get('onset_align'):sample,trimmed=trim_to_onset(sample)
  x=fit_sample(sample,event.get('duration'),event.get('rate',1),event.get('loop',False))
  if not len(x):raise ValueError('Empty sound: '+name)
  mono=x.mean(axis=1);mono=signal.sosfilt(signal.butter(2,65,btype='highpass',fs=SR,output='sos'),mono).astype(np.float32)
  if event.get('lowpass_hz'):
   cutoff=float(event['lowpass_hz'])
   if not 200<=cutoff<SR/2:raise ValueError('Invalid Foley lowpass cutoff')
   mono=signal.sosfilt(signal.butter(2,cutoff,btype='lowpass',fs=SR,output='sos'),mono).astype(np.float32)
  mono=np.tanh(mono/max(rms(mono)*3.5,1e-7));mono*=db(event.get('db',-14)-8)/max(rms(mono),1e-7)
  mono*=min(1,db(-4)/max(float(np.max(np.abs(mono))),1e-7));pan=max(-1,min(1,event.get('pan',0)))
  x=np.column_stack((mono*math.cos((pan+1)*math.pi/4),mono*math.sin((pan+1)*math.pi/4))).astype(np.float32)
  if event.get('timing_source')!='animation-state' or abs(event['t']-event['frame']/event['fps'])>1e-10:raise ValueError('Long-form contact needs exact measured frame')
  start=round(event['t']*SR);offset=max(0,-start);start=max(0,start);count=min(len(x)-offset,n-start)
  if count>0:contacts[start:start+count]+=x[offset:offset+count]
  events.append({**event,'audio_sample':round(event['t']*SR),'source_leading_samples_removed':trimmed,
                 'played_seconds':round(len(x)/SR,3),'event_rms_db':round(20*math.log10(rms(x)),2)})
 contacts.flush()
 policy=music_mix.settings(script);score,music_report=music_mix.prepare(decode(p/script['music']),policy)
 if not len(score):raise ValueError('Empty music source')
 spans=[]
 lines=json.loads((folder/'lines.json').read_text())['lines']
 for quiet in script.get('soundscape',[]):
  index=quiet['line']
  if not 0<=index<len(lines):raise ValueError('Invalid soundscape line clock')
  spans.append((round(lines[index]['start']*SR),round(lines[index]['end']*SR),db(quiet.get('music_db',-60))))
 premaster=raw_file('longform-premaster.f32');rng=np.random.default_rng(20261110)
 air_sos=signal.butter(2,[100,1900],btype='bandpass',fs=SR,output='sos');air_state=np.zeros((len(air_sos),2,2))
 duck_state=0;sums={k:0.0 for k in['voice','foley','music']}
 with premaster.open('wb') as stream:
  for at in range(0,n,block):
   count=min(block,n-at);v=np.zeros((count,2),np.float32);available=min(count,len(voice)-at)
   if available>0:v[:available]=voice[at:at+available]*voice_gain
   music,duck_state=music_mix.block(score,v,at,n,policy,duck_state)
   for start,end,gain in spans:
    a=max(0,start-at);b=min(count,end-at)
    if b>a:music[a:b]*=gain
   air,air_state=signal.sosfilt(air_sos,rng.standard_normal((count,2),dtype=np.float32),axis=0,zi=air_state)
   # Fixed low room tone; no block-by-block gain pumping.
   air=(air*.0048).astype(np.float32)
   f=contacts[at:at+count];pre=v+f+music+air;pre.astype('<f4').tofile(stream)
   for name,x in [('voice',v),('foley',f),('music',music)]:sums[name]+=float(np.sum(np.square(x,dtype=np.float64)))
   if at%(SR*60)==0:print('SOUND_PROGRESS',round(at/SR),'/',round(n/SR),'seconds',flush=True)
 result=subprocess.run([binary('ffmpeg'),'-y','-hide_banner','-nostats','-f','f32le','-ar',str(SR),'-ac','2','-i',str(premaster),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-ar',str(SR),'-c:a','pcm_s16le',str(folder/'mix.wav')],capture_output=True,text=True,check=True)
 (folder/'sound-normalization.log').write_text(result.stderr,encoding='utf-8');loudness=parse_loudness(result.stderr)
 with (folder/'mix.wav').open('rb') as stream:mix_hash=hashlib.file_digest(stream,'sha256').hexdigest()
 report={'inputs_sha256':key,'mix_sha256':mix_hash,'duration':cues['duration'],'sample_events':len(events),'unique_samples':len(cache),
         'narrator':'af_heart','speed':1.0,'memory_mode':'disk buses / two-second blocks','loudness':loudness,'events':events,
         **{k+'_rms_db':round(10*math.log10(max(1e-15,total/(n*2))),2) for k,total in sums.items()}}
 report['music_policy']={**policy,**music_report}
 (folder/'sound-report.json').write_text(json.dumps(report,indent=2));del f
 voice._mmap.close();contacts._mmap.close();del voice,contacts
 for path in temps:path.unlink(missing_ok=True)
 print('SOUND_MASTER',json.dumps({k:v for k,v in report.items() if k!='events'}),flush=True);return report
