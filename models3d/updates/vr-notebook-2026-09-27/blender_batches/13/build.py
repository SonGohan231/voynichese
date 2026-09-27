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
def rosette(x,z,r=.17,n=10):
 for j in range(n):a=j*math.tau/n;leaf((x,0,z),(x+r*math.cos(a),.014*math.sin(j),z+r*math.sin(a)),r*.15,G,bend=.035,name='Divided radial blade')
# f94v and 95r: preserve all three drawings in the foldout as one source ensemble.
begin('s0170','94v and 95r',0)
for k,x in enumerate([-.58,0,.58]):
 if k==0:
  for j in [-1,0,1]:bulb('Left detached root bulb',(x+j*.15,0,.13),(.1,.06,.11),TAN if j else ROOT)
  stem((x,0,.26),(x,0,1.6),.012);rosette(x,.97,.24,17);flower((x,0,1.62),.065,G,10)
 elif k==1:
  roots(base=(x,0,.33),spread=.23,n=9)
  for s in [-1,1]:
   stem((x,0,.31),(x+s*.18,0,1.56),.011)
   for j in range(7):
    z=.65+j*.12
    for d in [-1,1]:leaf((x+s*.16,0,z),(x+s*.16+d*.065,0,z+.095),.022,G,name='Middle small paired blade')
 else:
  bulb('Right ochre root tray',(x,0,.33),(.29,.09,.09),TAN)
  for j in range(9):leaf((x,0,.4),(x+(j-4)*.055,0,1.18-.025*abs(j-4)),.044,G,name='Right dense basal blade')
  for j in range(3):stem((x,0,.55),(x+(j-1)*.12,0,1.47),.008);bulb('Right dark terminal bud',(x+(j-1)*.12,0,1.47),(.044,.03,.052),BLUE)
# f95v part: forked red root, four coarse leaves, large many-pod crown.
begin('s0171','95v part',1)
for s in [-1,1]:
 pts=curve((0,0,.49),(s*.68,0,.11),s*.04,0,10);tube('Long red root arm',pts,.024,RED)
 for p in pts[2::2]:tube('Hanging root fibre',[p,p+Vector((0,0,-.1))],.006,RED,5)
stem((0,0,.48),(0,0,2.09),.018)
for x,z in [(-.35,1.04),(.36,1.19),(-.33,1.51),(.4,1.52)]:
 stem((0,0,z-.12),(x,0,z),.011);leaf((x*.6,0,z-.08),(x,0,z+.24),.098,G,serrate=.3,name='Coarse toothed oval blade')
for j in range(17):
 a=math.pi*.16+j*math.pi*.68/16;x=.58*math.cos(a);z=1.83+.58*math.sin(a);stem((0,0,1.6),(x,0,z),.006);tube('Outlined pale seed pod',[(x+.044*math.cos(t),0,z+.055*math.sin(t)) for t in [k*math.tau/16 for k in range(17)]],.008,TAN,6)
# f95v: three arched blue-flower shoots with deeply divided foliage, red branching base.
begin('s0172','95v',2)
tube('Broad russet rhizome',[(-.73,0,.25),(0,0,.4),(.71,0,.26)],.075,RED)
for x in [-.58,-.25,.1,.43,.66]:tube('Descending root leg',[(x,0,.3),(x-.05,0,.08)],.034,RED)
for x,h in [(-.44,1.84),(0,2.18),(.42,1.92)]:
 stem((x*.5,0,.4),(x,0,h),.018)
 for k in range(5):
  z=.81+k*.2;s=(-1)**k;stem((x,0,z-.1),(x+s*.13,0,z),.008);rosette(x+s*.13,z,.12,7)
 for j in range(9):
  a=j*math.pi/10;xx=x+.22*math.cos(a);zz=h+.24*math.sin(a);stem((x,0,h-.18),(xx,0,zz),.005);flower((xx,0,zz),.045,BLUE,7)
# f96r: divided stars on spreading branches, large curved pale terminal head, long segmented root fan.
begin('s0173','96r',3);stem((0,0,.39),(0,0,2.23),.023)
for s in [-1,1]:
 for k in range(4):
  end=(s*(.24+k*.16),0,.03);pts=curve((0,0,.4),end,s*.12,0,13);tube('Long curved ochre root',pts,.028,TAN)
  for p in pts[3::3]:bulb('Root segment band',p,(.032,.032,.017),ROOT)
for x,z in [(-.5,.95),(.44,1.01),(-.24,1.27),(.25,1.4),(-.45,1.65),(0,1.9)]:stem((0,0,z-.2),(x,0,z),.012);rosette(x,z,.22,11)
tube('Curving head stalk',[(0,0,1.85),(.07,0,2.28),(.36,0,2.46)],.016,G)
bulb('Broad pale terminal head',(.43,0,2.43),(.26,.11,.16),G2)
for j in range(45):a=j*2.4;r=.23*math.sqrt((j+1)/45);bulb('Pale head speck',(.43+r*math.cos(a),-.115,2.41+.55*r*math.sin(a)),(.011,.009,.011),WHITE)
# f96v: three tall shoots with alternate triangular blades and lower red seed sprays.
begin('s0174','96v',4);bulb('Ochre oval root',(0,0,.24),(.22,.10,.12),TAN);roots(base=(0,0,.27),spread=.42,n=15)
for x,h in [(-.35,2.2),(0,2.43),(.37,2.22)]:
 stem((0,0,.35),(x,0,h),.019)
 for k in range(9):
  s=(-1)**k;z=.71+k*.17;leaf((x,0,z),(x+s*.21,0,z+.16),.074,G,serrate=.12,name='Alternate triangular blade')
for s in [-1,1]:
 for j in range(4):
  x=s*(.36+j*.04);z=.67+j*.065;stem((s*.2,0,.82),(x,0,z),.005)
  for k in range(5):bulb('Lower red seed dot',(x+(k-2)*.022,0,z-.02*k),(.012,.009,.014),RED)
# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(5):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['94v and 95r','95v part','95v','96r','96v'][i];o.data.body='f'+['94v and 95r','95v part','95v','96r','96v'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='13';scene['source_folia']='f94v-and-95r f95v-part f95v f96r f96v';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':5,'batch':'13','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia13_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
