from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;out=R/'backup';out.mkdir(exist_ok=True);records=[];uploads=[]
for f in sorted((R/'release').glob('*.zip')):
 data=f.read_bytes();entry={'name':f.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'parts':[]}
 if len(data)>100*1024*1024:
  for i,start in enumerate(range(0,len(data),80*1024*1024)):
   b=data[start:start+80*1024*1024];p=out/(f.name+'.part%02d'%(i+1));p.write_bytes(b);entry['parts'].append({'name':p.name,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()});uploads.append(str(p.resolve()))
 else:uploads.append(str(f.resolve()))
 records.append(entry)
(out/'models-manifest.json').write_text(json.dumps(records,indent=2));(out/'upload-models.json').write_text(json.dumps(uploads,indent=2));print('uploads',len(uploads),'archives',len(records))
