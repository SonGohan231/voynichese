import bpy,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;A=R/'architecture';N=R.parent/'quest-native/assets'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(A/'archive_higgsfield.glb'))
# Store editable geometry as well as an optimized runtime version. Material batches reduce mobile draw calls.
for o in list(bpy.data.objects):
 if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
 elif o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.objects):
 if o.name.startswith(('PHARM_okno','PHARM_luk_okna','PHARM_parapet','PHARM_olow')):bpy.data.objects.remove(o,do_unlink=True)
# Procedural material details stay editable in Blender; runtime uses portable base materials.
for m in bpy.data.materials:
 if not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF')
 if p:p.inputs['Roughness'].default_value=max(.48,p.inputs['Roughness'].default_value)
# Preserve individual cabinetry and stonework in the source file.
bpy.ops.wm.save_as_mainfile(filepath=str(A/'Archive_editable_4_5.blend'))
# Batch static meshes per material. Originals remain in the editable file above.
bpy.ops.object.select_all(action='DESELECT')
meshes=[o for o in bpy.data.objects if o.type=='MESH'];groups={}
for o in meshes:
 key=o.data.materials[0].name if len(o.data.materials)==1 else o.name
 groups.setdefault(key,[]).append(o)
for key,obs in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
 if len(obs)>1:bpy.ops.object.join()
 bpy.context.object.name='Static_'+key
bpy.ops.export_scene.gltf(filepath=str(A/'archive.glb'),export_format='GLB',export_apply=True,export_extras=True)
shutil.copyfile(A/'archive.glb',N/'room/archive.glb')
manifest=json.load(open(R/'vessels/PROGRESS.json'))
catalog=json.load(open(N/'catalog.json'));catalog=[c for c in catalog if not c.get('id','').startswith('vessel_')]
for rec in manifest['models']:
 shutil.copyfile(R/'vessels'/rec['id']/(rec['id']+'.glb'),N/'models'/(rec['id']+'.glb'));catalog.append(rec)
(N/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
# Display reference pages at their original detail: exact source JPEG bytes.
atlas=json.load(open(R.parent/'voynich-3d/public/assets/atlas.json'))['pages']
for scan in ['s0161','s0163','s0175']:
 p=next(p for p in atlas if p['id']==scan);shutil.copyfile(R/'source/originals'/p['file'],N/'scans'/(scan+'.jpg'))
# Make complete furnished, source-grounded editable exhibition for Blender delivery.
for i,rec in enumerate(manifest['models']):
 old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'vessels'/rec['id']/(rec['id']+'.glb')))
 parent=bpy.data.objects.new('EXHIBIT_'+rec['id'],None);bpy.context.collection.objects.link(parent)
 for o in set(bpy.data.objects)-old-{parent}:
  if o.parent is None:o.parent=parent
 parent.location=(6.15+(i%5)*1.75,4.48 if i<5 else -2.4,1.0);parent.scale=(.88,.88,.88)
for i,scan in enumerate(['s0161','s0163','s0175']):
 p=next(p for p in atlas if p['id']==scan);image=bpy.data.images.load(str(R/'source/originals'/p['file']));image.pack()
 m=bpy.data.materials.new('Scan_'+scan);m.use_nodes=True;n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=image;pb=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(n.outputs['Color'],pb.inputs['Base Color']);pb.inputs['Roughness'].default_value=1
 w=min(1.9,1.96*image.size[0]/image.size[1]);h=1.96;me=bpy.data.meshes.new(scan);me.from_pydata([(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)],[],[(0,1,2,3)]);me.materials.append(m);uv=me.uv_layers.new()
 for j,u in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[j].uv=u
 o=bpy.data.objects.new('SOURCE_'+scan,me);bpy.context.collection.objects.link(o);o.location=(7.4+i*2.6,5.665,2.25)
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('World');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.13,.16,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.5
for name,pos in [('Archive_fill',(0,1,3.3)),('Pharmacy_fill',(10,1,3.3))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=1000;d.shape='DISK';d.size=7;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=pos
bpy.ops.object.camera_add(location=(9.7,-.7,2));cam=bpy.context.object;cam.rotation_euler=(Vector((10,4.5,1.7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=25;sc.camera=cam
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc['status']='CANDIDATE reconstruction; room is an original modern research environment.'
bpy.ops.wm.save_as_mainfile(filepath=str(A/'Sala_Naczyn_Komplet.blend'))
sc.render.filepath=str(A/'pharmacy-preview.png');bpy.ops.render.render(write_still=True)
print('ROOM READY',len(meshes),'->',len(groups),'static mesh groups; catalog',len(catalog),flush=True)
