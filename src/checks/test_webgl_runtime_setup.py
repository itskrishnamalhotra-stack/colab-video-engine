import ast,base64,json,tempfile,unittest,zipfile,io
from pathlib import Path
from unittest.mock import patch
import runtime_setup

class WebGLOnlySetup(unittest.TestCase):
 def test_setup_caches_only_webgl_and_reports_matching_worker_defaults(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(runtime_setup,'webgl_setup',return_value={'node':'/node','chrome':'/chrome','ffmpeg':'/ffmpeg'}),patch.object(runtime_setup.subprocess,'run') as run:
   run.return_value.returncode=0;run.return_value.stdout='Tesla T4'
   result=runtime_setup.setup(directory)
   self.assertEqual(result['render_backend'],'webgl');self.assertEqual(result['default_render_workers'],1);self.assertEqual(result['max_render_workers'],8)
   self.assertFalse(any(key in result for key in ('blender','snow_asset')))
   self.assertEqual(json.loads((Path(directory)/'runtime-capabilities.json').read_text()),result)
 def test_published_notebook_has_no_retired_dependencies_or_saved_output(self):
  repo=Path(__file__).resolve().parents[1]/'github/colab-video-engine'
  nb=json.loads((repo/'GPU_Runtime.ipynb').read_text(encoding='utf-8'));code=''.join(next(c['source'] for c in nb['cells'] if c['cell_type']=='code'))
  self.assertFalse(any(c.get('outputs') for c in nb['cells']))
  tree=ast.parse(code);payload=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='PAYLOAD')
  with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload))) as z:
   self.assertIn('video_engine/runtime_webgl.py',z.namelist())
   self.assertFalse(any(any(k in name.lower() for k in ('blender','snow','asset_recipe')) for name in z.namelist()))
   self.assertNotIn('prepare_snow',z.read('video_engine/runtime_setup.py').decode())
if __name__=='__main__':unittest.main()
