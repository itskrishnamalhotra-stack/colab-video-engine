"""Update a verified project's soundtrack while copying its video stream exactly."""
import json,subprocess
from pathlib import Path
from render_reuse import digest,signature,visual_signature

def video_digest(path,cfg):
 from video_engine import child_flags
 ffmpeg=Path(cfg['ffmpeg_bin'])/'ffmpeg.exe'
 return subprocess.check_output([str(ffmpeg),'-v','error','-i',str(path),'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-'],text=True,timeout=120,**child_flags()).strip()

def remux(job,cfg,run_command):
 from video_engine import verify_video,save_stage
 from webgl_pipeline import prepare_audio
 project=Path(job['project']);source=Path(job['source_video']);cache=json.loads((project/'data/render-cache.json').read_text())
 save_stage(job,'checking_audio_only_source')
 if not cache.get('verified') or digest(source)!=cache.get('video_sha256'):raise ValueError('Audio-only source must match this project\'s verified video.')
 expected=cache.get('visual_inputs_sha256')
 if not expected or visual_signature(project)!=expected:raise ValueError('Visuals or narration timing changed; an audio-only update cannot preserve the requested new visuals.')
 verify_video(source,project,cfg)
 backend=json.loads((project/'render_backend.json').read_text())
 if backend.get('audio_execution')=='colab':
  from cloud_soundtrack import remux_remote
  remux_remote(job,cfg,source,cache)
  original=video_digest(source,cfg);updated=video_digest(Path(job['render_file']),cfg)
  if original!=updated:raise ValueError('Cloud soundtrack revision changed the encoded video stream')
  job.update(video_stream_unchanged=True,video_stream_sha256=updated,audio_only=True)
  return
 prepare_audio(job,cfg,run_command)
 if visual_signature(project)!=expected:raise ValueError('Audio preparation changed the shot timing; use a full render.')
 job['render_inputs_sha256']=signature(project)
 target=Path(job['render_file']);target.parent.mkdir(parents=True,exist_ok=True)
 ffmpeg=Path(cfg['ffmpeg_bin'])/'ffmpeg.exe'
 from webgl_finalize import probe,soundtrack_clock
 info=probe(source,str(Path(cfg['ffmpeg_bin'])/'ffprobe.exe'))
 frames=int(next(s for s in info['streams'] if s['codec_type']=='video').get('nb_frames',0))
 run_command([str(ffmpeg),'-v','error','-y','-i',str(source),'-i',str(project/'data/mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',soundtrack_clock(frames),'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(target)],job,cfg,'replacing_audio_without_video_render')
 save_stage(job,'verifying_unchanged_video_stream')
 original=video_digest(source,cfg);updated=video_digest(target,cfg)
 if original!=updated:raise ValueError('Audio update unexpectedly changed the encoded video stream.')
 job.update(video_stream_unchanged=True,video_stream_sha256=updated,audio_only=True)
 with Path(job['log_file']).open('a',encoding='utf-8') as log:log.write('\nVERIFIED_UNCHANGED_VIDEO_STREAM '+updated+'\n')
