import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;N=R.parent/'quest-native';A=N/'assets';out=A/'display';out.mkdir(exist_ok=True);cat=json.load(open(A/'catalog.json'));records=[]
for i,c in enumerate(cat):
 path=N/c['model'].removeprefix('res://');name=c.get('id',c['scan']);dest=out/(name+'.glb')
 if not name.startswith(('relief_','flows_','marginal_','spatial_')):
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));groups={}
  for o in list(bpy.data.objects):
   if o.type=='MESH':
    world=o.matrix_world.copy();o.parent=None;o.matrix_world=world;groups.setdefault(tuple(m.name for m in o.data.materials),[]).append(o)
   else:bpy.data.objects.remove(o,do_unlink=True)
  for key,obs in groups.items():
   bpy.ops.object.select_all(action='DESELECT')
   for o in obs:o.select_set(True)
   bpy.context.view_layer.objects.active=obs[0]
   if len(obs)>1:bpy.ops.object.join()
  bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_apply=True,export_extras=False)
  c['display_model']='res://assets/display/'+name+'.glb';records.append({'id':name,'mesh_groups':len(groups),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
 else:c['display_model']=c['model']
 if i%10==9:(R/'DISPLAY_PROGRESS.json').write_text(json.dumps(records,indent=2));print('BATCH_LOD',i+1,flush=True)
(A/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2));(R/'DISPLAY_PROGRESS.json').write_text(json.dumps(records,indent=2));print('DONE',len(records),flush=True)
