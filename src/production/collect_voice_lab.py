"""Retrieve an isolated voice experiment; never activate it as the narrator."""
import argparse,json
from pathlib import Path
from gpu_runtime import Client,digest
ROOT=Path(__file__).resolve().parents[1]
def collect(remote_root='/content/video_engine/voice-lab',target=None):
 client=Client();report=client.read_json(remote_root+'/outputs/result.json')
 if report.get('state')!='complete':raise ValueError('The voice experiment is not complete')
 target=Path(target or ROOT/'assets/voices/experimental/liam-inno-20261115').resolve();target.mkdir(parents=True,exist_ok=True)
 for item in report['items']:
  for key in ('npy','pt','audio'):
   source=item[key];dest=target/Path(source).name;client.download(source,dest)
   if digest(dest)!=item[key+'_sha256']:raise ValueError('Voice artifact hash mismatch: '+key)
   item['local_'+key]=str(dest)
  ref=item['reference'];source=ref['path'];dest=target/(item['name']+'-reference.mp3');client.download(source,dest);item['local_reference']=str(dest)
 for name in ('setup.json','long-references.json','references.json'):
  value=client.read_json(remote_root+'/'+name);(target/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
 (target/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({'state':'downloaded','production_voice_changed':False,'result':str(target/'result.json'),'samples':[item['local_audio'] for item in report['items']]},indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--remote-root',default='/content/video_engine/voice-lab');p.add_argument('--target');a=p.parse_args();collect(a.remote_root,a.target)
