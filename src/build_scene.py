"""Original cookie performance using Blender Studio's unmodified Snow mesh/rig.
Run by the detached engine. --probe renders one initial asset-compatibility frame.
Snow Rig © Blender Foundation | studio.blender.org — CC BY 4.0.
"""
import argparse,json,math,random,sys,time
import faulthandler
from pathlib import Path
import bpy
from mathutils import Vector,Matrix,Quaternion

args=argparse.ArgumentParser()
args.add_argument('--project',required=True);args.add_argument('--frames',required=True)
args.add_argument('--probe',action='store_true')
args.add_argument('--device',choices=['EEVEE','CUDA'],default='EEVEE')
opt=args.parse_args(sys.argv[sys.argv.index('--')+1:])
P=Path(opt.project);OUT=Path(opt.frames);OUT.mkdir(parents=True,exist_ok=True)
faulthandler.enable();faulthandler.dump_traceback_later(90,repeat=True)
def stage(message):print('BUILD_STAGE',message,flush=True)
ROOT=P.parents[1]
source=ROOT/'assets/blender-studio/snow-v2/snow_v02.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=True)
stage('source rig loaded')
scene=bpy.context.scene
rig=bpy.data.objects['RIG-Snow']
rig.animation_data_clear()
# Clear the authoring metarig and the example lighting from this working scene only.
meta=bpy.data.objects.get('META-Snow')
if meta:bpy.data.objects.remove(meta,do_unlink=True)
for o in list(bpy.data.objects):
 if o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
for im in bpy.data.images:
 im.filepath=im.filepath.replace('\\','/')
 if im.filepath.startswith('//'):im.filepath=bpy.path.abspath(im.filepath)
 if im.source=='FILE' and max(im.size)>2048:
  factor=2048/max(im.size);im.scale(max(1,round(im.size[0]*factor)),max(1,round(im.size[1]*factor)))
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('GEO'):
  for mod in o.modifiers:
   if mod.type=='SUBSURF':mod.render_levels=min(mod.render_levels,1)
stage('textures and geometry prepared')
scene.render.engine='BLENDER_EEVEE'
device_name='Intel UHD 620 / EEVEE'
if opt.device=='CUDA':
 scene.render.engine='CYCLES'
 prefs=bpy.context.preferences.addons['cycles'].preferences
 prefs.compute_device_type='CUDA';prefs.get_devices()
 devices=[]
 for d in prefs.devices:
  d.use=d.type=='CUDA'
  if d.use:devices.append(d.name)
 if not devices:raise RuntimeError('CUDA GPU unavailable; refusing an unnoticed CPU fallback.')
 device_name=', '.join(devices)
 scene.cycles.device='GPU';scene.cycles.samples=64
 scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.035
 scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
 scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
 stage('verified CUDA devices: '+device_name)
(P/'data/render-device.json').write_text(json.dumps({'engine':scene.render.engine,'requested_device':opt.device,'device':device_name},indent=2),encoding='utf-8')
scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
scene.render.fps=30;scene.render.film_transparent=False
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.compression=15
scene.render.use_simplify=True;scene.render.simplify_subdivision_render=1
if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=24
elif hasattr(scene.eevee,'taa_samples'):scene.eevee.taa_samples=24
scene.eevee.use_raytracing=False
scene.eevee.shadow_ray_count=2;scene.eevee.shadow_step_count=6
if hasattr(scene.eevee,'shadow_pool_size'):scene.eevee.shadow_pool_size='256'
scene.world.color=(.15,.15,.15)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.3,.39,.5,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28
scene.view_settings.view_transform='AgX'
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass

def curves(action):return [f for l in action.layers for s in l.strips for b in s.channelbags for f in b.fcurves]
posekeys={}
def pose(name,frame,side=None):
 """Use the rig author's hand/face poses, preserving all original proportions."""
 a=bpy.data.actions[name]
 for f in curves(a):
  path=f.data_path
  if not path.startswith('pose.bones['):continue
  bone=path.split('"')[1]
  if side and not bone.endswith(side):continue
  if bone.startswith(('STR-','DEF-','ORG-')):continue
  posekeys.setdefault((path,f.array_index),{})[frame]=f.evaluate(a.frame_range[0])

