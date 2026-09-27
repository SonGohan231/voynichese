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
# f37v: paired drooping broad leaves, two circular basal leaves, three dark buds, thick brown branched root.
begin('s0074','37v',0);roots(spread=.41,n=6,color=ROOT);bulb('Brown root body',(0,0,.31),(.13,.09,.17),ROOT);stem((0,0,.43),(0,0,2.37),.018)
for side in [-1,1]:
 bulb('Round basal green leaf',(side*.32,0,.88),(.22,.047,.19),G2)
 for k in range(5):leaf((0,0,1.08+k*.22),(side*.43,.035,1.0+k*.22),.09,G2,bend=side*.05,depth=.08,name='Drooping paired blade')
for x,z in [(-.23,2.42),(0,2.64),(.24,2.41)]:stem((0,0,2.12),(x,0,z),.008);leaf((x,0,z),(x+.02,0,z+.13),.037,BLUE,name='Dark bud')
# f38r: a single tall V-notched dense pointed blade, several pale oval openings, slender split root.
begin('s0075','38r',1);roots(spread=.34,n=3,color=TAN);stem((0,0,.2),(0,0,2.53),.014)
for side in [-1,1]:
 leaf((0,0,.7),(side*.24,0,2.48),.20,G2,serrate=.23,name='Tall split crown blade')
 for k in range(12):z=.78+k*.12;leaf((side*.10,0,z),(side*(.17+k*.015),0,z+.30),.042,G2,name='Pointed edge tooth')
for k in range(5):bulb('Pale drawn oval',(0,-.074,1.00+k*.25),(.033,.012,.052),WHITE)
# f38v: alternating green and ochre thick oval leaf ladder, blue terminal petals, ochre forked root.
begin('s0076','38v',2);roots(spread=.43,n=5,color=TAN);stem((0,0,.24),(0,0,2.39),.018)
for k in range(7):
 for side in [-1,1]:leaf((0,0,.8+k*.22),(side*.30,.04*side,1.02+k*.22),.083,G2 if (k+(side==1))%2 else TAN,name='Alternating thick oval blade')
flower((0,0,2.65),.15,BLUE,8)
# f39r: multiple upright lance-leaf shoots over a horizontal root mat, one dark flower cap.
begin('s0077','39r',3);tube('Horizontal root mat',[(-.72,0,.20),(0,0,.23),(.72,0,.20)],[.045,.06,.045],TAN)
for j in range(17):x=(j-8)*.082;tube('Hanging root strand',[(x,0,.2),(x+.027,0,.09),(x,0,.02)],[.012,.009,.004],TAN,6)
for j in range(7):
 x=(j-3)*.17;z=1.5+.20*(j%3);stem((x,0,.26),(x,0,z),.012)
 for k in range(4):
  for side in [-1,1]:leaf((x,0,.64+k*.22),(x+side*.13,.02,.96+k*.22),.052,G2,name='Narrow upright blade')
leaf((.51,0,1.73),(.5,0,2.23),.067,BLUE,name='Terminal dark flower')
# f39v: four paired broad segmented fronds and two dark speckled terminal heads; fine red roots.
begin('s0078','39v',4);roots(spread=.59,n=18,color=RED);stem((0,0,.32),(0,0,2.35),.018)
for k in range(4):
 for side in [-1,1]:
  z=.94+k*.27;stem((0,0,z),(side*.59,0,z+.20),.012)
  for j in range(6):x=side*(.12+j*.077);leaf((x,0,z+j*.025),(x+side*.04,.03,z+.19+j*.025),.072,G2,name='Broad divided lobe')
for x in [-.23,.23]:
 stem((0,0,1.96),(x,0,2.38),.009)
 for j in range(39):a=j*2.4;r=.11*math.sqrt((j+1)/39);bulb('Dark seed cluster',(x+r*math.cos(a),.01,2.47+r*math.sin(a)),(.01,.01,.013),BLUE)
