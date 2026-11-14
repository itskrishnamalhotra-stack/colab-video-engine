"""Detached source upload/build/render/download through the reusable GPU runtime."""
import json
from pathlib import Path
from gpu_runtime import Client,start_project,digest

def render_remote(job,cfg):
 from video_engine import save_stage,write
 client=Client();capabilities=client.api('GET','/engine/capabilities')
 project=Path(job['project']);backend=json.loads((project/'render_backend.json').read_text())
 if not capabilities.get('root') or backend.get('backend')!='webgl':raise RuntimeError('Start GPU_Runtime.ipynb and wait for VIDEO TOOLS READY before submitting a video.')
 save_stage(job,'uploading_gpu_project')
 remote=start_project(client,project,task='render',workers=backend.get('workers',cfg.get('gpu_workers',4)),request_id=job['id'])
 job['colab_job_id']=remote['job_id'];job['runtime_result_path']=remote['result_path'];write(job['status_file'],job)
 save_stage(job,'building_and_rendering_on_gpu_runtime')
 def progress(value):
  job['progress']=value;write(job['status_file'],job)
 client.wait(remote['job_id'],job['log_file'],on_progress=progress)
 result=client.read_json(remote['result_path'])
 output=next((item for item in result['outputs'] if item['kind']=='video'),None)
 if output is None:raise RuntimeError('The runtime did not return a completed video.')
 save_stage(job,'downloading_gpu_video')
 target=client.download(output['path'],job['render_file'],on_progress=progress)
 if digest(target)!=output['sha256']:raise ValueError('Downloaded video differs from the remote result hash.')
