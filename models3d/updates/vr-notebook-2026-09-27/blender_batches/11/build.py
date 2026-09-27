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
# f52v: branched circular lobed blades with open curled centres.
begin('s0104','52v',0);roots(spread=.3,n=8);stem((0,0,.3),(0,0,2.22),.021)
for k in range(8):
 s=(-1)**k;z=.79+k*.19;x=s*(.31+.09*(k%2));stem((0,0,z-.14),(x,0,z),.012)
 for j in range(6):
  a=j*math.tau/6;leaf((x,0,z),(x+.19*math.cos(a),.015*math.sin(j),z+.19*math.sin(a)),.055,G,serrate=.38,name='Toothed radial lobe')
# f53r: two low fans, many pale round pods, patterned lower stem.
begin('s0105','53r',1)
tube('Curled root',[(.23*math.cos(j*.2),0,.23+.12*math.sin(j*.2)) for j in range(31)],.03,TAN);stem((0,0,.3),(0,0,2.1),.02)
for k in range(8):bulb('Stem pigment band',(0,-.019,.4+k*.045),(.026,.016,.012),TAN if k%2 else G)
for s in [-1,1]:
 for j in range(9):leaf((0,0,.89),(s*(.36+.025*j),.03*math.sin(j),.67+j*.05),.037,G if j%3 else TAN,name='Lower broad comb fan')
 for k in range(5):
  x=s*(.12+k*.065);z=1.59+k*.17;stem((0,0,1.1),(x,0,z),.009);flower((x,0,z),.061,WHITE,7)
# f53v: crossed leaf pairs, one blue-russet rounded flower.
begin('s0106','53v',2);roots(spread=.37,n=11);tube('Brown root neck',[(0,0,.23),(0,0,.64)],.049,ROOT);stem((0,0,.61),(0,0,2.2),.018)
for k in range(5):
 z=.85+k*.24
 for s in [-1,1]:leaf((0,0,z),(s*.27,0,z+.22),.072,G,bend=-s*.03,name='Crossed blade')
flower((0,0,2.24),.14,BLUE,9);bulb('Russet flower heart',(0,-.04,2.24),(.059,.03,.059),RED)
# f54r: oval crown of fine arching shoots and two pale heads.
begin('s0107','54r',3);roots(spread=.35,n=12)
for j in range(7):
 x=(j-3)*.17;z=1.84+.35*(1-abs(j-3)/4);pts=curve((0,0,.38),(x,0,z),x*.48,.02,12);tube('Arching branch',pts,.012,G)
 for k in range(3,11):
  p=pts[k]
  for s in [-1,1]:leaf(p,(p.x+s*.11,p.y,p.z+.13),.024,G2,name='Fine oval blade')
for x,z in [(-.2,2.35),(.3,2.28)]:stem((0,0,1.55),(x,0,z),.009);flower((x,0,z),.09,WHITE,11)
# f54v: one leafy curved branch and an arch bearing dark buds, linked red root bulbs.
begin('s0108','54v',4)
for k in range(4):bulb('Red chain root',(0,0,.16+k*.12),(.11-.012*k,.07,.08),RED)
stem((0,0,.55),(-.26,0,2.27),.021,bend=-.13)
for k in range(9):
 z=.78+k*.16;x=-.18
 for s in [-1,1]:leaf((x,0,z),(x+s*.18,0,z+.17),.04,G,name='Pointed blade')
 bulb('Red leaf junction',(x,-.023,z),(.026,.02,.025),RED)
pts=curve((0,0,.58),(.34,0,2.28),.34,.02,16);tube('Arched flower branch',pts,.018,G)
for p in pts[5::2]:bulb('Dark arched bud',p,(.05,.045,.07),BLUE)
# f55r: four scalloped leaf shoots, red spear heads with blue caps.
begin('s0109','55r',5);bulb('Broad ochre root body',(0,0,.3),(.49,.13,.19),TAN)
for k,x in enumerate([-.47,-.15,.16,.48]):
 h=2.1+.24*math.sin(k);stem((x*.55,0,.4),(x,0,h),.016)
 for i in range(7):
  for s in [-1,1]:leaf((x,0,.7+i*.17),(x+s*.1,0,.78+i*.17),.038,G,serrate=.25,name='Scalloped small blade')
 leaf((x,0,h-.1),(x,0,h+.24),.07,RED,name='Red lanceolate flower');bulb('Blue flower cap',(x,0,h+.19),(.05,.04,.06),BLUE)
# f55v: very large split fan and central dotted umbrella, three swollen roots.
begin('s0110','55v',6)
for x in [-.28,0,.28]:tube('Swollen red root leg',[(x,0,.07),(x*.65,0,.25),(0,0,.55)],[.05,.095,.055],RED)
stem((0,0,.52),(0,0,2.22),.024)
for j in range(15):leaf((0,0,.78),((j-7)*.08,.025*math.sin(j),2.3-.07*abs(j-7)),.042,G,name='Large split fan blade')
tube('Red central flower stem',[(0,-.07,.8),(0,-.07,2.33)],.025,RED)
for j in range(13):
 x=(j-6)*.06;z=2.44-.11*abs(x);tube('Umbrella flower ray',[(0,-.07,2.25),(x,-.07,z)],.007,WHITE,5);bulb('Pale umbrella dot',(x,-.07,z),(.015,.018,.018),WHITE)
