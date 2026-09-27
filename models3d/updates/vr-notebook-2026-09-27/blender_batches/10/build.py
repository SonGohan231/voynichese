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
# f47v: fork root, large basal leaves, three blue flowers.
begin('s0094','47v',0)
for s in [-1,1]:tube('Forked brown root',[(s*.35,0,.06),(s*.12,0,.32),(0,0,.56)],[.04,.055,.05],ROOT)
stem((0,0,.5),(0,0,2.07),.025)
for z,w in [(.62,.2),(1.3,.16)]:
 for s in [-1,1]:leaf((0,0,z),(s*.6,0,z+.43),w,G,name='Large pointed blade')
for x,z in [(-.4,2.19),(0,2.46),(.43,2.28)]:stem((0,0,1.6),(x,0,z),.013);flower((x,0,z),.12,BLUE,7)
# f48r: two slender shoots with sparse divided fingers.
begin('s0095','48r',1);roots(spread=.24,n=6)
for x in [-.22,.27]:
 stem((0,0,.32),(x,0,2.34),.013)
 for k in range(8):
  z=.71+k*.19;s=(-1)**k;c=(x+s*.12,0,z);stem((x*.8,0,z-.07),c,.008)
  for j in range(3):leaf(c,(c[0]+s*.2+(j-1)*.065,0,z+.14+(j-1)*.04),.022,G,name='Narrow divided finger')
# f48v: three star-leaf columns with small flowers.
begin('s0096','48v',2);roots(spread=.43,n=9)
for x,h in [(-.38,2.12),(0,2.43),(.38,2.12)]:
 stem((0,0,.35),(x,0,h),.016)
 for k in range(6):
  z=.8+k*.22
  for j in range(7):a=j*math.tau/7;leaf((x,0,z),(x+.14*math.cos(a),.02*math.sin(j),z+.14*math.sin(a)),.027,G,name='Star fan leaflet')
 flower((x,0,h),.075,BLUE,6)
# f49r: two broad lateral leaves on red stalks, two blue/red terminal heads.
begin('s0097','49r',3)
tube('Looped ochre root',[(.25*math.cos(j*math.tau/30),0,.2+.12*math.sin(j*math.tau/30)) for j in range(31)],.032,TAN)
for s in [-1,1]:
 tube('Red tall stem',[(0,0,.25),(s*.11,0,1.5),(s*.43,0,2.2)],.023,RED)
 leaf((s*.1,0,1.39),(s*.75,.015,1.92),.34,G,depth=.095,name='Broad round leaf')
 bulb('Blue flower head',(s*.43,0,2.23),(.105,.065,.12),BLUE);bulb('Red tip',(s*.43,-.015,2.34),(.045,.038,.08),RED)
# f49v: large perforated circular crown; curled lobes and central flower.
begin('s0098','49v',4);roots(spread=.2,n=5);stem((0,0,.25),(0,0,2.46),.017)
for j in range(11):
 a=j*math.tau/11;cx=.34*math.cos(a);cz=1.7+.4*math.sin(a)
 tube('Curled crown blade',[(cx+.18*math.cos(a+t),.015*math.sin(j),cz+.16*math.sin(a+t)) for t in [k*math.tau/18 for k in range(19)]],.044,G,8)
 stem((0,0,1.65),(cx,0,cz),.012)
flower((0,0,2.47),.095,BLUE,7)
# f50r: fan blades with blue ovals, large horizontal oval head.
begin('s0099','50r',5);roots(spread=.34,n=13);stem((0,0,.3),(0,0,2.12),.017)
for x,z in [(-.4,1.15),(.42,1.45),(0,1.64)]:
 stem((0,0,z-.27),(x,0,z),.012)
 for j in range(5):leaf((x,0,z),(x+(j-2)*.07,0,z+.32),.045,G,name='Fan leaf finger')
 bulb('Indigo leaf marking',(x,-.035,z+.14),(.04,.012,.09),BLUE)
bulb('Pale horizontal head',(0,0,2.18),(.36,.07,.12),WHITE)
tube('Blue oval head rim',[(.36*math.cos(j*math.tau/36),-.065,2.18+.12*math.sin(j*math.tau/36)) for j in range(37)],.022,BLUE)
# f50v: paired heart-like blades and a many-toothed brush flower.
begin('s0100','50v',6);roots(spread=.51,n=10);stem((0,0,.3),(0,0,2.12),.024)
for z in [.8,1.3]:
 for s in [-1,1]:
  for j in [-1,1]:leaf((0,0,z),(s*.48,0,z+.19+j*.12),.17,G,bend=s*.035,name='Heart leaf lobe')
for j in range(17):
 x=(j-8)*.035;leaf((0,0,2.05),(x,0,2.43-.1*abs(x)),.022,WHITE if j%2 else BLUE,name='Brush flower tooth')
# f51r: two-legged red bulb, hooked oval blades, three pale russet flowers.
begin('s0101','51r',7);bulb('Red root bulb',(0,0,.35),(.17,.11,.18),RED)
for s in [-1,1]:tube('Red root leg',[(s*.09,0,.31),(s*.17,0,.06)],.035,RED)
stem((0,0,.5),(0,0,2.07),.02)
for z in [.91,1.48]:
 for s in [-1,1]:leaf((0,0,z),(s*.55,0,z+.1),.13,G,bend=s*.02,serrate=.32,name='Hooked toothed blade')
for x,z in [(-.38,2.13),(0,2.38),(.37,2.23)]:stem((0,0,1.8),(x,0,z),.013);flower((x,0,z),.13,WHITE,7);bulb('Russet flower centre',(x,-.04,z),(.055,.04,.055),RED)
# f51v: heart-scroll pairs and two dotted blue flower arches.
begin('s0102','51v',8);roots(spread=.44,n=21,color=WHITE);stem((0,0,.34),(0,0,2.02),.025)
for z in [.7,1.04,1.37,1.7]:
 for s in [-1,1]:
  for j in [-1,1]:leaf((0,0,z),(s*.39,0,z+.19+j*.08),.105,G,bend=-s*.04,name='Curled heart lobe')
for s in [-1,1]:
 pts=[(s*.39*math.sin(t),0,2.04+.4*math.cos(t)) for t in [j*1.8/18 for j in range(19)]];tube('Blue flower arch',[(0,0,1.9)]+pts,.02,BLUE)
 for p in pts[::2]:bulb('Pale arch flower dot',(p[0],-.03,p[2]),(.018,.018,.018),WHITE)
# f52r: red scroll root, four grass tufts, one terminal head.
begin('s0103','52r',9)
for s in [-1,1]:tube('Red scroll root',[(0,0,.26)]+[(s*(.35+.24*math.cos(j*.15)),0,.18+.1*math.sin(j*.15)) for j in range(34)],.023,RED)
stem((0,0,.3),(0,0,2.24),.02)
for x,z in [(-.43,.79),(.42,.92),(-.3,1.34),(.34,1.49)]:
 stem((0,0,z-.18),(x,0,z),.014)
 for j in range(9):leaf((x,0,z),(x+(j-4)*.045,0,z+.39-.02*abs(j-4)),.025,G,name='Dense pointed tuft blade')
flower((0,0,2.24),.11,BLUE,9)
# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['47v','48r','48v','49r','49v','50r','50v','51r','51v','52r'][i];o.data.body='f'+['47v','48r','48v','49r','49v','50r','50v','51r','51v','52r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='10';scene['source_folia']='f47v f48r f48v f49r f49v f50r f50v f51r f51v f52r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'10','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia10_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