timing=json.loads((P/'data/lines.json').read_text(encoding='utf-8-sig')) if (P/'data/lines.json').exists() else {'duration':11.0,'lines':[{'s':.3,'e':3.2},{'s':3.35,'e':7.0},{'s':7.15,'e':9.9}]}
lines=timing['lines'];DUR=float(timing['duration']);N=round(DUR*30)
# voice.py uses start/end fields; accept either representation.
def start(i):return float(lines[i].get('start',lines[i].get('s',0)))
def end(i):return float(lines[i].get('end',lines[i].get('e',0)))
def F(t):return max(1,round(t*30)+1)
S1=start(1);S2=start(2)
grab=S1+.68;lift=grab+.85;react=S2+.6
scene.frame_start=1;scene.frame_end=N

props=rig.pose.bones['Properties']
for side in ['left','right']:
 props[f'ik_{side}_upperarm']=1.0
 props[f'ik_stretch_{side}_upperarm']=0.0
 props[f'ik_pole_follow_{side}_upperarm']=0.0

def bone_key(name,t,loc=None,rot=None):
 b=rig.pose.bones[name];frame=F(t)
 if loc is not None:b.location=loc;b.keyframe_insert('location',frame=frame,group='Performance')
 if rot is not None:
  b.rotation_mode='XYZ';b.rotation_euler=[math.radians(x) for x in rot]
  b.keyframe_insert('rotation_euler',frame=frame,group='Performance')

def wrist(side,t,pos,direction):
 b=rig.pose.bones[f'IK-MSTR-Wrist.{side}']
 rest=b.bone.matrix_local.copy()
 old=rest.to_3x3()@Vector((0,1,0))
 q=old.rotation_difference(Vector(direction).normalized())
 m=q.to_matrix().to_4x4()@rest
 m.translation=Vector(pos)
 b.matrix=m
 b.keyframe_insert('location',frame=F(t),group='Hand contacts')
 if b.rotation_mode=='QUATERNION':b.keyframe_insert('rotation_quaternion',frame=F(t),group='Hand contacts')
 else:b.keyframe_insert('rotation_euler',frame=F(t),group='Hand contacts')
 bpy.context.view_layer.update()

# Right arm rests naturally, with a small counterbalancing gesture on the reveal.
for t,pos,d in [(0,(-.27,-.02,.98),(0,0,-1)),(S1,(-.27,-.02,.98),(0,0,-1)),
               (lift,(-.27,-.09,1.01),(0,-.15,-1)),(react,(-.29,-.07,1.05),(-.05,-.1,-1)),
               (DUR,(-.29,-.07,1.03),(0,0,-1))]:wrist('R',t,pos,d)
# Left wrist anticipates, reaches the cookie, grips it, and withdraws to chest height.
handkeys=[(0,(.27,-.04,.99),(0,-.1,-1)),(S1-.35,(.27,-.04,.99),(0,-.1,-1)),
 (S1,(.27,-.10,1.05),(0,-.6,-.8)),(grab-.13,(.235,-.385,1.105),(0,-.83,-.56)),
 (grab,(.235,-.405,1.095),(0,-.83,-.56)),(grab+.18,(.235,-.405,1.095),(0,-.83,-.56)),
 (lift,(.24,-.32,1.30),(0,-.95,-.3)),(S2,(.24,-.32,1.30),(0,-.95,-.3)),
 (react,(.255,-.31,1.34),(0,-.95,-.3)),(react+.3,(.255,-.31,1.34),(0,-.95,-.3)),
 (DUR,(.25,-.31,1.33),(0,-.95,-.3))]
