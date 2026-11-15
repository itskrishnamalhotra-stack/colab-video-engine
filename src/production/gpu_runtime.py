"""Reusable authenticated runtime client. Credentials stay outside the repository."""
import argparse,base64,getpass,hashlib,io,json,os,re,subprocess,sys,time,uuid,zipfile
from pathlib import Path
from urllib.parse import urlparse
import requests
from webgl_partition import MAX_WEBGL_WORKERS

ROOT=Path(__file__).resolve().parents[1]
CONNECTION=Path.home()/'.colab-codex/config.json'

def digest(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

class Client:
 def __init__(self,connection=None):
  config=connection or json.loads(CONNECTION.read_text(encoding='utf-8-sig'))
  self.url=config['url'].rstrip('/');self.session=requests.Session()
  self.session.headers['Authorization']='Bearer '+config['token']
 def api(self,method,path,**kwargs):
  try:r=self.session.request(method,self.url+path,timeout=60,allow_redirects=False,**kwargs)
  except requests.RequestException:raise RuntimeError('The GPU runtime is unreachable. Reconnect using its current URL/token.') from None
  if r.status_code>=300:raise RuntimeError(f'Runtime API {path.split("?")[0]} returned HTTP {r.status_code}.')
  return r.json()
 def upload(self,source,target):
  source=Path(source);temporary=target+'.upload-'+uuid.uuid4().hex;offset=0
  with source.open('rb') as stream:
   while True:
    data=stream.read(3000000)
    if not data and offset:break
    response=self.api('POST','/files/write_chunk',json={'path':temporary,'offset':offset,'content_base64':base64.b64encode(data).decode()})
    offset=response['next_offset']
    if not data:break
  return self.api('POST','/files/commit',json={'temporary':temporary,'path':target,'size':source.stat().st_size,'sha256':digest(source)})
 def download(self,source,target,on_progress=None):
  info=self.api('GET','/files/stat',params={'path':source});target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
  temporary=target.with_name(target.name+'.partial');offset=0
  with temporary.open('wb') as stream:
   while offset<info['size_bytes']:
    data=self.api('GET','/files/read_chunk',params={'path':source,'offset':offset})
    block=base64.b64decode(data['content_base64'])
    if not block:raise RuntimeError('The runtime returned an incomplete download.')
    stream.write(block);offset=data['next_offset']
    if on_progress:on_progress({'stage':'downloading','downloaded_bytes':offset,'download_total_bytes':info['size_bytes']})
  if temporary.stat().st_size!=info['size_bytes'] or digest(temporary)!=info['sha256']:raise RuntimeError('Downloaded file failed its hash/size verification.')
  temporary.replace(target);return target
 def python(self,code,timeout=7200,cwd='/content'):
  return self.api('POST','/jobs/python',json={'code':code,'cwd':cwd,'timeout_seconds':timeout})
 def wait(self,identifier,log=None,on_progress=None):
  offset=0
  while True:
   result=self.api('GET',f'/jobs/{identifier}/output',params={'offset':offset,'limit':160000})
   if on_progress:on_progress(result['job'].get('progress') or {'stage':result['job']['status']})
   if result['text'] and log:
    with Path(log).open('a',encoding='utf-8') as stream:stream.write(result['text'])
   offset=result['next_offset']
   if result.get('has_more'):continue
   if result['job']['status']!='running':
    if result['job'].get('exit_code')!=0:raise RuntimeError('The runtime job failed. See its downloaded log for the native error.')
    return result
   time.sleep(3)
 def read_json(self,path):
  result=self.api('GET','/files/read',params={'path':path})
  return json.loads(base64.b64decode(result['content_base64']))

def project_bundle(project):
 project=Path(project).resolve()
 if not re.fullmatch(r'[A-Za-z0-9_-]+',project.name):raise ValueError('Project names may contain letters, digits, dashes and underscores.')
 allowed={'.py','.json','.txt','.js','.mjs','.html','.css','.wav','.ass','.ttf','.otf','.png','.jpg','.jpeg','.webp','.glb','.gltf','.bin'}
 files=[p for p in project.iterdir() if p.is_file() and p.suffix in ('.py','.json','.txt','.html','.js','.mjs','.css') and not p.name.startswith('.')]
 for folder in ('data','fonts','tools','src','assets','vendor'):
  files += [p for p in (project/folder).rglob('*') if p.is_file() and p.suffix.lower() in allowed and not any(n in p.parts for n in ('node_modules','__pycache__','.venv'))]
 files=sorted(set(files));fingerprint=hashlib.sha256()
 backend=project/'render_backend.json'
 if backend.is_file() and json.loads(backend.read_text()).get('backend')=='webgl':
  files=[p for p in files if p.relative_to(project).as_posix() not in ('data/narration.wav','data/narration-clean.wav','data/render-cache.json','data/sound-report.json')]
 folder=ROOT/'engine/runtime-uploads';folder.mkdir(exist_ok=True)
 archive=folder/(project.name+'.zip')
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as bundle:
  for path in files:
   relative=path.relative_to(project).as_posix();fingerprint.update((relative+'\0'+digest(path)+'\n').encode())
   bundle.write(path,'projects/'+project.name+'/'+relative)
 return archive,fingerprint.hexdigest()

def start_project(client,project,task='render',first=1,last=None,renderer='eevee',workers=None,request_id=None):
 project=Path(project).resolve()
 backend_file=project/'render_backend.json'
 webgl=backend_file.is_file() and json.loads(backend_file.read_text()).get('backend')=='webgl'
 if not webgl:raise ValueError('Only the illustrated WebGL production pipeline is enabled. Blender is permanently retired by the user.')
 if webgl:
  from install_webgl_kit import validate
  validate(project,production=True)
  workers=workers if workers is not None else json.loads(backend_file.read_text()).get('workers',2)
  if workers not in range(1,MAX_WEBGL_WORKERS+1):raise ValueError(f'WebGL supports one to {MAX_WEBGL_WORKERS} persistent browser workers.')
  if task not in ('build','render'):raise ValueError('Use --task build for a WebGL functional check, or render for the video.')
 if workers is None:
  settings=ROOT/'engine/video_defaults.json'
  workers=json.loads(settings.read_text()).get('gpu_workers',4) if settings.is_file() else 4
 limit=MAX_WEBGL_WORKERS if webgl else 4
 if workers not in range(1,limit+1):raise ValueError(f'Choose between 1 and {limit} workers for this backend.')
 if task=='render':
  for name in ('mix.wav','lines.json'):
   if not (project/'data'/name).is_file():raise FileNotFoundError('Prepare the narration/soundtrack before rendering: data/'+name)
  if (project/'data/words.json').is_file():
   from word_captions import make_captions
   make_captions(project)
  if not (project/'data/captions.ass').is_file():raise FileNotFoundError('The full render requires word captions or prepared data/captions.ass.')
 archive,fingerprint=project_bundle(project)
 capabilities=client.api('GET','/engine/capabilities');remote_root=capabilities.get('root')
 if not remote_root or (not webgl and not capabilities.get('blender')):raise RuntimeError('Run the reusable runtime notebook Setup cell first.')
 if webgl:
  for module in ('runtime_webgl.py','runtime_setup.py','runtime_webgl_setup.py','webgl_graphics_environment.py','webgl_partition.py','runtime_memory.py','runtime_progress.py','frame_cache.py','video_format.py','webgl_finalize.py'):
   client.upload(ROOT/'engine'/module,remote_root+'/'+module)
 identifier=request_id or uuid.uuid4().hex;remote_zip=remote_root+'/uploads/'+identifier+'.zip'
 client.upload(archive,remote_zip)
 code=f'''from pathlib import Path
import hashlib,zipfile,fcntl
source=Path({remote_zip!r});root=Path({remote_root!r}).resolve();project=root/'projects'/{project.name!r}
project.mkdir(parents=True,exist_ok=True)
lock=(project/'.runtime-job.lock').open('a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise RuntimeError('Project has an active GPU job; upload to a new project name or wait for it to finish.')
assert hashlib.file_digest(source.open('rb'),'sha256').hexdigest()=={digest(archive)!r},'Uploaded package hash mismatch'
with zipfile.ZipFile(source) as archive:
 for name in archive.namelist():
  if not (root/name).resolve().is_relative_to(project.resolve()):raise ValueError('Project archive escapes its project directory')
 archive.extractall(root)
(project/'.source-package.sha256').write_text({fingerprint!r})
print('PROJECT_INSTALLED',project.name,flush=True)
'''
 installed=client.python(code)
 bridge_dir=client.api('GET','/status')['bridge_dir']
 argv=[sys.executable,remote_root+'/runtime_project.py','--root',remote_root,'--project',project.name,'--task',task,'--request-id',identifier,'--renderer',renderer,'--workers',str(workers),'--first',str(first)]
 if webgl:argv=[sys.executable,remote_root+'/runtime_webgl.py','--root',remote_root,'--project',project.name,'--task',task,'--request-id',identifier,'--workers',str(workers)]
 # Use the remote Python, not this machine's Windows executable path.
 argv[0]='REMOTE_PYTHON'
 if last is not None:argv+=['--last',str(last)]
 code=f'''from pathlib import Path
import json,time,subprocess,sys
state=Path({bridge_dir!r})/'jobs'/{installed['job_id']!r}/'state.json'
while True:
 data=json.loads(state.read_text())
 if data['status']!='running':break
 time.sleep(.3)
assert data['status']=='succeeded','Project upload/extraction failed'
argv={argv!r};argv[0]=sys.executable
subprocess.run(argv,check=True)
'''
 timeout=json.loads(backend_file.read_text()).get('job_timeout_seconds',7200) if webgl else 7200
 job=client.python(code,timeout=timeout)
 return {'job_id':job['job_id'],'request_id':identifier,'project':project.name,'task':task,'workers':workers,'result_path':remote_root+'/results/'+identifier+'.json'}

def connect():
 url=input('Runtime URL: ').strip().rstrip('/');parsed=urlparse(url)
 if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('Use the HTTPS URL printed by the runtime notebook.')
 token=getpass.getpass('Private token (hidden): ').strip()
 if len(token)<32:raise ValueError('The token is missing or too short.')
 config={'url':url,'token':token};client=Client(config);client.api('GET','/health')
 CONNECTION.parent.mkdir(exist_ok=True);temporary=CONNECTION.with_suffix('.tmp')
 temporary.write_text(json.dumps(config),encoding='utf-8')
 if os.name=='nt':
  sys.path.insert(0,str(ROOT/'colab-codex-bridge'));from setup_codex import protect_windows
  protect_windows(temporary)
 else:temporary.chmod(0o600)
 temporary.replace(CONNECTION)
 print('Connected. Credentials saved privately.');print(json.dumps(client.api('GET','/engine/capabilities'),indent=2))

def watch(metadata):
 folder=ROOT/'engine/jobs'/('runtime-'+metadata['request_id']);folder.mkdir(parents=True,exist_ok=True)
 state=folder/'status.json';log=folder/'render.log'
 latest={}
 def update(progress):
  latest.update(progress)
  temporary=state.with_suffix('.tmp');temporary.write_text(json.dumps({**metadata,'state':'running','progress':latest},indent=2));temporary.replace(state)
 try:
  update({'stage':'connecting'});client=Client();client.wait(metadata['job_id'],log,on_progress=update)
  result=client.read_json(metadata['result_path']);outputs=[]
  for item in result['outputs']:
   source=Path(item['path']);target=ROOT/'outputs'/(metadata['project']+'-'+metadata['request_id'][:8]+'-'+source.name)
   client.download(item['path'],target,on_progress=update)
   if digest(target)!=item['sha256']:raise RuntimeError('Result manifest hash differs from the downloaded output.')
   outputs.append(str(target))
   if item['kind']=='video' and os.name=='nt':os.startfile(target)
  state.write_text(json.dumps({**metadata,'state':'complete','progress':{**latest,'stage':'complete'},'outputs':outputs},indent=2))
 except Exception as error:
  report=folder/'ERROR.txt';report.write_text(str(error)+'\nFull log: '+str(log),encoding='utf-8')
  state.write_text(json.dumps({**metadata,'state':'failed','progress':latest,'error':str(error)},indent=2))
  if os.name=='nt':os.startfile(report)

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('connect');sub.add_parser('status')
 for action in ('upload','download'):
  a=sub.add_parser(action);a.add_argument('source');a.add_argument('target')
 for action in ('python','shell'):
  a=sub.add_parser(action);a.add_argument('file')
 a=sub.add_parser('job');a.add_argument('id');a.add_argument('--offset',type=int,default=0)
 a=sub.add_parser('cancel');a.add_argument('id')
 a=sub.add_parser('project');a.add_argument('project');a.add_argument('--task',choices=['build','probe','render'],default='render');a.add_argument('--first',type=int,default=1);a.add_argument('--last',type=int);a.add_argument('--renderer',choices=['eevee','cycles'],default='eevee');a.add_argument('--workers',type=int,choices=range(1,MAX_WEBGL_WORKERS+1));a.add_argument('--no-watch',action='store_true')
 a=sub.add_parser('watch');a.add_argument('metadata')
 sub.add_parser('terminal-start')
 for action in ('terminal-read','terminal-write','terminal-close'):
  a=sub.add_parser(action);a.add_argument('id')
  if action=='terminal-read':a.add_argument('--offset',type=int,default=0)
  if action=='terminal-write':a.add_argument('text');a.add_argument('--raw',action='store_true')
 a=p.parse_args()
 if a.command=='connect':return connect()
 if a.command=='watch':return watch(json.loads(Path(a.metadata).read_text()))
 c=Client()
 if a.command=='status':result=c.api('GET','/status');result['engine']=c.api('GET','/engine/capabilities')
 elif a.command=='upload':result=c.upload(a.source,a.target)
 elif a.command=='download':result={'downloaded':str(c.download(a.source,a.target))}
 elif a.command=='python':result=c.python(Path(a.file).read_text(encoding='utf-8-sig'))
 elif a.command=='shell':result=c.api('POST','/jobs/command',json={'command':Path(a.file).read_text(encoding='utf-8-sig'),'cwd':'/content','timeout_seconds':7200})
 elif a.command=='job':result=c.api('GET',f'/jobs/{a.id}/output',params={'offset':a.offset,'limit':160000})
 elif a.command=='cancel':result=c.api('POST',f'/jobs/{a.id}/cancel')
 elif a.command=='terminal-start':result=c.api('POST','/terminals')
 elif a.command=='terminal-read':result=c.api('GET',f'/terminals/{a.id}/read',params={'offset':a.offset})
 elif a.command=='terminal-write':result=c.api('POST',f'/terminals/{a.id}/write',json={'text':a.text if a.raw or a.text.endswith('\n') else a.text+'\n'})
 elif a.command=='terminal-close':result=c.api('POST',f'/terminals/{a.id}/close')
 elif a.command=='project':
  result=start_project(c,a.project,a.task,a.first,a.last,a.renderer,a.workers)
  if not a.no_watch:
   folder=ROOT/'engine/jobs'/('runtime-'+result['request_id']);folder.mkdir(parents=True,exist_ok=True);metadata=folder/'request.json';metadata.write_text(json.dumps(result))
   # Reuse this working interpreter; the speech-only venv does not include requests.
   with (folder/'watcher-launch.log').open('ab',buffering=0) as output:
    subprocess.Popen([sys.executable,str(Path(__file__)),'watch',str(metadata)],stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),start_new_session=os.name!='nt')
   result['local_status']=str(folder/'status.json')
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
