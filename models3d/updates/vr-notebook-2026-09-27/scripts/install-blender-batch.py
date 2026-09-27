"""Register a completed, visually inspected Blender batch; preserve originals in a separate ZIP."""
import pathlib,sys,json,re,shutil,subprocess,hashlib,zipfile
repo=pathlib.Path(__file__).resolve().parents[1];number=sys.argv[1].zfill(2);project=sys.argv[2];revision=int(sys.argv[3]);b=repo.parent/('batch'+number);(b/'plants').mkdir(exist_ok=True)

if number!='02':shutil.copy(repo.parent/'batch02/split_glb.py',b/'split_glb.py')
subprocess.run([sys.executable,str(b/'split_glb.py')],check=True,stdout=subprocess.DEVNULL)
atlas=json.loads((repo/'public/assets/atlas.json').read_text());lookup={p['id']:p for p in atlas['pages']};out=repo/'public/assets'/('volume'+number);out.mkdir(exist_ok=True);entries=[]
for f in sorted((b/'plants').glob('s*.glb')):
 if not re.fullmatch(r's\d{4}',f.stem):continue
 p=lookup[f.stem];shutil.copy(f,out/f.name);entries.append({'scan':p['id'],'folio':p['label'],'category':p['category'],'description':'Bryła interpretacyjna rysunku; boki i głębia hipotetyczne.','status':'CANDIDATE_VOLUME_INTERPRETATION','source_sha256':p['sha256'],'source_width':p['width'],'source_height':p['height'],'model':f'assets/volume{number}/{f.name}','batch':number,'model_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'blender_project':project,'blender_revision':revision})
assert 1<=len(entries)<=10
for p in [out/'manifest.json',b/'manifest.json']:p.write_text(json.dumps(entries,ensure_ascii=False,indent=2))
flatpath=repo/'public/assets/volumes.json';flat=json.loads(flatpath.read_text());flat=[m for m in flat if m['batch']!=number]+entries;flat.sort(key=lambda m:m['scan']);flatpath.write_text(json.dumps(flat,ensure_ascii=False,indent=2))
d=repo/'blender_batches'/number;d.mkdir(exist_ok=True)
for n in ['build.py','split_glb.py','manifest.json','export-validation.json']:shutil.copy(b/n,d/n)
(b/'README.md').write_text(f'Partia {number} — {len(entries)} brył: '+', '.join('f'+m['folio'] for m in entries)+f'\nBlender 5.2; projekt {project}; rewizja {revision}.\nModele robocze wykonane w Blenderze. Układ widocznych elementów nawiązuje do rysunku; boki, tyły i głębia pozostają interpretacją. Ręczna weryfikacja konturów nadal potrzebna. Bez identyfikacji gatunków i bez wniosków o znaczeniu tekstu.\nWspółrzędne w metrach umownej skali ekspozycji.\n')
(b/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(b)) for p in sorted(b.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt')+'\n')
archive=repo.parent/f'Manuskrypt_Blender_Partia{number}_{len(entries)}_Modeli.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(b.rglob('*')):
  if p.is_file():z.write(p,'Partia'+number+'/'+str(p.relative_to(b)))
print(json.dumps({'batch':number,'models':len(entries),'catalog':len(flat),'archive':str(archive)}))
