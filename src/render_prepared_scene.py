"""Blender GPU tail: packed scene, OptiX preferred, persistent data and GPU OIDN."""
import argparse,hashlib,json,os,struct,sys,time
from pathlib import Path
import bpy

parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--frames',required=True)
parser.add_argument('--benchmark',action='store_true',help='Only two full-quality frames with GPU optimizations; no final video.')
parser.add_argument('--inspect-only',action='store_true',help='Check settings/API without rendering, including on a CPU-only workstation.')
parser.add_argument('--cycles-print-stats',action='store_true')
parser.add_argument('--renderer',choices=['cycles','eevee'],default='cycles')
parser.add_argument('--frame-start',type=int);parser.add_argument('--frame-end',type=int)
parser.add_argument('--worker-id',default='')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
project=Path(args.project);frames=Path(args.frames);frames.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(project/'prepared-scene.blend'),load_ui=False,use_scripts=True)
scene=bpy.context.scene
print('BUILD_STAGE packed animation scene loaded',flush=True)
scene.render.engine='BLENDER_EEVEE' if args.renderer=='eevee' else 'CYCLES'
prefs=bpy.context.preferences.addons['cycles'].preferences
backend='CUDA'
if args.renderer=='cycles' and not args.inspect_only:
 try:
  prefs.compute_device_type='OPTIX';prefs.get_devices()
  if any(d.type=='OPTIX' for d in prefs.devices):backend='OPTIX'
 except (TypeError,RuntimeError):pass
prefs.compute_device_type=backend;prefs.get_devices()
devices=[]
for device in prefs.devices:
 device.use=device.type==backend
 if device.use:devices.append(device.name)
if args.renderer=='cycles' and not devices and not args.inspect_only:raise RuntimeError('No NVIDIA render device available; CPU fallback is disabled.')
scene.cycles.device='GPU';scene.cycles.samples=64;scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.035;scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
scene.render.use_persistent_data=True
# Retain the high-quality OIDN algorithm/passes; move it to the GPU when supported.
scene.cycles.denoiser='OPENIMAGEDENOISE';scene.cycles.denoising_quality='HIGH'
scene.cycles.denoising_use_gpu=bool(devices and prefs.has_oidn_gpu_devices())
scene.render.threads_mode='AUTO'
graphics={}
if args.renderer=='eevee':
 backend='OPENGL'
 if not args.inspect_only:
  import gpu
  gpu.init()
  graphics={'vendor':gpu.platform.vendor_get(),'renderer':gpu.platform.renderer_get(),'backend':gpu.platform.backend_type_get()}
  if 'NVIDIA' not in graphics['vendor'].upper() or any(x in graphics['renderer'].lower() for x in ('llvmpipe','softpipe','software')):
   raise RuntimeError('EEVEE requires an NVIDIA graphics context; refusing software rendering. Detected: '+json.dumps(graphics))
  devices=[graphics['renderer']]
 scene.eevee.taa_render_samples=64
 scene.eevee.use_raytracing=True;scene.eevee.ray_tracing_method='SCREEN'
 scene.eevee.ray_tracing_options.resolution_scale='1'
 scene.eevee.ray_tracing_options.screen_trace_quality=.5
 scene.eevee.ray_tracing_options.use_denoise=True
 scene.eevee.fast_gi_quality=.5
 scene.eevee.shadow_ray_count=2;scene.eevee.shadow_step_count=6
 scene.eevee.shadow_pool_size='512'
 for obj in scene.objects:
  if obj.type=='LIGHT' and hasattr(obj.data,'use_shadow_jitter'):obj.data.use_shadow_jitter=True
scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
scene.render.fps=30;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.filepath=str(frames/'frame_');scene.render.use_file_extension=True;scene.render.use_overwrite=False
if args.benchmark:scene.frame_end=min(scene.frame_start+1,scene.frame_end)
device_info={'engine':scene.render.engine,'requested_device':backend,'device':', '.join(devices),'prepared_scene':True,
 'persistent_data':scene.render.use_persistent_data,'denoiser':scene.cycles.denoiser if args.renderer=='cycles' else 'EEVEE_RAYTRACE',
 'denoising_use_gpu':scene.cycles.denoising_use_gpu if args.renderer=='cycles' else True,'samples':64,
 'adaptive_threshold':scene.cycles.adaptive_threshold,'resolution':[1080,1920],
 'threads_mode':scene.render.threads_mode,'frame_range':[scene.frame_start,scene.frame_end],'benchmark':args.benchmark}
if args.renderer=='eevee':device_info.update(graphics=graphics,raytracing='SCREEN',raytrace_resolution_scale='1',raytrace_quality=.5,fast_gi_quality=.5,shadow_rays=2,shadow_steps=6)
print('BUILD_STAGE renderer settings '+json.dumps(device_info),flush=True)
requested_first=args.frame_start if args.frame_start is not None else scene.frame_start
requested_last=args.frame_end if args.frame_end is not None else scene.frame_end
if not scene.frame_start<=requested_first<=requested_last<=scene.frame_end:raise ValueError('Assigned frames are outside the prepared animation.')
print('BUILD_STAGE assigned frame window '+json.dumps({'first':requested_first,'last':requested_last,'worker':args.worker_id or 'single'}),flush=True)
if args.inspect_only:
 print('SETTINGS_INSPECTION_OK',flush=True)
 raise SystemExit(0)