for t,p,d in handkeys:wrist('L',t,p,d)
stage('body and wrist performance keyed')
for t,n in [(0,'relaxed'),(grab-.13,'relaxed'),(grab+.13,'crawl'),(DUR,'crawl')]:pose('Snow_hand_'+n,F(t),'.L')
# The right hand uses a modest curl instead of straight rigid fingers.
for b in rig.pose.bones:
 if b.name.startswith('FK-Finger_') and b.name.endswith('.R') and 'Carpal' not in b.name:
  b.rotation_mode='XYZ';b.rotation_euler.x=.16 if 'Thumb' not in b.name else .08
  b.keyframe_insert('rotation_euler',frame=1)

# Authored face poses: suspicion -> satisfaction -> startled recognition.
for t,eye,mouth in [(0,'default','default'),(.7,'cocky','teethsmile'),(S1-.3,'cocky','teethsmile'),
 (lift,'relaxed','teethsmile'),(S2,'relaxed','teethsmile'),(react,'scared','OO'),(DUR,'scared','OO')]:
 pose('Snow_eyemask_'+eye,F(t));pose('Snow_mouth_'+mouth,F(t))
# One natural blink, held facial expression does not mean frozen eyes.
blink=min(S1-.55,1.7)
pose('Snow_eyemask_cocky',F(blink-.08));pose('Snow_eyemask_closed',F(blink));pose('Snow_eyemask_cocky',F(blink+.13))
for t,r in [(0,(-2,0,2)),(.7,(5,-3,-5)),(S1-.25,(5,-3,-5)),(grab,(9,1,-3)),(lift,(-1,-2,3)),
 (S2,(-1,-2,3)),(react,(-4,-13,-11)),(react+.2,(-3,-12,-10)),(DUR,(-3,-12,-10))]:bone_key('FK-Head',t,rot=r)
for t,r in [(0,(0,0,0)),(S1-.25,(0,0,0)),(grab,(5,0,-2)),(lift,(1,0,0)),(react,(0,0,3)),(DUR,(0,0,3))]:bone_key('FK-Chest',t,rot=r)
# Eye target follows the cookie and then the camera before the head catches up.
eye=rig.pose.bones['MSTR-TGT-Eyes']
for t,p in [(0,(.02,0,-.06)),(.6,(.15,.2,-.22)),(grab,(.15,.3,-.3)),(lift,(.1,.3,-.1)),(S2,(.1,.3,-.1)),(react-.1,(-.4,.0,.22)),(DUR,(-.4,.0,.22))]:bone_key(eye.name,t,loc=p)

# Add the author's facial/hand pose curves in bulk. Calling keyframe_insert for
# thousands of individual components repeatedly updates the complex driver graph.
action=rig.animation_data.action
bag=action.layers[0].strips[0].channelbags[0]
for (path,index),keys in posekeys.items():
 try:rig.path_resolve(path)
 except (ValueError,TypeError):continue
 fc=bag.fcurves.find(path,index=index)
 if fc is None:fc=bag.fcurves.new(path,index=index)
 for frame,value in sorted(keys.items()):fc.keyframe_points.insert(frame,value,options={'FAST'})
 fc.update()
stage('face and finger pose curves ready')
# Clamped handles prevent reach overshoot and hand/prop penetration at contact.
if rig.animation_data and rig.animation_data.action:
 for fc in curves(rig.animation_data.action):
  for k in fc.keyframe_points:k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'

def material(name,color,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1)
 n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=metal
 return m
teal=material('Cabinet | deep petrol',(.035,.18,.19));wall=material('Warm plaster',(.64,.56,.40))
wood=material('Honey oak',(.35,.16,.055));edge=material('Brass',(.55,.32,.09),.28,.65)
stone=material('Cream terrazzo',(.72,.68,.53),.4);white=material('Ivory ceramic',(.82,.81,.69),.23)
black=material('Camera charcoal',(.018,.025,.028),.34);glass=material('Camera lens',(.015,.07,.1),.18,.4)
green=material('Leaf sage',(.08,.25,.09));soil=material('Soil',(.055,.028,.012));red=material('Warm terracotta',(.51,.16,.075))
dough=material('Baked golden cookie',(.55,.25,.07),.8);chip=material('Chocolate',(.07,.023,.009),.8)
tile=material('Muted turquoise tile',(.18,.36,.36),.3);grout=material('Tile grout',(.56,.58,.48))
blue=material('Sky beyond window',(.27,.51,.72))

