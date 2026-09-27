from pathlib import Path
import zipfile,shutil,json,hashlib,os
R=Path(__file__).resolve().parent;root=R.parent;N=root/'quest-native/assets'
# Checkpoint the ten newly reconstructed objects as a separate batch.
path=root/'Manuskrypt_Blender_Partia20_10_Naczyn.zip'
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in sorted((R/'vessels').rglob('*')):
  if f.is_file() and f.suffix not in ['.blend1']:z.write(f,'Partia20/'+str(f.relative_to(R/'vessels')))
 for f in (R/'source/originals').glob('*.jpg'):z.write(f,'Partia20/original_scans/'+f.name)
with path.open('rb') as f:os.fsync(f.fileno())
# Room sources, full tarot deck, native-ready assets and visual verification.
path=root/'Manuskrypt_Blender_Sale_Tarot_0.2.zip'
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in ['Pracownia_i_Sala_Naczyn_Tarot.blend','Archive_editable_4_5.blend','archive_higgsfield_rev2.blend','Manuskrypt_otwarty.blend','pharmacy-preview.png','furnished-preview.png','preview-final.png']:
  f=R/'architecture'/name
  if f.exists():z.write(f,'Sale_Tarot/architecture/'+name)
 for name in ['Tarot_78_editable.blend','cards.json','provenance.json','README.md']:z.write(R/'tarot'/name,'Sale_Tarot/tarot/'+name)
 for f in (R/'tarot/models').glob('*.glb'):z.write(f,'Sale_Tarot/native_assets/tarot/models/'+f.name)
 for name in ['cards.json','provenance.json','README.md']:z.write(R/'tarot'/name,'Sale_Tarot/native_assets/tarot/'+name)
 for name in ['archive.glb','open_book.glb']:z.write(N/'room'/name,'Sale_Tarot/native_assets/room/'+name)
 for scan in ['s0161','s0163','s0175']:z.write(N/'scans'/(scan+'.jpg'),'Sale_Tarot/native_assets/scans/'+scan+'.jpg')
 for name in ['tarot-preview.png','gallery-preview.png','menu-preview.png']:z.write(root/'quest-native'/name,'Sale_Tarot/vr_preview/'+name)
 z.writestr('Sale_Tarot/README.md','''# Pracownia i sala naczyń + tarot 0.2\n\nDwie połączone sale z meblami, oświetleniem, portalem, regałami, świecami, otwartym Manuskryptem i stołem tarota.\n\nPracownia_i_Sala_Naczyn_Tarot.blend: gotowa scena Blendera 4.5.4. Archive_editable_4_5.blend: osobne meble i elementy architektury. archive_higgsfield_rev2.blend: źródło Higgsfield / Blender 5.2. Tarot_78_editable.blend: wszystkie 78 kart jako osobne obiekty. native_assets: zasoby do Godot/Quest.\n\nW plikach GLB sceny statyczne pogrupowano według materiału dla wydajności. Modele naczyń są w osobnej partii 20 i w aplikacji. W pliku kompletnej sceny również są osadzone. Interakcje, interpretacja tarota i zapis są realizowane przez kod aplikacji Godot zapisany w repozytorium. Sam plik Blender nie wykonuje tych interakcji.\n\nModele naczyń są kandydacką rekonstrukcją brył; źródła i ograniczenia opisuje partia 20. Architektura jest nową aranżacją badawczą, nie historyczną rekonstrukcją miejsca powstania Manuskryptu.\n\nPodglądy vr_preview pochodzą z faktycznego renderowania Godot na komputerze. Nie są testem wydajności gogli.\n''')
with path.open('rb') as f:os.fsync(f.fileno())
for p in [root/'Manuskrypt_Blender_Partia20_10_Naczyn.zip',path]:
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
 print(p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
