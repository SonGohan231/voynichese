"""Blender 5.2: first ten manually interpreted source plants, full volume, no scan displacement.
Front is -Y. Source drawings determine visible organisation; unpictured depth is interpretive.
Metres are exhibition scale, not measured botanical dimensions. Deterministic seed 17.
"""
import bpy, math, random
from mathutils import Vector
random.seed(17)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.engine='BLENDER_EEVEE'
scene.world=bpy.data.worlds.new('Garden daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.28,.36,.42,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.render.resolution_x=1500;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
def mat(name,c,rough=.72):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;return m
G=mat('Pigment / muted green',(.16,.34,.19));G2=mat('Pigment / sage',(.29,.43,.23));TAN=mat('Pigment / ochre',(.57,.36,.15));RED=mat('Pigment / russet',(.43,.13,.075));BLUE=mat('Pigment / dark indigo',(.035,.12,.20));WHITE=mat('Parchment-white flowers',(.84,.78,.61));ROOT=mat('Roots / warm earth',(.37,.23,.10));VEIN=mat('Veins / olive',(.39,.43,.19));SOIL=mat('Bed / earth',(.105,.078,.04));STONE=mat('Garden limestone',(.42,.43,.35));PATH=mat('Walkway',(.32,.30,.24));BRASS=mat('Label lettering',(.70,.52,.22))
current=None;prefix='';counts=[]
def mesh(name,verts,faces,material):
 me=bpy.data.meshes.new(prefix+name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(prefix+name,me);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 if current:o.parent=current
 for p in me.polygons:p.use_smooth=True
 return o
def tube(name,pts,radii,material,sides=8):
 pts=[Vector(p) for p in pts];radii=[radii]*len(pts) if isinstance(radii,(float,int)) else radii;vs=[];fs=[]
 for i,p in enumerate(pts):
  tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();ref=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0));u=tangent.cross(ref).normalized();v=tangent.cross(u).normalized()
  for j in range(sides):vs.append(p+radii[i]*(math.cos(j*2*math.pi/sides)*u+math.sin(j*2*math.pi/sides)*v))
 for i in range(len(pts)-1):
  for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))]);return mesh(name,vs,fs,material)
def curve(a,b,bend=0,depth=0,n=9):
 a=Vector(a);b=Vector(b);return [a.lerp(b,i/(n-1))+Vector((bend*math.sin(math.pi*i/(n-1)),depth*math.sin(math.pi*i/(n-1)),0)) for i in range(n)]
def stem(a,b,r=.021,bend=0,depth=0,name='Stem'):
 pts=curve(a,b,bend,depth);return tube(name,pts,[r*(1-.6*i/8) for i in range(9)],G)
def leaf(a,b,w=.12,material=G,bend=0,depth=.06,serrate=0,name='Leaf'):
 pts=curve(a,b,bend,depth,13);v=(Vector(b)-Vector(a)).normalized();u=Vector((v.z,0,-v.x)).normalized();vs=[];faces=[]
 for i,p in enumerate(pts):
  t=i/12;profile=max(.012,math.sin(math.pi*t)**.8);profile*=1-serrate*(i%2)
  for j in range(10):ang=j*2*math.pi/10;vs.append(p+u*(math.cos(ang)*w*profile)+Vector((0,math.sin(ang)*max(.008,w*.17)*profile,0)))
 for i in range(12):
  for j in range(10):a0=i*10+j;b0=i*10+(j+1)%10;faces.append((a0,b0,b0+10,a0+10))
 faces += [tuple(reversed(range(10))),tuple(120+j for j in range(10))];o=mesh(name,vs,faces,material);tube(name+' midrib',[p+Vector((0,-.012,0)) for p in pts],.0035,VEIN,5);return o
def bulb(name,p,scale,material):
 vs=[];fs=[];seg=16;rings=10
 for i in range(rings+1):
  lat=math.pi*i/rings
  for j in range(seg):ang=2*math.pi*j/seg;vs.append((p[0]+scale[0]*math.sin(lat)*math.cos(ang),p[1]+scale[1]*math.sin(lat)*math.sin(ang),p[2]+scale[2]*math.cos(lat)))
 for i in range(rings):
  for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;fs.append((a,b,b+seg,a+seg))
 return mesh(name,vs,fs,material)
