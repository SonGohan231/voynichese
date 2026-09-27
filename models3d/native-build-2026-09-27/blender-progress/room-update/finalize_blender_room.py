import bpy,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;A=R/'architecture'
bpy.ops.wm.open_mainfile(filepath=str(A/'Sala_Naczyn_Komplet.blend'))
def add_glb(path,name,pos,rot=(0,0,0)):
 old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));root=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(root)
 for o in set(bpy.data.objects)-old-{root}:
  if o.parent is None:o.parent=root
 root.location=pos;root.rotation_euler=rot;return root
add_glb(R.parent/'quest-native/assets/room/open_book.glb','Manuskrypt_na_pulpicie',(0,2.12,1.07))
for i,key in enumerate(['00_fool','01_magician','02_high_priestess']):add_glb(R/'tarot/models'/(key+'.glb'),'Tarot_'+key,(3+(i-1)*.38,1.7,.915))
for i in range(8):add_glb(R/'tarot/models/21_world.glb','Talia_rewers',(2.15,1.17,.899+i*.0025),(math.pi,0,0))
sc=bpy.context.scene;sc.camera.location=(.7,-3.55,2.10);sc.camera.rotation_euler=(Vector((2.4,3.1,1.20))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.lens=23
bpy.ops.wm.save_as_mainfile(filepath=str(A/'Pracownia_i_Sala_Naczyn_Tarot.blend'))
sc.render.filepath=str(A/'furnished-preview.png');sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.cycles.samples=16;bpy.ops.render.render(write_still=True)
