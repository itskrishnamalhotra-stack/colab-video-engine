import json,tempfile,unittest
from pathlib import Path,PurePosixPath,PureWindowsPath
from unittest.mock import patch
from render_reuse import signature,visual_signature,remember,restore,path_order

class VerifiedReuse(unittest.TestCase):
 def test_mixed_case_visual_hash_order_matches_on_windows_and_linux(self):
  names=['fonts/a.ttf','fonts/Inter.ttf','src/Foo.js','src/actor.js','src/a/inner.js','src/a.js']
  for cls,base in ((PureWindowsPath,'E:/project'),(PurePosixPath,'/content/project')):
   root=cls(base);paths=[root/name for name in names]
   actual=[p.relative_to(root).as_posix() for p in sorted(paths,key=lambda p:path_order(p,root))]
   expected=[p.relative_to(PureWindowsPath('E:/project')).as_posix() for p in sorted(PureWindowsPath('E:/project')/name for name in names)]
   self.assertEqual(actual,expected)
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.p=Path(self.temp.name)
  (self.p/'renders').mkdir();(self.p/'data').mkdir();(self.p/'src').mkdir();(self.p/'src/story.js').write_text('original scene');(self.p/'script.json').write_text('{"title":"original"}');(self.p/'render_backend.json').write_text('{"backend":"webgl","workers":8}')
  source=self.p/'renders/verified.mp4';source.write_bytes(b'previously verified video')
  self.job={'project':str(self.p),'render_file':str(source),'state':'complete','render_inputs_sha256':signature(self.p)};remember(self.job)
 def test_unchanged_export_reused_and_worker_count_does_not_change_content(self):
  (self.p/'render_backend.json').write_text('{"backend":"webgl","workers":1}')
  job={**self.job,'state':'running','render_file':str(self.p/'renders/repeated.mp4')}
  with patch('video_engine.save_stage'):self.assertTrue(restore(job))
  self.assertEqual(Path(job['render_file']).read_bytes(),b'previously verified video')
 def test_scene_change_invalidates_reuse(self):
  (self.p/'src/story.js').write_text('new camera/action')
  self.assertFalse(restore(self.job))
 def test_sound_events_can_change_without_changing_visual_signature(self):
  plan=self.p/'action_plan.json';plan.write_text(json.dumps({'shots':[{'id':'one','line':0}],'events':[{'sample':'metalClick.ogg'}]}));before=visual_signature(self.p)
  plan.write_text(json.dumps({'shots':[{'id':'one','line':0}],'events':[{'sample':'bookFlip1.ogg'}]}));self.assertEqual(visual_signature(self.p),before)
  plan.write_text(json.dumps({'shots':[{'id':'one','line':1}],'events':[]}));self.assertNotEqual(visual_signature(self.p),before)
 def test_caption_timing_changes_invalidate_audio_only_reuse(self):
  before=visual_signature(self.p);(self.p/'data/words.json').write_text('[{"w":"hello","s":1,"e":2}]');self.assertNotEqual(visual_signature(self.p),before)
 def test_cloud_audio_execution_and_music_policy_do_not_change_pictures(self):
  before=visual_signature(self.p);(self.p/'render_backend.json').write_text('{"backend":"webgl","workers":8,"audio_execution":"colab"}')
  script=json.loads((self.p/'script.json').read_text());script.update(sound_design={'music':{'bed_rms_db':-24}});(self.p/'script.json').write_text(json.dumps(script))
  self.assertEqual(visual_signature(self.p),before)
 def test_corrupt_video_and_forced_render_are_not_reused(self):
  Path(self.job['render_file']).write_bytes(b'corrupt')
  self.assertFalse(restore(self.job))
  (self.p/'render_backend.json').write_text('{"backend":"webgl","force_render":true}')
  self.assertFalse(restore(self.job))
 def test_failed_job_or_source_changes_during_render_are_not_cached(self):
  cache=self.p/'data/render-cache.json';before=cache.read_bytes();job={**self.job,'state':'failed'};remember(job);self.assertEqual(cache.read_bytes(),before)
  (self.p/'src/story.js').write_text('edited while job was running');remember(self.job);self.assertEqual(cache.read_bytes(),before)

if __name__=='__main__':unittest.main()
