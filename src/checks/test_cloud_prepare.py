import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gpu_runtime import digest
import cloud_prepare

class PreparedSound(unittest.TestCase):
 def test_reuse_requires_unchanged_mix_report_inputs_and_measured_cues(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);data=p/'data';data.mkdir();(data/'mix.wav').write_bytes(b'verified master');(data/'sound-report.json').write_text('{}');(data/'cues.json').write_text('{"cues":[]}')
   receipt=dict(inputs_sha256='same',mix_sha256=digest(data/'mix.wav'),report_sha256=digest(data/'sound-report.json'))
   (data/'cloud-sound-prepared.json').write_text(json.dumps(receipt))
   with patch.object(cloud_prepare,'preparation_key',return_value='same'),patch('animation_events.verify_cues') as verify:
    self.assertEqual(cloud_prepare.prepared(p),receipt);verify.assert_called_once()
    verify.side_effect=ValueError('Stale contacts');self.assertIsNone(cloud_prepare.prepared(p));verify.side_effect=None
    (data/'mix.wav').write_bytes(b'edited master');self.assertIsNone(cloud_prepare.prepared(p))
   with patch.object(cloud_prepare,'preparation_key',return_value='changed'):self.assertIsNone(cloud_prepare.prepared(p))
 def test_verified_preparation_does_not_upload_or_mix_twice(self):
  with patch('install_foley.install'),patch.object(cloud_prepare,'prepared',return_value={'verified':'ready'}),patch.object(cloud_prepare,'Client') as client,patch('video_engine.save_stage') as stage:
   result=cloud_prepare.prepare({'project':'some-project'},{});self.assertEqual(result,{'verified':'ready'});client.assert_not_called();stage.assert_called_once_with({'project':'some-project'},'reusing_verified_cloud_soundtrack')

if __name__=='__main__':unittest.main()
