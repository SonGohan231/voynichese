"""Source-projected Blender geometry. Depth remains an explicitly labelled interpretation."""
import bpy,math,json,hashlib,shutil,os
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent;ROOT=R.parent;OUT=R/'models';OUT.mkdir(exist_ok=True);N=ROOT/'quest-native/assets';A=json.load(open(ROOT/'voynich-3d/public/assets/atlas.json'))['pages']
records=[];SCALE=12.;H=None;W=None;texmat=None;paper=None;source=None

def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.92;return m

def mesh(name,verts,faces,mat=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(mat or texmat);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 if mat is None:
  uv=me.uv_layers.new(name='SourceXY')
  for poly in me.polygons:
   for li in poly.loop_indices:
    v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x/SCALE+.5,v.y/(SCALE*H/W)+.5)
 ob['folio']=source['label'];ob['source_sha256']=source['sha256'];ob['depth_status']='CANDIDATE_inferred_not_measured';return ob

def coord(u,v,z=0):return ((u-.5)*SCALE,(.5-v)*SCALE*H/W,z)

def setup(p):
 global H,W,source,texmat,paper
 source=p;W=p['width'];H=p['height'];bpy.ops.wm.read_factory_settings(use_empty=True)
 f=N/'source_pixels'/(p['id']+'.jpgbin');assert f.exists(),f
 im=Image.open(f);im.thumbnail((4096,4096));fp=OUT/(p['id']+'_texture.jpg');im.convert('RGB').save(fp,quality=96)
 img=bpy.data.images.load(str(fp));img.pack();texmat=material('Dokladny_skan_'+p['id'],(.8,.72,.55));nd=texmat.node_tree.nodes.new('ShaderNodeTexImage');nd.image=img;pr=texmat.node_tree.nodes.get('Principled BSDF');texmat.node_tree.links.new(nd.outputs['Color'],pr.inputs['Base Color'])
 paper=material('Krawedzie_rekonstrukcji',(.70,.59,.4));return im

def grid(im,name,n=120,amplitude=.055,kind='relief',bbox=(0,0,1,1)):
 x0,y0,x1,y1=bbox;w=n;h=max(20,round(n*H/W*(y1-y0)/(x1-x0)));small=np.asarray(im.convert('RGB').crop((int(x0*im.width),int(y0*im.height),int(x1*im.width),int(y1*im.height))).resize((w+1,h+1)),dtype=float)/255
 verts=[];faces=[]
 for y in range(h+1):
  for x in range(w+1):
   r,g,b=small[y,x];pigment=max(0.,g-r*.99,b-r*1.05)*3;ink=max(0.,.5-(r+g+b)/3)
   z=.012+amplitude*min(1.,pigment+ink*.35)
   verts.append(coord(x0+(x1-x0)*x/w,y0+(y1-y0)*y/h,z))
 for y in range(h):
  for x in range(w):
   a=y*(w+1)+x;faces.append((a,a+w+1,a+w+2,a+1))
 ob=mesh(name,verts,faces);solid=ob.modifiers.new('Rzeczywista_grubosc_podloza','SOLIDIFY');solid.thickness=.014;solid.offset=-1
 return ob

ROSETTES=[(.243,.205,.095,.113),(.551,.182,.103,.108),(.825,.193,.091,.114),(.251,.496,.108,.109),(.543,.498,.154,.170),(.822,.503,.099,.106),(.252,.785,.103,.103),(.534,.813,.108,.109),(.823,.821,.101,.113)]

def rosette(i,c):
 u,v,rx,ry=c;verts=[];faces=[];na=144;nr=22
 for j in range(nr+1):
  q=j/nr
  for k in range(na):
   a=k*2*math.pi/na;ripple=1+.018*math.sin(a*(24 if i==4 else 18))
   rim=math.exp(-((q-.85)/.052)**2)*.18+math.exp(-((q-.61)/.035)**2)*.08
   h=.045+.21*(1-q*q)+rim
   if i in [1,7]:h+=max(0,math.sin(a*(6 if i==1 else 4)))*.14*(1-q)
   if i==4:h+=.10
   verts.append(coord(u+rx*q*math.cos(a)*ripple,v+ry*q*math.sin(a)*ripple,h))
 for j in range(nr):
  for k in range(na):
   a=j*na+k;b=j*na+(k+1)%na;faces.append((a,b,b+na,a+na))
 ob=mesh('Rozeta_%02d_zrodlo_%s'%(i+1,source['id']),verts,faces)
 s=ob.modifiers.new('Pelna_bryla','SOLIDIFY');s.thickness=.07;s.offset=-1
 ob['source_bbox_norm']=json.dumps([u-rx,v-ry,u+rx,v+ry]);ob['interpretation']='Contour anchored to scan; ring relief and curvature inferred'

