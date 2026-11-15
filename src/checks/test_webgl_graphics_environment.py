import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from webgl_graphics_environment import select_nvidia,capture_environment,SOFTWARE_FLAGS

class GraphicsSelection(unittest.TestCase):
 def test_installed_driver_without_system_vendor_registration_gets_private_manifest(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);driver=root/'driver/libEGL_nvidia.so.0';driver.parent.mkdir();driver.touch()
   with patch('webgl_graphics_environment.driver_candidates',return_value=[driver]),patch('webgl_graphics_environment.ctypes.CDLL'):
    selected=select_nvidia(root,{'LD_LIBRARY_PATH':str(driver.parent),'PRIVATE_TOKEN':'must-not-persist'})
   vendor=json.loads(Path(selected['__EGL_VENDOR_LIBRARY_FILENAMES']).read_text())
   self.assertEqual(vendor['ICD']['library_path'],str(driver.resolve()))
   self.assertEqual(selected['LD_LIBRARY_PATH'],str(driver.parent))
   self.assertNotIn('PRIVATE_TOKEN',(root/'gpu-environment.json').read_text())
 def test_missing_or_unloadable_driver_fails_before_browser_launch(self):
  with tempfile.TemporaryDirectory() as directory,patch('webgl_graphics_environment.driver_candidates',return_value=[Path('libEGL_nvidia.so.0')]),patch('webgl_graphics_environment.ctypes.CDLL',side_effect=OSError('absent')):
   with self.assertRaisesRegex(RuntimeError,'No loadable NVIDIA EGL'):select_nvidia(directory,{})
   self.assertFalse((Path(directory)/'gpu-environment.json').exists())
 def test_capture_removes_software_overrides_without_mutating_parent(self):
  base={name:'software' for name in SOFTWARE_FLAGS};base['OTHER']='retained';selected={'__EGL_VENDOR_LIBRARY_FILENAMES':'verified-nvidia.json'}
  child=capture_environment(base,selected)
  self.assertTrue(all(name not in child for name in SOFTWARE_FLAGS));self.assertEqual(child['OTHER'],'retained');self.assertEqual(base['SOFTWARE_GL'],'software')

if __name__=='__main__':unittest.main()
