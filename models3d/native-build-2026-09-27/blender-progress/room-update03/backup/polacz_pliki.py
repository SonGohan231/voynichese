"""Run in the downloaded release folder: verifies parts, rebuilds large ZIP/APK files."""
from pathlib import Path
import json,hashlib,os
R=Path(__file__).resolve().parent
for manifest in sorted(R.glob('*manifest.json')):
 entries=json.loads(manifest.read_text());entries=entries if isinstance(entries,list) else [entries]
 for e in entries:
  if not e.get('parts'):continue
  dest=R/e['name'];temporary=dest.with_name(dest.name+'.assembling');whole=hashlib.sha256()
  try:
   with temporary.open('wb') as out:
    for part in e['parts']:
     f=R/part['name'];data=f.read_bytes();assert len(data)==part['size'] and hashlib.sha256(data).hexdigest()==part['sha256'],f'Niepoprawna część: {f.name}'
     out.write(data);whole.update(data)
    out.flush();os.fsync(out.fileno())
   assert temporary.stat().st_size==e['size'] and whole.hexdigest()==e['sha256'],'Niezgodna suma całego pliku'
   temporary.replace(dest);print('OK',dest.name)
  except BaseException:
   if temporary.exists():temporary.unlink()
   raise
