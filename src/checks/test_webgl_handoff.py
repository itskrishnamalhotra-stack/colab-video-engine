"""Ensure the cloud WebGL path includes its assets and never invokes Blender."""
import json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import gpu_runtime
import video_engine

class WebGLHandoff(unittest.TestCase):
 def test_standard_cloud_render_worker_uses_http_capable_host_interpreter(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);p=root/'project';p.mkdir();(p/'script.json').write_text('{}');(p/'tools').mkdir();(p/'tools/capture.mjs').write_text('')
   (p/'render_backend.json').write_text('{"backend":"webgl","execution":"colab"}')
   cfg=video_engine.settings();cfg.update(output_root=str(root/'outputs'))
   with patch.object(video_engine,'JOBS',root/'jobs'),patch.object(video_engine,'settings',return_value=cfg),patch.object(video_engine.subprocess,'Popen') as launch:
    launch.return_value.pid=123;video_engine.start_job('render',p)
    self.assertEqual(launch.call_args.args[0][0],sys.executable)
 def test_package_contains_html_vendor_and_gltf_binary_but_no_render_or_reference(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(gpu_runtime,'ROOT',Path(directory)):
   root=Path(directory);(root/'engine').mkdir();p=root/'webgl-test';p.mkdir()
   for name in ('index.html','vendor/three.module.js','assets/actor.gltf','assets/actor.bin','renders/old.mp4','reference.mp4'):
    f=p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'test')
   archive,_=gpu_runtime.project_bundle(p)
   with zipfile.ZipFile(archive) as z:
    names=z.namelist()
    for expected in ('index.html','vendor/three.module.js','assets/actor.gltf','assets/actor.bin'):self.assertIn('projects/webgl-test/'+expected,names)
    self.assertFalse(any(name.endswith('.mp4') for name in names))
 def test_webgl_dispatch_does_not_require_or_launch_blender(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(gpu_runtime,'ROOT',Path(directory)):
   root=Path(directory);(root/'engine').mkdir();p=root/'webgl-test';p.mkdir()
   (p/'render_backend.json').write_text('{"backend":"webgl"}')
   for name in ('runtime_webgl.py','runtime_webgl_setup.py','webgl_partition.py','runtime_memory.py','runtime_progress.py','frame_cache.py'):(root/'engine'/name).write_text('')
   class FakeClient:
    def __init__(self):self.codes=[];self.uploaded=[]
    def api(self,method,path):return {'root':'/content/video_engine'} if path=='/engine/capabilities' else {'bridge_dir':'/content/bridge'}
    def upload(self,source,target):self.uploaded.append(target)
    def python(self,code,timeout=7200):self.codes.append(code);return {'job_id':str(len(self.codes))}
   c=FakeClient();result=gpu_runtime.start_project(c,p,task='build')
   self.assertIn('runtime_webgl.py',c.codes[-1]);self.assertNotIn('runtime_project.py',c.codes[-1])
   self.assertEqual(result['workers'],2);self.assertTrue(any(p.endswith('runtime_webgl_setup.py') for p in c.uploaded))
   self.assertTrue(any(p.endswith('runtime_memory.py') for p in c.uploaded))
   self.assertTrue(any(p.endswith('runtime_progress.py') for p in c.uploaded))
   self.assertTrue(any(p.endswith('frame_cache.py') for p in c.uploaded))
   self.assertTrue(any(p.endswith('webgl_finalize.py') for p in c.uploaded))
   four=gpu_runtime.start_project(c,p,task='build',workers=4)
   self.assertEqual(four['workers'],4);self.assertIn("'--workers', '4'",c.codes[-1])
   eight=gpu_runtime.start_project(c,p,task='build',workers=8)
   self.assertEqual(eight['workers'],8);self.assertIn("'--workers', '8'",c.codes[-1])
   with self.assertRaises(ValueError):gpu_runtime.start_project(c,p,task='build',workers=9)
   (p/'render_backend.json').write_text('{"backend":"blender"}')
   with self.assertRaisesRegex(ValueError,'permanently retired'):gpu_runtime.start_project(c,p,task='build',workers=8)

if __name__=='__main__':unittest.main(verbosity=2)
