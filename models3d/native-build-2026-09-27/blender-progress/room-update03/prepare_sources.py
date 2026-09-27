from pathlib import Path
import json,hashlib,sys,shutil,urllib.request,os
sys.path.insert(0,'/tmp/vct-py7zr');import py7zr
from PIL import Image
R=Path(__file__).resolve().parent;ROOT=R.parent;A=json.load(open(ROOT/'voynich-3d/public/assets/atlas.json'))['pages'];out=ROOT/'quest-native/assets/source_pixels';out.mkdir(exist_ok=True)
tmp=R/'extracted';tmp.mkdir(exist_ok=True);records=[]
for ar in sorted(set(p['archive'] for p in A)):
 pages=[p for p in A if p['archive']==ar]
 with py7zr.SevenZipFile(ROOT/'project_sources'/ar) as z:
  names=z.getnames();targets=[n for n in names if Path(n).name in {p['file'] for p in pages}];z.extract(tmp,targets=targets)
 for p in pages:
  f=next(tmp.rglob(p['file']));sha=hashlib.sha256(f.read_bytes()).hexdigest()
  if sha!=p['sha256']:
   if p.get('repair',{}).get('download_url'):
    with urllib.request.urlopen(p['repair']['download_url']) as r:f.write_bytes(r.read())
    sha=hashlib.sha256(f.read_bytes()).hexdigest()
   assert sha==p['sha256'],p['id']
  im=Image.open(f);im.load();assert im.size==(p['width'],p['height'])
  shutil.copyfile(f,out/(p['id']+'.jpgbin'))
  # source-faithful visual texture, CPU sample still uses full source bytes
  if p['category'] in ['Diagramy','Sceny i postacie','Zodiak']:
   visual=im.copy();visual.thumbnail((3072,3072));visual.convert('RGB').save(ROOT/'quest-native/assets/scans'/(p['id']+'.jpg'),quality=94)
  records.append({k:p[k] for k in ['id','label','width','height','sha256','category']}|{'bytes':f.stat().st_size,'icc_profile_present':bool(im.info.get('icc_profile')),'sample_space':'decoded source RGB; assumed sRGB/D65, not calibrated pigment'})
 print(ar,len(records),flush=True)
 (out/'index.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('ALL_SOURCE_PIXELS',len(records),sum(p['bytes'] for p in records),flush=True)
