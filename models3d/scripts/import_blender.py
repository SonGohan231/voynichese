"""Blender > Scripting > Run. Select extraction folder, scan and layer below."""
import bpy,json
from pathlib import Path
PACKAGE=Path(bpy.path.abspath('//'))  # change to unpacked models directory
SCAN='s0004'
LAYER='parts'  # page | art | parts | all
atlas=json.loads((PACKAGE/'assets/atlas.json').read_text())
page=next(p for p in atlas['pages'] if p['id']==SCAN)
paths=({'page':[page['page_model']],'art':[page.get('art_model',page['page_model'])],
 'parts':[p['model'] for p in page['parts']],'all':['assets/manuscript_all.glb']})[LAYER]
collection=bpy.data.collections.new('Voynich '+SCAN+' '+LAYER);bpy.context.scene.collection.children.link(collection)
for path in paths:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(PACKAGE/path))
 for obj in set(bpy.data.objects)-before:
  for old in list(obj.users_collection):old.objects.unlink(obj)
  collection.objects.link(obj)
# Fragment vertices use the source scan coordinates: no recentering is needed.
