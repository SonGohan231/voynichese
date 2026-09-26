"""Compact unused vertices and validate all deliverable meshes / provenance."""
import json,struct,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]/'dist';A=ROOT/'assets'
def rewrite(path):
 raw=path.read_bytes();magic,version,total=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and total==len(raw)
 jl,jt=struct.unpack_from('<II',raw,12);assert jt==0x4e4f534a;g=json.loads(raw[20:20+jl]);bl,bt=struct.unpack_from('<II',raw,20+jl);assert bt==0x004e4942;old=raw[28+jl:28+jl+bl];new=bytearray();views=[];accessors=[]
 def data(b,target=None):
  new.extend(b'\0'*((-len(new))%4));v={'buffer':0,'byteOffset':len(new),'byteLength':len(b)}
  if target:v['target']=target
  views.append(v);new.extend(b);return len(views)-1
 def arr(i):
  a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];off=v.get('byteOffset',0)+a.get('byteOffset',0);dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];dim={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
  return np.frombuffer(old,dtype=dt,count=a['count']*dim,offset=off).reshape(a['count'],dim)
 def attr(a,kind):
  component=5126 if a.dtype.kind=='f' else (5123 if a.dtype.itemsize==2 else 5125);v=data(a.tobytes(),34963 if kind=='SCALAR' else 34962);obj={'bufferView':v,'componentType':component,'count':len(a),'type':kind}
  if kind=='VEC3':obj.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
  accessors.append(obj);return len(accessors)-1
 faces=verts=0
 for mesh in g['meshes']:
  for p in mesh['primitives']:
   idx=arr(p['indices']).ravel();pos=arr(p['attributes']['POSITION']);assert len(idx)%3==0 and idx.max()<len(pos) and np.isfinite(pos).all()
   unique,inv=np.unique(idx,return_inverse=True);f=inv.astype(np.uint16 if len(unique)<65536 else np.uint32)
   attrs={}
   for k,v in p['attributes'].items():
    a=arr(v)[unique];assert np.isfinite(a).all();attrs[k]=attr(a,g['accessors'][v]['type'])
   p['attributes']=attrs;p['indices']=attr(f.reshape(-1,1),'SCALAR');verts+=len(unique);faces+=len(idx)//3
 for image in g['images']:
  v=g['bufferViews'][image['bufferView']];image['bufferView']=data(old[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
 g['accessors']=accessors;g['bufferViews']=views;g['buffers']=[{'byteLength':len(new)}]
 j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);new+=b'\0'*((-len(new))%4);out=struct.pack('<III',magic,2,28+len(j)+len(new))+struct.pack('<II',len(j),jt)+j+struct.pack('<II',len(new),bt)+new;path.write_bytes(out)
 return len(raw),len(out),faces,verts,hashlib.sha256(out).hexdigest()
if __name__=='__main__':
 atlas=json.loads((A/'atlas.json').read_text());expected={p['page_model'] for p in atlas['pages']}|{p['art_model'] for p in atlas['pages'] if p.get('art_model')}|{q['model'] for p in atlas['pages'] for q in p['parts']}|{'assets/manuscript_all.glb'}
 # Remove only stale generated files from older pipeline passes.
 for folder in ['pages','art','parts']:
  for path in (A/folder).glob('*.glb'):
   if path.relative_to(ROOT).as_posix() not in expected:path.unlink()
 report={'scan_count':len(atlas['pages']),'part_count':sum(len(p['parts']) for p in atlas['pages']),'model_count':len(expected),'before_bytes':0,'after_bytes':0,'triangles':0,'vertices':0,'hashes':{}}
 for i,name in enumerate(sorted(expected)):
  before,after,tri,ver,sha=rewrite(ROOT/name);report['before_bytes']+=before;report['after_bytes']+=after;report['triangles']+=tri;report['vertices']+=ver;report['hashes'][name]=sha
  if i%500==0:print('validated',i,flush=True)
 for p in atlas['pages']:
  p['page_model_sha256']=report['hashes'][p['page_model']]
  if p.get('art_model'):p['art_model_sha256']=report['hashes'][p['art_model']]
  for q in p['parts']:q['sha256']=report['hashes'][q['model']]
 assert [p['scan_number'] for p in atlas['pages']]==list(range(1,207))
 assert len(set(p['id'] for p in atlas['pages']))==206
 (A/'atlas.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
 (A/'validation.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='hashes'})
