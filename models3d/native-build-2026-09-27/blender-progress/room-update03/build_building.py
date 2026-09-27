import bpy,math,json,random,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;ROOT=R.parent;OUT=R/'building';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room-update/architecture/Archive_editable_4_5.blend'))
for ob in list(bpy.data.objects):
 if any(k in ob.name for k in ['sciana','Portal_','okno','luk_okna','parapet','olow','listwa']) or ob.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(ob,do_unlink=True)
sc=bpy.context.scene;sc.unit_settings.system='METRIC'
def mat(name,c,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.8;p.inputs['Metallic'].default_value=metal;return m
stone=mat('Budynek_wapien',(.46,.42,.34));floor=mat('Posadzka_jasna',(.35,.32,.28));ceiling=mat('Sklepienie',(.63,.58,.46));wood=mat('Dab_nowy',(.19,.09,.035));gold=mat('Mosiadz_nowy',(.49,.33,.10),.6);soil=mat('Ziemia',(.13,.09,.047));grass=mat('Trawa',(.105,.21,.075));hedge=mat('Zywoplot',(.055,.125,.058));sky=mat('Dach_obserwatorium',(.06,.105,.16));water=mat('Woda_rekwizyt',(.12,.35,.37))
def box(name,pos,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o
def cyl(name,pos,r,h,m,segments=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=h,location=pos);o=bpy.context.object;o.name=name;o.data.materials.append(m);return o
def rod(name,a,b,r,m):
 a=Vector(a);b=Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,m,12);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def text(name,body,pos,rot=(math.pi/2,0,0),size=.24):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER';o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=rot;o.data.materials.append(gold)
ROOMS=[('Pracownia',-5,5,-4,6,4.2),('Naczynia',5,15,-4,6,4.2),('Hydraulika',15,27,-4,6,4.2),('Korytarz',-5,27,-8,-4,4.2),('Diagramy',-5,15,-28,-8,5.5),('Obserwatorium',15,27,-28,-8,5.5)]
# Openings declared once in world coordinates. Thick complete walls get actual Boolean cuts.
DOORS=[('wejscie_ogrod','X',-5,1,2.8,3.0),('pracownia_naczynia','X',5,1.15,2.8,3.0),('naczynia_hydraulika','X',15,1.15,2.8,3.0),('pracownia_korytarz','Y',-4,0,3,3.0),('naczynia_korytarz','Y',-4,10,3,3.0),('hydraulika_korytarz','Y',-4,21,3,3.0),('ogrod_korytarz','X',-5,-6,3,3.0),('diagramy_korytarz','Y',-8,5,3,3.4),('obserwatorium_korytarz','Y',-8,21,3,3.4),('diagramy_obserwatorium','X',15,-12,3,3.4),('diagramy_ogrod','X',-5,-12,3,3.4)]
openings=[];surfaces=[]
for name,x0,x1,y0,y1,h in ROOMS:
 box(name+'_podloga',((x0+x1)/2,(y0+y1)/2,-.16),(x1-x0,y1-y0,.3),floor)
 box(name+'_sufit',((x0+x1)/2,(y0+y1)/2,h+.13),(x1-x0+.3,y1-y0+.3,.26),ceiling if name!='Obserwatorium' else sky)
 for axis,value,a,b in [('X',x0,y0,y1),('X',x1,y0,y1),('Y',y0,x0,x1),('Y',y1,x0,x1)]:
  pos=(value,(a+b)/2,h/2) if axis=='X' else ((a+b)/2,value,h/2);sz=(.28,b-a,h) if axis=='X' else (b-a,.28,h)
  wall=box(name+'_sciana_'+axis+str(value),pos,sz,stone);surfaces.append({'id':wall.name,'axis':axis,'bounds':list(pos)+list(sz)})
  for did,da,dv,dc,dw,dh in DOORS:
   if axis!=da or abs(value-dv)>.01 or dc-dw/2<a-.01 or dc+dw/2>b+.01:continue
   cp=(dv,dc,dh/2-.02) if da=='X' else (dc,dv,dh/2-.02);cs=(.8,dw,dh+.06) if da=='X' else (dw,.8,dh+.06)
   cutter=box('CUT_'+did,cp,cs,stone);mod=wall.modifiers.new('Otwor_'+did,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.context.view_layer.objects.active=wall;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
   openings.append({'id':did+'_'+name,'type':'door','wall':wall.name,'widthMeters':dw,'heightMeters':dh,'depthMeters':.28,'thresholdMeters':0,'destination':did,'booleanApplied':True})
  # Real glazed openings on exposed northern wall; no planes masquerading as holes.
  if axis=='Y' and value==6:
   for wx in [a+1.6,b-1.6]:
    cutter=box('CUT_okno',(wx,6,2.4),(1.2,.8,1.4),stone);mod=wall.modifiers.new('Otwor_okienny','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.context.view_layer.objects.active=wall;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    box(name+'_rama_dol',(wx,6,1.7),(1.5,.5,.1),wood);box(name+'_rama_gora',(wx,6,3.1),(1.5,.4,.1),wood)
    for xx in [wx-.65,wx,wx+.65]:box(name+'_rama_pion',(xx,6,2.4),(.055,.15,1.4),wood)
 for x in [x0+.35,x1-.35]:
  for y in [y0+.35,y1-.35]:box(name+'_pilaster',(x,y,h/2),(.22,.22,h),wood)
 for yy in range(math.ceil(y0+1),int(y1),3):box(name+'_belka',((x0+x1)/2,yy,h-.12),(x1-x0,.17,.24),wood)
 # Only actual entrances receive labels; signs face incoming corridor.
 if name not in ['Korytarz']:
  text(name+'_szyld',name.upper(),((x0+x1)/2,y0-.16,3.65))
# Garden with continuous paths and selectable manuscript plants loaded at runtime, not generic botanical substitutes.
box('Ogrod_teren',(-12,-11,-.14),(14,34,.26),grass)
for x in [-18.8,-5.2]:box('Ogrod_zywoplot',(x,-11,.44),(.22,34,.86),hedge)
for y in [-27.8,5.8]:box('Ogrod_zywoplot',(-12,y,.44),(14,.22,.86),hedge)
# Clear actual garden entry gaps in the right hedge.
for ob in list(bpy.data.objects):
 if ob.name.startswith('Ogrod_zywoplot') and ob.location.x>-6:
  bpy.data.objects.remove(ob,do_unlink=True)
for a,b in [(-27.8,-13.7),(-10.3,-7.7),(-4.3,-.6),(2.6,5.8)]:box('Ogrod_zywoplot_wejscia',(-5.2,(a+b)/2,.44),(.22,b-a,.86),hedge)
box('Ogrod_sciezka_glowna',(-11,-11,-.005),(2.8,33,.028),floor)
for y in [1,-6,-12]:box('Ogrod_sciezka_poprzeczna',(-9.25,y,0),(8.5,2.6,.035),floor)
for x in [-16,-7.4]:
 for y in [-3,-10,-18,-24]:
  box('Ogrod_grzadka',(x,y,.16),(2.5,2.6,.3),wood);box('Ogrod_ziemia',(x,y,.32),(2.3,2.4,.06),soil)
# Archive to corridor left unobstructed; new room working tables and categorized plinths along edges.
for name,cx,cy in [('Hydro_stol',21,1),('Obs_stol',21,-24)]:
 box(name+'_blat',(cx,cy,.89),(2.8,1.2,.12),wood)
 for xx in [-1.2,1.2]:
  for yy in [-.43,.43]:box(name+'_noga',(cx+xx,cy+yy,.43),(.13,.13,.86),wood)
for i in range(6):
 x=16.1+(i%3)*4.5;y=4.6 if i<3 else -2.5
 box('Hydro_ekspozycja',(x,y,.4),(1.5,1.35,.8),stone)
# Observatory open-access armillary, actual source zodiac models remain separate exhibits.
cyl('Obserwatorium_podstawa',(21,-18,.32),1.15,.64,stone)
rod('Obserwatorium_os',(21,-18,.64),(21,-18,2.55),.035,gold)
for r,rot in [(1.08,(0,0,0)),(.97,(1.15,0,0)),(.85,(0,1.1,0))]:
 bpy.ops.mesh.primitive_torus_add(major_segments=72,minor_segments=8,location=(21,-18,1.65),major_radius=r,minor_radius=.014);o=bpy.context.object;o.name='Obserwatorium_sfera';o.rotation_euler=rot;o.data.materials.append(gold)
for i in range(8):
 a=2*math.pi*i/8;x=21+4.35*math.cos(a);y=-18+6.5*math.sin(a);cyl('Zodiak_cokol',(x,y,.45),.6,.9,stone)
# Six low reading plinths for the paged diagram/text gallery.
for i in range(6):
 x=-3.3+(i%3)*6.1;y=-11.5 if i<3 else -26.2
 box('Diagramy_gablota',(x,y,.4),(1.65,1.3,.8),stone)
 box('Diagramy_gablota_blat',(x,y,.82),(1.72,1.37,.04),wood)
# Reading balcony-like low rails around 3D relief reserve; 2.5D floor remains walkable and unobstructed.
for x in [-4.3,14.3]:
 for y in [-25,-19]:box('Diagramy_pulpit',(x,y,.85),(.85,1.3,.16),wood)
# Delivery camera and area lights for Blender QA; runtime ambient uses the same colour palette.
sc.world=bpy.data.worlds.new('Swiat');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.19,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for name,x0,x1,y0,y1,h in ROOMS:
 d=bpy.data.lights.new('Fill_'+name,'AREA');d.energy=1600 if name!='Diagramy' else 4500;d.shape='DISK';d.size=min(x1-x0,y1-y0)*.8;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=((x0+x1)/2,(y0+y1)/2,h-.25)
bpy.ops.object.camera_add(location=(5,-10,2.2));cam=bpy.context.object;cam.name='Delivery';cam.rotation_euler=(Vector((5,-21,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=22;sc.camera=cam
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.render.resolution_x=1440;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc['interpretation']='Modern fictional research building. Manuscript exhibits separately source-anchored.'
(OUT/'layout.json').write_text(json.dumps({'rooms':ROOMS,'doors':DOORS,'garden':[-19,-5,-28,6],'units':'m'},indent=2))
(OUT/'openings.json').write_text(json.dumps({'schema':'game-room.opening-schedule.v1','roomId':'voynich-compound-03','primaryArrival':{'openingId':'wejscie_ogrod_Pracownia','exception':''},'openings':openings},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Budynek_i_ogrod_editable.blend'))
# Static material batching only in runtime copy. Source remains separated editable geometry.
for o in list(bpy.data.objects):
 if o.type=='FONT':bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
groups={}
for o in bpy.data.objects:
 if o.type=='MESH':groups.setdefault(o.data.materials[0].name if len(o.data.materials)==1 else o.name,[]).append(o)
for name,obs in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
 # Evaluate bevels individually before join.
 for o in obs:
  bpy.context.view_layer.objects.active=o
  for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.context.view_layer.objects.active=obs[0]
 if len(obs)>1:bpy.ops.object.join()
 bpy.context.object.name='Static_'+name
bpy.ops.export_scene.gltf(filepath=str(OUT/'compound.glb'),export_format='GLB',export_apply=True,export_lights=False,export_cameras=False)
shutil.copyfile(OUT/'compound.glb',ROOT/'quest-native/assets/room/compound.glb')
print('BUILDING',len(ROOMS),'rooms',len(openings),'door sides',len(groups),'mesh groups',flush=True)