def cube(name,loc,scale,mat,bevel=.02):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if mat:o.data.materials.append(mat)
 if bevel:
  b=o.modifiers.new('Soft manufactured edges','BEVEL');b.width=bevel;b.segments=3
  o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return o
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def cylinder(name,loc,r,depth,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=loc)
 o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 b=o.modifiers.new('Soft lip','BEVEL');b.width=min(.008,depth/4);b.segments=3
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
def text(name,body,loc,size,mat,rot=(math.pi/2,0,0)):
 c=bpy.data.curves.new(name,'FONT');c.body=body;c.align_x='CENTER';c.size=size;c.extrude=.0005
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=rot;c.materials.append(mat);return o

# A complete kitchen set with foreground, working counter and layered background.
cube('Oak floor',(0,0,-.05),(7,7,.1),wood)
for x in range(-6,7):cube('Floorboard seam',(x*.42,0,.001),(.006,7,.002),black,.001)
cube('Back wall',(0,1.45,1.5),(6,.12,3.2),wall)
cube('Skirting',(0,1.36,.09),(6,.08,.18),white)
cube('Side wall',(2.15,.0,1.5),(.12,3,3.2),wall)
# Rear cabinetry and tiled splashback, naturally out of focus in close shots.
cube('Rear cabinet',(0,1.12,.48),(3.4,.48,.96),teal)
cube('Rear stone',(0,1.08,.99),(3.6,.65,.07),stone)
for x in [-1.25,-.42,.42,1.25]:
 cube('Cabinet door',(x,.866,.48),(.78,.035,.79),teal,.012)
 cube('Brass handle',(x,.827,.73),(.24,.025,.025),edge,.008)
cube('Grouted backsplash',(0,1.36,1.38),(3.5,.025,.65),grout,.002)
for row in range(3):
 for col in range(14):cube('Glazed tile',(-1.63+col*.25+(row%2)*.06,1.332,1.13+row*.21),(.239,.03,.195),tile,.007)
cube('Upper shelf',(0,1.10,1.94),(3.6,.52,.065),wood)
for x,z in [(-1.43,2.10),(-1.17,2.08),(-.9,2.13)]:
 cylinder('Storage jar',(x,1.12,z),.085,.23,white);cylinder('Wood jar lid',(x,1.12,z+.12),.09,.025,wood)
for i,color in enumerate([red,teal,white]):
 cylinder('Ceramic mug',(.65+i*.24,1.12,2.07),.075,.2,color)
 bpy.ops.mesh.primitive_torus_add(major_radius=.056,minor_radius=.012,major_segments=24,minor_segments=8,location=(.735+i*.24,1.12,2.07),rotation=(math.pi/2,0,0))
 bpy.context.object.data.materials.append(color)
# Window on the rear left, framed with mullions and an outside sky panel.
cube('Window frame',(-1.25,1.36,2.57),(1.25,.08,.85),white)
cube('Window blue',(-1.25,1.303,2.57),(1.12,.02,.72),blue,.003)
cube('Window vertical',(-1.25,1.276,2.57),(.035,.03,.72),white)
cube('Window horizontal',(-1.25,1.276,2.57),(1.12,.03,.035),white)
# Counter in front of the actor; her reach is staged above its rear edge.
cube('Island cabinet',(0,-.94,.47),(2.8,1.02,.94),teal)
cube('Island stone',(0,-.93,.985),(2.93,1.15,.06),stone)
for x in [-.9,0,.9]:
 cube('Island panel',(x,-1.464,.47),(.84,.035,.79),teal,.014)
 cube('Island brass pull',(x,-1.496,.75),(.24,.02,.025),edge,.006)