def flower(p,r=.09,material=WHITE,n=6):
 for i in range(n):a=i*math.tau/n;leaf(p,(p[0]+r*math.cos(a),p[1]-.035,p[2]+r*math.sin(a)),r*.26,material,depth=-.015,name='Petal')
 bulb('Flower centre',(p[0],p[1]-.024,p[2]),(r*.26,r*.23,r*.26),TAN)
def roots(base=(0,0,.38),spread=.42,n=9,color=ROOT):
 for i in range(n):a=-math.pi/2+i*math.pi/(n-1);end=(base[0]+spread*math.sin(a),.09*math.cos(i*1.9),.025+.05*(i%3));pts=curve(base,end,.045*math.sin(i*2),.03,8);tube('Root %02d'%i,pts,[.025*(1-k/9)+.002 for k in range(8)],color)
def begin(scan,folio,index):
 global current,prefix
 prefix=scan+' | ';current=bpy.data.objects.new('PLANT_'+scan,None);bpy.context.collection.objects.link(current);current.location=((index%5-2)*2.45,(index//5)*4.2,0.17);current['folio']=folio;current['scan_id']=scan;current['status']='CANDIDATE_VOLUME_INTERPRETATION';current['depth']='unpictured sides interpreted, no species identification';current['source_view']='front -Y';return current
def consolidate(objects,name,role):
 objects=[o for o in objects if o.type=='MESH']
 if not objects:return
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 if len(objects)>1:bpy.ops.object.join()
 objects[0].name=prefix+name;objects[0]['semantic_role']=role
def conduit(name,pts,r=.035):
 pts=[Vector(p) for p in pts];n=10;vs=[];fs=[]
 for i,p in enumerate(pts):
  t=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();u=t.cross(Vector((0,1,0))).normalized();v=t.cross(u).normalized()
  for rr in [r,r*.65]:
   for j in range(n):a=j*math.tau/n;vs.append(p+rr*(math.cos(a)*u+math.sin(a)*v))
 for i in range(len(pts)-1):
  for ring in [0,1]:
   for j in range(n):a=i*2*n+ring*n+j;b=i*2*n+ring*n+(j+1)%n;f=(a,b,b+2*n,a+2*n);fs.append(f if ring==0 else tuple(reversed(f)))
 for i in [0,len(pts)-1]:
  for j in range(n):a=i*2*n+j;b=i*2*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 o=mesh(name,vs,fs,TAN);o['semantic_role']='channel';return o
# Miniature specimen ensembles, mapped by observed row and order; contour audit still required.
def jar(x,z,h=.45,palette='red',tiered=False):
 old=set(bpy.data.objects);n=32;profile=[(.04,0),(.055,.06),(.032,.12),(.045,.21),(.085,.27),(.10,.36),(.085,.48),(.10,.56),(.085,.68),(.1,.78),(.085,.9),(.09,1)] if tiered else [(.075,0),(.08,.08),(.075,.88),(.085,.95),(.085,1)]
 vs=[];fs=[]
 for r,hh in profile:
  for j in range(n):a=j*math.tau/n;vs.append((x+r*math.cos(a),r*math.sin(a),z+h*hh))
 for k in range(len(profile)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 fs.append(tuple(reversed(range(n))));mesh('Vessel outer body',vs,fs,RED if palette=='red' else BLUE)
 ring('Vessel lip',x,z+h,.083,TAN) if False else tube('Vessel open lip',[(x+.083*math.cos(j*math.tau/32),.083*math.sin(j*math.tau/32),z+h) for j in range(33)],.008,WHITE)
 for hh in [.14,.47,.74,.94]:tube('Vessel pigment band',[(x+.082*math.cos(j*math.tau/32),.082*math.sin(j*math.tau/32),z+h*hh) for j in range(33)],.011,WHITE if hh==.47 else G2)
 # Inner wall and visible floor make the opening volumetric.
 tube('Vessel interior rim',[(x+.071*math.cos(j*math.tau/32),.071*math.sin(j*math.tau/32),z+h-.012) for j in range(33)],.012,TAN)
 consolidate(set(bpy.data.objects)-old,'Vessel at %.2f %.2f'%(x,z),'vessel')
def specimen(x,z,kind,s=.35,number=0):
 old=set(bpy.data.objects)
 if kind in ['root','bulb','chain','scroll','fork']:
  if kind=='bulb':bulb('Root bulb',(x,0,z+s*.42),(s*.2,s*.12,s*.24),RED)
  if kind=='chain':
   for j in range(4):bulb('Segmented root',(x+(j-1.5)*s*.17,0,z+s*.22),(s*.14,s*.065,s*.075),TAN)
  if kind=='scroll':tube('Scrolling root',[(x+s*.37*math.cos(j*.17),0,z+s*.2+s*.14*math.sin(j*.17)) for j in range(37)],s*.045,RED)
  for j in range(5 if kind!='fork' else 2):
   dx=(j-2)*s*.12 if kind!='fork' else (-1 if j==0 else 1)*s*.35;tube('Root strand',curve((x,0,z+s*.5),(x+dx,0,z),dx*.25,0,7),s*.024,TAN if kind!='fork' else RED,6)
  if number%2==0:leaf((x,0,z+s*.53),(x+.05,0,z+s*.86),s*.1,G,name='Small root crown blade')
 elif kind in ['fan','star','fern','oval','heart','grass','branch']:
  stem((x,0,z),(x,0,z+s*.5),s*.035)
  if kind=='fern':
   for k in range(7):
    for side in [-1,1]:leaf((x,0,z+s*(.25+k*.08)),(x+side*s*.24,0,z+s*(.35+k*.08)),s*.045,G,name='Miniature fern blade')
  elif kind=='branch':
   for k in range(5):
    side=(-1)**k;leaf((x,0,z+s*(.2+k*.13)),(x+side*s*.25,0,z+s*(.35+k*.13)),s*.055,G,name='Miniature branch oval')
  elif kind in ['oval','heart']:
   for side in ([-1,1] if kind=='heart' else [0]):leaf((x,0,z+s*.25),(x+side*s*.1,0,z+s*.9),s*.17,G,name='Broad miniature blade')
  else:
   n=9 if kind!='grass' else 13
   for j in range(n):
    a=j*math.tau/n if kind=='star' else .18+j*math.pi*.8/(n-1);leaf((x,0,z+s*.38),(x+s*.37*math.cos(a),.015*math.sin(j),z+s*.38+s*.43*math.sin(a)),s*(.025 if kind=='grass' else .058),G,name='Divided miniature blade')
 consolidate(set(bpy.data.objects)-old,'Specimen %02d %s'%(number,kind),'specimen')
def row(z,kinds,xmin=-.43,xmax=.7,s=.32):
 for j,kind in enumerate(kinds.split()):specimen(xmin+(xmax-xmin)*j/max(1,len(kinds.split())-1),z,kind,s,j+1)
def pharma(scan,folio,index,rows,palette='red',tiered=False):
 begin(scan,folio,index);current['fidelity']='manual schematic specimens; row correspondence approximate; individual contour verification pending'
 for z,kinds in rows:jar(-.68,z,.36,palette,tiered);row(z,kinds,s=.35)
# f88r: tiered vessels; three specimen rows and long root at foot.
pharma('s0161','88r',0,[(2.05,'root bulb root fork fan oval'),(1.23,'fork branch bulb oval fern branch'),(.49,'oval root star fork root')],tiered=True)
tube('Long lower root',[(-.55,0,.17),(-.2,0,.22),(.35,0,.15),(.72,0,.08)],.026,TAN)
# f88v/89r: three columns in foldout, each with rows of specimens and vessels.
begin('s0162','88v and 89r',1)
for col,x in enumerate([-.62,0,.62]):
 for k,z in enumerate([.53,1.23,1.98]):
  jar(x-.24,z,.33,'red',True)
  for j,kind in enumerate([['root','fan','star'],['bulb','scroll','branch'],['oval','fork','chain']][(col+k)%3]):specimen(x-.08+j*.15,z,kind,.26,j+col*9+k*3)
# f89v part: blue tiered vessels and mixed roots, lobed leaves.
pharma('s0163','89v part',2,[(2.04,'root fan bulb oval fork star'),(1.22,'scroll oval chain star bulb'),(.48,'oval fern fan root branch')],'blue',True)
# f89v/90r: left small specimens; central two blue disks; right branching round leaves.
begin('s0164','89v part and 90r',3)
for z in [.53,1.74]:jar(-.72,z,.4,'blue',True);row(z,'root star bulb',-.5,-.1,.29)
for x,z in [(.04,1.99),(.04,1.24)]:bulb('Blue circular lobe',(x,0,z),(.16,.055,.17),BLUE)
stem((.38,0,.3),(.47,0,2.19),.021);roots(base=(.38,0,.31),spread=.31,n=7)
for k in range(7):
 z=.93+k*.16
 for side in [-1,1]:stem((.45,0,z-.15),(.45+side*.23,0,z),.008);bulb('Round branch leaf',(.45+side*.23,0,z),(.045,.022,.059),G)
# f99r: four red jars and roots of several visibly different types.
pharma('s0175','99r',4,[(2.12,'fork bulb root chain scroll root'),(1.54,'scroll bulb fork root chain root'),(.96,'bulb fork scroll chain root'),(.38,'root chain fork branch')])
# f99v: red banded vessels, roots, and large curling green lower form.
pharma('s0176','99v',5,[(2.1,'fork root bulb root scroll'),(1.46,'root fork bulb bulb root'),(.84,'scroll chain fork bulb branch')])
for j in range(4):conduit('Long lower root course',[(-.53,0,.13+j*.025),(0,0,.35+j*.035),(.62,0,.18+j*.03)],.018)
leaf((.5,0,.34),(.52,0,.71),.22,G,name='Broad lower green blade')
# f100r: two red jars, broad and divided leaves in two clusters.
pharma('s0177','100r',6,[(2.01,'heart fan fern star branch'),(1.43,'oval fan grass branch heart'),(.56,'heart scroll star fan branch')])
# f100v/101r: two panels filled with green leaf specimens.
begin('s0178','100v and 101r',7)
for col,x in enumerate([-.44,.44]):
 for k,z in enumerate([.51,1.19,1.96]):
  jar(x-.38,z,.31,'blue' if col else 'red')
  for j,kind in enumerate([['fan','fern','branch','heart'],['star','oval','grass','fan'],['heart','branch','fern','star']][k]):specimen(x-.18+j*.14,z,kind,.28,j+k*4+col*12)
# f101v part: three jars, mixed round and segmented leaves.
pharma('s0179','101v part',8,[(2.1,'star fern branch fork fan'),(1.43,'heart oval fan scroll root'),(.76,'fern branch oval star heart')])
# f101v/102r: wide foldout, fine leaves on left, roots and isolated leaves right.
begin('s0180','101v part and 102r',9)
for col,x in enumerate([-.59,0,.59]):
 for k,z in enumerate([.66,1.82]):
  jar(x-.23,z,.38,'red')
  for j,kind in enumerate([['branch','oval','fern'],['root','fan','bulb'],['fork','star','chain']][col]):specimen(x-.05+j*.15,z,kind,.32,j+k*3+col*6)
row(.18,'root chain fork root',-.53,.65,.3)
# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['88r','88v 89r','89v part','89v 90r','99r','99v','100r','100v 101r','101v part','101v 102r'][i];o.data.body='f'+['88r','88v 89r','89v part','89v 90r','99r','99v','100r','100v 101r','101v part','101v 102r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='18';scene['source_folia']='f65r f65v f66v f87r f87v f90r f90v-part f93r f93v f94r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
scene.render.resolution_x=1400;scene.render.resolution_y=1000
result={'plants':[o.name for o in bpy.data.objects if o.name.startswith('PLANT_')], 'meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'), 'interpretation':scene['interpretation']}

# Ensure portable front-face orientation for glTF/WebGL.
import bmesh
for obj in bpy.data.objects:
 if obj.type=='MESH':
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
result={'plants':10,'batch':'18','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia18_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
