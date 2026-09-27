import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;ROOT=R.parent;OUT=R/'review';OUT.mkdir(exist_ok=True);N=ROOT/'quest-native/assets'
bpy.ops.wm.open_mainfile(filepath=str(R/'building/Budynek_i_ogrod_editable.blend'));sc=bpy.context.scene

def import_model(path,name,pos,scale=1.,size=None):
 old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));created=set(bpy.data.objects)-old;root=bpy.data.objects.new(name,None);sc.collection.objects.link(root)
 for o in created:
  if o.parent is None:o.parent=root
 if size:
  pts=[o.matrix_world@Vector(v) for o in created if o.type=='MESH' for v in o.bound_box]
  lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);fac=size/max(hi-lo);root.scale=(fac,fac,fac);root.location=Vector(pos)-Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))*fac
 else:root.location=pos;root.scale=(scale,)*3
 return root
for id,x in [('relief_s0158',-.2),('spatial_s0158',9.3)]:import_model(N/'models'/(id+'.glb'),id,(x,-20,.04),8.7/12)
for i,c in enumerate(json.load(open(ROOT/'room-update/vessels/PROGRESS.json'))['models']):import_model(N/'models'/(c['id']+'.glb'),c['id'],(6.15+(i%5)*1.75,4.48 if i<5 else -2.4,1),size=.98)
import_model(N/'room/open_book.glb','Manuskrypt_na_stole',(0,2.12,1.07))
for i,id in enumerate(['00_fool','01_magician','02_high_priestess']):import_model(N/'tarot/models'/(id+'.glb'),id,(2.55+i*.45,1.7,.91))
cat=json.load(open(N/'catalog.json'));plants=[c for c in cat if c['category']=='Rośliny']
for i,c in enumerate(plants[:6]):import_model(ROOT/'quest-native'/c.get('display_model',c['model']).removeprefix('res://'),c['scan'],(-16 if i<3 else -7.4,-[3,10,18][i%3],.37),size=1.5)
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
for light in bpy.data.lights:light.energy*=.28
cam=sc.camera

def shot(name,pos,target,lens=22,size=(960,600)):
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.lens=lens;sc.render.resolution_x=size[0];sc.render.resolution_y=size[1];sc.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('RENDER',name,flush=True)
shot('diagramy-oba',(5,-11.9,3.4),(4.7,-21,.20),18,(1440,900))
shot('diagram-3d-detale',(9.35,-17.3,1.85),(9.35,-20,.32),25,(1200,900))
# Four 120-degree engineering corner views of the hero hall, plus ceiling views.
for i,pos in enumerate([(-4,-9,2),(14,-9,2),(14,-27,2),(-4,-27,2)]):shot('corner-'+str(i+1),pos,(5,-18,1.8),10.4,(800,500))
shot('ceiling-up',(5,-18,1.7),(5,-18,5.4),12,(800,500))
shot('ceiling-oblique-a',(-3,-10,1.8),(10,-24,5.3),14,(800,500))
shot('ceiling-oblique-b',(13,-26,1.8),(0,-11,5.3),14,(800,500))
shot('ogrod',(-11,3.5,2.3),(-11,-17,1),20,(1200,800))
# Orthographic plan from the actual mesh silhouettes, with roof objects hidden for the lower layer.
roof=[]
for o in bpy.data.objects:
 if any(k in o.name for k in ['sufit','belka']):o.hide_render=True;roof.append(o)
cam.data.type='ORTHO';cam.data.ortho_scale=52;cam.location=(4,-11,55);cam.rotation_euler=(0,0,0);sc.render.resolution_x=1400;sc.render.resolution_y=1150;sc.render.filepath=str(OUT/'floor-plan.png');bpy.ops.render.render(write_still=True)
for o in roof:o.hide_render=False
cam.data.type='PERSP';cam.data.lens=18;cam.location=(5,-11.9,3.4);cam.rotation_euler=(Vector((4.7,-21,.2))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.render.resolution_x=1440;sc.render.resolution_y=900
bpy.ops.wm.save_as_mainfile(filepath=str(R/'building/Manuskrypt_Budynek_Galerie_0_3.blend'));print('COMPLETE_REVIEW',flush=True)
