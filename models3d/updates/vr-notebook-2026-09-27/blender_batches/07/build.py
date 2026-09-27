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
def star(c,r=.2,n=5,w=.05,material=G2):
 for j in range(n):a=j*math.tau/n;leaf(c,(c[0]+r*math.cos(a),c[1]+.025*math.sin(j),c[2]+r*math.sin(a)),w,material,name='Radiating leaf lobe')
def comb(a,b,n=9,w=.13,material=G2):
 stem(a,b,.012)
 for k in range(1,n):
  p=Vector(a).lerp(Vector(b),k/n)
  for side in [-1,1]:leaf(p,(p.x+side*w,p.y+.02*side,p.z+.11),.027,material,name='Divided comb blade')
def wheel(c,r=.18,n=14,material=G2):
 for j in range(n):a=j*math.tau/n;leaf((c[0]+r*.6*math.cos(a),0,c[2]+r*.6*math.sin(a)),(c[0]+r*math.cos(a),.02,c[2]+r*math.sin(a)),r*.14,material,name='Radial wheel lobe')
# f32v: small star-leaf branches and three indigo arrow-like flowers, curved lower root.
begin('s0064','32v',0);tube('Curved ochre root',[(-.18,0,.03),(0,0,.33),(.07,0,.63)], [.035,.075,.055],TAN);stem((.07,0,.63),(0,0,2.45),.013)
for k in range(8):side=(-1)**k;c=(side*.24,0,.85+k*.16);stem((0,0,.74+k*.16),c,.006);star(c,.13,5,.026)
for x,z in [(-.36,1.99),(.38,2.07),(0,2.63)]:stem((0,0,1.55),(x,0,z),.007);star((x,0,z),.13,4,.058,BLUE)
# f33r: broad pointed lower rosette and two circular radial heads above pale fibres.
begin('s0065','33r',1);roots(spread=.44,n=15,color=TAN)
for j in range(10):a=j*math.tau/10;leaf((0,0,.72),(.58*math.cos(a),.04*math.sin(j),1.08+.62*math.sin(a)),.104,G2,name='Large pointed rosette blade')
for x,z in [(-.29,2.09),(.31,2.19)]:stem((0,0,.6),(x,0,z),.01);wheel((x,0,z),.23,18,G2)
# f33v: four green star-whorls, two tilted pale/indigo oval heads, round ochre root structures.
begin('s0066','33v',2);roots(spread=.40,n=8,color=TAN);stem((0,0,.29),(0,0,2.1),.017)
for x,z in [(-.3,.95),(.33,.94),(-.3,1.43),(.35,1.48)]:stem((0,0,z-.12),(x,0,z),.01);star((x,0,z),.28,12,.035)
for side in [-1,1]:
 c=(side*.32,0,2.25);stem((0,0,1.61),c,.011)
 for j in range(17):a=j*math.tau/17;leaf((c[0]+.28*math.cos(a),0,c[2]+.12*math.sin(a)),(c[0]+.34*math.cos(a),.025,c[2]+.19*math.sin(a)),.041,BLUE,name='Blue ring tooth')
 bulb('Pale oval centre',c,(.26,.055,.13),WHITE)
 bulb('Round root body',(side*.43,0,.13),(.14,.1,.13),TAN)
# f34r: six dense pointed fan clusters, thin upper wheels and wide red root fan.
begin('s0067','34r',3);roots(spread=.68,n=19,color=RED);stem((0,0,.30),(0,0,2.45),.016)
for k in range(3):
 for side in [-1,1]:
  c=(side*.30,0,.82+k*.39);stem((0,0,c[2]-.12),c,.009)
  for j in range(9):leaf(c,(c[0]+(j-4)*.048,.02,c[2]+.27-.035*abs(j-4)),.024,G2,name='Dense pointed fan blade')
for x,z in [(-.18,2.28),(.23,2.5),(-.11,2.65)]:wheel((x,0,z),.10,12,G2)
# f34v: three tiers of bead-like green/ochre leaves and broad thick root lobes.
begin('s0068','34v',4);roots(spread=.63,n=8,color=TAN);stem((0,0,.30),(0,0,2.29),.018)
for side in [-1,1]:
 for k in range(3):
  z=.86+k*.38;stem((0,0,z),(side*.66,0,z+.07),.012)
  for j in range(7):bulb('Bead-like leaf',(side*(.13+j*.078),0,z+.075),(.056,.033,.054),G2 if (j+k)%3 else TAN)
