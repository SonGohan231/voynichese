"""Voynich source-grounded relief atlas. Depth is interpretive, not measured.
Inputs are read-only decoded photographs. Every extraction remains CANDIDATE.
"""
import json,struct,hashlib,io,math,os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np,cv2
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parent;OUT=BASE/'dist/assets'
for sub in ['pages','art','parts','images','thumbs','masks']: (OUT/sub).mkdir(parents=True,exist_ok=True)
source=json.loads((ROOT/'work/source_manifest.json').read_text());VERSION='2.0.0'

def category(n):
 if n<3:return 'Okładki'
 if n in [3,115,116,119,155,157] or n>=183:return 'Tekst i drobne znaki'
 if n in [114,121,122,123,124,125,126,156,158]:return 'Diagramy'
 if 127<=n<=134:return 'Zodiak'
 if 135<=n<=154:return 'Sceny i postacie'
 if 161<=n<=164 or 175<=n<=182:return 'Małe rośliny i naczynia'
 return 'Rośliny'

class GLB:
 def __init__(self):
  self.bin=bytearray();self.g={'asset':{'version':'2.0','generator':'Voynich relief atlas '+VERSION},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'textures':[],'images':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],'accessors':[],'bufferViews':[]}
 def data(self,b,target=None):
  self.bin.extend(b'\0'*((-len(self.bin))%4));v={'buffer':0,'byteOffset':len(self.bin),'byteLength':len(b)}
  if target:v['target']=target
  i=len(self.g['bufferViews']);self.g['bufferViews'].append(v);self.bin.extend(b);return i
 def attr(self,a,kind):
  a=np.ascontiguousarray(a);idx=len(self.g['accessors']);v=self.data(a.tobytes(),34963 if kind=='SCALAR' else 34962)
  d={'bufferView':v,'componentType':5125 if a.dtype==np.uint32 else 5126,'count':len(a),'type':kind}
  if kind=='VEC3':d.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
  self.g['accessors'].append(d);return idx
 def texture(self,image,alpha=False):
  b=io.BytesIO();image.save(b,format='PNG' if alpha else 'JPEG',**({} if alpha else {'quality':88}))
  v=self.data(b.getvalue());i=len(self.g['images']);self.g['images'].append({'bufferView':v,'mimeType':'image/png' if alpha else 'image/jpeg'});self.g['textures'].append({'source':i,'sampler':0})
  mat={'name':'Source pigments','pbrMetallicRoughness':{'baseColorTexture':{'index':i},'metallicFactor':0,'roughnessFactor':.9},'doubleSided':True}
  if alpha:mat.update(alphaMode='MASK',alphaCutoff=.35)
  self.g['materials'].append(mat);return len(self.g['materials'])-1
 def mesh(self,name,vertices,triangles,uv,material,extras=None,translation=None):
  # Area-weighted vertex normals on the actual geometry.
  v=np.asarray(vertices,dtype=np.float32);f=np.asarray(triangles,dtype=np.uint32);n=np.zeros_like(v)
  cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
  for j in range(3):np.add.at(n,f[:,j],cross)
  norm=np.linalg.norm(n,axis=1);n/=np.maximum(norm[:,None],1e-12)
  attrs={'POSITION':self.attr(v,'VEC3'),'NORMAL':self.attr(n,'VEC3'),'TEXCOORD_0':self.attr(np.asarray(uv,np.float32),'VEC2')}
  m=len(self.g['meshes']);self.g['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'indices':self.attr(f.ravel(),'SCALAR'),'material':material}]})
  node={'name':name,'mesh':m,'extras':extras or {}}
  if translation is not None:node['translation']=translation
  self.g['scenes'][0]['nodes'].append(len(self.g['nodes']));self.g['nodes'].append(node)
 def save(self,path,extras=None):
  g=self.g;g['buffers']=[{'byteLength':len(self.bin)}];g['extras']=extras or {}
  j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);b=bytes(self.bin);b+=b'\0'*((-len(b))%4)
  data=struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b;path.write_bytes(data)
  return hashlib.sha256(data).hexdigest()

