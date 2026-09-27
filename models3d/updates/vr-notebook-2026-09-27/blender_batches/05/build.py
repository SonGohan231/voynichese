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
# f22v: four tiers of curling segmented oval leaves, indigo/ochre hooked flower, red thorn rhizome.
begin('s0044','22v',0);tube('Red horizontal rhizome',[(-.65,0,.11),(-.25,0,.13),(.2,0,.15),(.65,0,.12)],[.04,.06,.075,.045],RED)
for k in range(13):x=k*.1-.6;tube('Root thorn',[(x,0,.12),(x+.03,0,.27)],[.016,.003],RED,6)
stem((0,0,.2),(0,0,2.15),.018)
for k in range(4):
 for side in [-1,1]:
  x=side*.4;z=.78+k*.32;stem((0,0,z-.15),(x,0,z),.012)
  for j in range(4):leaf((x-side*j*.07,0,z),(x-side*j*.07,.055,z+.15),.064,G2,depth=.06,name='Segmented oval blade')
tube('Hooked flower stalk',[(0,0,2.0),(0,0,2.29),(-.11,0,2.47),(-.28,0,2.35)],.012,G);flower((-.28,0,2.35),.13,TAN,5);leaf((-.28,-.03,2.32),(-.26,-.04,2.18),.07,BLUE,name='Dark flower tip')
# f23r: compound fan leaflets on arched branches, tiny blue flowers, jointed pale rhizome.
begin('s0045','23r',1);tube('Pale segmented rhizome',[(-.7,0,.14),(0,0,.14),(.7,0,.14)],[.09,.095,.075],TAN)
for k in range(13):x=-.65+k*.1;roots((x,0,.13),.025,3,color=ROOT)
for side in [-1,1]:
 stem((0,0,.27),(side*.49,0,1.89),.012,side*.13)
 for k in range(7):
  c=(side*(.12+k*.052),0,.68+k*.17);star(c,.17,5,.037)
 for x,z in [(side*.42,2.03),(side*.22,2.29)]:flower((x,0,z),.053,BLUE,5)
# f23v: 3 clusters of broad green/ochre leaves; red branching roots and tall eye-centred flower.
begin('s0046','23v',2);roots(spread=.66,n=11,color=RED);stem((0,0,.24),(0,0,2.31),.018)
for x,z in [(-.43,.88),(.39,.82),(0,1.72)]:
 stem((0,0,.3),(x,0,z),.013)
 for j in range(7):a=j*math.tau/7;leaf((x,0,z),(x+.3*math.cos(a),.045*math.sin(j),z+.28*math.sin(a)),.115,G2 if j%3 else TAN,name='Round clustered blade')
 for j in range(3):flower((x+(j-1)*.08,0,z+.37),.04,BLUE,4)
for j in range(7):a=j*math.tau/7;leaf((0,0,2.45),(.18*math.cos(a),.03,2.45+.17*math.sin(a)),.058,BLUE,name='Radial dark petal')
bulb('Pale eye',(0,-.04,2.45),(.09,.05,.05),WHITE)
# f24r: three tall thin stalks, many alternating small lobes and two bent terminal leaf tips.
begin('s0047','24r',3);roots(spread=.36,n=18,color=TAN)
for x in [-.25,0,.25]:
 stem((0,0,.3),(x,0,2.25),.014)
 for k in range(8):
  z=.71+k*.17;side=(-1)**k;leaf((x,0,z),(x+side*.11,.02,z+.10),.05,G2,name='Alternating side lobe')
for x,side in [(-.25,1),(.25,1)]:leaf((x,0,2.22),(x+side*.23,.04,2.48),.16,G2,bend=-.04,depth=.08,name='Bent terminal blade')
# f24v: paired round leaves with tapering extensions, five blue terminal flowers, five pointed ochre roots.
begin('s0048','24v',4);roots(spread=.42,n=5,color=TAN);stem((0,0,.31),(0,0,2.32),.017)
for k in range(4):
 for side in [-1,1]:
  z=.72+k*.29;c=(side*.31,0,z);stem((0,0,z-.13),c,.011);bulb('Round green blade',c,(.105,.038,.105),G2);leaf(c,(c[0]+side*.23,.02,z-.1),.035,G2,name='Tapered leaf extension')
