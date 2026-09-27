import json,urllib.request,hashlib,os,time
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent/'tarot'; (root/'originals').mkdir(exist_ok=True); (root/'textures').mkdir(exist_ok=True)
raw=json.load(open(root/'commons-thumbnails.json'))
records=[]
for page in sorted(raw['query']['pages'].values(),key=lambda p:p['title']):
 title=page['title']; info=page['imageinfo'][0]
 if 'cropped' in title: continue
 key=title.replace('File:RWS1909 - ','').replace('File:Waite–Smith Tarot Roses and Lilies','back').replace('.jpeg','').replace('.jpg','').lower().replace(' ','_')
 out=root/'originals'/(key+'.jpg')
 if not out.exists():
  for attempt in range(4):
   try:
    data=urllib.request.urlopen(urllib.request.Request(info['thumburl'],headers={'User-Agent':'ManuskryptVR/0.2 (educational historical VR deck)'}),timeout=60).read()
    assert len(data)>1000
    time.sleep(1.5)
    with out.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    break
   except Exception as e:
    if attempt==3: raise
    time.sleep(20)
 im=Image.open(out).convert('RGB'); im.thumbnail((384,640)); im.save(root/'textures'/(key+'.jpg'),quality=93)
 meta=info['extmetadata']; license=meta.get('LicenseShortName',{}).get('value',''); assert 'Public domain' in license or 'PD' in license, (title,license)
 records.append({'id':key,'title':title,'source':info['descriptionurl'],'image_url':info['url'],'original_sha1':info['sha1'],'download_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'download_url':info.get('thumburl',info['url']),'license':license,'artist':meta.get('Artist',{}).get('value',''),'credit':meta.get('Credit',{}).get('value',''),'texture':key+'.jpg','size':list(im.size)})
 print(len(records),key,flush=True)
(root/'provenance.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
