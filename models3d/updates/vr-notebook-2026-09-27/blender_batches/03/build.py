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
# f11v: tight green/russet oval leaf head, three dark terminal shoots, pale forked roots.
begin('s0024','11v',0);roots(spread=.39,n=6,color=TAN);stem((0,0,.24),(0,0,1.7),.025)
for row in range(7):
 z=1.22+row*.15;reach=.47*math.sin(math.pi*(row+1)/9)
 for j in range(7):x=(j-3)/3*reach;leaf((x,0,z),(x+.025,.03*(j%2),z+.19),.058,G if (row+j)%2 else RED,name='Dense oval blade')
for x in [-.13,0,.13]:leaf((x,0,2.1),(x-.07,.02,2.45),.03,BLUE,name='Dark terminal shoot')
# f13r: round lobed leaves, large russet root bulb and dark central spike.
begin('s0025','13r',1);bulb('Red root bulb',(0,0,.42),(.27,.13,.30),RED);roots((0,0,.45),.47,7,color=RED);stem((0,0,.65),(0,0,2.38),.024)
for k in range(3):
 for side in [-1,1]:
  c=(side*.36,0,1.02+k*.36);stem((0,0,.9+k*.3),c,.013)
  for j in range(6):a=j*math.tau/6;leaf(c,(c[0]+.24*math.cos(a),.035*math.sin(j),c[2]+.22*math.sin(a)),.11,G2,name='Rounded leaf lobe')
for k in range(7):leaf((0,0,2.05+k*.046),((-.035 if k%2 else .035),-.02,2.14+k*.046),.022,BLUE,name='Dark upright spike')
# f13v: two branching stacks of looped green/ochre leaves, three upright blue heads.
begin('s0026','13v',2);roots(spread=.34,n=6,color=TAN);stem((0,0,.25),(0,0,1.22),.019)
for side in [-1,1]:
 stem((0,0,.8),(side*.33,0,2.05+side*.18),.014)
 for k in range(4):
  z=1.04+k*.27+side*.1;c=(side*.31,0,z)
  for j in [-1,0,1]:leaf(c,(c[0]+j*.16,.04,z-.18),.10,TAN,name='Ochre loop margin');leaf(c,(c[0]+j*.15,-.012,z-.155),.08,G2,name='Green loop blade')
for x in [-.42,-.28,-.14]:leaf((x,0,2.12),(x,.0,2.29),.023,BLUE,name='Upright indigo head')
# f14r: tall narrow leaves in two whorls and a jointed horizontal pale root.
begin('s0027','14r',3);tube('Horizontal ribbed root',[(x*.11,0,.13) for x in range(-6,7)],.055,TAN,12)
for x in range(-6,7):bulb('Root joint',(x*.11,0,.13),(.021,.061,.061),ROOT)
stem((0,0,.17),(0,0,2.3),.019)
for z in [1.0,1.75]:
 for j in range(7):x=(j-3)*.14;leaf((0,0,z),(x,.03*(j%2),z+.5+.18*(1-abs(j-3)/3)),.044,G2,name='Upright lance blade')
leaf((0,0,2.27),(0,0,2.58),.044,RED,name='Tall terminal bud')
# f14v: two large toothed green blades and a scroll-shaped red root.
begin('s0028','14v',4)
for side in [-1,1]:
 tube('Red scroll root',[(0,0,.27),(side*.28,0,.15),(side*.43,.02,.27),(side*.22,.015,.31),(side*.15,0,.23)],.035,RED)
 stem((0,0,.27),(side*.36,0,2.03),.02)
 leaf((side*.22,0,1.05),(side*.38,.02,2.32),.24,G,serrate=.26,name='Large toothed blade')
 for k in range(10):
  z=1.22+k*.09;reach=.24*math.sin(math.pi*(k+1)/12)
  for ss in [-1,1]:leaf((side*.32,0,z),(side*.32+ss*reach,.015,z+.14),.027,G,name='Serrated tooth')
 for z in [1.5,1.8,2.02]:bulb('Pale inset',(side*.33,-.075,z),(.035,.035,.047),WHITE)
