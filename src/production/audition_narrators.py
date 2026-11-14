"""Generate standalone narration comparisons without editing any video project."""
import argparse,json,os
from pathlib import Path
import numpy as np
from scipy.io import wavfile
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--voices',nargs='+',default=['am_fenrir','am_liam']);a=p.parse_args()
 from kokoro_onnx import Kokoro
 home=Path(os.environ.get('FACELESS_HOME',Path.home()/'.faceless-shorts'))/'kokoro';out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 model=Kokoro(str(home/'kokoro-v1.0.onnx'),str(home/'voices-v1.0.bin'))
 text="The radio spoke in his voice. But the battery was on the table. Then someone whispered, don't turn around."
 items=[]
 for voice in a.voices:
  audio,sr=model.create(text,voice=voice,speed=1.0,lang='en-us');audio=np.asarray(audio);audio*=.85/max(float(np.abs(audio).max()),1e-7)
  target=out/(voice+'.wav');wavfile.write(target,sr,(audio*32767).astype(np.int16));items.append(dict(voice=voice,path=str(target.resolve()),seconds=round(len(audio)/sr,2),text=text,speed=1.0));print('VOICE_SAMPLE_READY',voice,str(target),flush=True)
 (out/'local-samples.json').write_text(json.dumps(items,indent=2))
if __name__=='__main__':main()
