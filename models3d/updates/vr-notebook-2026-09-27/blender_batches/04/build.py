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
# f17v: paired broad leaves, curved pale root and bowed terminal spray of russet grains.
begin('s0034','17v',0);tube('Curved pale root',[(0,0,.5),(0,0,.25),(-.12,0,.07),(-.48,0,.06)], [.1,.07,.045,.02],TAN);stem((0,0,.48),(0,0,2.06),.014)
for k in range(6):
 for side in [-1,1]:leaf((0,0,.84+k*.18),(side*.35,.025*side,.89+k*.18),.079,G2)
tube('Bowed grain stem',[(0,0,1.99),(-.22,0,2.4),(-.65,0,2.58),(-.94,0,2.38)],.01,TAN)
for i in range(8):x=-.06-i*.11;z=2.31+.25*math.sin(i*math.pi/8);leaf((x,0,z),(x-.055,.02,z+.15),.025,RED,name='Russet grain')
# f18r: broad lower pairs, branching narrower upper leaves, fan of dark flowers.
begin('s0035','18r',1);roots(spread=.27,n=10);stem((0,0,.3),(0,0,2.42),.02)
for k in range(7):
 for side in [-1,1]:leaf((0,0,.68+k*.22),(side*(.45-k*.039),.02*side,1.02+k*.20),.10-k*.01,G2)
for j in range(9):x=(j-4)*.054;z=2.36+.15*(1-abs(j-4)/4);stem((0,0,2.05),(x,0,z),.006);leaf((x,0,z),(x+.02,.03,z+.17),.03,BLUE,name='Indigo terminal flower')
# f18v: long ribbed horizontal rhizome and a sparse branched cluster of lobed leaves.
begin('s0036','18v',2);tube('Long pale rhizome',[(-.6,0,.08),(-.2,0,.08),(.3,0,.09),(.74,0,.11)],[.065,.09,.075,.04],TAN)
for i in range(16):tube('Root joint',[(i*.08-.6,0,.04),(i*.08-.59,-.02,.17)],.006,ROOT,5)
stem((-.15,0,.1),(-.12,0,1.91),.018)
for k,(x,z) in enumerate([(-.51,.9),(.34,.92),(-.4,1.32),(.43,1.42),(-.3,1.7),(.13,1.81)]):stem((-.12,0,.4+k*.19),(x,0,z),.01);star((x,0,z),.16,6,.055)
flower((-.12,0,2.18),.14,WHITE,9)
# f19r: two large hanging divided fronds and blue chalice above small upright leaf shoots.
begin('s0037','19r',3);roots(spread=.4,n=8,color=TAN);bulb('Pale crown',(0,0,.36),(.2,.09,.11),TAN);stem((0,0,.39),(0,0,2.23),.017)
for side in [-1,1]:
 stem((0,0,.89),(side*.56,0,1.6),.014)
 for k in range(8):x=side*(.13+k*.06);z=1.35+.19*math.sin(k/8*math.pi);leaf((x,0,z),(x+side*.035,.02,z-.3),.055,G2,name='Drooping fern blade')
 for k in range(3):leaf((0,0,1.55+k*.15),(side*.2,.02,1.79+k*.15),.04,G2)
for j in range(5):a=j*math.tau/5;leaf((0,0,2.1),(.23*math.cos(a),.12*math.sin(a),2.39),.10,BLUE,name='Blue chalice petal')
# f19v: two stacked dense pointed brush whorls and red branching root.
begin('s0038','19v',4);roots(spread=.51,n=5,color=RED);bulb('Red root crown',(0,0,.23),(.115,.07,.21),RED);stem((0,0,.43),(0,0,2.38),.018)
for z in [1.26,2.08]:
 for j in range(19):x=(j-9)*.04;leaf((0,0,z-.27),(x,.035*math.sin(j),z+.25-.10*abs(j-9)/9),.023,G2,name='Dense brush leaf')
# f20r: low fine compound foliage and three upright dotted seed spikes.
begin('s0039','20r',5);roots(spread=.22,n=10);stem((0,0,.22),(0,0,1.42),.012)
for j in range(9):x=(j-4)*.11;z=.82+.42*(1-abs(j-4)/4);comb((0,0,.3),(x,0,z),10,.064)
for x,z in [(-.27,1.64),(0,1.93),(.25,1.75)]:
 stem((0,0,.5),(x,0,z),.007)
 for k in range(5):bulb('Small rust seed',(x,0,z-k*.12),(.022,.016,.028),RED)
# f20v: slender three-branched plant, short groups of narrow blades and small dark heads.
begin('s0040','20v',6);roots(spread=.2,n=7)
for x,z in [(-.34,2.10),(.08,2.45),(.40,2.05)]:
 stem((0,0,.28),(x,0,z),.009)
 for k in range(3):
  zz=.92+k*.12
  for side in [-1,1]:leaf((x*.7,0,zz),(x*.7+side*.31,.015,zz+.025),.012,G2)
 flower((x,0,z),.044,BLUE,5)
for x,z in [(-.15,2.36),(.3,2.40),(-.42,1.62),(.3,1.62)]:flower((x,0,z),.028,BLUE,4)
# f21r: broad rosette of fine radiating divided branches, no separate showy flowers.
begin('s0041','21r',7);roots(spread=.3,n=8);stem((0,0,.25),(0,0,1.1),.012)
for j in range(15):
 a=j*math.tau/15;end=(.63*math.cos(a),.045*math.sin(j),1.34+.64*math.sin(a));comb((0,0,1.32),end,12,.06)
# f21v: three paired divided fronds and five thin indigo flower sprays.
begin('s0042','21v',8);bulb('Small ochre root',(0,0,.15),(.12,.07,.09),TAN);stem((0,0,.23),(0,0,2.26),.014)
for side in [-1,1]:
 for k in range(3):
  z=.74+k*.31;stem((0,0,z),(side*.60,0,z+.14),.009)
  for j in range(7):x=side*(.13+j*.067);leaf((x,0,z+.08),(x+side*.08,.02,z+.25),.03,G2,name='Crescent comb leaflet')
for x,z in [(-.33,1.95),(.31,1.95),(-.20,2.29),(.25,2.35),(0,2.55)]:stem((0,0,1.47),(x,0,z),.007);flower((x,0,z),.051,BLUE,5)
# f22r: lower curling broad blades, fan-shaped upper seed stalks with three blue flower caps.
begin('s0043','22r',9);roots(spread=.42,n=10,color=RED);stem((0,0,.32),(0,0,2.15),.014)
for x,z in [(-.37,1.0),(.31,.9),(-.22,1.42),(.28,1.38)]:
 stem((0,0,z-.1),(x,0,z),.012)
 for side in [-1,1]:leaf((x,0,z),(x+side*.08,.04,z+.22),.08,G2,bend=side*.08,name='Curled broad blade')
for j in range(17):x=(j-8)*.055;z=2.17+.19*(1-abs(j-8)/8);tube('Russet seed stalk',curve((0,0,1.89),(x,0,z)),.007,TAN);leaf((x,0,z),(x+.01,0,z+.17),.019,RED,name='Russet spike')
for x,z in [(-.24,2.58),(0,2.8),(.24,2.62)]:stem((0,0,2.1),(x,0,z),.005);flower((x,0,z),.065,BLUE,7)

# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['17v','18r','18v','19r','19v','20r','20v','21r','21v','22r'][i];o.data.body='f'+['17v','18r','18v','19r','19v','20r','20v','21r','21v','22r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='04';scene['source_folia']='f17v f18r f18v f19r f19v f20r f20v f21r f21v f22r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'04','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia04_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
