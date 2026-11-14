"""Detached custom-voice narration handoff using the cached Colab voice toolchain."""
import json
from pathlib import Path
from gpu_runtime import Client
def generate(job,cfg,profile):
 from video_engine import save_stage,write
 p=Path(job['project']);client=Client();root=client.api('GET','/engine/capabilities')['root'];remote=root+'/projects/'+p.name
 save_stage(job,'uploading_selected_voice_and_script')
 for name in ('script.json','narrator.json',profile['pack']):client.upload(p/name,remote+'/'+name)
 client.upload(Path(__file__).with_name('runtime_custom_narration.py'),root+'/runtime_custom_narration.py')
 code=f'''from pathlib import Path
import subprocess,json
root=Path({root!r});setup=root/'voice-lab/setup.json'
if not setup.is_file():raise RuntimeError('The cached GPU voice environment is missing in this runtime')
python=json.loads(setup.read_text())['python']
subprocess.run([python,'-u',str(root/'runtime_custom_narration.py'),{remote!r}],check=True)
'''
 remote_job=client.python(code,timeout=1800);job['colab_audio_job_id']=remote_job['job_id'];write(job['status_file'],job);save_stage(job,'generating_custom_narration_on_gpu')
 client.wait(remote_job['job_id'],job['log_file'])
 for name in ('script.json','data/narration.wav','data/lines.json','data/words.json','data/words.txt','data/narration-report.json'):client.download(remote+'/'+name,p/name)
