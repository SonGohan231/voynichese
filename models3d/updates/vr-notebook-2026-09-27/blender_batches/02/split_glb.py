import json,struct,copy,pathlib,hashlib
ROOT=pathlib.Path(__file__).parent
raw=(ROOT/'garden.glb').read_bytes();size,typ=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+size]);p=20+size;bs,bt=struct.unpack_from('<II',raw,p);binary=raw[p+8:p+8+bs]
def write_subset(root_ids,path,recenter=False):
 ids=[]
 def walk(i):
  ids.append(i)
  for c in doc['nodes'][i].get('children',[]):walk(c)
 for i in root_ids:walk(i)
 nm={o:i for i,o in enumerate(ids)};out={'asset':doc['asset'],'scene':0,'scenes':[{'nodes':[nm[i] for i in root_ids]}],'nodes':[],'meshes':[],'materials':copy.deepcopy(doc.get('materials',[])),'accessors':[],'bufferViews':[],'buffers':[]};blob=bytearray();accmap={};meshmap={};viewmap={}
 def acc(i):
  if i in accmap:return accmap[i]
  a=copy.deepcopy(doc['accessors'][i]);vi=a['bufferView']
  if vi not in viewmap:
   view=copy.deepcopy(doc['bufferViews'][vi]);start=view.get('byteOffset',0);chunk=binary[start:start+view['byteLength']];blob.extend(b'\0'*((-len(blob))%4));view['byteOffset']=len(blob);view['buffer']=0;blob.extend(chunk);viewmap[vi]=len(out['bufferViews']);out['bufferViews'].append(view)
  a['bufferView']=viewmap[vi];accmap[i]=len(out['accessors']);out['accessors'].append(a);return accmap[i]
 for i in ids:
  n=copy.deepcopy(doc['nodes'][i]);n['children']=[nm[c] for c in n.get('children',[])];n.pop('camera',None);n.pop('extensions',None)
  if i in root_ids and recenter:n['translation']=[0,0,0]
  if 'mesh' in n:
   mi=n['mesh']
   if mi not in meshmap:
    m=copy.deepcopy(doc['meshes'][mi])
    for pr in m['primitives']:
     pr['attributes']={k:acc(v) for k,v in pr['attributes'].items()}
     if 'indices'in pr:pr['indices']=acc(pr['indices'])
    meshmap[mi]=len(out['meshes']);out['meshes'].append(m)
   n['mesh']=meshmap[mi]
  out['nodes'].append(n)
 out['buffers']=[{'byteLength':len(blob)}];j=json.dumps(out,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob.extend(b'\0'*((-len(blob))%4));result=struct.pack('<III',0x46546c67,2,28+len(j)+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob;path.write_bytes(result)
 return {'bytes':len(result),'sha256':hashlib.sha256(result).hexdigest(),'meshes':len(out['meshes']),'primitives':sum(len(m['primitives']) for m in out['meshes'])}
results=[]
for i,n in enumerate(doc['nodes']):
 if __import__('re').fullmatch(r'PLANT_s\d{4}',n.get('name','')):
  scan=n['name'][6:];stats=write_subset([i],ROOT/'plants'/f'{scan}.glb',True);results.append({'scan':scan,**stats})
(ROOT/'export-validation.json').write_text(json.dumps(results,indent=2));print(json.dumps(results));print('Total',len(results), 'garden mesh primitives',sum(len(m['primitives']) for m in doc['meshes']))
