"""Install a pinned copy of shared, regression-checked WebGL production components."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent;KIT=ROOT/'webgl_kit';VERSION='2.1.0'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def install(project,activate=False,shots='shots.js'):
 project=Path(project).resolve();target=project/'src/studio';target.mkdir(parents=True,exist_ok=True);files={}
 for source in KIT.iterdir():
  if source.suffix in ('.js','.mjs') and source.name!='main.js':
   if source.name=='frame_reader.mjs':source=ROOT/'frame_reader.mjs'
   output=target/source.name;shutil.copy2(source,output);files[output.relative_to(project).as_posix()]=digest(output)
 if activate:
  script=json.loads((project/'script.json').read_text()) if (project/'script.json').is_file() else {}
  directional=script.get('visual_style')=='reference-cartoon-directional-v2'
  profile=ROOT/'visual_profiles/reference_directional_v2.json' if directional else ROOT/'visual_profile.json'
  shutil.copy2(profile,project/'visual_profile.json');files['visual_profile.json']=digest(project/'visual_profile.json')
  if not shots.endswith('.js') or '/' in shots or '\\' in shots:raise ValueError('Use a shot module filename inside src/.')
  text=(KIT/'main.js').read_text().replace("'./shots.js'",repr('./'+shots))
  (project/'src/main.js').write_text(text,encoding='utf-8')
  files['src/main.js']=digest(project/'src/main.js')
  script=json.loads((project/'script.json').read_text()) if (project/'script.json').is_file() else {}
  from video_format import format_dimensions
  width,height=format_dimensions(script.get('format','portrait'))
  format_file=project/'src/core/video_format.js'
  format_file.parent.mkdir(parents=True,exist_ok=True)
  format_file.write_text("import {resolveVideoFormat} from '../studio/video_format.mjs';\nexport const FORMAT=resolveVideoFormat("+json.dumps(script.get('format','portrait'))+");\n",encoding='utf-8')
  files['src/core/video_format.js']=digest(format_file)
  lib=project/'src/core/lib.js'
  text=lib.read_text(encoding='utf-8') if lib.is_file() else ''
  text=text.replace('export const W = 1080, H = 1920, FPS = 30;',"import {FORMAT} from './video_format.js';\nexport const W=FORMAT.width,H=FORMAT.height,FPS=30;")
  if lib.is_file():lib.write_text(text,encoding='utf-8');files['src/core/lib.js']=digest(lib)
  captions=project/'src/core/captions.js';text=captions.read_text(encoding='utf-8') if captions.is_file() else ''
  if "import {FORMAT}" not in text:text="import {FORMAT} from './video_format.js';\n"+text
  text=text.replace('export const CAP = { y: 1340, size: 88, maxW: 960 };','export const CAP = {y:FORMAT.caption.y,size:FORMAT.caption.size,maxW:FORMAT.caption.maxW};')
  text=text.replace('x = 540','x = FORMAT.width / 2').replace('c.text, 540, CAP.y','c.text, FORMAT.width / 2, CAP.y')
  if captions.is_file():captions.write_text(text,encoding='utf-8');files['src/core/captions.js']=digest(captions)
  index=project/'index.html';text=index.read_text(encoding='utf-8') if index.is_file() else ''
  import re
  text=re.sub(r'(<canvas id="(?:cv|gl)" width=")\d+(" height=")\d+',lambda m:m[1]+str(width)+m[2]+str(height),text)
  if index.is_file():index.write_text(text,encoding='utf-8');files['index.html']=digest(index)
  fast=script.get('capture',{}).get('scene_overlay')=='none'
  (project/'render_backend.json').write_text(json.dumps({'backend':'webgl','execution':'colab','workers':1 if fast else 2,'fps':30,'width':width,'height':height,'capture_query':'&res=1&aa=4&shadow=2048','capture_transport':'webcodecs' if fast else 'raw','video_encoder':'auto' if fast else 'libx264','job_timeout_seconds':7200},indent=2))
  (project/'tools').mkdir(exist_ok=True)
  for name in ('cloud_capture.mjs','capture_transport.mjs'):
   shutil.copy2(ROOT/name,project/'tools'/name);files['tools/'+name]=digest(project/'tools'/name)
 manifest={'version':VERSION,'character_style':'reference cartoon puppets','story_module':'src/'+shots if activate else None,'capture':'synchronized readback with blank-frame rejection','workers':1 if activate and fast else 2,'framing_required':activate,'files':files}
 (project/'webgl_kit.json').write_text(json.dumps(manifest,indent=2));return manifest

def validate(project,production=False):
 project=Path(project);path=project/'webgl_kit.json'
 if not path.exists():return None
 manifest=json.loads(path.read_text())
 for name,expected in manifest['files'].items():
  target=(project/name).resolve()
  if not target.is_relative_to(project.resolve()) or not target.is_file() or digest(target)!=expected:raise ValueError(f'Shared WebGL kit drift: {name}. Update the canonical kit and reinstall it instead of retaining an untracked repair.')
 if production and (project/'visual_profile.json').is_file():
  story=manifest.get('story_module')
  if not story:raise ValueError('The approved character profile requires a pinned story module.')
  source=(project/story).resolve()
  if not source.is_relative_to(project.resolve()) or not source.is_file():raise ValueError('Author the new story module before rendering.')
  text=source.read_text(encoding='utf-8')
  if any(name in text for name in ('core/toon.js','core/actor.js','FilmActor')):raise ValueError('Rejected/legacy character rig in story module. Use the approved studio/actor.js family.')
  profile=json.loads((project/'visual_profile.json').read_text())
  if profile.get('id')=='reference-cartoon-directional-v2' and any(name in text for name in ('rigged_actor','GLTFLoader','snow-portable')):raise ValueError('This correction test uses the normal illustrated WebGL characters, without Blender-derived assets.')
  if manifest.get('framing_required') and ('camera_framing.mjs' not in text or 'frameShot(' not in text):
   raise ValueError('Declare shot framing subjects and apply frameShot from studio/camera_framing.mjs before production upload.')
 return manifest['version']

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('project');p.add_argument('--activate',action='store_true');p.add_argument('--shots',default='shots.js');a=p.parse_args();print(json.dumps(install(a.project,a.activate,a.shots),indent=2))
