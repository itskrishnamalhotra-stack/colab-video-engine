"""Blender GPU tail: open the packed, baked scene; select CUDA; render missing frames."""
import argparse,json,struct,sys,time
from pathlib import Path
import bpy

parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--frames',required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
project=Path(args.project);frames=Path(args.frames);frames.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(project/'prepared-scene.blend'),load_ui=False,use_scripts=True)
scene=bpy.context.scene
print('BUILD_STAGE packed animation scene loaded',flush=True)
scene.render.engine='CYCLES'
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
devices=[]
for device in prefs.devices:
 device.use=device.type=='CUDA'
 if device.use:devices.append(device.name)
if not devices:raise RuntimeError('No CUDA device available; CPU fallback is disabled.')
scene.cycles.device='GPU';scene.cycles.samples=64;scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.035;scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
scene.render.fps=30;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.filepath=str(frames/'frame_');scene.render.use_file_extension=True;scene.render.use_overwrite=False
device_info={'engine':'CYCLES','requested_device':'CUDA','device':', '.join(devices),'prepared_scene':True}
(project/'data/render-device.json').write_text(json.dumps(device_info,indent=2))
print('BUILD_STAGE verified CUDA devices: '+', '.join(devices),flush=True)

def valid_png(path):
 try:
  with path.open('rb') as f:
   header=f.read(24);f.seek(-12,2);end=f.read(12)
  return header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(1080,1920) and end==b'\x00\x00\x00\x00IEND\xaeB`\x82'
 except (OSError,ValueError,struct.error):return False

first=scene.frame_start;last=scene.frame_end
for path in frames.glob('frame_*.png'):
 if not valid_png(path):path.unlink() # Only incomplete renderer-owned PNGs in this exact frames folder.
cached=sum(valid_png(frames/f'frame_{f:04d}.png') for f in range(first,last+1))
progress_path=project/'data/render-progress.json'
def save_progress(scene,*_):
 progress={'frame':scene.frame_current,'total_frames':last-first+1,'updated':time.time(),'cached_at_start':cached}
 temporary=progress_path.with_suffix('.tmp');temporary.write_text(json.dumps(progress));temporary.replace(progress_path)
 print(f'FRAME_PROGRESS {scene.frame_current}/{last}',flush=True)
bpy.app.handlers.render_write.append(save_progress)
print(f'BUILD_STAGE resuming with {cached}/{last-first+1} valid cached frames',flush=True)
if cached<last-first+1:bpy.ops.render.render(animation=True)
print('BLENDER_FRAMES_COMPLETE',flush=True)
