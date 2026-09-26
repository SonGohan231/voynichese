"""Deduplicate assembled GLTFs and create lighter full-scan web reliefs.
Run only after full-quality package has been exported and persisted.
"""
import json,struct,hashlib,copy,io
from pathlib import Path
from PIL import Image
import build_atlas as B
from optimize_validate import rewrite
A=B.OUT;atlas=json.loads((A/'atlas.json').read_text())
for p in atlas['pages']:
 # Keep original full-quality per-fragment GLB assets unchanged.
 im=Image.open(A/'images'/f"{p['id']}.jpg").convert('RGB');im.thumbnail((1100,1100));im.save(A/'images'/f"{p['id']}.jpg",quality=72,optimize=True)
 tex=im.copy();tex.thumbnail((800,800));g=B.GLB();mat=g.texture(tex);w,h=tex.size;geo=B.geom(tex,[0,0,w,h],(w,h),grid=36,depth=.009)
 extras={'source_scan':p['id'],'source_sha256':p['sha256'],'model_status':'CANDIDATE','depth_basis':'interpretive relief','quality':'web; full quality in downloadable ZIP'}
 g.mesh(p['id']+'_page',*geo,mat,extras);g.save(B.BASE/'dist'/p['page_model'],extras);p['page_model_sha256']=rewrite(B.BASE/'dist'/p['page_model'])[-1];p['web_texture_size']=[w,h]
 if p.get('art_model'):
  oldpath=B.BASE/'dist'/p['art_model'];cg={'asset':{'version':'2.0','generator':'Voynich shared-source assembly'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'textures':[],'images':[],'samplers':[],'accessors':[],'bufferViews':[],'buffers':[],'extras':{'scan_id':p['id'],'status':'CANDIDATE','depth_basis':'interpretive relief'}}
  for q in p['parts']:
   path=B.BASE/'dist'/q['model'];raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jl]);off={key:len(cg[key]) for key in ['nodes','meshes','materials','textures','images','samplers','accessors','bufferViews','buffers']}
   cg['buffers'].append({'uri':'../parts/'+path.name,'byteLength':len(raw)})
   for v in g['bufferViews']:v['buffer']=off['buffers'];v['byteOffset']=v.get('byteOffset',0)+28+jl;cg['bufferViews'].append(v)
   for a in g['accessors']:a['bufferView']+=off['bufferViews'];cg['accessors'].append(a)
   for im in g['images']:im['bufferView']+=off['bufferViews'];cg['images'].append(im)
   cg['samplers'].extend(g['samplers'])
   for t in g['textures']:t['source']+=off['images'];t['sampler']+=off['samplers'];cg['textures'].append(t)
   for m in g['materials']:m['pbrMetallicRoughness']['baseColorTexture']['index']+=off['textures'];cg['materials'].append(m)
   for m in g['meshes']:
    for prim in m['primitives']:
     prim['indices']+=off['accessors'];prim['material']+=off['materials'];prim['attributes']={k:v+off['accessors'] for k,v in prim['attributes'].items()}
    cg['meshes'].append(m)
   for n in g['nodes']:n['mesh']+=off['meshes'];cg['scenes'][0]['nodes'].append(len(cg['nodes']));cg['nodes'].append(n)
  newpath=oldpath.with_suffix('.gltf');newpath.write_text(json.dumps(cg,separators=(',',':'),ensure_ascii=False));p['art_model']=p['art_model'].replace('.glb','.gltf');p['art_model_sha256']=hashlib.sha256(newpath.read_bytes()).hexdigest();oldpath.unlink()
(A/'atlas.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
print('Web assets prepared:',len(atlas['pages']),flush=True)

for stale in (A/'art').glob('*.glb'):stale.unlink()