(project/('data/benchmark-device.json' if args.benchmark else 'data/render-device.json')).write_text(json.dumps(device_info,indent=2))
print('BUILD_STAGE verified '+backend+' devices: '+', '.join(devices),flush=True)

def valid_png(path):
 try:
  with path.open('rb') as f:
   header=f.read(24);f.seek(-12,2);end=f.read(12)
  return header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(1080,1920) and end==b'\x00\x00\x00\x00IEND\xaeB`\x82'
 except (OSError,ValueError,struct.error):return False

first=scene.frame_start;last=scene.frame_end
if args.benchmark:
 # A separate empty folder is required; never mix benchmark frames with the current render.
 if any(frames.iterdir()):raise RuntimeError('Benchmark frames folder must be new and empty.')
else:
 # Refuse to mix cached frames from different backends/settings or scene versions.
 with (project/'prepared-scene.blend').open('rb') as source:scene_sha=hashlib.file_digest(source,'sha256').hexdigest()
 cache_config={**device_info,'scene_sha256':scene_sha}
 marker=frames/'render-config.json'
 if marker.is_file():
  if json.loads(marker.read_text())!=cache_config:raise RuntimeError('Cached frame settings differ. Use a fresh frames folder for this render configuration.')
 elif any(frames.glob('frame_*.png')):raise RuntimeError('Cached frames have no settings record. Use a fresh frames folder.')
 temporary=marker.with_suffix(f'.{os.getpid()}.tmp');temporary.write_text(json.dumps(cache_config,indent=2));temporary.replace(marker)
for path in frames.glob('frame_*.png'):
 if not valid_png(path):path.unlink() # Only incomplete renderer-owned PNGs in this exact frames folder.
cached=sum(valid_png(frames/f'frame_{f:04d}.png') for f in range(first,last+1))
progress_path=project/'data/render-progress.json'
if args.worker_id:
 if not args.worker_id.replace('-','').isalnum():raise ValueError('Invalid worker ID.')
 progress_path=project/('data/render-progress-'+args.worker_id+'.json')
if args.benchmark:progress_path=project/'data/benchmark-progress.json'
assigned_first=args.frame_start if args.frame_start is not None else first
assigned_last=args.frame_end if args.frame_end is not None else last
if not first<=assigned_first<=assigned_last<=last:raise ValueError('Assigned frames are outside the prepared animation.')
scene.frame_start=assigned_first;scene.frame_end=assigned_last
timings=[];frame_started=None;written_at=None;wall_checkpoint=time.monotonic()
def start_frame(scene,*_):
 global frame_started
 frame_started=time.monotonic()
 print('FRAME_STARTED '+str(scene.frame_current),flush=True)
def rendered_frame(scene,*_):
 global written_at
 written_at=time.monotonic()
 if frame_started is not None:
  print('FRAME_RENDER_SECONDS '+json.dumps({'frame':scene.frame_current,'seconds':round(written_at-frame_started,3)}),flush=True)
def save_progress(scene,*_):
 global wall_checkpoint
 now=time.monotonic()
 elapsed=round(time.monotonic()-frame_started,3) if frame_started is not None else None
 timings.append({'frame':scene.frame_current,'render_callback_seconds':elapsed,'wall_interval_seconds':round(now-wall_checkpoint,3)})
 wall_checkpoint=now
 progress={'frame':scene.frame_current,'total_frames':last-first+1,'updated':time.time(),'cached_at_start':cached}
 temporary=progress_path.with_suffix('.tmp');temporary.write_text(json.dumps(progress));temporary.replace(progress_path)
 print(f'FRAME_PROGRESS {scene.frame_current}/{last}',flush=True)
 print('FRAME_TIMING '+json.dumps(timings[-1]),flush=True)
bpy.app.handlers.render_pre.append(start_frame)
bpy.app.handlers.render_post.append(rendered_frame)
bpy.app.handlers.render_write.append(save_progress)
print(f'BUILD_STAGE resuming with {cached}/{last-first+1} valid cached frames',flush=True)
if not all(valid_png(frames/f'frame_{f:04d}.png') for f in range(assigned_first,assigned_last+1)):bpy.ops.render.render(animation=True)
if args.benchmark:
 report={'status':'benchmark_complete','settings':device_info,'frames':timings,
  'baseline_observed_seconds_per_frame':56.9,
  'scope':'Two consecutive opening-shot frames only; this is not a full-animation timing or visual-quality validation.'}
 (project/'data/gpu-benchmark.json').write_text(json.dumps(report,indent=2))
 print('GPU_BENCHMARK '+json.dumps(report),flush=True)
print('BLENDER_FRAMES_COMPLETE',flush=True)
