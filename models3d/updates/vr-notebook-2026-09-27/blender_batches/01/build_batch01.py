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
# 01 f1v: wide branching oval leaves, tan/green alternating, single pale flower, fine fan roots.
begin('s0004','1v',0);roots(spread=.62,n=21);stem((0,0,.32),(.06,0,2.35),.03,.025)
for side in [-1,1]:
 for k in range(3):
  a=(.02,0,.92+k*.35);b=(side*(.43+.10*k),.03*side,1.23+k*.27);stem(a,b,.014,bend=side*.09)
  for j in range(3):t=(j+1)/3;p=tuple(Vector(a).lerp(Vector(b),t));leaf(p,(p[0]+side*.13,p[1]+.05*(j%2),p[2]+.30),.092,G if (j+k)%2 else TAN,name='Oval leaf')
for k in range(5):side=(-1)**k;leaf((.03,0,1.15+k*.22),(side*.22,0,1.38+k*.22),.084,G if k%2 else TAN)
flower((.06,0,2.38),.13,WHITE,5)
# 02 f2r: three seed/flower heads, five divided fan leaves and scroll roots.
begin('s0005','2r',1);stem((0,0,.22),(0,0,2.12),.027)
for side,z in [(-1,1.0),(1,1.1),(-1,1.58),(1,1.72),(0,1.4)]:
 c=(side*.34,-.015,z);stem((0,0,z-.25),c,.012)
 for j in range(5):leaf(c,(c[0]+(j-2)*.115+side*.15,.035*math.sin(j),z+.25+.055*(2-abs(j-2))),.037,G,serrate=.18,name='Divided fan leaflet')
for x,z in [(-.45,2.2),(0,2.5),(.5,2.4)]:
 stem((0,0,1.6),(x,0,z),.013)
 for j in range(19):a=j*2.4;rr=.12*math.sqrt((j+1)/19);end=(x+rr*math.cos(a),rr*.4*math.sin(a),z+.15+rr*math.sin(a));tube('Flower filament',curve((x,0,z-.04),end,.01,0,5),.003,TAN,5);bulb('Seed tip',end,(.012,.012,.014),TAN)
for side in [-1,1]:
 pts=[(side*(.16+.15*math.cos(i*.18)),.025*math.sin(i*.18),.20+.08*math.sin(i*.18)) for i in range(35)];tube('Scroll root',[(0,0,.3)]+pts,.018,RED)
# 03 f2v: kidney leaf and tall pale chalice.
begin('s0006','2v',2);stem((0,0,.06),(0,0,1.75),.022,.025);roots(spread=.19,n=5)
outline=[(0,1.07),(-.12,.9),(-.35,.88),(-.55,1.08),(-.61,1.43),(-.50,1.68),(-.24,1.78),(.17,1.78),(.48,1.65),(.59,1.37),(.50,1.07),(.3,.88),(.12,.93)]
vs=[(x,0,z) for x,z in outline]+[(0,-.105,1.42),(0,.105,1.42)];n=len(outline);fs=[]
for i in range(n):fs.extend([(i,(i+1)%n,n),((i+1)%n,i,n+1)])
mesh('Kidney leaf',vs,fs,G2)
stem((0,0,1.66),(.25,.02,2.12),.014,.05)
# Five cup walls, explicitly volumetric petals.
for j in range(5):a=j*math.tau/5;leaf((.25,.02,2.04),(.25+.18*math.cos(a),.02+.16*math.sin(a),2.44),.10,WHITE,bend=.035,name='Chalice lobe')
# 04 f3r: striped fern silhouette, green/russet recurved leaf pairs, exposed red roots.
begin('s0007','3r',3);roots(spread=.53,n=10,color=RED);stem((0,0,.3),(.02,0,2.49),.023,.015)
for k in range(11):
 z=1.18+k*.114;reach=.43*(1-k/14)
 for side in [-1,1]:leaf((0,0,z),(side*reach,.055*side,z+.13),.072*(1-k/16),G if k%2==0 else RED,bend=side*.055,depth=.04,name='Recurved striped blade')
# 05 f3v: jointed long rhizome; pointed lobed leaves; dark blue terminal curled flower.
begin('s0008','3v',4);tube('Long segmented rhizome',[(-.66,0,.05),(-.5,.01,.08),(-.3,.02,.1),(-.1,0,.13),(.10,0,.21),(.21,0,.37)],[.014,.024,.033,.035,.04,.052],RED,12);stem((.21,0,.35),(.18,0,2.3),.022)
for k in range(3):
 for side in [-1,1]:
  c=(.18+side*.34,0,.75+k*.35);stem((.18,0,.72+k*.35),c,.013)
  for j in range(5):a=(j-2)*.9;leaf(c,(c[0]+side*.19*math.cos(a),.02*math.sin(j),c[2]+.21*math.sin(a)),.055,G,name='Pointed lobed leaflet')
leaf((.18,0,1.8),(-.04,-.015,2.04),.075,BLUE,name='Small dark bract');leaf((.18,0,2.06),(.52,.02,2.47),.19,BLUE,bend=-.07,depth=.11,name='Blue curled flower')
# 06 f4r: branching spray of tiny paired alternating leaves, small pale heads.
begin('s0009','4r',5);roots(spread=.25,n=12);stem((0,0,.33),(0,0,2.3),.013)
for b,(x,z) in enumerate([(-.36,1.65),(.39,1.95),(-.50,2.15),(.50,2.1),(0,2.43)]):
 pts=curve((0,0,.55),(x,0,z),.035*math.sin(b),.03,12);tube('Spray branch',pts,.009,G,6)
 for k in range(2,11):
  p=pts[k]
  for side in [-1,1]:leaf(p,(p.x+side*.085,p.y+.01*side,p.z+.13),.023,G if (k+side)%3 else RED,depth=.014,name='Small paired leaf')
 flower((x,0,z+.04),.075,WHITE,5)
