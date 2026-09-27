from pathlib import Path
import json,zipfile,hashlib,os
R=Path(__file__).resolve().parent;ROOT=R.parent;OUT=R/'release';OUT.mkdir(exist_ok=True)
recs=json.load(open(R/'PROGRESS.json'))['models']+json.load(open(R/'details/PROGRESS.json'));batches=sorted(set(m['batch'] for m in recs));man=[]
for batch in batches:
 models=[m for m in recs if m['batch']==batch];dest=OUT/('Manuskrypt_Blender_Partia'+batch+'_'+str(len(models))+'_Modeli.zip')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.writestr('PROGRESS.json',json.dumps({'models':models,'status':'CANDIDATE; source-projected reliefs and inferred volumes','count':len(models)},ensure_ascii=False,indent=2))
  z.writestr('CZYTAJ.txt','Modele wykonano w Blenderze 4.5.4. Każdy plik .blend jest edytowalny, tekstury spakowane. GLB do VR. Głębia nie jest pomiarem: reliefy zachowują pełny rysunek w teksturze; bryły przestrzenne są interpretacjami. Nie potwierdzono kompletnego spisu pojedynczych rysunków. SHA-256 i folio w PROGRESS.json. Oryginały pochodzą z dostarczonych archiwów; APK 0.3 zawiera pełne skany do próbnika RGB.\n')
  for m in models:
   d=(R/'details' if batch=='28' else R/'models')/m['id']
   for ext in ['.blend','.glb']:z.write(d/(m['id']+ext),m['id']+'/'+m['id']+ext)
 with dest.open('rb') as f:os.fsync(f.fileno())
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
 rec={'name':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'models':len(models)};man.append(rec);print(rec,flush=True)
(OUT/'CHECKPOINTS.json').write_text(json.dumps(man,indent=2))
