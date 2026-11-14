"""Shared speech-aware music policy for short and long-form mixers."""
import json,math
from pathlib import Path
import numpy as np
from scipy import signal
SR=48000
POLICY=Path(__file__).with_name('music_policy.json')
def settings(script):
 base=json.loads(POLICY.read_text());base.update(script.get('sound_design',{}).get('music',{}))
 for key in ('bed_rms_db','duck_db','attack_seconds','release_seconds','fade_in_seconds','fade_out_seconds'):
  if not math.isfinite(float(base[key])):raise ValueError('Invalid music policy: '+key)
 if not -36<=base['bed_rms_db']<=-20 or not 2<=base['duck_db']<=12:raise ValueError('Music must remain below the narrator')
 if not .02<=base['attack_seconds']<=.5 or not .1<=base['release_seconds']<=2:raise ValueError('Invalid music duck timing')
 return base
def prepare(score,policy):
 if len(score)<SR//4:raise ValueError('Missing or empty music source')
 energy=float(np.mean(score.astype(np.float64)**2))
 if energy<1e-12:raise ValueError('Silent music source')
 audible=signal.sosfilt(signal.butter(2,[250,4000],btype='bandpass',fs=SR,output='sos'),score,axis=0)
 fraction=float(np.mean(audible**2)/energy)
 score=score*(10**(policy['bed_rms_db']/20)/math.sqrt(energy))
 return score.astype(np.float32),{'phone_band_energy_fraction':round(fraction,4),'source_has_audible_midrange':fraction>=.02}
def block(score,voice,at,total,policy,state=None):
 # Fast attack and slower release on a 10ms control clock; state is carried
 # through long-form blocks. The same policy applies regardless of duration.
 hop=480;count=len(voice);controls=[];level=float(state or 0)
 for start in range(0,count,hop):
  part=voice[start:start+hop];target=min(1,float(np.sqrt(np.mean(part**2)))/10**(-30/20))
  tau=policy['attack_seconds'] if target>level else policy['release_seconds']
  before=level;level=target+(level-target)*math.exp(-len(part)/(SR*tau));controls.append(np.linspace(before,level,len(part),endpoint=False))
 envelope=np.concatenate(controls)
 clock=np.arange(at,at+count);gain=10**(-policy['duck_db']*envelope/20)
 gain*=np.minimum(1,clock/max(1,SR*policy['fade_in_seconds']))
 gain*=np.minimum(1,(total-1-clock)/max(1,SR*policy['fade_out_seconds']))
 return score[clock%len(score)]*gain[:,None],level