def geom(image,box,page_size,mask=None,grid=105,depth=.014):
 w,h=image.size;nx=max(3,round(grid*w/max(w,h)));ny=max(3,round(grid*h/max(w,h)))
 gray=cv2.cvtColor(np.asarray(image.convert('RGB')),cv2.COLOR_RGB2GRAY)/255
 strength=np.maximum(0,cv2.GaussianBlur(gray,(0,0),7)-gray)
 height=cv2.resize(strength,(nx+1,ny+1),interpolation=cv2.INTER_AREA)*depth
 if mask is not None:
  dist=cv2.distanceTransform(np.asarray(mask,dtype=np.uint8),cv2.DIST_L2,5)
  height+=cv2.resize((1-np.exp(-dist/9))*depth,(nx+1,ny+1),interpolation=cv2.INTER_AREA)
 height+=.0012
 xs=np.linspace(box[0],box[2],nx+1);ys=np.linspace(box[1],box[3],ny+1);xx,yy=np.meshgrid(xs,ys)
 ph=page_size[1];pw=page_size[0];front=np.stack(((xx-pw/2)/ph,(ph/2-yy)/ph,height),axis=-1).reshape(-1,3)
 u,v=np.meshgrid(np.linspace(0,1,nx+1),np.linspace(0,1,ny+1));uv=np.stack((u,v),axis=-1).reshape(-1,2)
 ids=np.arange((nx+1)*(ny+1)).reshape(ny+1,nx+1);a=ids[:-1,:-1].ravel();b=ids[1:,:-1].ravel();c=ids[:-1,1:].ravel();d=ids[1:,1:].ravel()
 faces=np.concatenate((np.stack((a,b,c),1),np.stack((b,d,c),1)))
 if mask is not None:
  small=cv2.resize(np.asarray(mask,dtype=np.uint8),(nx,ny),interpolation=cv2.INTER_AREA)>15
  keep=np.r_[small.ravel(),small.ravel()];faces=faces[keep]
 if not len(faces):return None
 # Actual thickness, back faces and boundary walls; no flat billboards.
 N=len(front);back=front.copy();back[:,2]=-.0008
 allf=[faces,faces[:,::-1]+N];edges={}
 for face in faces:
  for a,b in zip(face,np.roll(face,-1)):
   key=tuple(sorted((int(a),int(b))));edges[key]=None if key in edges else (a,b)
 walls=[]
 for e in edges.values():
  if e is not None:
   a,b=e;walls.extend([[a,b+N,b],[a,a+N,b+N]])
 if walls:allf.append(np.asarray(walls,np.uint32))
 return np.concatenate((front,back)),np.concatenate(allf),np.concatenate((uv,uv))

# Manual exclusions for the first three plants. Coordinates normalized to scans.
# Text/paper excluded; shapes retain scan pigments. These are editorial masks, not botanical claims.
regions3={
4:[('Ulistnienie',[.177,.219,.949,.485]),('Dolne liście',[.371,.465,.658,.651]),('Kwiat',[.490,.112,.611,.222]),('Liście górne',[.440,.157,.656,.313]),('Łodyga dolna',[.501,.577,.544,.838]),('Część korzeniowa',[.200,.772,.796,.949])],
5:[('Kwiat lewy',[.228,.147,.390,.285]),('Kwiat środkowy',[.419,.053,.549,.194]),('Kwiat prawy',[.659,.059,.837,.211]),('Liście i rozgałęzienia',[.171,.266,.899,.652]),('Łodyga dolna',[.547,.608,.601,.889]),('Część korzeniowa',[.428,.851,.720,.969])],
6:[('Kwiat',[.630,.040,.873,.222]),('Szypułka',[.671,.207,.724,.300]),('Duży liść',[.344,.271,.866,.615]),('Łodyga',[.579,.495,.684,.915]),('Część korzeniowa',[.142,.879,.950,.952])]}