# 07 f4v: stacked root bulbs, many crescent leaflets, two star whorls, blue hanging flower.
begin('s0010','4v',6);roots(spread=.34,n=6)
for k in range(3):bulb('Stacked rhizome',(0,0,.26+k*.16),(.105-k*.022,.07,.11),TAN)
stem((0,0,.65),(.12,0,2.31),.016,.025)
for side in [-1,1]:
 for k in range(12):
  z=.78+k*.105;p=(.06,0,z);end=(side*(.18+.04*math.sin(k)),.025*side,z+.085);leaf(p,end,.032,G,bend=-side*.05,depth=.025,name='Crescent leaflet')
for z in [1.48,2.02]:
 for j in range(8):a=j*math.tau/8;leaf((.12,0,z),(.12+.15*math.cos(a),.015,z+.15*math.sin(a)),.018,G,name='Star whorl')
leaf((.12,0,2.24),(.15,.03,2.57),.12,BLUE,bend=-.075,name='Blue pendent flower')
# 08 f5r: basket of broad looped leaves, open heart, narrow pendant bud.
begin('s0011','5r',7);stem((0,0,.12),(0,0,1.73),.017);roots(spread=.30,n=7)
for side in [-1,1]:
 for k in range(4):
  a=(0,.06*k,1.65);b=(side*.2,.05*k,.93);pts=[]
  for j in range(17):t=j/16;pts.append((side*(.5+.04*k)*math.sin(math.pi*t),.065*k+.075*math.sin(math.pi*t),1.65-.78*t+.1*math.sin(math.pi*t)))
  # flattened thick ribbons following the full loop
  vs=[];fs=[]
  for j,p in enumerate(pts):
   for q in range(8):ang=q*math.tau/8;vs.append((p[0]+.065*math.cos(ang),p[1]+.018*math.sin(ang),p[2]))
  for j in range(16):
   for q in range(8):a0=j*8+q;b0=j*8+(q+1)%8;fs.append((a0,b0,b0+8,a0+8))
  fs += [tuple(reversed(range(8))),tuple(128+q for q in range(8))];mesh('Looped broad leaf',vs,fs,G if k%2 else G2)
tube('Flower hook',[(0,0,1.65),(0,0,1.9),(-.07,0,2.02),(-.13,0,1.96),(-.13,0,1.88)],.012,G);leaf((-.13,0,1.94),(-.13,0,1.81),.043,BLUE,name='Pendant bud')
# 09 f5v: delicate divided palmate foliage and small red star flowers.
begin('s0012','5v',8);roots(spread=.39,n=7);bulb('Root crown',(0,0,.27),(.16,.07,.075),TAN);stem((0,0,.29),(-.05,0,1.72),.012,.05)
for k in range(7):
 side=(-1)**k;z=.54+k*.19;c=(side*(.22+.05*(k%3)),.04*side,z+.16);stem((0,0,z-.08),c,.008,bend=side*.04)
 for j in range(5):a=j*math.pi/3-math.pi/6;leaf(c,(c[0]+.17*math.cos(a),c[1]+.025*math.sin(j),c[2]+.17*math.sin(a)),.037,G,serrate=.3,name='Palmate lobe')
for x,z in [(-.24,1.94),(.34,1.81),(.43,2.18),(.02,2.30)]:stem((0,0,1.3),(x,0,z),.007);flower((x,0,z),.053,RED,7)
# 10 f6r: three comb-like segmented blades and three thick green tubular blooms.
begin('s0013','6r',9);roots(spread=.31,n=13);stem((0,0,.35),(0,0,2.44),.018)
for side,z in [(-1,1.05),(1,.7),(1,1.37)]:
 a=(0,0,z);b=(side*.57,0,z+.03);stem(a,b,.023)
 for k in range(1,9):
  p=Vector(a).lerp(Vector(b),k/9)
  for up in [-1,1]:leaf(p,(p.x+side*.035,.015*up,p.z+up*.15),.029,G,bend=side*.017,depth=.027,name='Comb tooth')
for x,z in [(-.25,1.84),(.35,2.02),(.33,2.43)]:
 stem((0,0,z-.30),(x,0,z),.011);pts=curve((x,0,z),(x+.12,0,z+.14),-.06,.03,7);tube('Tubular green bloom',pts,[.037,.047,.052,.054,.049,.043,.04],G,12);bulb('Russet mouth',(x+.12,-.005,z+.14),(.044,.032,.022),RED)
# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['1v','2r','2v','3r','3v','4r','4v','5r','5v','6r'][i];o.data.body='f'+['1v','2r','2v','3r','3v','4r','4v','5r','5v','6r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='01';scene['source_folia']='f1v f2r f2v f3r f3v f4r f4v f5r f5v f6r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
scene.render.resolution_x=1400;scene.render.resolution_y=1000
result={'plants':[o.name for o in bpy.data.objects if o.name.startswith('PLANT_')], 'meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'), 'interpretation':scene['interpretation']}

# Ensure portable front-face orientation for glTF/WebGL.
import bmesh
for obj in bpy.data.objects:
 if obj.type=='MESH':
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
