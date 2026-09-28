"""Prepare the twenty source fragments for the native VR resource importer.

Crop textures losslessly to native pixel bounds. Preserve original Blender
masters separately; do not downsample, recolor, or JPEG-recompress the VR texture.
"""
import argparse,hashlib,io,json,struct
from pathlib import Path
import bpy,numpy as np
from PIL import Image

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--project',type=Path,required=True);args=ap.parse_args()
 work=args.work;dest=args.project/'assets/models/rebuilt';dest.mkdir(parents=True,exist_ok=True)
 (work/'vr-crops').mkdir(exist_ok=True)
 updated={p['id']:p for p in json.loads((work/'hollow/PROGRESS.json').read_text())['models']}
 pages={p['id']:p for p in json.loads((args.project/'assets/pages.json').read_text())}
 records=[]
 for batch in ('01','02'):
  for original in json.loads((work/f'batch{batch}/PROGRESS.json').read_text())['models']:
   rec=updated.get(original['id'],original);pid=rec['id'];page=pages[rec['scan']]
   src=work/('hollow' if pid in updated else f'batch{batch}')/'glb'/(pid+'.glb')
   source=next((work/'sources').glob(rec['scan'][1:]+'*.jpg'));assert hashlib.sha256(source.read_bytes()).hexdigest()==rec['source_sha256']
   crop=Image.open(source).convert('RGB').crop(rec['crop']);cropfile=work/'vr-crops'/(pid+'.png');crop.save(cropfile)
   bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
   im=bpy.data.images.load(str(cropfile.resolve()));im.colorspace_settings.name='sRGB';im.pack()
   x0,y0,x1,y1=rec['crop'];W,H=page['width'],page['height']
   for mat in bpy.data.materials:
    if mat.use_nodes:
     for node in mat.node_tree.nodes:
      if node.type=='TEX_IMAGE':node.image=im;node.interpolation='Closest'
   for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    for uv in obj.data.uv_layers.active.data:uv.uv=((uv.uv.x*W-x0)/(x1-x0),(uv.uv.y*H-(H-y1))/(y1-y0))
    obj['source_scan']=rec['scan'];obj['folio']=rec['folio'];obj['source_sha256']=rec['source_sha256'];obj['native_crop']=rec['crop'];obj['geometry_status']=rec['status']
   target=dest/(pid+'.glb');bpy.ops.export_scene.gltf(filepath=str(target.resolve()),export_format='GLB',export_extras=True,export_image_format='AUTO')
   data=target.read_bytes();jlen=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+jlen]);blob=data[28+jlen:]
   checks=[]
   for image in doc.get('images',[]):
    view=doc['bufferViews'][image['bufferView']];start=view.get('byteOffset',0);decoded=Image.open(io.BytesIO(blob[start:start+view['byteLength']])).convert('RGB')
    checks.append(decoded.size==crop.size and np.array_equal(np.array(decoded),np.array(crop)))
   assert checks and all(checks) and 'KHR_materials_unlit' in doc['extensionsUsed'],pid
   title=pid.replace('f78r_','').replace('_',' ')
   entry={'id':'rebuilt_'+pid,'scan':rec['scan'],'folio':rec['folio'],'title':title,'description':'Przebudowana bryła robocza; kolory i wzory ze skanu; geometria niezatwierdzona.',
    'category':'Rośliny' if 'root' in pid else 'Przepływy · przebudowa','model':'res://assets/models/rebuilt/'+pid+'.glb','display_model':'res://assets/models/rebuilt/'+pid+'.glb',
    'rebuild_batch':'F01','source_sha256':rec['source_sha256'],'source_bbox_px':rec['crop'],'status':rec['status'],'contour_verified':False,'depth':'inferred; not uniquely determined by source',
    'model_sha256':hashlib.sha256(data).hexdigest(),'texture_pixels_preserved':True,'texture_dimensions':list(crop.size),'hollow':pid in updated}
   records.append(entry)
 catalogpath=args.project/'assets/catalog.json';catalog=json.loads(catalogpath.read_text());catalog=[p for p in catalog if p.get('rebuild_batch')!='F01'];catalog+=records
 catalogpath.write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
 (work/'VR_BATCH_F01.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('VR_BATCH',len(records),'catalog',len(catalog),'exact lossless crop pixels',flush=True)

if __name__=='__main__':main()