def tube(name,u,v,r=.047,height=.35,lean=(0,0)):
 x,y,z=coord(u,v,.32);verts=[];faces=[];steps=28
 # Closed annular wall, genuinely hollow top. At source-anchor positions.
 for zz,rr in [(0,r), (height,r*.92),(height,r*.65),(.02,r*.70)]:
  for k in range(steps):
   a=k*2*math.pi/steps;verts.append((x+rr*math.cos(a)+lean[0]*zz,y+rr*math.sin(a)+lean[1]*zz,z+zz))
 for j in range(4):
  for k in range(steps):faces.append((j*steps+k,j*steps+(k+1)%steps,((j+1)%4)*steps+(k+1)%steps,((j+1)%4)*steps+k))
 return mesh(name,verts,faces)

def finial(name,u,v,height=.6,r=.14):
 x,y,z=coord(u,v,.31);profile=[(0,.6),(.08,.64),(.11,.80),(.16,.83),(.2,.5),(.3,.87),(.42,1),(.55,.9),(.69,.57),(.81,.23),(.88,.20),(1,0)]
 verts=[];faces=[];steps=32
 for hh,rr in profile:
  for k in range(steps):
   a=k*2*math.pi/steps;rad=r*rr*(1+.035*math.cos(a*12));verts.append((x+rad*math.cos(a),y+rad*math.sin(a),z+height*hh))
 for j in range(len(profile)-1):
  for k in range(steps):faces.append((j*steps+k,j*steps+(k+1)%steps,(j+1)*steps+(k+1)%steps,(j+1)*steps+k))
 return mesh(name,verts,faces)

def connector(name,pts,widths,height=.13):
 vs=[];faces=[]
 for i,(u,v) in enumerate(pts):
  prev=pts[max(0,i-1)];nex=pts[min(len(pts)-1,i+1)];dx=nex[0]-prev[0];dy=nex[1]-prev[1];le=math.hypot(dx,dy);nx=-dy/le;ny=dx/le
  for j in range(9):
   q=(j/8-.5)*2;vs.append(coord(u+nx*widths[i]*q,v+ny*widths[i]*q,.025+height*(1-q*q)))
 for i in range(len(pts)-1):
  for j in range(8):a=i*9+j;faces.append((a,a+1,a+10,a+9))
 ob=mesh(name,vs,faces);s=ob.modifiers.new('Brzeg_przeplywu','SOLIDIFY');s.thickness=.045

CONNECTORS=[([( .324,.24),(.378,.23),(.425,.23),(.467,.242)],[.01,.011,.013,.015]), ([(.327,.157),(.386,.158),(.428,.14),(.465,.123)],[.008,.015,.015,.011]), ([(.611,.27),(.654,.225),(.716,.202),(.747,.18)],[.025,.021,.016,.025]), ([(.207,.307),(.204,.35),(.195,.393)],[.014,.014,.009]), ([(.296,.295),(.268,.331),(.284,.39)],[.023,.016,.009]), ([(.299,.592),(.276,.637),(.249,.672),(.212,.701)],[.026,.04,.02,.029]), ([(.249,.699),(.302,.672),(.353,.65),(.346,.617)],[.012,.018,.025,.014]), ([(.789,.294),(.808,.344),(.814,.394)],[.029,.025,.018]), ([(.805,.608),(.793,.657),(.766,.706)],[.032,.022,.025]), ([(.605,.853),(.654,.87),(.689,.863),(.75,.841)],[.023,.027,.018,.025]), ([(.341,.827),(.393,.832),(.433,.827)],[.012,.024,.029]), ([(.343,.763),(.397,.745),(.454,.756)],[.012,.02,.024]), ([(.546,.332),(.535,.309),(.531,.267)],[.004,.015,.03])]

def save(id,p,kind,batch,description):
 path=OUT/id;path.mkdir(exist_ok=True)
 sc=bpy.context.scene;sc['status']='CANDIDATE';sc['source_sha256']=p['sha256'];sc['source_folio']=p['label'];sc['depth_not_measured']=True
 bpy.ops.wm.save_as_mainfile(filepath=str(path/(id+'.blend')))
 bpy.ops.export_scene.gltf(filepath=str(path/(id+'.glb')),export_format='GLB',export_apply=True,export_extras=True,export_cameras=False,export_lights=False)
 shutil.copyfile(path/(id+'.glb'),N/'models'/(id+'.glb'))
 rec={'id':id,'scan':p['id'],'folio':p['label'],'category':kind,'description':description,'status':'CANDIDATE_SOURCE_PROJECTED','source_sha256':p['sha256'],'source_width':p['width'],'source_height':p['height'],'model':'res://assets/models/'+id+'.glb','batch':str(batch),'model_sha256':hashlib.sha256((path/(id+'.glb')).read_bytes()).hexdigest(),'contour_verified':False,'depth_inferred':True}
 records.append(rec);(R/'PROGRESS.json').write_text(json.dumps({'models':records,'completed':len(records),'blender':bpy.app.version_string},ensure_ascii=False,indent=2));print('CHECKPOINT',id,len(records),flush=True)

