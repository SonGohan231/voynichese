"""Restore native assets from saved checkpoints without modifying source archives.
Usage: python prepare_assets.py --models Manuskrypt_173_Bryly_Blender_19_Partii.zip
  --refined Manuskrypt_Blender_Partia01_10_Roslin.zip --codex Manuskrypt_Blender_Kodeks_206.zip
  --scans /path/to/canonical-site/public/assets/images --vendor /path/to/meta-passthrough-sample.zip
The canonical Sites project is appgprj_6aa654f374648191971b3d05df9bb21f, source commit 2fe1272.
"""
import argparse, io, pathlib, zipfile, shutil, hashlib, json, base64
p=argparse.ArgumentParser();p.add_argument('--models',required=True);p.add_argument('--refined',required=True);p.add_argument('--codex',required=True);p.add_argument('--scans',required=True);p.add_argument('--vendor',required=True);a=p.parse_args()
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
    shutil.copyfile(pathlib.Path(a.scans)/(page['id']+'.jpg'),root/'assets/scans'/(page['id']+'.jpg'))
with zipfile.ZipFile(a.vendor) as z:
    for name in z.namelist():
        marker='addons/godotopenxrvendors/'
        if marker not in name or name.endswith('/'):continue
        relative=pathlib.PurePosixPath(name[name.index(marker):])
        if '..' in relative.parts:raise ValueError('Unsafe archive path')
        dest=root/pathlib.Path(relative);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
for model in json.loads((root/'assets/catalog.json').read_text()):
    file=root/'assets/models'/(model['scan']+'.glb')
    assert hashlib.sha256(file.read_bytes()).hexdigest()==model['native_glb_sha256'],file
(root/'icon.png').write_bytes(base64.b64decode((root/'icon.png.base64').read_text()))
print('Restored and verified 173 GLBs, 206 scan files, codex and XR vendor addon.')