for x,z in [(-.32,2.08),(.32,2.14),(-.3,2.48),(0,2.62),(.32,2.49)]:stem((0,0,1.82),(x,0,z),.007);flower((x,0,z),.068,BLUE,5)
# f25r: few opposite oval leaves, larger pointed top cluster, small reddish junctions.
begin('s0049','25r',5);roots(spread=.30,n=5,color=RED);stem((0,0,.21),(0,0,2.1),.012)
for k in [0,1,3,4]:
 for side in [-1,1]:leaf((0,0,.54+k*.27),(side*.36,.02,.58+k*.27),.093,G2,name='Opposite oval leaf')
for j in range(5):x=(j-2)*.18;leaf((0,0,1.98),(x,0,2.45-abs(j-2)*.08),.105,G2,name='Pointed terminal blade')
for z in [.78,1.29,1.9]:flower((0,-.015,z),.025,RED,4)
# f25v: large dense radial fan of pointed broad leaves and fine spreading roots.
begin('s0050','25v',6);roots(spread=.55,n=21,color=TAN);stem((0,0,.25),(0,0,1.39),.024)
for j in range(13):a=j*math.tau/13;leaf((0,0,1.68),(.65*math.cos(a),.06*math.sin(j),1.68+.73*math.sin(a)),.112,G2,depth=.065,name='Large radial pointed blade')
# f26r: alternate rounded scalloped leaves, a forked terminal dotted spray and red looping root.
begin('s0051','26r',7);roots(spread=.19,n=4,color=RED);stem((0,0,.24),(0,0,2.33),.016)
for k in range(8):
 side=(-1)**k;c=(side*.26,0,.62+k*.19);stem((0,0,c[2]-.1),c,.01)
 for j in range(7):a=j*math.tau/7;leaf(c,(c[0]+.15*math.cos(a),.01,c[2]+.15*math.sin(a)),.074,G2,name='Scalloped rounded blade')
for side in [-1,1]:
 stem((0,0,2.06),(side*.43,0,2.71),.006)
 for j in range(11):x=side*(.04+j*.036);z=2.14+j*.05;bulb('Tiny dark seed',(x,0,z),(.016,.014,.018),BLUE)
# f26v: paired loop-shaped fronds made of rounded green beads, indigo upper flower clusters.
begin('s0052','26v',8);roots(spread=.61,n=8,color=RED);stem((0,0,.28),(0,0,2.25),.018)
for side in [-1,1]:
 for k in range(3):
  z=.78+k*.33;stem((0,0,z),(side*.20,0,z+.05),.01)
  for j in range(17):a=j*math.tau/17;x=side*(.4+.24*math.cos(a));zz=z+.13*math.sin(a);bulb('Looped round leaflet',(x,0,zz),(.047,.026,.043),G2)
for j in range(7):x=(j-3)*.095;z=2.21+.2*(1-abs(j-3)/3);stem((0,0,1.72),(x,0,z),.007);flower((x,0,z),.047,BLUE,5)
# f27r: large three-pointed green crown, small three rounded lower leaves, paired hooked root ends.
begin('s0053','27r',9);stem((0,0,.25),(0,0,1.8),.018)
for side in [-1,1]:tube('Hooked root',[(0,0,.28),(side*.4,0,.05),(side*.59,0,.1),(side*.62,0,.28)],[.03,.028,.025,.012],TAN)
for x,z in [(0,.81),(.2,1.05),(.37,.85)]:leaf((0,0,.84),(x+.08,0,z+.14),.11,G2,name='Small rounded lower leaf')
for x,z in [(-.49,2.15),(0,2.6),(.5,2.21)]:leaf((0,0,1.47),(x,0,z),.23,G2,depth=.09,name='Large pointed crown blade')
for x,z in [(-.13,2.68),(.15,2.76)]:leaf((0,0,2.43),(x,0,z),.053,TAN,name='Small pale top leaf')

# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['22v','23r','23v','24r','24v','25r','25v','26r','26v','27r'][i];o.data.body='f'+['22v','23r','23v','24r','24v','25r','25v','26r','26v','27r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='05';scene['source_folia']='f22v f23r f23v f24r f24v f25r f25v f26r f26v f27r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'05','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia05_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
