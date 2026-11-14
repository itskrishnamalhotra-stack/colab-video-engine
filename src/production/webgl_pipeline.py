"""Keep the standard detached workflow while moving WebGL capture onto the GPU VM."""
from pathlib import Path
from runtime_bridge import render_remote

def prepare_audio(job,cfg,run_command):
 project=Path(job['project']);cue_script=project/'prepare_cues.py'
 if (project/'visual_profile.json').is_file() and not (project/'action_plan.json').is_file():
  raise ValueError('Reference-cartoon projects require action_plan.json with authored clean contact Foley; do not reuse the legacy procedural soundtrack.')
 if (project/'action_plan.json').is_file():
  from install_foley import install
  install(project)
  engine=Path(__file__).resolve().parent
  run_command([cfg['python'],'-u',str(engine/'action_sound.py'),str(project)],job,cfg,'exporting_action_foley')
  run_command([cfg['python'],'-u',str(engine/'foley_mix.py'),str(project)],job,cfg,'mixing_sample_soundtrack')
 else:
  if not cue_script.is_file():raise FileNotFoundError('Cloud WebGL projects require prepare_cues.py or action_plan.json.')
  run_command([cfg['python'],'-u',str(cue_script)],job,cfg,'exporting_sound_cues')
  run_command([cfg['python'],'-u',str(project/'tools/mix.py'),str(project)],job,cfg,'mixing_soundtrack')

def render(job,cfg,run_command):
 from render_reuse import restore
 if restore(job):return
 prepare_audio(job,cfg,run_command)
 render_remote(job,cfg)
