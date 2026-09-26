"""Compact only web textures; retain complete mesh geometry and float UVs."""
from pathlib import Path
import json,struct,io,hashlib
from PIL import Image
A=Path(__file__).resolve().parents[1]/'dist/assets'
atlas=json.loads((A/'atlas.json').read_text());parts={};before=after=0
for p in (A/'parts').glob('*.glb'):
 raw=p.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jl]);old=raw[28+jl:];new=bytearray();replace={}
 for im in g['images']:
  v=g['bufferViews'][im['bufferView']];img=Image.open(io.BytesIO(old[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGBA');img=img.quantize(colors=64,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE);out=io.BytesIO();img.save(out,format='PNG',optimize=True);replace[im['bufferView']]=out.getvalue();im['mimeType']='image/png'
 for i,v in enumerate(g['bufferViews']):
  data=replace.get(i,old[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);new.extend(b'\0'*((-len(new))%4));v['byteOffset']=len(new);v['byteLength']=len(data);new.extend(data)
 g['buffers'][0]['byteLength']=len(new);g['extras']['web_optimization']='64-color palette textures only. Full texture quality in downloadable ZIP.'
 j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);new+=b'\0'*((-len(new))%4);out=struct.pack('<III',0x46546c67,2,28+len(j)+len(new))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(new),0x004e4942)+new;p.write_bytes(out);before+=len(raw);after+=len(out);parts[p.name]=(g,len(out),28+len(j))
for p in atlas['pages']:
 for q in p['parts']:q['sha256']=hashlib.sha256((A.parent/q['model']).read_bytes()).hexdigest()
 if p.get('art_model'):
  path=A.parent/p['art_model'];g=json.loads(path.read_text())
  for bi,buf in enumerate(g['buffers']):
   pg,total,offset=parts[Path(buf['uri']).name];buf['byteLength']=total
   views=[v for v in g['bufferViews'] if v['buffer']==bi];assert len(views)==len(pg['bufferViews'])
   for v,newv in zip(views,pg['bufferViews']):v['byteOffset']=newv.get('byteOffset',0)+offset;v['byteLength']=newv['byteLength']
  path.write_text(json.dumps(g,separators=(',',':'),ensure_ascii=False));p['art_model_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(A/'atlas.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
for obsolete in (A/'art').glob('*.glb'):obsolete.unlink()
print({'before':before,'after':after,'saved':before-after,'static_bytes':sum(p.stat().st_size for p in A.parent.rglob('*') if p.is_file())},flush=True)
