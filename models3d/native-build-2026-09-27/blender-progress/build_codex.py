"""A study object: 206 scans as removable thick leaves, not a codicological reconstruction."""
import bpy, json, pathlib, math
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'blender-progress/Kodeks_206';OUT.mkdir(exist_ok=True)
PAGES=json.loads((ROOT/'quest-native/assets/pages.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
root=bpy.data.objects.new('CODEX_206_SCANS',None);bpy.context.collection.objects.link(root)
root['status']='Virtual scan index, not historic binding reconstruction'
root['scan_count']=len(PAGES)
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);return m
edge=mat('Paper_edges',(0.72,0.64,0.46));leather=mat('Study_binding',(0.16,0.085,0.04))
for i,p in enumerate(PAGES):
 # Vertical leaves make the prototype easy to examine or take apart in a VR workbench.
 h=1.4;w=h*p['width']/p['height'];depth=.0016
 y=i*.0020
 verts=[(-w/2,y-depth/2,0),(w/2,y-depth/2,0),(w/2,y-depth/2,h),(-w/2,y-depth/2,h),(-w/2,y+depth/2,0),(w/2,y+depth/2,0),(w/2,y+depth/2,h),(-w/2,y+depth/2,h)]
 faces=[(0,1,2,3),(5,4,7,6),(4,5,1,0),(1,5,6,2),(2,6,7,3),(4,0,3,7)]
 mesh=bpy.data.meshes.new('Scan_'+p['id']);mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new('PAGE_'+p['id']+'_f'+p['label'],mesh);bpy.context.collection.objects.link(obj);obj.parent=root
 obj['scan']=p['id'];obj['folio']=p['label'];obj['source_sha256']=p['sha256'];obj['role']='removable scan leaf'
 image=bpy.data.images.load(str(ROOT/'quest-native/assets/scans'/f'{p["id"]}.jpg'))
 ratio=min(1,384/max(image.size));image.scale(max(1,int(image.size[0]*ratio)),max(1,int(image.size[1]*ratio)));image.pack()
 m=mat('SOURCE_'+p['id'],(1,1,1));nodes=m.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage');tex.image=image;m.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color']);nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
 mesh.materials.append(m);mesh.materials.append(edge);uv=mesh.uv_layers.new()
 for poly in mesh.polygons:
  poly.material_index=0 if poly.index==0 else 1
  for li,xy in zip(poly.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=xy
 # Center the manipulation pivot on each scan, keeping its world location intact.
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS')
 if i and i%10==0:
  (OUT/'PROGRESS.json').write_text(json.dumps({'completed_scans':i+1,'total':206}))
# Study binding is intentionally separate from removable source leaves.
for name,loc,size in [('Study_front_cover',(0,-.013,.7),(1.22,.02,1.48)),('Study_back_cover',(0,.425,.7),(1.22,.02,1.48)),('Study_spine',(-.62,.21,.7),(.035,.46,1.48))]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(leather);o.parent=root
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in root.children_recursive:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'codex.glb'),export_format='GLB',use_selection=True,export_extras=True,export_lights=False,export_cameras=False)
scene=bpy.context.scene;scene.world=bpy.data.worlds.new('Studio');scene.world.color=(.2,.2,.2)
bpy.ops.object.camera_add(location=(3,-4,2.3));cam=bpy.context.object;cam.rotation_euler=((Vector((0,.2,.7))-cam.location).to_track_quat('-Z','Y').to_euler());cam.data.type='ORTHO';cam.data.ortho_scale=5.8;scene.camera=cam
for loc,power in [((2,-3,5),650),((-3,2,4),500)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=4;o.rotation_euler=((Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler())
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.render.resolution_x=800;scene.render.resolution_y=650;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Kodeks_206_Skanow.blend'))
(OUT/'PROGRESS.json').write_text(json.dumps({'completed_scans':206,'total':206,'status':'complete virtual scan stack; not historic binding','blender':bpy.app.version_string},indent=2))
(OUT/'README.md').write_text('206 skanów jako osobne, grube karty. Kolejność archiwum nie jest hipotezą o kolejności historycznej. Wielokartowe rozkładówki pozostają jednym skanem. Każda karta ma skan, folio i SHA-256 źródła. Tekstury 384 px służą przeglądowi całego kodeksu; większe skany są dostępne w katalogu aplikacji. Oprawa jest współczesnym obiektem pomocniczym.\n')
scene.render.filepath=str(OUT/'preview.png');bpy.ops.render.render(write_still=True)
print('CODEX_COMPLETE',len(PAGES),flush=True)
