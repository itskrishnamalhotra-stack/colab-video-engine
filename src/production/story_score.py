"""Original restrained suspense music with phone-audible harmonic detail."""
import argparse
from pathlib import Path
import numpy as np
from scipy.io import wavfile
def author(project,seconds=60,semitones=0,motif_period=3.8):
 sr=48000;t=np.arange(round(sr*seconds))/sr;left=np.zeros(len(t));right=left.copy();pitch=2**(semitones/12)
 # Evolving D-minor colours; musical layers only, never fake physical contacts.
 chords=[(146.83,174.61,220),(130.81,164.81,196),(146.83,174.61,233.08),(138.59,174.61,220)]
 for index,start in enumerate(np.arange(-1,seconds,7.5)):
  age=t-start;env=np.where(age>=0,np.minimum(1,np.maximum(0,age)/1.5)*np.minimum(1,np.maximum(0,9-age)/2),0)*.065
  for j,note in enumerate(chords[index%len(chords)]):
   for harmonic,amount in [(1,.65),(2,.35),(3,.12)]:
    drift=.012*np.sin(t*(.22+j*.03));left+=env*amount*np.sin(2*np.pi*note*pitch*harmonic*t+drift)
    right+=env*amount*np.sin(2*np.pi*note*pitch*harmonic*t+drift+.08*(j+1))
 for index,start in enumerate(np.arange(2.1,seconds,motif_period)):
  note=[587.33,523.25,440,493.88,392,440,554.37,587.33][index%8];age=np.maximum(0,t-start)
  env=np.where(t>=start,(1-np.exp(-age/.025))*np.exp(-age/1.1),0)*.055
  tone=env*(np.sin(2*np.pi*note*pitch*t)+.16*np.sin(2*np.pi*note*pitch*2*t))
  left+=tone*(.8 if index%2 else 1);right+=tone*(1 if index%2 else .8)
 pulse=(.6+.4*np.cos(2*np.pi*t/2.4))*.025
 left+=pulse*np.sin(2*np.pi*98*t);right+=pulse*np.sin(2*np.pi*98*t+.06)
 edge=np.minimum(1,t/1.1)*np.minimum(1,(seconds-t)/1.5);audio=np.column_stack((left,right))*edge[:,None]
 audio*=.8/max(np.max(np.abs(audio)),1e-7)
 folder=Path(project)/'audio/music';folder.mkdir(parents=True,exist_ok=True);target=folder/'suspense-phone-v2.wav'
 wavfile.write(target,sr,(audio*32767).astype(np.int16))
 (folder/'SUSPENSE_V2_CREDITS.txt').write_text('Original suspense composition authored with engine/story_score.py. No external composition or film audio. CC0 1.0. Musical texture is separate from measured physical Foley.\n')
 print('ORIGINAL_MUSIC',target,seconds,'seconds');return target
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('project');p.add_argument('--seconds',type=float,default=60);a=p.parse_args();author(a.project,a.seconds)
