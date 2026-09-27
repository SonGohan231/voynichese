import bpy,math,json,hashlib,shutil
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parent;ROOT=R.parent;A=json.load(open(ROOT/'voynich-3d/public/assets/atlas.json'))['pages'];N=ROOT/'quest-native/assets';OUT=R/'details';OUT.mkdir(exist_ok=True);records=[]
def start(scan,bbox):
 global p,B,W,H,mat
 p=next(p for p in A if p['id']==scan);B=bbox;W=p['width'];H=p['height'];bpy.ops.wm.read_factory_settings(use_empty=True)
 im=Image.open(N/'source_pixels'/(scan+'.jpgbin'));im=im.crop((int(B[0]*W),int(B[1]*H),int(B[2]*W),int(B[3]*H)));im.thumbnail((2048,2048));fp=OUT/(scan+'_'+str(len(records))+'.jpg');im.save(fp,quality=98);img=bpy.data.images.load(str(fp));img.pack()
 mat=bpy.data.materials.new('Oryginalny_rysunek');mat.use_nodes=True;tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=img;bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.9

def mesh(name,vs,faces):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.materials.append(mat);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);uv=me.uv_layers.new()
 for poly in me.polygons:
  for li in poly.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x/((B[2]-B[0])*W/((B[3]-B[1])*H))+.5,v.y+.5)
 o['source_bbox_norm']=json.dumps(B);o['source_sha256']=p['sha256'];o['status']='CANDIDATE_DEPTH';return o

def xyz(u,v,z):return ((u-(B[0]+B[2])/2)*W/((B[3]-B[1])*H),((B[1]+B[3])/2-v)/(B[3]-B[1]),z)
def ellipse(name,u,v,rx,ry,depth):
 vs=[];fs=[];na=32;nr=16
 for j in range(nr+1):
  t=-math.pi/2+j*math.pi/nr
  for k in range(na):
   a=k*2*math.pi/na;vs.append(xyz(u+rx*math.cos(t)*math.cos(a),v+ry*math.sin(t),depth*math.cos(t)*math.sin(a)))
 for j in range(nr):
  for k in range(na):a=j*na+k;b=j*na+(k+1)%na;fs.append((a,b,b+na,a+na))
 mesh(name,vs,fs)
def limb(name,pts,r):
 for i,(u,v) in enumerate(pts):ellipse(name+'_'+str(i),u,v,r,r*.8,.05)
def shape(name,rows,depth):
 vs=[];faces=[];na=48
 for v,left,right in rows:
  for i in range(na):
   a=i*2*math.pi/na;vs.append(xyz((left+right)/2+(right-left)/2*math.cos(a),v,depth*math.sin(a)))
 for j in range(len(rows)-1):
  for i in range(na):a=j*na+i;b=j*na+(i+1)%na;faces.append((a,a+na,b+na,b))
 faces.extend([tuple(range(na-1,-1,-1)),tuple(range((len(rows)-1)*na,len(rows)*na))]);mesh(name,vs,faces)