for x,z in [(-.26,2.31),(.23,2.41),(0,2.16)]:flower((x,0,z),.055,WHITE,11)
# f35r: large open ochre/green chalice with six curling indigo stamens; red fine roots.
begin('s0069','35r',5);roots(spread=.50,n=10,color=RED);stem((0,0,.3),(0,0,1.39),.017)
for j in range(20):
 a=j*math.tau/20;leaf((0,0,1.12),(.56*math.cos(a),.32*math.sin(a),2.11),.13,TAN,depth=.04,name='Chalice ochre wall');leaf((.42*math.cos(a),.24*math.sin(a),1.86),(.56*math.cos(a),.32*math.sin(a),2.17),.075,G2,name='Chalice green rim')
for j in range(6):x=(j-2.5)*.065;stem((0,0,1.39),(x,0,2.48),.009);tube('Blue curved stamen',[(x,0,2.46),(x-.035,0,2.61),(x-.10,0,2.58),(x-.11,0,2.47)],.012,BLUE)
# f35v: long looped lower stalk, scattered small round lobes, a large lobed crown.
begin('s0070','35v',6);roots(spread=.55,n=9,color=RED)
for side in [-1,1]:tube('Looped lower stem',[(0,0,.28),(side*.22,0,.72),(0,0,1.09)],.014,G2)
stem((0,0,1.08),(0,0,2.48),.016)
for k in range(7):side=(-1)**k;c=(side*.20,0,1.14+k*.15);stem((0,0,c[2]-.07),c,.005);star(c,.12,6,.04)
for j in range(13):a=j*math.pi/12;leaf((0,0,2.15),(.52*math.cos(a),.025,2.19+.43*math.sin(a)),.09,G2,name='Large lobed crown')
# f36r: branching lobed leaves with several dense ochre flower clusters, curled root crown.
begin('s0071','36r',7);roots(spread=.54,n=13,color=RED);stem((0,0,.26),(0,0,2.33),.015)
for k in range(9):
 side=(-1)**k;c=(side*.28,0,.68+k*.2);stem((0,0,c[2]-.1),c,.007);star(c,.20,6,.048)
 if k%3==0:
  for j in range(16):a=j*2.4;r=.12*math.sqrt((j+1)/16);bulb('Ochre clustered floret',(c[0]+r*math.cos(a),0,c[2]+.20+r*math.sin(a)),(.014,.014,.015),TAN)
# f36v: 12 small star whorls with pale seed heads and strongly ribbed root.
begin('s0072','36v',8);roots(spread=.34,n=10,color=RED);stem((0,0,.30),(0,0,2.49),.016)
for k in range(10):side=(-1)**k;c=(side*(.2+.06*(k%2)),0,.7+k*.16);stem((0,0,c[2]-.1),c,.007);star(c,.16,8,.025)
for x,z in [(-.16,2.44),(0,2.64),(.2,2.45)]:flower((x,0,z),.08,WHITE,14)
# f37r: long hanging narrow leaves on alternate branches, russet spherical flower clusters.
begin('s0073','37r',9);roots(spread=.24,n=9,color=RED);stem((0,0,.3),(0,0,2.34),.014)
for k in range(6):
 side=(-1)**k;z=.88+k*.20;stem((0,0,z),(side*.24,0,z+.16),.008);leaf((side*.24,0,z+.16),(side*.30,.05,z-.21),.074,G2,bend=side*.04,depth=.10,name='Hanging curved blade')
for x,z in [(-.17,2.40),(.13,2.53),(0,2.24)]:flower((x,0,z),.08,RED,12)

# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['32v','33r','33v','34r','34v','35r','35v','36r','36v','37r'][i];o.data.body='f'+['32v','33r','33v','34r','34v','35r','35v','36r','36v','37r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='07';scene['source_folia']='f32v f33r f33v f34r f34v f35r f35v f36r f36v f37r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
scene.render.resolution_x=1400;scene.render.resolution_y=1000
result={'plants':[o.name for o in bpy.data.objects if o.name.startswith('PLANT_')], 'meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'), 'interpretation':scene['interpretation']}

# Ensure portable front-face orientation for glTF/WebGL.
import bmesh
for obj in bpy.data.objects:
 if obj.type=='MESH':
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
# Consolidate semantic roles to reduce draw calls without flattening the plant roots.
for root in [o for o in bpy.data.objects if o.name.startswith('PLANT_')]:
 for role,words in [('roots',['root','rhizome']),('flowers',['head','flower','floret','bud','spike','petal']),('stems',['stem','branch']),('leaves',[])]:
  group=[o for o in list(root.children) if o.type=='MESH' and not o.get('semantic_role') and (any(w in o.name.lower() for w in words) if words else True)]
  if not group:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in group:o.select_set(True)
  bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();group[0].name=root.name+' | '+role;group[0]['semantic_role']=role
result={'plants':10,'batch':'07','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia07_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
