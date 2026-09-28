"""Add the reviewed F01 resource delta over the exact, signed 0.3.1 base.

Keeps native libraries and Android classes intact. Output is unsigned: run
zipalign -P 16, then apksigner using the retained private signing key.
"""
import argparse,hashlib,json,struct,zipfile
from pathlib import Path

BASE_SHA='e5d3ff497a82f337177d488ac6a93124fbab34922c56fcd7fa849a3f7eceaeed'

def bump(data):
 b=bytearray(data);old='0.3.1'.encode('utf-16-le');new='0.3.2'.encode('utf-16-le');assert b.count(old)==1;b[b.index(old):b.index(old)+len(old)]=new
 cursor=8;resources=[];count=0
 while cursor<len(b):
  kind,header,size=struct.unpack_from('<HHI',b,cursor);assert size>=header and size>0
  if kind==0x0180:resources=list(struct.unpack_from('<'+'I'*((size-header)//4),b,cursor+header))
  elif kind==0x0102:
   start,step,n=struct.unpack_from('<HHH',b,cursor+24)
   for i in range(n):
    at=cursor+16+start+i*step;name=struct.unpack_from('<I',b,at+4)[0]
    if name<len(resources) and resources[name]==0x0101021b:
     assert b[at+15]==0x10 and struct.unpack_from('<I',b,at+16)[0]==4
     struct.pack_into('<I',b,at+16,5);count+=1
  cursor+=size
 assert count==1;return bytes(b)

def main():
 p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('delta',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE_SHA
 replacement={'assets/'+str(p.relative_to(a.delta)):p for p in a.delta.rglob('*') if p.is_file()}
 removed={'assets/scripts/workroom.gd.remap','assets/scripts/workroom.gdc'}
 with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'w',allowZip64=True) as new:
  for info in old.infolist():
   name=info.filename
   if name in replacement or name in removed:continue
   if name.startswith('META-INF/') and (name.endswith(('.RSA','.DSA','.EC','.SF')) or name=='META-INF/MANIFEST.MF'):continue
   data=old.read(info);info.extra=b''
   if name=='AndroidManifest.xml':data=bump(data)
   new.writestr(info,data)
  for name,path in sorted(replacement.items()):new.write(path,name,compress_type=zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(a.output) as z:
  assert z.testzip() is None
  catalog=json.loads(z.read('assets/assets/catalog.json'));assert len(catalog)==274 and sum(x.get('rebuild_batch')=='F01' for x in catalog)==20
  assert len(z.namelist())==len(set(z.namelist()))
 print('Unsigned 0.3.2, versionCode 5; 20 F01 additions; native libraries unchanged.')

if __name__=='__main__':main()
