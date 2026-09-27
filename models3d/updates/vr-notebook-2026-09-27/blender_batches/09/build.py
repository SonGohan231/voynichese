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
# f42v: elevated broad divided crown on one long stalk.
begin('s0084','42v',0);roots(spread=.31,n=6);stem((0,0,.3),(0,0,1.83),.02)
for j in range(7):
 a=(j-3)*.34;leaf((0,0,1.78),(.64*math.sin(a),.04*math.cos(j),1.83+.7*math.cos(a)),.15,G,serrate=.15,name='Crown palmate lobe')
# f43r: many short sprigs, broad red filament-root bed.
begin('s0085','43r',1)
tube('Horizontal rhizome',[(-.73,0,.57),(0,0,.58),(.73,0,.57)],.04,RED)
for k in range(13):
 x=(k-6)*.115;stem((x,0,.56),(x+.025,0,1.44+.15*math.sin(k)),.009)
 for z in [.79,.98,1.15]:
  for s in [-1,1]:leaf((x,0,z),(x+s*.095,.02*s,z+.17),.034,G,name='Small paired sprig leaf')
 for j in range(3):tube('Fine red root',curve((x,0,.56),(x+.06*math.sin(j+k),.025*j,.045),.035*math.cos(k),.02,8),.008,RED,5)
# f43v: separate left and right figures, two root types.
begin('s0086','43v',2)
for x in [-.42,.42]:
 stem((x,0,.54),(x,0,2.1),.014)
 for k in range(8):
  z=.86+k*.15
  for s in [-1,1]:
   for j in range(3 if x<0 else 1):leaf((x,0,z),(x+s*(.17+.035*j),.025*s,z+.12+.035*j),.018 if x<0 else .047,G,bend=-s*.06,name='Divided leaflet' if x<0 else 'Curled crescent blade')
 if x<0:
  for z in [.29,.49]:bulb('Stacked ochre root bulb',(x,0,z),(.11,.09,.13),TAN)
 else:roots(base=(x,0,.57),spread=.28,n=13,color=WHITE)
# f44r: long red stalk, tall striped chalice fan.
begin('s0087','44r',3);roots(spread=.32,n=6,color=RED);tube('Red long stem',[(0,0,.28),(0,0,1.45)],.022,RED)
for j in range(13):
 a=(j-6)*.13;leaf((0,0,1.35),(.56*math.sin(a),.05*math.sin(j),2.42-.2*abs(a)),.047,G if j%3 else BLUE,name='Striped fan blade')
stem((0,0,2.3),(0,0,2.65),.009);bulb('Small crown bud',(0,0,2.63),(.04,.035,.06),G)
# f44v: Y root body and three curled fans.
begin('s0088','44v',4)
for s in [-1,1]:tube('Forked ochre root',[(s*.39,0,.08),(s*.22,0,.23),(0,0,.63)],[.05,.08,.07],TAN)
stem((0,0,.6),(0,0,1.47),.035)
for x,z in [(-.4,1.5),(.42,1.7),(0,2.05)]:
 stem((0,0,1.12),(x,0,z),.021)
 for j in range(9):
  a=j*math.tau/9;leaf((x,0,z),(x+.33*math.cos(a),.04*math.sin(j),z+.32*math.sin(a)),.088,G,bend=.09*math.sin(a),serrate=.28,name='Curled fan lobe')
# f45r: branched triangular foliage and ring-shaped heads.
begin('s0089','45r',5);tube('Broad horizontal root',[(-.65,0,.18),(0,0,.33),(.56,0,.17)],.06,RED)
for k,x in enumerate([-.52,-.27,0,.28,.53]):
 z=1.9+.25*math.sin(k);stem((x*.6,0,.27),(x,0,z),.013)
 for i in range(4):
  h=.68+i*.24
  for s in [-1,1]:leaf((x*.9,0,h),(x*.9+s*.17,0,h+.18),.085,G,serrate=.4,name='Triangular toothed blade')
 pts=[(x+.09*math.cos(a),0,z+.13*math.sin(a)) for a in [j*math.tau/28 for j in range(29)]];tube('Open oval flower head',pts,.027,WHITE)
# f45v: serpentine root, three narrow-leaved shoots with indigo heads.
begin('s0090','45v',6);tube('Serpentine ochre rhizome',[(-.73,0,.08),(-.4,0,.14),(0,0,.1),(.33,0,.25),(.69,0,.12)],.047,TAN)
for x,z in [(-.45,2.16),(0,2.39),(.46,2.12)]:
 stem((x,0,.17),(x,0,z),.016)
 for k in range(7):
  for s in [-1,1]:leaf((x,0,.58+k*.18),(x+s*.13,0,.74+k*.18),.04,G,name='Narrow shoot blade')
 bulb('Indigo terminal cap',(x,0,z),(.085,.055,.07),BLUE)
# f46r: three wavy fronds on pale horizontal rhizome.
begin('s0091','46r',7);tube('Pale root body',[(-.66,0,.3),(0,0,.33),(.64,0,.3)],.045,WHITE)
for x in [-.45,0,.45]:
 roots(base=(x,0,.3),spread=.18,n=6,color=TAN);stem((x,0,.31),(x,0,2.13),.014)
 for k in range(10):
  for s in [-1,1]:leaf((x,0,.77+k*.11),(x+s*.12,0,.86+k*.11),.034,G,bend=s*.025,name='Wavy pinnate segment')
 bulb('Pale terminal head',(x,0,2.18),(.10,.055,.08),WHITE)
# f46v: broad leaf pairs and eight pale rounded flower heads.
begin('s0092','46v',8);roots(spread=.55,n=16);stem((0,0,.3),(0,0,1.8),.025)
for k in range(3):
 for s in [-1,1]:leaf((0,0,.72+k*.32),(s*.57,0,1.04+k*.32),.19,G,serrate=.24,name='Broad oval toothed leaf')
for j in range(8):
 x=(j-3.5)*.15;z=2.19+.28*math.sin(j*.5);stem((0,0,1.6),(x,0,z),.009);flower((x,0,z),.09,WHITE,10)
# f47r: low rounded lobed rosette and one high palmate blade.
begin('s0093','47r',9);roots(spread=.23,n=6,color=RED);stem((0,0,.28),(.18,0,1.99),.017,bend=-.13)
for x,z,r in [(-.12,.92,.57),(.18,2.08,.4)]:
 for j in range(9):
  a=j*math.tau/9;leaf((x,0,z),(x+r*math.cos(a),.03*math.sin(j),z+r*math.sin(a)),r*.24,G,serrate=.1,name='Rounded divided blade')
# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['42v','43r','43v','44r','44v','45r','45v','46r','46v','47r'][i];o.data.body='f'+['42v','43r','43v','44r','44v','45r','45v','46r','46v','47r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='09';scene['source_folia']='f42v f43r f43v f44r f44v f45r f45v f46r f46v f47r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'09','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia09_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