# f40r: two comb fronds, oval green neck and a large indigo/pale wheel; thick root fan.
begin('s0079','40r',5);roots(spread=.58,n=12,color=TAN);stem((0,0,.35),(0,0,2.54),.018)
for side in [-1,1]:
 stem((0,0,.98),(side*.42,0,1.57),.013)
 for k in range(15):x=side*(.08+k*.026);z=1.03+k*.035;leaf((x,0,z),(x+side*.26,.02,z+.18),.021,G2,name='Fine comb frond blade')
bulb('Green oval neck',(0,0,2.12),(.10,.056,.15),G2);wheel((0,0,2.55),.23,17,BLUE);bulb('Pale central disk',(0,0,2.55),(.115,.042,.115),WHITE)
# f40v: four scalloped round leaves and a red lattice funnel crowned by a broad ring.
begin('s0080','40v',6);roots(spread=.52,n=9,color=TAN);stem((0,0,.27),(0,0,1.6),.02)
for x,z in [(-.48,.92),(-.18,1.05),(.29,.99),(.48,1.14)]:
 stem((0,0,.55),(x,0,z),.012)
 for j in range(8):a=j*math.tau/8;leaf((x,0,z),(x+.16*math.cos(a),.01,z+.16*math.sin(a)),.07,G2,name='Scalloped rounded leaf')
for j in range(16):a=j*math.tau/16;tube('Red funnel rib',[(0,0,1.35),(.44*math.cos(a),.22*math.sin(a),2.35)],.011,RED,7)
for z in [1.63,1.86,2.1]:r=(z-1.35)*.44;tube('Funnel cross ring',[(r*math.cos(j*math.tau/24),r*.5*math.sin(j*math.tau/24),z)for j in range(25)],.007,RED,6)
for j in range(20):a=j*math.tau/20;leaf((.41*math.cos(a),.2*math.sin(a),2.35),(.49*math.cos(a),.24*math.sin(a),2.46),.052,BLUE,name='Indigo crown tooth')
# f41r: several pale-green fine comb branches, ochre bifid root.
begin('s0081','41r',7);roots(spread=.37,n=12,color=TAN)
for j in range(8):
 x=(j-3.5)*.12;z=1.4+.70*(1-abs(j-3.5)/3.5);comb((0,0,.30),(x,0,z),13,.11,G2)
# f41v: seven deeply dissected leaf fans, two red swollen roots, small pale dotted umbrella.
begin('s0082','41v',8)
for side in [-1,1]:bulb('Red swollen root',(side*.12,0,.31),(.078,.07,.22),RED);tube('Root filament',[(side*.12,0,.14),(side*.19,0,.025)],[.018,.003],RED)
stem((0,0,.49),(0,0,2.22),.014)
for k in range(7):side=(-1)**k;c=(side*.34,0,.94+k*.16);stem((0,0,c[2]-.11),c,.01);star(c,.26,9,.029)
for j in range(31):x=(j%11-5)*.047;z=2.27+(j//11)*.055;bulb('Pale umbrella speck',(x,0,z),(.015,.012,.017),WHITE)
# f42r: long slender stem with three russet bulbs at the neck, one large bifurcated leaf crown.
begin('s0083','42r',9);roots(spread=.51,n=3,color=TAN);stem((0,0,.20),(0,0,2.06),.014)
for x in [-.18,0,.18]:leaf((0,0,1.63),(x,0,1.4),.087,RED,name='Red neck bulb')
for j in range(8):x=(j-3.5)*.075;leaf((0,0,1.75),(x,.025,2.62-abs(j-3.5)*.03),.066,G2,name='Divided large crown blade')

# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['37v','38r','38v','39r','39v','40r','40v','41r','41v','42r'][i];o.data.body='f'+['37v','38r','38v','39r','39v','40r','40v','41r','41v','42r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='08';scene['source_folia']='f37v f38r f38v f39r f39v f40r f40v f41r f41v f42r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'08','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia08_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
