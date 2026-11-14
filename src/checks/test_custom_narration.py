import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from narration_profile import resolve
from runtime_custom_narration import map_native_words,fit_outro
import video_engine

class NativeWordTiming(unittest.TestCase):
 def test_small_overflow_only_shortens_silent_outro(self):
  outro,removed=fit_outro(60.045,60,.5);self.assertAlmostEqual(outro,.455);self.assertAlmostEqual(removed,.045)
  self.assertEqual(fit_outro(61,60,.5),(.5,0.0));self.assertEqual(fit_outro(59,60,.5),(.5,0))
 def test_contractions_join_native_tokens_without_estimating_timestamps(self):
  tokens=[dict(text='Alex',s=0,e=.3),dict(text='had',s=.3,e=.45),dict(text="n't",s=.45,e=.6),dict(text='spoken',s=.6,e=1)]
  result=map_native_words("Alex hadn't spoken.",tokens,2,10,12)
  self.assertEqual(result,[dict(w='Alex',line=2,s=10,e=10.3),dict(w="hadn't",line=2,s=10.3,e=10.6),dict(w='spoken.',line=2,s=10.6,e=11)])
 def test_text_mismatch_and_missing_native_clock_fail(self):
  for tokens in ([dict(text='wrong',s=0,e=1)],[dict(text='hello',s=None,e=None)]):
   with self.assertRaises(ValueError):map_native_words('hello',tokens,0,0,1)

class CustomNarrator(unittest.TestCase):
 def test_override_is_project_scoped_and_pack_hash_is_checked(self):
  cfg=dict(voice='af_heart',speed=1.0)
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);self.assertEqual(resolve(p,cfg)['voice'],'af_heart');pack=p/'pack.npy';pack.write_bytes(b'approved pack')
   spec=dict(engine='kokoro-custom',execution='colab',voice='am_liam_clean_1',pack='pack.npy',pack_sha256=hashlib.sha256(pack.read_bytes()).hexdigest())
   (p/'narrator.json').write_text(json.dumps(spec));self.assertEqual(resolve(p,cfg)['voice'],'am_liam_clean_1');self.assertEqual(cfg['voice'],'af_heart')
   pack.write_bytes(b'unapproved other pack')
   with self.assertRaisesRegex(ValueError,'differs'):resolve(p,cfg)
 def test_cloud_audio_job_uses_the_host_orchestrator(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory)/'project';p.mkdir();(p/'script.json').write_text('{}');(p/'narrator.json').write_text('{}');cfg=video_engine.settings();cfg['output_root']=str(Path(directory)/'outputs')
   with patch.object(video_engine,'JOBS',Path(directory)/'jobs'),patch.object(video_engine,'settings',return_value=cfg),patch.object(video_engine.subprocess,'Popen') as launch:
    launch.return_value.pid=123;video_engine.start_job('audio',p);self.assertEqual(launch.call_args.args[0][0],sys.executable)
if __name__=='__main__':unittest.main()
