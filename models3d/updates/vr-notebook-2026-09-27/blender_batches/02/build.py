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
# f6v: 5 radiating pointed leaves, 5 round green heads.
begin('s0014','6v',0);roots(spread=.48,n=16);stem((0,0,.3),(0,0,2.35),.02)
for x,z in [(-.45,.9),(.45,.9),(-.32,1.4),(0,1.13),(.3,1.65)]:
 stem((0,0,.6),(x,0,z),.012)
 for j in range(6):a=j*math.tau/6;leaf((x,0,z),(x+.27*math.cos(a),.025*math.sin(j),z+.27*math.sin(a)),.038,G,name='Star blade')
for x,z in [(-.5,2.0),(-.2,2.27),(.16,1.98),(.5,2.13),(.4,2.5)]:stem((0,0,1.1),(x,0,z),.009);bulb('Green spherical head',(x,0,z),(.093,.083,.103),G2)
# f7r: long stem, single large radial divided leaf, bifid reddish root.
begin('s0015','7r',1);stem((0,0,.22),(0,0,1.85),.023)
for side in [-1,1]:tube('Forked root',[(0,0,.3),(side*.13,0,.13),(side*.43,.03,.08),(side*.78,.01,.025)],[.04,.036,.021,.006],RED)
for j in range(9):a=j*math.tau/9;leaf((0,0,1.85),(.67*math.cos(a),.025*math.sin(j),1.85+.70*math.sin(a)),.10,G,depth=.1,name='Radial lanceolate blade')
# f7v: low oval rosette, alternate leaves and russet lance buds.
begin('s0016','7v',2);roots(spread=.16,n=6);stem((0,0,.32),(0,0,2.18),.013)
for j in range(9):a=j*math.tau/9;leaf((0,0,.8),(.42*math.cos(a),.04*math.sin(j),.8+.37*math.sin(a)),.096,G2,name='Rosette oval leaf')
for k in range(5):side=(-1)**k;leaf((0,0,1.0+k*.23),(side*.28,.02,1.29+k*.23),.076,G if k%2 else RED,name='Alternate blade')
# f8r: long stalk with one large pointed basal-lobed leaf.
begin('s0017','8r',3);roots(spread=.54,n=4,color=ROOT);stem((0,0,.19),(0,0,2.0),.014)
vs=[(x,0,z) for x,z in [(0,2.65),(.18,2.35),(.5,2.1),(.36,1.86),(.13,1.99),(0,1.84),(-.14,1.99),(-.38,1.86),(-.5,2.11),(-.18,2.35)]]+[(0,-.13,2.17),(0,.13,2.17)];mesh('Pointed lobed leaf',vs,[(i,(i+1)%10,10) for i in range(10)]+[((i+1)%10,i,11) for i in range(10)],G2)
# f8v: basal large pair, paired pointed leaflets, small upper buds.
begin('s0018','8v',4);roots(spread=.64,n=5,color=TAN);stem((0,0,.22),(0,0,2.6),.018)
for k in range(7):
 z=.65+k*.24
 for side in [-1,1]:leaf((0,0,z),(side*(.42 if k<2 else .34-k*.018),.03*side,z+.28),.125 if k<2 else .054,G2,name='Opposite lance leaf')
for x,z in [(-.22,2.49),(0,2.65),(.21,2.40)]:stem((0,0,2.12),(x,0,z),.006);bulb('Small rust bud',(x,0,z),(.035,.029,.061),RED)
# f9r: asymmetric red branches, deeply lobed green leaves, tall brown inflorescence.
begin('s0019','9r',5);roots(spread=.6,n=24,color=TAN);stem((.12,0,.3),(.12,0,2.6),.024)
for k,(x,z) in enumerate([(-.5,.65),(.35,.7),(-.57,1.1),(.43,1.05),(-.29,1.6),(.44,1.66)]):
 tube('Russet branch',curve((.12,0,.55),(x,0,z),.025),.012,RED)
 for j in range(7):a=j*math.tau/7;leaf((x,0,z),(x+.18*math.cos(a),.025*math.sin(j),z+.18*math.sin(a)),.038,G,bend=.045,serrate=.3,name='Curled lobed leaf')
for k in range(7):
 for side in [-1,1]:leaf((.12,0,1.8+k*.11),(.12+side*.09,0,1.95+k*.11),.018,TAN,name='Branched dry spike')
# f9v: opposing broad lower leaves, slender shoots and indigo flowers.
begin('s0020','9v',6);roots(spread=.22,n=9);stem((0,0,.3),(0,0,2.4),.013)
for k in range(3):
 for side in [-1,1]:leaf((0,0,.7+k*.16),(side*.40,.02*side,.84+k*.16),.055,G2)
for x,z in [(-.34,1.56),(.4,1.7),(-.38,2.27),(.32,2.42),(0,2.34)]:
 stem((0,0,1.05),(x,0,z),.008)
 for side in [-1,1]:leaf((x*.72,0,z-.21),(x*.72+side*.11,.015,z-.02),.019,G2)
 flower((x,0,z),.093,BLUE,5)
# f10r: paired downward curling broad leaves with ochre margins and blue flower.
begin('s0021','10r',7);roots(spread=.42,n=5);stem((0,0,.35),(.02,0,2.2),.018)
for k in range(4):
 for side in [-1,1]:
  a=(0,0,.86+k*.28);b=(side*(.42-k*.025),.04,.75+k*.28);leaf(a,b,.14,TAN,bend=side*.04,depth=.06,name='Ochre leaf edge');leaf(a,(b[0]*.93,-.02,b[2]+.02),.112,G,depth=.065,name='Green leaf centre')
stem((0,0,1.65),(.48,0,2.31),.012,.05);flower((.48,0,2.31),.15,BLUE,11)
for side in [-1,1]:bulb('Red root tip',(side*.4,0,.08),(.13,.06,.065),RED)
# f10v: two long curved lobed green blades and two blue heads.
begin('s0022','10v',8);roots(spread=.25,n=5,color=TAN)
for side in [-1,1]:
 stem((0,0,.25),(side*.28,0,2.28),.015,side*.05)
 for k in range(7):leaf((side*.22,0,.63+k*.20),(side*(.42 if k%2 else .13),.035,.81+k*.20),.10,G,bend=side*.03,depth=.045,name='Wavy leaf lobe')
 flower((side*.28,0,2.31),.071,BLUE,6)
# f11r: umbrella with crossing ribs, five lower hanging green bulbs and blue florets.
begin('s0023','11r',9);roots(spread=.64,n=6,color=TAN)
for k in range(7):
 x=(k-3)*.19;stem((0,0,.25),(x,0,1.85+.2*(1-abs(k-3)/3)),.012,.03)
 for j in range(4):
  xx=x+(j-1.5)*.065;zz=1.86+j*.13+.22*(1-abs(k-3)/3);stem((x,0,1.5),(xx,0,zz),.006)
  leaf((xx,0,zz-.08),(xx+.09,.03,zz+.01),.025,G);flower((xx,0,zz),.038,BLUE,5)
for x in [-.42,-.2,0,.2,.42]:bulb('Pendant green bud',(x,0,1.33),(.065,.045,.09),G2)

# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['6v','7r','7v','8r','8v','9r','9v','10r','10v','11r'][i];o.data.body='f'+['6v','7r','7v','8r','8v','9r','9v','10r','10v','11r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='02';scene['source_folia']='f6v f7r f7v f8r f8v f9r f9v f10r f10v f11r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'02','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia02_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