def save(id,label):
 d=OUT/id;d.mkdir(exist_ok=True);sc=bpy.context.scene;sc['source_folio']=p['label'];sc['depth_inferred']=True
 bpy.ops.wm.save_as_mainfile(filepath=str(d/(id+'.blend')));bpy.ops.export_scene.gltf(filepath=str(d/(id+'.glb')),export_format='GLB',export_apply=True,export_extras=True)
 shutil.copyfile(d/(id+'.glb'),N/'models'/(id+'.glb'))
 records.append({'id':id,'scan':p['id'],'folio':p['label'],'category':'Uzupełnienia · rysunki marginalne','description':label+'; ręcznie wskazany obszar źródła. Kształt przestrzenny przybliżony, tył i głębia hipotetyczne.','model':'res://assets/models/'+id+'.glb','display_model':'res://assets/models/'+id+'.glb','batch':'28','source_sha256':p['sha256'],'source_bbox_norm':B,'status':'CANDIDATE_VOLUME','contour_verified':False,'model_sha256':hashlib.sha256((d/(id+'.glb')).read_bytes()).hexdigest()});(OUT/'PROGRESS.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('DETAIL',len(records),id,flush=True)
# Reclinant figure in lower margin f66r. Separate body/head/limbs, anchored in source projection.
start('s0119',(.105,.864,.246,.959));ellipse('Tulow',.18,.911,.025,.019,.065);ellipse('Glowa',.225,.879,.012,.015,.055)
limb('Ramie_lewe',[(.169,.908),(.17,.895),(.18,.887),(.187,.895)],.006)
limb('Ramie_prawe',[(.207,.899),(.219,.91),(.212,.924)],.005)
limb('Noga_1',[(.162,.923),(.147,.936),(.132,.946),(.117,.950)],.006)
limb('Noga_2',[(.177,.929),(.159,.943),(.14,.95),(.129,.954)],.006)
save('detail_f66r_figure','Postać w dolnym marginesie')
start('s0119',(.037,.925,.073,.956));shape('Naczynie',[(.929,.042,.069),(.952,.045,.068)],.12);save('detail_f66r_vessel','Mała forma naczyniowa obok postaci')
for i,(cx,cy,r) in enumerate([(.086,.919,.009),(.108,.910,.012)]):
 start('s0119',(cx-r*1.5,cy-r*1.5,cx+r*1.5,cy+r*1.5));ellipse('Forma_kolista',cx,cy,r,r*.75,.15);save('detail_f66r_round_'+str(i+1),'Kolisty detal przy postaci')
start('s0206',(.12,.115,.19,.165));ellipse('Tulow_zwierzecia',.15,.137,.024,.005,.05);ellipse('Glowa',.129,.129,.009,.009,.045)
for j,u in enumerate([.132,.145,.164,.171]):limb('Konczyna_'+str(j),[(u,.14),(u-.002,.153)],.003)
save('detail_f116v_animal','Drobna sylwetka zwierzęca w lewym marginesie')
start('s0206',(.117,.168,.203,.26));ellipse('Glowa',.168,.185,.016,.013,.06);ellipse('Tulow',.164,.219,.015,.027,.06)
limb('Ramie',[(.149,.205),(.134,.215)],.005);limb('Ramie2',[(.180,.207),(.187,.224)],.005);limb('Noga',[(.157,.237),(.148,.25)],.006);limb('Noga2',[(.168,.237),(.157,.253)],.006);save('detail_f116v_figure','Postać poniżej sylwetki zwierzęcej')
# Four independent lobed/tubular forms around text on f86v partial foldout.
forms=[('NW',(.486,.033,.657,.30),[(.045,.544,.59),(.10,.528,.605),(.17,.498,.608),(.205,.515,.598),(.224,.57,.589),(.285,.628,.649)]),('NE',(.79,.045,.973,.293),[(.055,.891,.937),(.10,.87,.965),(.17,.865,.959),(.225,.84,.886),(.29,.802,.824)]),('SW',(.471,.633,.683,.976),[(.647,.607,.661),(.70,.595,.648),(.76,.563,.626),(.825,.557,.613),(.90,.498,.591),(.967,.491,.57)]),('SE',(.778,.565,.961,.975),[(.575,.790,.822),(.60,.826,.857),(.65,.847,.88),(.71,.851,.9),(.79,.853,.931),(.865,.876,.933),(.952,.873,.92)])]
for name,bbox,rows in forms:
 start('s0157',bbox);shape('Forma_przeplywowa_'+name,rows,.12);save('detail_f86v_'+name,'Forma przepływowa '+name+'; ornament i kontury w teksturze źródłowej')
cat=json.load(open(N/'catalog.json'));ids={r['id'] for r in records};cat=[c for c in cat if c.get('id') not in ids]+records;(N/'catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2));print('DETAILS_DONE',len(records),len(cat),flush=True)
