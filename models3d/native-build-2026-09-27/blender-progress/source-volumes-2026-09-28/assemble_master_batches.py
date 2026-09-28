"""Save the current editable twenty models in two batches, including upgraded tubes."""
import argparse,hashlib,json
from pathlib import Path
import bpy
ap=argparse.ArgumentParser();ap.add_argument('work',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
for batch in ('01','02'):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 records=json.loads((a.work/f'batch{batch}/PROGRESS.json').read_text())['models']
 image_cache={}
 for i,rec in enumerate(records):
  pid=rec['id'];override=a.work/'hollow/glb'/(pid+'.glb');source=override if override.exists() else a.work/f'batch{batch}/glb'/(pid+'.glb')
  bpy.ops.object.select_all(action='DESELECT');bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
  nodes=list(bpy.context.selected_objects)
  for obj in nodes:
   if obj.parent is None:obj.location.x+=(i%5)*2.;obj.location.z-=(i//5)*2.
   obj['source_scan']=rec['scan'];obj['folio']=rec['folio'];obj['source_sha256']=rec['source_sha256'];obj['status']='DRAFT_HOLLOW_VOLUME' if override.exists() else rec['status']
  for mat in bpy.data.materials:
   if not mat.use_nodes:continue
   for node in mat.node_tree.nodes:
    if node.type!='TEX_IMAGE' or not node.image:continue
    img=node.image
    if not img.packed_file:img.pack()
    digest=hashlib.sha256(bytes(img.packed_file.data)).hexdigest()
    if digest in image_cache:node.image=image_cache[digest]
    else:image_cache[digest]=img
  for img in list(bpy.data.images):
   if img.users==0:bpy.data.images.remove(img)
 bpy.context.scene.view_settings.view_transform='Standard';bpy.context.scene.view_settings.look='None'
 bpy.context.scene['complete_manuscript']=False;bpy.context.scene['verified_1_to_1_geometry']=False
 bpy.context.scene['status']='10 editable candidates; source colors retained; depth interpreted'
 bpy.ops.wm.save_as_mainfile(filepath=str((a.output/f'Partia_{batch}_10_Bryl_0.3.2.blend').resolve()),compress=True)
 print('SAVED_BATCH',batch,len(records),flush=True)
