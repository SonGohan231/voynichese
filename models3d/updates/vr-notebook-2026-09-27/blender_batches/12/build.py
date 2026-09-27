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
def radial_blade(x,z,r=.18,n=9,material=G):
 for j in range(n):
  a=j*math.tau/n;leaf((x,0,z),(x+r*math.cos(a),.016*math.sin(j),z+r*math.sin(a)),r*.22,material,name='Rounded radial leaf lobe')
# f65r: wide branching leaves, terminal spray, branching root chain.
begin('s0117','65r',0);stem((0,0,.62),(0,0,2.23),.022)
for s in [-1,1]:
 pts=curve((0,0,.62),(s*.63,0,.1),s*.08,0,12);tube('Branching red root chain',pts,.015,RED)
 for p in pts[2::3]:bulb('Red root chain swelling',p,(.12,.055,.05),RED)
for k in range(9):
 s=(-1)**k;z=.88+k*.135;x=s*(.31+.14*(k%2));stem((0,0,z-.12),(x,0,z),.014);radial_blade(x,z,.2,10)
for j in range(7):x=(j-3)*.13;stem((0,0,1.9),(x,0,2.35),.006);bulb('Pale green terminal bud',(x,0,2.35),(.043,.026,.043),G2)
# f65v: multi-branched small lobed flowers and single tall green chalice.
begin('s0118','65v',1);roots(spread=.51,n=11);stem((0,0,.34),(0,0,2.17),.022)
for j in range(8):
 s=(-1)**j;z=1.27+j*.115;x=s*(.29+.06*(j%3));stem((0,0,.65+j*.1),(x,0,z),.012)
 for k in range(3):xx=x+s*k*.06;zz=z+k*.11;stem((x,0,z-.2),(xx,0,zz),.006);radial_blade(xx,zz,.063,5,G2)
for j in range(5):leaf((0,0,2.13),((j-2)*.046,0,2.53),.032,G,name='Tall chalice lobe')
flower((0,0,2.5),.095,BLUE,6)
# f66v: three arches of segmented green blades, red fork root.
begin('s0120','66v',2)
for s in [-1,1]:tube('Red fork root',[(s*.35,0,.07),(s*.21,0,.18),(0,0,.45)],.032,RED)
stem((0,0,.44),(0,0,2.03),.02)
for x,z,r,n in [(-.4,1.07,.25,5),(.4,1.1,.25,5),(0,1.42,.41,8)]:
 stem((0,0,.72),(x,0,z),.016)
 for k in range(n):
  h=z+k*.105
  for s in [-1,1]:leaf((x,0,h),(x+s*r*(1-k/(n+3)),0,h-.05),.036,G,bend=-s*.035,name='Curved segmented blade')
# f87r: two dense stacked fans, upper floral stalks, large russet fork.
begin('s0159','87r',3)
for s in [-1,1]:tube('Long russet root',[(s*.67,0,.03),(s*.32,0,.22),(0,0,.48)],[.018,.065,.09],RED)
stem((0,0,.44),(0,0,2.16),.018)
for z in [.79,1.59]:
 for j in range(9):leaf((0,0,z),((j-4)*.09,0,z+.5-.04*abs(j-4)),.074,G,name='Stacked broad fan blade')
for x,z in [(-.15,2.53),(.32,2.39)]:stem((0,0,2.03),(x,0,z),.008);flower((x,0,z),.07,BLUE,5)
# f87v: two joined root bodies, left fan and right fern with red inflorescences.
begin('s0160','87v',4)
for x in [-.46,.38]:
 bulb('Russet rhizome body',(x,0,.29),(.13,.08,.16),RED);roots(base=(x,0,.3),spread=.26,n=5,color=RED)
tube('Connected russet rhizome',[(-.46,0,.31),(0,0,.24),(.38,0,.34)],.04,RED)
for j in range(7):leaf((-.46,0,.44),(-.46+(j-3)*.063,0,1.1-.03*abs(j-3)),.05,G,name='Left fan leaf')
stem((-.46,0,.45),(-.53,0,1.4),.01);radial_blade(-.53,1.4,.072,9)
for x,h in [(.13,1.82),(.4,2.2),(.66,1.87)]:
 stem((.38,0,.43),(x,0,h),.015)
 for k in range(7):
  for s in [-1,1]:leaf((x,0,.68+k*.15),(x+s*.13,0,.83+k*.15),.031,G,name='Right fern blade')
 for j in range(4):xx=x+(j-1.5)*.085;stem((x,0,h),(xx,0,h+.28),.006);bulb('Red flower cap',(xx,0,h+.28),(.042,.025,.025),RED)
