import json,tempfile,unittest
from pathlib import Path
from cloud_soundtrack import soundtrack_inputs
class CloudSoundtrackInputs(unittest.TestCase):
 def test_sample_audio_is_uploaded_even_when_the_render_package_omits_ogg(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory)
   for name in ('script.json','action_plan.json','action_probe.json','data/narration.wav','data/lines.json','data/words.json','data/cues.json','data/animation-events.json','audio/music/score.wav','audio/foley/step.ogg'):
    f=p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'input')
   (p/'script.json').write_text(json.dumps({'music':'audio/music/score.wav'}));(p/'data/cues.json').write_text(json.dumps({'cues':[{'sample':'step.ogg'},{'sample':'step.ogg'}]}))
   names=soundtrack_inputs(p);self.assertEqual(names.count('audio/foley/step.ogg'),1)
   (p/'audio/foley/step.ogg').unlink()
   with self.assertRaisesRegex(ValueError,'Missing/invalid soundtrack input'):soundtrack_inputs(p)
if __name__=='__main__':unittest.main()