# f56r: two fine comb bursts and three swirling blue-pale flower heads.
begin('s0111','56r',7);roots(spread=.32,n=15)
for x in [-.33,.28]:
 for j in range(15):a=.3+j*math.pi/16;leaf((x,0,.7),(x+.34*math.cos(a),.015*math.sin(j),.7+.4*math.sin(a)),.012,G,name='Comb burst fine leaf')
 stem((0,0,.32),(x,0,.7),.02)
for x,z,r in [(-.36,1.82,.11),(.08,2.3,.13),(.6,1.85,.23)]:
 stem((0,0,.5),(x,0,z),.013,bend=x*.4)
 for j in range(8):a=j*math.tau/8;leaf((x,0,z),(x+r*math.cos(a),.035*math.sin(j),z+r*math.sin(a)),r*.2,BLUE if j%2 else WHITE,bend=.04,name='Swirling flower ray')
# f56v: tall pointed fan/fir form, pale side flower, red curled roots.
begin('s0112','56v',8)
for s in [-1,1]:tube('Red curled root',[(0,0,.35)]+[(s*(.19+.14*math.cos(j*.16)),0,.2+.11*math.sin(j*.16)) for j in range(30)],.025,RED)
stem((0,0,.35),(0,0,2.36),.02)
for k in range(12):
 z=.72+k*.115;r=.52*(1-k/16)
 for s in [-1,1]:leaf((0,0,z),(s*r,0,z+.43),.052,G,name='V-shaped pointed fan blade')
stem((0,0,1.92),(.41,0,2.4),.012);flower((.41,0,2.4),.12,WHITE,12)
# f57r: numerous divided fan leaves, a terminal indigo arrow bloom.
begin('s0113','57r',9);roots(spread=.35,n=12);stem((0,0,.33),(0,0,2.28),.019)
for k in range(7):
 s=(-1)**k;z=.7+k*.21;x=s*.34;stem((0,0,z-.15),(x,0,z),.009)
 for j in range(7):a=j*math.tau/7;leaf((x,0,z),(x+.19*math.cos(a),.018*math.sin(j),z+.2*math.sin(a)),.027,G,name='Seven-lobed divided fan')
leaf((0,0,2.2),(0,0,2.6),.12,BLUE,serrate=.38,name='Indigo arrow flower')
# Exhibition garden, not a reconstructed historical garden.
current=None;prefix='GARDEN | '
def box(name,p,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=prefix+name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
box('Ground',(0,2.1,-.14),(14,11,.22),G2);box('Central promenade',(0,2.1,-.015),(13,1.75,.06),PATH)
for i in range(10):
 x=(i%5-2)*2.45;y=(i//5)*4.2;box('Raised bed %02d'%i,(x,y,.04),(1.8,1.05,.15),STONE);box('Root display bed %02d'%i,(x,y,.12),(1.66,.91,.04),SOIL)
 bpy.ops.object.text_add(location=(x-.49,y-.565,.13),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='LABEL_f'+['52v','53r','53v','54r','54v','55r','55v','56r','56v','57r'][i];o.data.body='f'+['52v','53r','53v','54r','54v','55r','55v','56r','56v','57r'][i]+' / '+str(i+1).zfill(2);o.data.size=.16;o.data.extrude=.002;o.data.materials.append(BRASS);bpy.ops.object.convert(target='MESH')
for name,loc,power,color in [('Sun key',(-5,-6,9),1800,(1,.91,.75)),('Sky fill',(6,-2,6),1000,(.7,.83,1)),('Rim',(0,7,7),1700,(1,.88,.65))]:
 d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=4;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc
sun=bpy.data.lights.new('Day sun','SUN');sun.energy=1.7;so=bpy.data.objects.new('Day sun',sun);scene.collection.objects.link(so);so.rotation_euler=(.4,-.5,-.4)
d=bpy.data.cameras.new('Garden overview camera');cam=bpy.data.objects.new('Garden overview camera',d);scene.collection.objects.link(cam);cam.location=(10,-13,10);cam.rotation_euler=(Vector((0,2,1))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=17;scene.camera=cam
scene['batch']='11';scene['source_folia']='f52v f53r f53v f54r f54v f55r f55v f56r f56v f57r';scene['interpretation']='Full volumes manually interpreted from drawings; depth and back surfaces conjectural; no botanical identity claimed.'
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
result={'plants':10,'batch':'11','meshes':sum(o.type=='MESH' for o in bpy.data.objects),'polygons':sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH'),'status':'CANDIDATE_VOLUME_INTERPRETATION'}
scene.render.resolution_x=1200;scene.render.resolution_y=820;scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
target=artifacts.file(name='Partia11_ogrod.png',media_type='image/png');scene.render.filepath=target.path;bpy.ops.render.render(write_still=True);target.publish()
