import json,tempfile,unittest
from pathlib import Path
from runtime_voice_tune import load_references
class ReferencePolicy(unittest.TestCase):
 def test_default_does_not_pick_longer_but_dramatic_audio(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);(p/'long-references.json').write_text('[{"name":"panic-acting"}]');(p/'references.json').write_text('[{"name":"official-liam"},{"name":"other"}]')
   self.assertEqual(load_references(p),[{'name':'official-liam'}])
 def test_missing_explicit_manifest_fails_without_a_fallback(self):
  with tempfile.TemporaryDirectory() as directory:
   with self.assertRaises(ValueError):load_references(directory,'missing.json')
 def test_explicitly_screened_references_are_preserved(self):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);refs=[{'name':'normal-speech','screened_delivery':'conversational'}];(p/'approved-references.json').write_text(json.dumps(refs));self.assertEqual(load_references(p),refs)
if __name__=='__main__':unittest.main()