# f15r: deeply divided pointed leaf fronds, pale long flower stalks, red root crown.
begin('s0029','15r',5);roots(spread=.52,n=7,color=RED);stem((0,0,.18),(0,0,1.56),.018);leaf((0,0,.18),(.04,0,.59),.10,RED,name='Red crown')
for side in [-1,1]:
 for k in range(3):
  z=.9+k*.23;c=(side*.21,0,z);stem((0,0,z+.12),c,.01)
  for j in range(4):leaf(c,(side*(.36+j*.09),.02,z-.12+j*.055),.043,G2,serrate=.35,name='Divided serrate leaflet')
for x,z in [(-.27,2.46),(0,2.64),(.32,2.42)]:stem((0,0,1.4),(x,0,z),.009);flower((x,0,z),.065,WHITE,5)
# f15v: four thick oval leaves in a cross, looped upper stalk and dark terminal seedhead.
begin('s0030','15v',6);roots(spread=.49,n=5,color=TAN);stem((0,0,.25),(0,0,1.51),.017)
for j in range(4):a=j*math.tau/4+.35;leaf((0,0,1.35),(.46*math.cos(a),.045*math.sin(j),1.35+.43*math.sin(a)),.18,G2,name='Four oval blades')
tube('Looping upper stalk',[(0,0,1.4),(.1,0,1.75),(.08,0,2.0),(-.13,0,2.12),(-.2,0,1.92)],.012,G)
# f16r: four six-pointed radial leaves, branching upper ochre clusters, thick spreading root.
begin('s0031','16r',7);roots(spread=.60,n=9,color=TAN);stem((0,0,.28),(0,0,2.54),.023)
for x,z in [(-.4,.95),(.38,1.12),(-.35,1.47),(.4,1.7)]:
 stem((0,0,z-.18),(x,0,z),.012)
 for j in range(6):a=j*math.tau/6;leaf((x,0,z),(x+.29*math.cos(a),.02,z+.29*math.sin(a)),.03,G2,name='Six pointed star blade')
for k in range(6):
 for side in [-1,1]:
  x=side*.08*(k%3+1);z=2.0+k*.1;stem((0,0,z-.1),(x,0,z),.005);flower((x,0,z),.026,TAN,4)
# f16v: four russet serrate wheel flowers and one large indigo terminal flower.
begin('s0032','16v',8);roots(spread=.28,n=8,color=TAN);bulb('Ochre root',(0,0,.22),(.18,.10,.18),TAN);stem((0,0,.32),(0,0,2.47),.018)
for x,z in [(-.33,1.02),(.31,1.08),(-.34,1.65),(.35,1.77)]:
 stem((0,0,.5),(x,0,z),.012);flower((x,0,z),.26,RED,13)
flower((0,0,2.49),.35,BLUE,14)
# f17r: flat paired long narrow leaf ladder and three dark flower heads.
begin('s0033','17r',9);roots(spread=.37,n=12,color=TAN);stem((0,0,.35),(0,0,2.52),.016)
for k in range(7):
 for side in [-1,1]:leaf((0,0,.85+k*.15),(side*(.48-k*.018),.025*side,.87+k*.15),.026,G2,name='Narrow paired blade')
for x,z in [(-.32,2.1),(.32,2.12),(0,2.56)]:stem((0,0,1.75),(x,0,z),.009);flower((x,0,z),.095,BLUE,12)

# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['11v','13r','13v','14r','14v','15r','15v','16r','16v','17r'][i];o.data.body='f'+['11v','13r','13v','14r','14v','15r','15v','16r','16v','17r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='03';scene['source_folia']='f11v f13r f13v f14r f14v f15r f15v f16r f16v f17r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'03','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia03_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