def foreground(im,n,cat):
 rgb=np.asarray(im);h,w=rgb.shape[:2];hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV).astype(float);H,S,V=hsv[:,:,0],hsv[:,:,1]/255,hsv[:,:,2]/255
 gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(float)/255;local=cv2.GaussianBlur(gray,(0,0),8)
 color=(((H>31)&(H<115)&(S>.12)&(V<.85))|((H<14)&(S>.39)&(V<.77))|((H>94)&(S>.3)&(V<.72))|((H<30)&(S>.45)&(V<.72)))
 if n==4:
  region=np.zeros((h,w),bool);region[int(h*.16):int(h*.66),int(w*.17):int(w*.95)]=True
  color|=region&(H>9)&(H<31)&(S>.34)&(V<.86)
 ink=(local-gray>.090)&(gray<.63)
 ink[:int(h*.045)]=False;ink[int(h*.97):]=False;ink[:,:int(w*.07)]=False;ink[:,int(w*.965):]=False
 color[:int(h*.045)]=False;color[int(h*.97):]=False;color[:,:int(w*.07)]=False;color[:,int(w*.965):]=False
 # Keep large connected drawing lines and colored regions, discard most isolated text glyphs.
 cc=cv2.connectedComponentsWithStats(ink.astype(np.uint8),8);lines=np.zeros((h,w),np.uint8)
 for i in range(1,cc[0]):
  x,y,bw,bh,area=cc[2][i]
  if area>max(30,w*h*.00028) and max(bw,bh)>h*.032:lines[cc[1]==i]=255
 near=cv2.dilate(color.astype(np.uint8),np.ones((7,7),np.uint8))>0
 mask=(color|(ink&near)|(lines>0)).astype(np.uint8)*255
 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
 # Connected components are candidate fragments; do not give anatomical identities.
 count,labels,stats,cents=cv2.connectedComponentsWithStats(mask,8)
 good=[]
 for i in range(1,count):
  x,y,bw,bh,area=stats[i]
  if (x<w*.12 or x>w*.88) and bh>h*.12 and bw<w*.035:continue
  if y>h*.94 and bw>w*.22:continue
  if area>=max(65,w*h*.00055) and bw>4 and bh>4:good.append((i,[int(x),int(y),int(x+bw),int(y+bh)],int(area)))
 good.sort(key=lambda c:(c[1][1]//50,c[1][0]));out=np.zeros((h,w),np.uint8)
 for i,b,a in good:out[labels==i]=255
 return out,labels,good

def process(p):
 im=Image.open(ROOT/p['source_path']).convert('RGB');assert im.size==(p['width'],p['height'])
 im.thumbnail((1550,1550));im.save(OUT/'images'/f"{p['id']}.jpg",quality=90)
 thumb=im.copy();thumb.thumbnail((150,180));thumb.save(OUT/'thumbs'/f"{p['id']}.jpg",quality=82)
 tex=im.copy();tex.thumbnail((1200,1200));pw,ph=tex.size
 cat=category(p['scan_number']);p['category']=cat;p['texture_size']=[pw,ph];p['parts']=[]
 ex={'source_scan':p['id'],'source_sha256':p['sha256'],'source_dimensions':[p['width'],p['height']],'model_status':'CANDIDATE','depth_basis':'interpretive relief, not measured','units':'relative: source height = 1 unit'}
 g=GLB();mat=g.texture(tex);geo=geom(tex,[0,0,pw,ph],(pw,ph),grid=80,depth=.009);g.mesh(p['id']+'_page',*geo,mat,ex)
 p['page_model']='assets/pages/'+p['id']+'.glb';p['page_model_sha256']=g.save(BASE/'dist'/p['page_model'],ex)
 if cat=='Okładki':return p
 small=im.copy();small.thumbnail((850,850));w,h=small.size;mask,labels,components=foreground(small,p['scan_number'],cat)
 # Source layer covers the entire original drawing; auto fragments may be incomplete.
 allg=GLB();made=0
 if p['scan_number'] in regions3:
  # Source-grounded detail patches, containing complete visible features including unpainted contours.
  items=[]
  for j,(name,box) in enumerate(regions3[p['scan_number']]):
   b=[round(box[0]*w),round(box[1]*h),round(box[2]*w),round(box[3]*h)]
   if name in ['Część korzeniowa','Kwiat','Kwiat lewy','Kwiat środkowy','Kwiat prawy','Łodyga dolna','Łodyga','Szypułka']:
    # Exact source patch retained where paint-only segmentation would lose line work.
    gray=cv2.cvtColor(np.asarray(small),cv2.COLOR_RGB2GRAY).astype(float)/255
    lines=(cv2.GaussianBlur(gray,(0,0),5)-gray>.045).astype(np.uint8)*255
    cut=np.zeros_like(lines);cut[b[1]:b[3],b[0]:b[2]]=lines[b[1]:b[3],b[0]:b[2]]
    cut=cv2.morphologyEx(cut,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    count,lab,stats,_=cv2.connectedComponentsWithStats(cut,8);clean=np.zeros_like(cut)
    for ci in range(1,count):
     if stats[ci,4]>12:clean[lab==ci]=255
    clean=cv2.dilate(clean,np.ones((2,2),np.uint8))
    items.append((name,b,clean,'source_patch'))
  for j,(i,b,a) in enumerate(components):items.append(('Kontur '+str(j+1),b,(labels==i).astype(np.uint8)*255,'automatic_contour'))
 else:items=[('Kontur '+str(j+1),b,(labels==i).astype(np.uint8)*255,'automatic_contour') for j,(i,b,a) in enumerate(components)]
 if cat in ['Diagramy','Zodiak','Sceny i postacie','Małe rośliny i naczynia']:
  # Complete source plate kept as its own separately editable relief, without dropping pale/unpainted details.
  # Detected contours are offered in addition, never as an assertion of exhaustive semantic segmentation.
  pass
 for j,(name,b,fullmask,kind) in enumerate(items):
  pad=3;x0=max(0,b[0]-pad);y0=max(0,b[1]-pad);x1=min(w,b[2]+pad);y1=min(h,b[3]+pad);b=[x0,y0,x1,y1]
  crop=small.crop(b);cm=None
  if fullmask is not None:
   cm=fullmask[y0:y1,x0:x1];crop=crop.convert('RGBA');crop.putalpha(Image.fromarray(cm))
  geo=geom(crop,b,(w,h),cm,grid=min(88,max(20,round(max(crop.size)/2))),depth=.022 if cat=='Rośliny' else .010)
  if geo is None:continue
  pid=p['id']+f'_p{j+1:03d}';fname='assets/parts/'+pid+'.glb';part={'id':pid,'label':name,'kind':kind,'bbox_norm':[x0/w,y0/h,x1/w,y1/h],'source_bbox_px':[round(x0/w*p['width']),round(y0/h*p['height']),round(x1/w*p['width']),round(y1/h*p['height'])],'model':fname,'status':'CANDIDATE'}
  extras={**ex,'part_id':pid,'kind':kind,'source_bbox_px':part['source_bbox_px'],'segmentation_review':'candidate, not independently audited'}
  pg=GLB();mat=pg.texture(crop,cm is not None);pg.mesh(pid,*geo,mat,extras);part['sha256']=pg.save(BASE/'dist'/fname,extras)
  mat=allg.texture(crop,cm is not None);allg.mesh(pid,*geo,mat,extras);p['parts'].append(part);made+=1
 if made:
  p['art_model']='assets/art/'+p['id']+'.glb';p['art_model_sha256']=allg.save(BASE/'dist'/p['art_model'],{**ex,'segmentation_complete':False,'part_count':made})
 Image.fromarray(mask).save(OUT/'masks'/f"{p['id']}.png")
 return p

if __name__=='__main__':
 import sys
 limit=int(sys.argv[1]) if len(sys.argv)>1 else 0
 pages=source['pages'][:limit] if limit else source['pages']
 processed=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for i,p in enumerate(pool.map(process,pages)):
   processed.append(p)
   if i%10==0:print('processed',i+1,'parts',sum(len(q['parts']) for q in processed),flush=True)
 atlas={'version':VERSION,'source_scan_count':len(processed),'repaired_sources':source['repaired_count'],'pages':processed,'model_type':'2.5D textured reliefs','segmentation_status':'CANDIDATE; automatic contours not exhaustive semantic illustration annotation','scale':'Source scan height 1 unit. Original physical scale unknown.'}
 (OUT/'atlas.json').write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
 # One portable combined GLB, with all scans as named independent objects in an atlas layout.
 whole=GLB()
 for i,p in enumerate(processed):
  img=Image.open(OUT/'images'/f"{p['id']}.jpg");img.thumbnail((370,370));w,h=img.size
  mat=whole.texture(img);geo=geom(img,[0,0,w,h],(w,h),grid=8,depth=.003)
  # Fixed spacious cells preserve unusually wide foldouts.
  whole.mesh(p['id']+'_page',*geo,mat,{'scan_id':p['id'],'source_sha256':p['sha256']},translation=[(i%12)*3.0,-(i//12)*1.22,0])
 whole.save(OUT/'manuscript_all.glb',{'source_scan_count':len(processed),'layout':'editorial atlas grid; not a physical binding reconstruction','status':'CANDIDATE'})
 print('DONE',len(processed),'scans',sum(len(p['parts']) for p in processed),'parts',flush=True)