# f90r: symmetrical compound lanceolate leaves and three round heads.
begin('s0165','90r',5);roots(spread=.48,n=13,color=RED);stem((0,0,.3),(0,0,2.24),.022)
for k in range(5):
 z=.76+k*.27
 for s in [-1,1]:
  a=(0,0,z);b=(s*(.39+.03*k),0,z+.2);stem(a,b,.011)
  for j in range(1,5):p=Vector(a).lerp(Vector(b),j/4);leaf(p,(p.x+s*.095,0,p.z+.17),.031,G,name='Compound narrow blade')
for x,z in [(-.31,2.25),(0,2.46),(.31,2.26)]:stem((0,0,1.85),(x,0,z),.01);flower((x,0,z),.087,G,10)
# f90v part: three pointed segmented blades and three blue-white flowers, long ochre root.
begin('s0166','90v part',6)
tube('Long ochre rhizome',[(-.7,0,.06),(-.45,0,.2),(0,0,.46),(.26,0,.15),(.4,0,.13)],[.02,.065,.09,.037,.02],TAN)
stem((0,0,.43),(0,0,2.06),.018)
for x,z in [(-.63,1.14),(.64,1.2),(0,1.94)]:
 a=(0,0,.85);b=(x,0,z);stem(a,b,.012)
 for k in range(1,8):
  p=Vector(a).lerp(Vector(b),k/8)
  for s in [-1,1]:leaf(p,(p.x+s*.12,0,p.z+.2),.025,G,name='Pointed divided blade')
for x,z in [(-.29,2.25),(0,2.52),(.36,2.3)]:stem((0,0,1.7),(x,0,z),.009);flower((x,0,z),.115,WHITE,5);flower((x,-.022,z),.07,BLUE,5)
# f93r: huge paired curled blades, dotted ochre broad head and fine roots.
begin('s0167','93r',7);roots(spread=.37,n=21,color=RED);stem((0,0,.36),(0,0,2.08),.021)
for k in range(8):
 z=.6+k*.17
 for s in [-1,1]:leaf((0,0,z),(s*.43,0,z-.09),.105,G,bend=-s*.04,name='Broad curled paired blade')
bulb('Broad ochre seed head',(0,0,2.21),(.47,.12,.26),TAN)
for j in range(83):
 a=j*2.4;r=.42*math.sqrt((j+.5)/83);x=r*math.cos(a);z=2.21+r*.53*math.sin(a);bulb('Dark seed dot',(x,-.126,z),(.009,.006,.009),ROOT)
# f93v: six narrow curved star leaves, dotted red spray, four swollen root lobes.
begin('s0168','93v',8);stem((0,0,.57),(0,0,2.14),.021)
for x in [-.5,-.17,.17,.5]:bulb('Swollen ochre root lobe',(x,0,.2),(.17,.09,.15),TAN);tube('Root link',[(0,0,.5),(x,0,.28)],.016,ROOT)
for z in [.84,1.29,1.7]:
 for s in [-1,1]:
  x=s*.32;stem((0,0,z-.11),(x,0,z),.009)
  for j in range(9):a=j*math.tau/9;leaf((x,0,z),(x+.22*math.cos(a),.03*math.sin(j),z+.22*math.sin(a)),.018,G,bend=.035,name='Curved star leaf finger')
for k in range(5):
 x=(k-2)*.11;stem((0,0,1.96),(x,0,2.49),.007)
 for j in range(4):bulb('Red spray dot',(x,0,2.2+j*.095),(.025,.022,.024),RED)
# f94r: paired leaves on centre shoot and two arching side shoots, dark terminal buds.
begin('s0169','94r',9);roots(spread=.51,n=17,color=RED);stem((0,0,.36),(0,0,2.17),.02)
for k in range(9):
 for s in [-1,1]:leaf((0,0,.71+k*.145),(s*.13,0,.8+k*.145),.047,G,name='Central rounded leaf')
for s in [-1,1]:
 pts=[(s*(.18+.4*math.sin(t)),0,.62+1.2*math.sin(t/2)) for t in [j*math.pi/15 for j in range(16)]];tube('Arched leafy side branch',[(0,0,.4)]+pts,.015,G)
 for p in pts[2:]:
  for d in [-1,1]:leaf(p,(p[0]+d*.08,0,p[2]+.11),.038,G2,name='Rounded arch blade')
for x,z in [(-.12,2.27),(0,2.4),(.13,2.26)]:stem((0,0,2),(x,0,z),.009);bulb('Dark terminal bud',(x,0,z),(.055,.035,.065),BLUE)
# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['65r','65v','66v','87r','87v','90r','90v part','93r','93v','94r'][i];o.data.body='f'+['65r','65v','66v','87r','87v','90r','90v part','93r','93v','94r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='12';scene['source_folia']='f65r f65v f66v f87r f87v f90r f90v-part f93r f93v f94r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'12','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia12_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
