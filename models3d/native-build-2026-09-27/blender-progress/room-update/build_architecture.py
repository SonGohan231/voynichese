import bpy, math, random
from mathutils import Vector
random.seed(88)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene; sc.unit_settings.system='METRIC'; sc.render.engine='BLENDER_EEVEE'; sc.render.resolution_x=1440;sc.render.resolution_y=960;sc.render.resolution_percentage=100
if not sc.world: sc.world=bpy.data.worlds.new('Ambient')
sc.world.color=(.16,.19,.25)
def mat(n,c,metal=0,rough=.65,emit=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 return m
stone=[mat('Wapien_%02d'%i,(.36+i*.018,.33+i*.017,.28+i*.015)) for i in range(6)]
wood=mat('Dab_ciemny',(.115,.054,.024),rough=.45);wood2=mat('Dab_krawedzie',(.22,.105,.044),rough=.43);gold=mat('Mosiadz_patynowany',(.42,.29,.105),.72,.35);iron=mat('Zelazo',(.038,.052,.054),.7,.4);velvet=mat('Aksamit_butelkowy',(.027,.12,.1),rough=.95);red=mat('Aksamit_bordo',(.15,.024,.034),rough=.95);wax=mat('Wosk',(.83,.66,.37),rough=.5);flame=mat('Swiatlo_swiecy',(1,.41,.065),emit=3);paper=mat('Papier',(.7,.57,.37),rough=.9);glass=mat('Szyba_bursztynowa',(.26,.4,.4),.18,.23);blue=mat('Skora_atlasu',(.044,.12,.18));green=mat('Skora_zielona',(.05,.16,.08))
def cube(n,p,s,m,b=.0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=n;o.dimensions=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if b:mod=o.modifiers.new('Krawedzie_stolarskie','BEVEL');mod.width=b;mod.segments=2
 return o
def cyl(n,p,r,h,m,v=24):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=h,location=p);o=bpy.context.object;o.name=n;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o
def sphere(n,p,s,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=p);o=bpy.context.object;o.name=n;o.scale=s;o.data.materials.append(m);return o
def rod(n,a,b,r,m):
 a=Vector(a);b=Vector(b);o=cyl(n,(a+b)/2,r,(b-a).length,m,12);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def arch(n,x,y,z,r,thick,depth):
 # Arch runs in XZ; open portal below springline.
 for i in range(16):
  a=i*math.pi/16;b=(i+1)*math.pi/16
  vs=[(x+R*math.cos(t),Y,z+R*math.sin(t)) for Y in [y-depth/2,y+depth/2] for R in [r,r+thick] for t in [a,b]]
  faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
  me=bpy.data.meshes.new(n);me.from_pydata(vs,[],faces);me.materials.append(stone[i%6]);o=bpy.data.objects.new(n+'_%02d'%i,me);sc.collection.objects.link(o)
def text(n,body,p,size,m,rot=(math.pi/2,0,0)):
 d=bpy.data.curves.new(n,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.extrude=.001;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;o.rotation_euler=rot;o.data.materials.append(m)
 return o
def candle(n,p):
 x,y,z=p;cyl(n+'_stopa',(x,y,z+.018),.09,.036,gold);cyl(n+'_trzon',(x,y,z+.15),.026,.25,gold);cyl(n+'_miseczka',(x,y,z+.285),.063,.024,gold);cyl(n+'_wosk',(x,y,z+.40),.035,.22,wax,16);sphere(n+'_plomien',(x,y,z+.535),(.018,.018,.05),flame)
 ld=bpy.data.lights.new(n+'_light','POINT');ld.energy=22;ld.color=(1,.68,.3);ld.shadow_soft_size=.14;lo=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(lo);lo.location=(x,y,z+.54)
def table(n,x,y,w=2.4,d=1.2,h=.88,cloth=False):
 cube(n+'_blat',(x,y,h-.045),(w,d,.09),wood2,.035)
 for xx in [-w/2+.14,w/2-.14]:
  for yy in [-d/2+.12,d/2-.12]:
   cube(n+'_noga',(x+xx,y+yy,(h-.1)/2),(.12,.12,h-.1),wood,.016);cyl(n+'_stopka',(x+xx,y+yy,.07),.10,.14,wood2)
 cube(n+'_fartuch',(x,y,h-.19),(w-.12,d-.12,.20),wood,.012)
 cube(n+'_rozpora',(x,y,.24),(w-.1,.09,.09),wood2,.012)
 if cloth:cube(n+'_aksamit',(x,y,h+.004),(w-.14,d-.12,.016),velvet,.015)
 return h
# One two-chamber building. Clear central work zones, real metre proportions.
for center,prefix in [(0,'ARCH'),(10,'PHARM')]:
 for ix in range(10):
  for iy in range(10):cube(prefix+'_plyta_%d_%d'%(ix,iy),(center-4.5+ix,-3.5+iy,-.065),(.986,.986,.12),random.choice(stone),.007)
 cube(prefix+'_sciana_tyl',(center,6.05,1.9),(10,.22,3.8),stone[2])
 cube(prefix+'_sciana_przod',(center,-4.05,1.9),(10,.22,3.8),stone[1])
 for y in [-3.8,-1.6,.6,2.8,5.6]:
  cube(prefix+'_belka_poprzeczna',(center,y,3.65),(10,.18,.24),wood,.01)
 for x in [center-4.85,center,center+4.85]:cube(prefix+'_belka_podluzna',(x,1,3.62),(.2,10,.26),wood,.01)
 for x in [center-4.85,center+4.85]:
  for y in [-3.85,5.85]:cube(prefix+'_filar',(x,y,1.8),(.27,.28,3.6),wood2,.02)
 for x in [center-4.8,center+4.8]:cube(prefix+'_listwa',(x,1,.18),(.18,10,.3),wood,.01)
 cube(prefix+'_listwa_tyl',(center,5.85,.18),(10,.16,.3),wood,.01)
 # Four arched leaded window panels on rear wall.
 for wx in [center-3.6,center+3.6]:
  cube(prefix+'_okno_swiatlo',(wx,5.91,2.05),(1.35,.04,1.62),glass)
  for xx in [-.69,.69]:cube(prefix+'_okno_bok',(wx+xx,5.78,1.83),(.17,.28,1.6),stone[5],.018)
  arch(prefix+'_luk_okna',wx,5.78,2.61,.70,.18,.28)
  cube(prefix+'_parapet',(wx,5.66,1.04),(1.8,.55,.16),stone[4],.02)
  for xx in [-.45,0,.45]:rod(prefix+'_olow',(wx+xx,5.73,1.2),(wx+xx,5.73,2.85),.014,iron)
  for zz in [1.4,1.9,2.4,2.8]:rod(prefix+'_olow',(wx-.62,5.73,zz),(wx+.62,5.73,zz),.014,iron)
# Outer sides, interior doorway. Partition gap y=-.4..2.4, rotated arch.
cube('ARCH_sciana_boczna',(-5.05,1,1.9),(.22,10,3.8),stone[2]);cube('PHARM_sciana_boczna',(15.05,1,1.9),(.22,10,3.8),stone[2])
cube('Portal_sciana_A',(5,-2.25,1.9),(.24,3.5,3.8),stone[3]);cube('Portal_sciana_B',(5,4.4,1.9),(.24,3.2,3.8),stone[3]);cube('Portal_nadproze',(5,1.15,3.58),(.28,3.0,.45),stone[2])
old=set(bpy.data.objects);arch('Portal_luk',0,0,2.05,1.4,.26,.36)
for o in set(bpy.data.objects)-old:
 o.rotation_euler.z=math.pi/2;o.location=(5,1.15,0)
for y in [-.32,2.62]:cube('Portal_wegar',(5,y,1.02),(.42,.25,2.04),stone[5],.025)
# Main manuscript table, neighboring tarot table (independent seating spaces).
table('ARCH_Stol_manuskryptu',0,1.95,2.5,1.25,.88)
table('TAROT_Stol',3.0,1.70,2.45,1.38,.88,True)
for x in [-.99,.99]:candle('ARCH_Swieca',(x,2.37,.88))
for x in [2.0,4.0]:candle('TAROT_Swieca',(x,2.2,.89))
# Open book cradle, manuscript itself is loaded from actual scans by runtime.
for x in [-.27,.27]:
 o=cube('ARCH_Pulpit',(x,2.1,1.01),(.56,.74,.065),wood2,.012);o.rotation_euler.y=-.18 if x<0 else .18
# Rug as individual border and centre, no expensive transparent textures.
cube('ARCH_Dywan',(0,-.5,.005),(3.4,2.35,.018),red,.012)
for x in [-1.62,1.62]:cube('ARCH_Dywan_obwod',(x,-.5,.018),(.10,2.28,.006),gold)
for y in [-1.60,.60]:cube('ARCH_Dywan_obwod',(0,y,.018),(3.24,.10,.006),gold)
# Bookcases, drawer cupboards, varied bound books.
for cx in [-2,1.1]:
 for x in [cx-.88,cx+.88]:cube('ARCH_Regal_bok',(x,5.5,1.5),(.10,.62,2.75),wood,.012)
 for z in [.2,.88,1.56,2.24,2.9]:cube('ARCH_Regal_polka',(cx,5.5,z),(1.85,.65,.09),wood2,.012)
 for row in range(4):
  for k in range(13):
   w=random.uniform(.075,.12);h=random.uniform(.36,.56);x=cx-.77+k*.122;z=.26+row*.68+h/2
   m=random.choice([red,green,blue,wood2]);cube('ARCH_Ksiega',(x,5.40,z),(w,.4,h),m,.007)
   for zz in [z-h*.33,z+h*.33]:cube('ARCH_Ksiega_tloczenie',(x,5.19,zz),(w*.9,.012,.012),gold)
# Pharmacy display plinths along walls and island bench; no generic vessels falsely labelled as manuscript.
for i in range(5):
 x=6.15+i*1.75
 cube('PHARM_Gablota_podstawa',(x,4.48,.46),(1.32,.98,.92),wood,.025);cube('PHARM_Gablota_blat',(x,4.48,.95),(1.44,1.1,.08),wood2,.02)
 cube('PHARM_Gablota_mosiadz',(x,3.974,.6),(1.05,.016,.06),gold,.006)
 for row in range(2):cube('PHARM_Szuflada',(x,3.967,.27+row*.31),(1.12,.035,.23),wood2,.012);cyl('PHARM_Uchwyt',(x,3.935,.27+row*.31),.04,.04,gold,12).rotation_euler.x=math.pi/2
for x in [6.3,8.15,10,11.85,13.7]:
 cube('PHARM_Stol_ekspozycji',(x,-2.4,.46),(1.42,1.25,.92),wood,.018);cube('PHARM_Stol_ekspozycji_blat',(x,-2.4,.95),(1.50,1.33,.07),wood2,.012)
table('PHARM_Stol_badawczy',10,1.2,3.1,1.4,.90,True)
for x in [8.65,11.35]:candle('PHARM_Swieca',(x,1.7,.91))
# Framed manuscript display areas left empty for real scan textures installed locally.
for x in [7.4,10,12.6]:
 cube('PHARM_Rama',(x,5.8,2.25),(2.22,.12,2.24),wood2,.022);cube('PHARM_Tablica',(x,5.70,2.25),(2.04,.035,2.06),paper)
# Observation brass armillary ornament, period-inspired setting only.
for radius,angle in [(.30,0),(.34,.75),(.37,1.5)]:
 bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=8,major_radius=radius,minor_radius=.012,location=(-3.65,2.7,1.36));o=bpy.context.object;o.name='ARCH_Sfera_armilarna';o.rotation_euler=(math.pi/2,angle,0);o.data.materials.append(gold)
table('ARCH_Konsola',-3.65,2.7,1.3,.85,.85);cyl('ARCH_Sfera_podstawa',(-3.65,2.7,.89),.2,.08,gold);rod('ARCH_Sfera_os',(-3.65,2.7,.92),(-3.65,2.7,1.75),.023,gold)
# Bench stools at safe edges, working area kept uncluttered.
for x,y in [(-1.7,1.9),(3,3.25),(10,2.7)]:
 cyl('Taboret_siedzisko',(x,y,.49),.3,.10,wood2)
 for a in [0,2.094,4.189]:rod('Taboret_noga',(x+.24*math.cos(a),y+.24*math.sin(a),.04),(x+.2*math.cos(a),y+.2*math.sin(a),.45),.037,wood)
text('ARCH_Szyld','SCRIPTORIUM',(0,5.74,3.23),.25,gold)
text('PHARM_Szyld','HERBARIUM',(10,5.74,3.47),.22,gold)
# Delivery camera and physically motivated illumination.
def light(n,kind,p,power,color,size=1):
 d=bpy.data.lights.new(n,kind);d.energy=power;d.color=color
 if kind=='POINT':d.shadow_soft_size=size
 o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=p;return o
light('Dzienne_arch','POINT',(0,3,3.2),1150,(.78,.86,1),2)
light('Dzienne_pharm','POINT',(10,2.5,3.15),1250,(.78,.87,1),2)
light('Wypelnienie','POINT',(3,-2.8,3.1),950,(1,.79,.55),2)
bpy.ops.object.camera_add(location=(.7,-3.55,2.1));cam=bpy.context.object;cam.name='Camera_delivery';cam.rotation_euler=(Vector((2.5,3.1,1.3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=23;sc.camera=cam
sc['intent']='Contemporary research setting inspired by historical materials; not a reconstruction of a documented Voynich room.'
sc['units']='metres';sc['tarot_anchor_blender']=[3,1.7,.9];sc['pharmacy_origin_blender']=[10,0,0]
result={'objects':len(bpy.data.objects),'rooms':2,'tarot_table_m':[2.45,1.38,.88],'geometry':'Blender mesh, editable materials and bevel modifiers','source_reference':'manuscript models added locally from real scans'}