cylinder('Cookie plate',(.235,-.575,1.023),.18,.018,white)
# Ring on the plate gives its rim form without flat graphic substitutes.
bpy.ops.mesh.primitive_torus_add(major_radius=.155,minor_radius=.009,major_segments=48,minor_segments=10,location=(.235,-.575,1.035))
bpy.context.object.data.materials.append(white)
cookie=sphere('Last cookie',(.235,-.526,1.057),(.059,.059,.015),dough)
cookieparts=[];rng=random.Random(8)
for i in range(14):
 a=rng.random()*math.tau;r=.043*math.sqrt(rng.random())
 o=sphere('Chocolate piece',(cookie.location.x+math.cos(a)*r,cookie.location.y+math.sin(a)*r,1.069),(.006,.006,.0035),chip)
 o.parent=cookie;o.matrix_parent_inverse=cookie.matrix_world.inverted();cookieparts.append(o)
for i in range(9):
 a=rng.random()*math.tau;r=rng.uniform(.075,.13)
 sphere('Crumb',(.235+math.cos(a)*r,-.575+math.sin(a)*r,1.039),(.003,.004,.002),dough)
# Details support the set rather than cover up the performance.
cube('Chopping board',(-.8,-.86,1.031),(.47,.34,.028),wood,.035)
cube('Tea towel',(.96,-1.15,1.03),(.36,.43,.014),white,.012)
for i in range(5):cube('Towel woven stripe',(.84+i*.06,-1.15,1.039),(.008,.42,.002),teal,.001)
cylinder('Plant pot',(1.36,1.03,1.15),.13,.28,red)
cylinder('Pot soil',(1.36,1.03,1.292),.118,.01,soil)
for i in range(9):
 a=i*2.4;v=Vector((math.cos(a)*.17,math.sin(a)*.12,.25+rng.random()*.18))
 o=sphere('Herb leaf',Vector((1.36,1.03,1.30))+v*.6,(.045,.022,v.length*.45),green)
 o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
cylinder('Utensil crock',(-1.32,1.01,1.17),.11,.32,white)
for i in range(4):
 x=-1.39+i*.047
 cube('Spoon handle',(x,1.01,1.44),(.014,.018,.34),wood,.006)
 sphere('Spoon bowl',(x,1.01,1.62),(.03,.013,.046),wood)
text('Tiny shelf sign','FRESHLY BAKED',(.02,1.30,2.18),.082,wood)
# Security camera mounted on an off-axis front wall location.
security=Vector((-1.25,-.38,2.20))
cube('Camera wall bracket',(-1.46,-.38,2.22),(.10,.16,.24),white)
cube('Camera support',(-1.35,-.38,2.22),(.2,.05,.055),black)
body=cube('Security camera',security,(.25,.16,.14),white,.025)
lens=cylinder('Lens barrel',security+Vector((0,-.095,0)),.047,.05,black);lens.rotation_euler.x=math.pi/2
gl=sphere('Lens glass',security+Vector((0,-.124,0)),(.033,.009,.033),glass)
led=material('Recording LED',(.6,.005,.002),.3)
n=led.node_tree.nodes['Principled BSDF'];n.inputs['Emission Color'].default_value=(1,.01,.001,1);n.inputs['Emission Strength'].default_value=2
sphere('Red recording LED',security+Vector((.082,-.083,-.025)),(.007,.005,.007),led)
stage('kitchen set complete')

def area(name,loc,power,color,size,target):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
 o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc
 o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Large warm key',(-2.2,-2.0,3.8),420,(1,.80,.60),3,(0,-.05,1.25))
