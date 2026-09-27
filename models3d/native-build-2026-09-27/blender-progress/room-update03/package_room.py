from pathlib import Path
import zipfile,json,hashlib,os
R=Path(__file__).resolve().parent;ROOT=R.parent;dest=R/'release/Manuskrypt_Blender_Budynek_Ogrod_0.3.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in ['Manuskrypt_Budynek_Galerie_0_3.blend','Budynek_i_ogrod_editable.blend','Higgsfield_budynek_rev3.blend','compound.glb','layout.json','openings.json']:
  z.write(R/'building'/name,'Blender/'+name)
 for f in (R/'review').glob('*'):
  if f.is_file():z.write(f,'Review/'+f.name)
 for f in (ROOT/'quest-native').glob('*03-preview.png'):z.write(f,'VR/'+f.name)
 for f in (ROOT/'quest-native/assets/display').glob('*.glb'):z.write(f,'native_assets/display/'+f.name)
 z.write(R/'building/compound.glb','native_assets/room/compound.glb')
 z.write(R/'DISPLAY_PROGRESS.json','DISPLAY_PROGRESS.json');z.write(R/'recommendations.md','GitHub_5_rozwiazan.md')
 z.writestr('CZYTAJ.txt','Pełna scena lokalna Blender 4.5.4 zawiera budynek, ogród, porównanie rozet, 10 naczyń, książkę, karty i przykładowe rośliny. APK ładuje kolejne eksponaty z katalogu po 6. Higgsfield rev3 zawiera samą architekturę i meble. To współczesna fikcyjna pracownia badawcza, nie historyczna rekonstrukcja budynku. Plany i screenshoty opisują zakres testów; nie przeprowadzono próby fizycznego Questa.\n')
with dest.open('rb') as f:os.fsync(f.fileno())
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
print(dest.name,dest.stat().st_size,hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
with zipfile.ZipFile(R/'release/Manuskrypt_Audyt_206_0.3.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in (R/'audit').rglob('*'):
  if f.is_file():z.write(f,f.relative_to(R/'audit'))
 z.write(R/'recommendations.md','GitHub_5_rozwiazan.md')
