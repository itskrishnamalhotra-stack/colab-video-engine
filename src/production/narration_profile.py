"""Pin the selected default voice into new projects; preserve existing narrators."""
import hashlib,json,math,shutil
from pathlib import Path

def install_default(project,cfg):
 p=Path(project).resolve();default=cfg.get('default_narrator')
 if not default:return None
 if (p/'narrator.json').exists():raise ValueError('Project already has a selected narrator')
 spec=dict(default);source=Path(spec.pop('pack_source')).resolve()
 if spec.get('voice')!=cfg['voice']:raise ValueError('Default narrator identity differs from saved settings')
 if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=spec.get('pack_sha256'):raise ValueError('Approved default voice pack is missing or changed')
 pack=(p/spec['pack']).resolve()
 if not pack.is_relative_to(p):raise ValueError('Default narrator destination escapes its project')
 pack.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,pack)
 (p/'narrator.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
 return resolve(p,cfg)
def resolve(project,cfg):
 p=Path(project).resolve();path=p/'narrator.json'
 if not path.is_file():
  script=json.loads((p/'script.json').read_text(encoding='utf-8-sig')) if (p/'script.json').is_file() else {}
  voice=script.get('voice',cfg['voice'])
  if voice==cfg.get('default_narrator',{}).get('voice'):raise ValueError('Custom default voice requires a pinned project narrator.json; initialize the project voice first')
  return dict(voice=voice,speed=script.get('speed',cfg['speed']),custom=False)
 spec=json.loads(path.read_text());pack=(p/spec['pack']).resolve()
 if spec.get('engine')!='kokoro-custom' or spec.get('execution')!='colab':raise ValueError('Unsupported project narrator backend')
 if not pack.is_relative_to(p) or not pack.is_file():raise ValueError('Project voice pack is missing or outside its project')
 if hashlib.sha256(pack.read_bytes()).hexdigest()!=spec.get('pack_sha256'):raise ValueError('Custom voice pack differs from the selected narrator')
 speed=float(spec.get('speed',1));maximum=float(spec.get('maximum_speed',speed))
 if not math.isfinite(speed) or not speed>0 or not speed<=maximum<=1.2:raise ValueError('Invalid bounded narration speed')
 return {**spec,'pack_path':str(pack),'speed':speed,'maximum_speed':maximum,'custom':True}
