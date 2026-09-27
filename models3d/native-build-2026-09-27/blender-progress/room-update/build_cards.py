import bpy,json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent/'tarot';out=R/'models';out.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
def image_mat(n,path):
 m=bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.84
 t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path),check_existing=True);t.image.pack();m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']);return m
back=image_mat('Rewers_1909',R/'textures/back.jpg');edge=bpy.data.materials.new('Kartonik');edge.diffuse_color=(.78,.72,.58,1)
carddata=json.load(open(R/'cards.json'))
for i,c in enumerate(carddata):
 front=image_mat(c['id'],R/'textures'/(c['id']+'.jpg'));w=.16;h=.275;t=.002
 # Independent front/back UVs; full face occupies the full plane, all six sides have thickness.
 vs=[(-w/2,-h/2,-t/2),(w/2,-h/2,-t/2),(w/2,h/2,-t/2),(-w/2,h/2,-t/2),(-w/2,-h/2,t/2),(w/2,-h/2,t/2),(w/2,h/2,t/2),(-w/2,h/2,t/2)]
 faces=[(4,5,6,7),(1,0,3,2),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 me=bpy.data.meshes.new(c['id']);me.from_pydata(vs,[],faces);me.materials.append(front);me.materials.append(back);me.materials.append(edge);uv=me.uv_layers.new()
 for poly in me.polygons:
  poly.material_index=poly.index if poly.index<2 else 2
  for j,li in enumerate(poly.loop_indices):uv.data[li].uv=[(0,0),(1,0),(1,1),(0,1)][j]
 o=bpy.data.objects.new('CARD_'+c['id'],me);bpy.context.collection.objects.link(o);o['card_id']=c['id'];o['art_source']=c['art_source'];o['art_license']=c['art_license'];o['dimensions_m']=[w,h,t]
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.export_scene.gltf(filepath=str(out/(c['id']+'.glb')),export_format='GLB',use_selection=True,export_extras=True)
 o.location=((i%13)*.20,(i//13)*.32,0)
 c['model_sha256']=hashlib.sha256((out/(c['id']+'.glb')).read_bytes()).hexdigest()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Tarot_78_editable.blend'));(R/'cards.json').write_text(json.dumps(carddata,ensure_ascii=False,indent=2));print('SAVED 78 cards',flush=True)