area('Cool window fill',(1.3,-.4,2.8),190,(.65,.8,1),2,(0,0,1.4))
area('Shelf rim',(.2,1.0,2.7),260,(1,.67,.34),1.7,(0,0,1.2))
area('Ceiling bounce',(0,-.7,3.3),170,(1,.92,.75),3,(0,-.5,0))

def camera(name,pos,target,lens,fstop=4):
 data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);scene.collection.objects.link(o)
 o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 data.lens=lens;data.sensor_width=36;data.dof.use_dof=True;data.dof.aperture_fstop=fstop
 data.dof.focus_distance=(Vector(pos)-Vector(target)).length
 return o
wide=camera('01 Establish and anticipate',(-1.65,-3.35,2.10),(0,-.15,1.24),48,5.6)
handcam=camera('02 Physical hand contact',(.85,-1.72,1.52),(.235,-.45,1.13),62,5.6)
face=camera('03 Satisfaction to recognition',(-.48,-1.48,1.78),(-.005,-.04,1.54),62,4)
insert=camera('04 The witness',(-1.03,-1.0,2.23),security,58,4)
for f,cam in [(1,wide),(F(S1-.1),handcam),(F(lift+.12),face),(F(react+.55),insert),(F(react+1.32),face)]:
 marker=scene.timeline_markers.new(cam.name,frame=f);marker.camera=cam
scene.camera=wide
# Small motivated dollies; the body and facial acting carry the action.
for cam,ta,tb,delta in [(wide,0,S1,Vector((.09,.14,-.015))),(face,lift,DUR,Vector((.025,.07,-.005)))]:
 cam.keyframe_insert('location',frame=F(ta));cam.location+=delta;cam.keyframe_insert('location',frame=F(tb))

# Derive the pickup attachment at the exact contact frame. It remains rigidly
# attached to the palm thereafter, rather than following an independent guessed arc.
scene.frame_set(F(grab));bpy.context.view_layer.update()
hand=rig.pose.bones['ORG-Wrist.L']
grip_offset=(rig.matrix_world@hand.matrix).inverted()@cookie.matrix_world
original_cookie=cookie.matrix_world.copy()
def update_cookie(frame):
 scene.frame_set(frame);bpy.context.view_layer.update()
 cookie.matrix_world=(rig.matrix_world@hand.matrix)@grip_offset if frame>=F(grab) else original_cookie
 bpy.context.view_layer.update()

# Save an editable, self-contained scene with external original texture references.
for frame in range(1,N+1):
 update_cookie(frame);cookie.keyframe_insert('location',frame=frame);cookie.keyframe_insert('rotation_euler',frame=frame)
for fc in curves(cookie.animation_data.action):
 for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.frame_set(1)
faulthandler.cancel_dump_traceback_later()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'scene.blend'))
stage('editable scene saved')
if opt.probe:
 frame=F(lift+.3);update_cookie(frame)
 scene.camera=face;scene.render.resolution_percentage=50
 scene.render.filepath=str(OUT/'rig-compatibility.png')
 before=time.monotonic();bpy.ops.render.render(write_still=True)
 report={'frame':frame,'duration_seconds':DUR,'render_seconds':round(time.monotonic()-before,2),'blender':bpy.app.version_string,'rig':rig.name,'source':str(source),'renderer':scene.render.engine,'device':device_name,'resolution':[540,960]}
 (OUT/'probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('RIG_COMPATIBILITY_PASSED',json.dumps(report),flush=True)
else:
 # Keep the native animation render session alive. Restarting a still render
 # for every frame needlessly repeats EEVEE initialization on this laptop.
 scene.render.filepath=str(OUT/'frame_')
 scene.render.use_file_extension=True
 def progress(scene,*_):
  if scene.frame_current==1 or scene.frame_current%30==0:print(f'FRAME_PROGRESS {scene.frame_current}/{N}',flush=True)
 bpy.app.handlers.render_write.append(progress)
 faulthandler.cancel_dump_traceback_later()
 bpy.ops.render.render(animation=True)
 print('BLENDER_FRAMES_COMPLETE',flush=True)
