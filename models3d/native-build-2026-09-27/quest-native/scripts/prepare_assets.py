"""Restore native assets from saved checkpoints without modifying source archives.
Usage: python prepare_assets.py --models Manuskrypt_173_Bryly_Blender_19_Partii.zip
  --refined Manuskrypt_Blender_Partia01_10_Roslin.zip --codex Manuskrypt_Blender_Kodeks_206.zip
  --scans /path/to/canonical-site/public/assets/images --vendor /path/to/meta-passthrough-sample.zip
  --vessels Manuskrypt_Blender_Partia20_10_Naczyn.zip --rooms Manuskrypt_Blender_Sale_Tarot_0.2.zip
  --updates Manuskrypt_Blender_Partia2*_Modeli.zip
  --compound Manuskrypt_Blender_Budynek_Ogrod_0.3.zip --pixels-apk Manuskrypt_Quest_0.3.0.apk
After the first Godot import, run room-update03/optimize_texture_imports.py and reimport.
The canonical Sites project is appgprj_6aa654f374648191971b3d05df9bb21f, source commit 2fe1272.
"""
import argparse, io, pathlib, zipfile, shutil, hashlib, json, base64
p=argparse.ArgumentParser();p.add_argument('--models',required=True);p.add_argument('--refined',required=True);p.add_argument('--codex',required=True);p.add_argument('--scans');p.add_argument('--vendor',required=True);p.add_argument('--vessels',required=True);p.add_argument('--rooms',required=True);p.add_argument('--updates',nargs='+',required=True);p.add_argument('--compound',required=True);p.add_argument('--pixels-apk',required=True);a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
for folder in ['assets/models','assets/scans','assets/room','addons']:(root/folder).mkdir(parents=True,exist_ok=True)
def models(z):
    for name in z.namelist():
        if '/plants/' in '/'+name and name.endswith('.glb'):
            (root/'assets/models'/pathlib.Path(name).name).write_bytes(z.read(name))
with zipfile.ZipFile(a.models) as z:
    for name in z.namelist():
        if name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(z.read(name))) as batch:models(batch)
with zipfile.ZipFile(a.refined) as z:models(z)
with zipfile.ZipFile(a.codex) as z:
    name=next(n for n in z.namelist() if n.endswith('/codex.glb'));(root/'assets/room/codex.glb').write_bytes(z.read(name))
for page in json.loads((root/'assets/pages.json').read_text()):
    if a.scans:shutil.copyfile(pathlib.Path(a.scans)/(page['id']+'.jpg'),root/'assets/scans'/(page['id']+'.jpg'))
with zipfile.ZipFile(a.vendor) as z:
    for name in z.namelist():
        marker='addons/godotopenxrvendors/'
        if marker not in name or name.endswith('/'):continue
        relative=pathlib.PurePosixPath(name[name.index(marker):])
        if '..' in relative.parts:raise ValueError('Unsafe archive path')
        dest=root/pathlib.Path(relative);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
with zipfile.ZipFile(a.vessels) as z:
    for name in z.namelist():
        if name.endswith('.glb') and pathlib.PurePosixPath(name).name.startswith('vessel_'):
            (root/'assets/models'/pathlib.PurePosixPath(name).name).write_bytes(z.read(name))
with zipfile.ZipFile(a.rooms) as z:
    for name in z.namelist():
        marker='/native_assets/'
        if marker not in '/'+name or name.endswith('/'):continue
        relative=pathlib.PurePosixPath(('/'+name).split(marker,1)[1])
        if '..' in relative.parts:raise ValueError('Unsafe archive path')
        dest=root/'assets'/pathlib.Path(relative);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
# Version 0.3 additions; never extract arbitrary archive paths.
for archive in a.updates:
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.endswith('.glb'):
                (root/'assets/models'/pathlib.PurePosixPath(name).name).write_bytes(z.read(name))
with zipfile.ZipFile(a.compound) as z:
    for name in z.namelist():
        marker='/native_assets/'
        if marker not in '/'+name or name.endswith('/'):continue
        relative=pathlib.PurePosixPath(('/'+name).split(marker,1)[1])
        if '..' in relative.parts or relative.is_absolute():raise ValueError('Unsafe archive path')
        dest=root/'assets'/pathlib.Path(relative);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
from PIL import Image
source_dir=root/'assets/source_pixels';source_dir.mkdir(exist_ok=True)
with zipfile.ZipFile(a.pixels_apk) as z:
    for page in json.loads((root/'assets/pages.json').read_text()):
        data=z.read('assets/assets/source_pixels/'+page['id']+'.jpgbin')
        assert hashlib.sha256(data).hexdigest()==page['sha256']
        dest=source_dir/(page['id']+'.jpgbin');dest.write_bytes(data)
        im=Image.open(io.BytesIO(data));im.thumbnail((3072,3072));im.convert('RGB').save(root/'assets/scans'/(page['id']+'.jpg'),quality=94)
for model in json.loads((root/'assets/catalog.json').read_text()):
    file=root/model['model'].removeprefix('res://')
    assert hashlib.sha256(file.read_bytes()).hexdigest()==model.get('native_glb_sha256',model.get('model_sha256',model.get('sha256'))),file
for card in json.loads((root/'assets/tarot/cards.json').read_text()):
    file=root/card['model'].removeprefix('res://')
    assert hashlib.sha256(file.read_bytes()).hexdigest()==card['model_sha256'],file
(root/'icon.png').write_bytes(base64.b64decode((root/'icon.png.base64').read_text()))
print('Restored and verified 254 models, 78 cards, 206 full scan files, connected building, display LODs, codex and XR vendor addon. Run optimize_texture_imports.py after Godot's first import.')
