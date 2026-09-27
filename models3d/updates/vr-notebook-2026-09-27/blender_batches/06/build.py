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
# f27v: two broad branches with paired lance leaves and a fine upper flower spray.
begin('s0054','27v',0);roots(spread=.35,n=8,color=TAN)
for side in [-1,1]:
 stem((0,0,.25),(side*.52,0,2.0),.015,side*.04)
 for k in range(6):
  p=(side*(.08+k*.07),0,.68+k*.2)
  for ss in [-1,1]:leaf(p,(p[0]+ss*.18,.03,p[2]+.18),.057,G2)
for x in [-.25,0,.28]:stem((0,0,1.3),(x,0,2.46),.006);flower((x,0,2.46),.04,RED,5)
# f28r: one large split and lobed leaf on a slender stalk, small upper pale flower, red curled root.
begin('s0055','28r',1);roots(spread=.31,n=4,color=RED);stem((0,0,.26),(0,0,2.35),.014)
for side in [-1,1]:
 leaf((0,0,1.13),(side*.25,0,2.07),.18,G2,serrate=.22,name='Split leaf half')
 for k in range(4):leaf((side*.17,0,1.34+k*.14),(side*.43,0,1.46+k*.14),.073,G2,bend=side*.03,name='Side leaf lobe')
flower((0,0,2.43),.07,WHITE,6)
# f28v: circle of small inward curling leaves on a tall branching stalk, basal small star.
begin('s0056','28v',2);roots(spread=.40,n=10,color=TAN);stem((0,0,.27),(0,0,1.75),.019);star((0,0,.88),.27,5,.054)
for j in range(15):a=j*math.tau/15;c=(.51*math.cos(a),0,1.83+.48*math.sin(a));stem((0,0,1.3),c,.004);leaf(c,(c[0]-.12*math.sin(a),.035,c[2]+.16*math.cos(a)),.033,G2,bend=.04,name='Circular curled leaflet')
# f29r: central root strands, four heavy blue-green folded leaves and a delicate upper red-dot stem.
begin('s0057','29r',3);roots(spread=.30,n=17,color=TAN);stem((0,0,.3),(0,0,2.51),.013)
for side in [-1,1]:
 for k in range(2):leaf((0,0,1.04+k*.34),(side*.48,0,1.18+k*.30),.20,G2,bend=side*.05,depth=.13,name='Folded broad leaf');leaf((0,-.025,1.1+k*.34),(side*.39,-.035,1.20+k*.30),.115,BLUE,depth=.08,name='Dark leaf fold')
for k in range(6):bulb('Red small terminal bead',((-.04 if k%2 else .04),0,2.05+k*.09),(.019,.016,.023),RED)
# f29v: two basal deeply cut drooping fronds and sparse upper finger leaves with indigo curl.
begin('s0058','29v',4);roots(spread=.44,n=6,color=TAN);stem((0,0,.25),(0,0,2.57),.016)
for side in [-1,1]:
 for k in range(9):x=side*(.06+k*.055);z=1.08+.3*math.sin(k/9*math.pi);leaf((0,0,1.05),(x,0,z),.019,G2);leaf((x,0,z),(x+side*.03,.02,z-.27),.026,G2,name='Drooping divided frond')
 for k in range(3):c=(side*.2,0,1.62+k*.23);stem((0,0,c[2]-.10),c,.007);star(c,.13,3,.034)
flower((0,0,2.58),.08,BLUE,5)
# f30r: three long upright leaf clusters, diagonal blue dotted terminal spike.
begin('s0059','30r',5);roots(spread=.19,n=8)
for x,z in [(-.27,1.49),(.28,1.49),(.3,.75)]:
 stem((0,0,.26),(x,0,z),.012)
 for j in [-1,0,1]:leaf((x,0,z),(x+j*.2,.02,z+.52-abs(j)*.12),.058,G2,name='Upright triplet blade')
stem((0,0,.3),(.27,0,2.43),.009)
for k in range(8):bulb('Diagonal dark seed',(.04+k*.04,0,2.02+k*.07),(.026,.021,.022),BLUE)
# f30v: three paired ochre serrated leaves, beaded oval inflorescence, toothed horizontal root.
begin('s0060','30v',6);tube('Ochre horizontal root',[(-.64,0,.06),(0,0,.09),(.7,0,.08)],[.04,.052,.035],TAN)
for k in range(11):tube('Root tooth',[(k*.12-.6,0,.08),(k*.12-.6,0,.17)],[.018,.003],TAN,5)
stem((0,0,.13),(0,0,2.3),.014)
for k in range(3):
 for side in [-1,1]:leaf((0,0,.82+k*.3),(side*.40,0,1.01+k*.3),.12,TAN,serrate=.22,name='Ochre serrated blade')
for j in range(20):a=j*math.tau/20;bulb('Pale oval seed chain',(.22*math.cos(a),0,2.12+.36*math.sin(a)),(.024,.023,.032),WHITE)
# f31r: broad hanging left leaves, right scrolling flower stems and thick red serpentine root.
begin('s0061','31r',7);tube('Serpentine red root',[(-.56,0,.25),(-.36,0,.49),(0,0,.34),(.46,0,.45),(.38,0,.25)],[.07,.055,.05,.044,.032],RED)
for side in [-1,1]:roots((side*.43,0,.24),.24,7,color=RED)
stem((0,0,.37),(0,0,2.58),.016)
for k in range(3):leaf((0,0,.92+k*.37),(-.45,.04,.91+k*.37),.16,G2,bend=-.05,depth=.085,name='Hanging broad blade')
for k in range(4):
 z=1.2+k*.30;tube('Scrolling side stem',[(0,0,z),(.30,0,z+.07),(.37,0,z+.18),(.29,0,z+.23)],.008,G2);flower((.29,0,z+.23),.041,WHITE,5)
flower((0,0,2.57),.13,WHITE,7)
# f31v: one wide right-facing row of green diamond blades over ochre lobes, fine pale upper flower.
begin('s0062','31v',8);roots(spread=.35,n=12,color=TAN);stem((0,0,.25),(0,0,2.36),.014)
for j in range(9):x=.12+j*.078;leaf((x,0,1.26),(x,0,1.83),.07,G2,name='Upright diamond blade');leaf((x,0,1.36),(x,0,1.1),.053,TAN,name='Ochre lower lobe')
stem((0,0,1.28),(.75,0,1.48),.016)
for x,z in [(-.16,1.26),(-.18,1.58)]:leaf((0,0,z),(x,0,z+.15),.04,G2)
flower((0,0,2.37),.17,WHITE,16)
# f32r: zigzag alternating oval leaves and several small dotted lateral flower clusters.
begin('s0063','32r',9);roots(spread=.26,n=5,color=TAN);stem((0,0,.28),(.06,0,2.51),.016,.06)
for k in range(9):
 side=(-1)**k;z=.76+k*.20;leaf((.025,0,z),(side*.35,.025,z+.10),.095,G2,name='Alternate broad blade')
 if k%2==0:
  for j in range(7):a=j*math.tau/7;bulb('Dotted flower cluster',(side*.39+.04*math.cos(a),0,z+.22+.04*math.sin(a)),(.016,.016,.017),BLUE)

# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['27v','28r','28v','29r','29v','30r','30v','31r','31v','32r'][i];o.data.body='f'+['27v','28r','28v','29r','29v','30r','30v','31r','31v','32r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='06';scene['source_folia']='f27v f28r f28v f29r f29v f30r f30v f31r f31v f32r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'06','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia06_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
