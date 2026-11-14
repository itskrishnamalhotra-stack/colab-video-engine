"""Project-specific approved narrator overrides; global defaults stay unchanged."""
import hashlib,json,math
from pathlib import Path
def resolve(project,cfg):
 p=Path(project).resolve();path=p/'narrator.json'
 if not path.is_file():return dict(voice=cfg['voice'],speed=cfg['speed'],custom=False)
 spec=json.loads(path.read_text());pack=(p/spec['pack']).resolve()
 if spec.get('engine')!='kokoro-custom' or spec.get('execution')!='colab':raise ValueError('Unsupported project narrator backend')
 if not pack.is_relative_to(p) or not pack.is_file():raise ValueError('Project voice pack is missing or outside its project')
 if hashlib.sha256(pack.read_bytes()).hexdigest()!=spec.get('pack_sha256'):raise ValueError('Custom voice pack differs from the selected narrator')
 speed=float(spec.get('speed',1));maximum=float(spec.get('maximum_speed',speed))
 if not math.isfinite(speed) or not speed>0 or not speed<=maximum<=1.2:raise ValueError('Invalid bounded narration speed')
 return {**spec,'pack_path':str(pack),'speed':speed,'maximum_speed':maximum,'custom':True}
