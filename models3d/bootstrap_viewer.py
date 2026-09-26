"""Prepare this GitHub checkout from the full-quality model ZIP.
python models3d/bootstrap_viewer.py /path/Manuskrypt_206_modele_3D.zip
Requires Pillow; source scans already live in repository data/yale_hq_scans.
"""
import sys,json,zipfile,hashlib,urllib.request
from pathlib import Path
from PIL import Image
base=Path(__file__).resolve().parent;out=base/'dist';repo=base.parent
with zipfile.ZipFile(sys.argv[1]) as z:
 for item in z.infolist():
  if not item.filename.startswith('assets/') or item.is_dir():continue
  target=(out/item.filename).resolve()
  if not target.is_relative_to(out.resolve()):raise ValueError('Unsafe archive member')
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
atlas=json.loads((out/'assets/atlas.json').read_text());sources={p.name:p for p in (repo/'data/yale_hq_scans').rglob('*.jpg')}
for sub in ['images','thumbs']:(out/'assets'/sub).mkdir(exist_ok=True)
for p in atlas['pages']:
 src=sources[p['file']]
 if hashlib.sha256(src.read_bytes()).hexdigest()!=p['sha256']:raise ValueError('Source SHA mismatch: '+str(src))
 im=Image.open(src).convert('RGB');im.thumbnail((1550,1550));im.save(out/'assets/images'/f"{p['id']}.jpg",quality=90)
 im.thumbnail((150,180));im.save(out/'assets/thumbs'/f"{p['id']}.jpg",quality=82)
paths={'three.module.js':'build/three.module.js','three.core.js':'build/three.core.js','OrbitControls.js':'examples/jsm/controls/OrbitControls.js','TransformControls.js':'examples/jsm/controls/TransformControls.js','GLTFLoader.js':'examples/jsm/loaders/GLTFLoader.js','GLTFExporter.js':'examples/jsm/exporters/GLTFExporter.js','BufferGeometryUtils.js':'examples/jsm/utils/BufferGeometryUtils.js','THREE-LICENSE.txt':'LICENSE'}
(out/'vendor').mkdir(exist_ok=True)
for name,path in paths.items():
 data=urllib.request.urlopen('https://cdn.jsdelivr.net/npm/three@0.180.0/'+path).read().decode().replace('../utils/BufferGeometryUtils.js','./BufferGeometryUtils.js')
 (out/'vendor'/name).write_text(data)
print('Desktop: cd models3d/dist && python -m http.server 8000. Quest requires an HTTPS deployment of this directory.')