pages=[p for p in A if p['category']=='Diagramy']
for p in pages:
 im=setup(p);grid(im,'Pełny_diagram_2_5D',190 if p['id']=='s0158' else 112, .035);save('relief_'+p['id'],p,'Diagramy · relief 2.5D',21,'Pełny rysunek i pismo ze skanu; subtelny relief barw/kresek, nie zmierzona głębia.')
p=next(p for p in A if p['id']=='s0158');im=setup(p);grid(im,'Podłoże_z_wszystkimi_napisami',96,.015)
for i,c in enumerate(ROSETTES):rosette(i,c)
for i,(pts,widths) in enumerate(CONNECTORS):connector('Pasmo_przeplywowe_%02d'%(i+1),pts,widths)
# Individually recorded tube groups visible around central rosette; positions from source image.
for i,(u,v) in enumerate([(.426,.383),(.467,.344),(.527,.326),(.584,.346),(.63,.379),(.681,.426),(.686,.55),(.646,.618),(.591,.653),(.49,.653),(.414,.594),(.405,.461)]):
 for j in range(3):tube('Rozeta5_otwarta_tuba_%02d_%d'%(i,j),u+(j%2)*.008,v+(j//2)*.01,.043,.22+.1*(j==0),(.2,-.15))
for i,(u,v,h) in enumerate([(.5,.48,.58),(.513,.512,.67),(.551,.518,.66),(.575,.485,.7),(.522,.447,.4),(.551,.443,.43)]):finial('Rozeta5_forma_ozdobna_'+str(i+1),u,v,h)
# Castle-like silhouettes at lower-right island: separate masonry masses, tops are inferred.
for i,(u,v,w,h) in enumerate([(.79,.769,.018,.22),(.809,.789,.015,.25),(.799,.805,.016,.30),(.78,.812,.013,.27)]):
 x,y,z=coord(u,v,.32);bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z+h/2));o=bpy.context.object;o.name='Forma_architektoniczna_%d'%i;o.dimensions=(w*12,.20,h);o.data.materials.append(paper);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for j in range(3):
  bpy.ops.mesh.primitive_cube_add(size=1,location=(x+(j-1)*w*4,y,z+h+.025));o=bpy.context.object;o.name='Blankowanie_%d_%d'%(i,j);o.dimensions=(w*2,.20,.05);o.data.materials.append(paper)
save('spatial_s0158',p,'Diagramy · model przestrzenny',21,'Dziewięć rozet, 13 pasm, 36 otwartych tub, 6 form ozdobnych; rozmieszczenie ze skanu, głębia i tyły interpretacyjne.')
# All pages assigned scenes/flows gain a source-projected companion; original volumetric ensembles retained.
flow=[p for p in A if p['category']=='Sceny i postacie' and p['id']!='s0137']+[next(p for p in A if p['id']=='s0157')]
for j,p in enumerate(flow):
 im=setup(p);grid(im,'Rysunek_przeplywow_i_postaci',140,.22);save('flows_'+p['id'],p,'Przepływy · relief źródłowy',22+j//10,'Kompletny skan sceny w reliefie. Nazwa przepływy to kategoria robocza; funkcja form niepotwierdzona.')
# Missing scan-only folios: preserve small decorations and marginal signs as editable raised surfaces.
existing={m['scan'] for m in json.load(open(N/'catalog.json'))}
missing=[p for p in A if p['id'] not in existing and p['category']!='Okładki']
for j,p in enumerate(missing):
 im=setup(p);grid(im,'Strona_i_marginalia',100,.07)
 save('marginal_'+p['id'],p,'Tekst i drobne znaki · relief',24+j//10,'Relief całej strony obejmuje drobne znaki. Nie jest katalogiem ręcznie rozdzielonych rysunków.')
cat=json.load(open(N/'catalog.json'));ids={r['id'] for r in records};cat=[r for r in cat if r.get('id') not in ids];cat.extend(records);(N/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2));print('FINAL',len(records),'catalog',len(cat),flush=True)
