import bpy,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
from PIL import Image
R=Path(__file__).resolve().parent;out=R/'vessels';out.mkdir(exist_ok=True)
atlas=json.load(open(R.parent/'voynich-3d/public/assets/atlas.json'))['pages']
# Traced against the supplied scans. Coordinates use the inspected reference raster dimensions.
DATA=[
 ('s0161',1,(799,1100),(60,78,176,380),112,[(82,13),(89,20),(104,17),(128,19),(135,31),(144,35),(155,30),(180,28),(184,35),(194,29),(227,27),(239,22),(258,8),(264,14),(270,8),(286,11),(296,25),(312,27),(337,25),(346,31),(365,39),(375,34)],'green',[(143,33),(184,34),(263,13),(298,27),(341,27)]),
 ('s0161',2,(799,1100),(78,380,184,689),126,[(384,3),(395,6),(400,3),(411,15),(420,23),(430,26),(440,28),(449,33),(461,31),(483,29),(492,34),(518,31),(533,40),(544,42),(553,32),(576,15),(590,11),(598,18),(604,9),(620,14),(630,29),(641,34),(658,33),(669,24),(682,42)],'green',[(425,24),(449,33),(489,32),(532,40),(544,39),(597,16),(638,34),(653,32)]),
 ('s0161',3,(799,1100),(80,695,179,999),128,[(698,4),(709,6),(718,3),(729,8),(739,12),(744,8),(763,8),(773,23),(785,26),(805,29),(818,26),(844,29),(852,29),(862,38),(873,39),(885,29),(908,12),(919,6),(928,12),(933,6),(953,19),(959,28),(969,29),(977,27),(990,29)],'green',[(737,11),(773,24),(815,29),(854,29),(866,38),(918,10),(960,29),(982,29)]),
 ('s0163',1,(1100,996),(70,76,181,314),123,[(79,2),(87,5),(97,3),(115,3),(121,11),(134,21),(143,29),(155,29),(179,22),(188,17),(208,19),(217,34),(231,38),(242,41),(252,33),(274,18),(289,10),(297,41),(307,43)],'blue',[(143,28),(188,18),(211,24),(243,39),(250,36),(299,41)]),
 ('s0163',2,(1100,996),(78,321,184,603),127,[(329,1),(347,3),(354,7),(363,2),(380,4),(387,10),(395,14),(402,10),(418,6),(429,13),(438,21),(450,21),(475,20),(484,26),(494,36),(505,40),(519,31),(537,20),(545,7),(558,10),(572,10),(582,16),(590,42),(599,35)],'blue',[(394,13),(436,21),(450,20),(490,32),(507,40),(545,10),(582,14),(592,41)]),
 ('s0163',3,(1100,996),(90,603,204,817),144,[(607,2),(616,6),(626,12),(632,4),(646,5),(656,20),(668,32),(681,36),(704,38),(721,28),(731,13),(741,26),(748,23),(752,9),(770,10),(785,35),(800,46)],'blue',[(625,10),(664,25),(677,35),(739,25),(748,24)]),
 ('s0175',1,(789,1100),(75,76,165,249),121,[(80,32),(87,38),(103,38),(115,36),(142,35),(150,37),(157,39),(234,37),(242,36)],'red',[(109,37),(149,38),(158,38),(238,37)]),
 ('s0175',2,(789,1100),(81,311,160,463),121,[(316,21),(323,29),(334,28),(340,25),(358,25),(367,28),(374,30),(438,30),(452,27),(459,24)],'red',[(326,28),(339,27),(366,27),(374,29),(446,29)]),
 ('s0175',3,(789,1100),(75,479,173,650),122,[(490,20),(501,28),(510,27),(548,28),(559,33),(569,29),(615,30),(627,29),(637,44),(646,36)],'red',[(507,26),(553,30),(566,30),(623,30)]),
 ('s0175',4,(789,1100),(70,699,158,870),116,[(705,19),(713,27),(725,24),(754,24),(762,32),(772,30),(839,32),(848,36),(858,33),(864,29)],'red',[(717,26),(761,31),(770,30),(850,34),(860,31)])]
COL={'green':(.04,.28,.21,1),'blue':(.018,.17,.29,1),'red':(.39,.065,.032,1)}
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=c;m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=c;p.inputs['Roughness'].default_value=.73;return m
def mesh(n,vs,fs,materials):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o)
 for m in materials:me.materials.append(m)
 return o
def curve(n,points,r,material):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=r;c.bevel_resolution=2;s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for b,p in zip(s.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);o.data.materials.append(material);return o
records=[]
for scan,number,ref,bbox,cx,profile,color,rings in DATA:
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.unit_settings.system='METRIC'
 entry=next(p for p in atlas if p['id']==scan);original=R/'source/originals'/entry['file'];assert hashlib.sha256(original.read_bytes()).hexdigest()==entry['sha256']
 im=Image.open(original).convert('RGB');sx=im.width/ref[0];sy=im.height/ref[1];cropbox=tuple(round(v*(sx if k%2==0 else sy)) for k,v in enumerate(bbox));crop=im.crop(cropbox)
 ident='vessel_%s_%02d'%(scan,number);dest=out/ident;dest.mkdir(exist_ok=True);texpath=dest/'source_crop.jpg';crop.save(texpath,quality=98)
 m=mat('SOURCE_front_scan',(1,1,1,1));image=bpy.data.images.load(str(texpath));image.pack();nt=m.node_tree;node=nt.nodes.new('ShaderNodeTexImage');node.image=image;nt.links.new(node.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
 back=mat('Interpretowany_tyl_jednolity',COL[color]);rim=mat('Ozdobniki_parchment',(.57,.46,.27,1));rootmat=mat('Korzen_ochra',(.39,.19,.067,1));stemmat=mat('Lodyga',(.25,.26,.105,1));leafmat=mat('Lisc_zielony',(.06,.25,.12,1))
 zmax=profile[0][0];zmin=profile[-1][0];factor=1.0/(zmin-zmax);N=48;vs=[];fs=[]
 # Open, hollow rotational volume. Front UV is a projection of the observed drawing.
 for y,r in profile:
  for j in range(N):
   a=2*math.pi*j/N;vs.append((r*factor*math.cos(a),r*factor*math.sin(a),(zmin-y)*factor))
 for k in range(len(profile)-1):
  for j in range(N):fs.append((k*N+j,(k+1)*N+j,(k+1)*N+(j+1)%N,k*N+(j+1)%N))
 o=mesh(ident+'_Bryla',vs,fs,[m,back]);uv=o.data.uv_layers.new(name='Projection_from_source')
 for poly in o.data.polygons:
  ymid=sum(o.data.vertices[v].co.y for v in poly.vertices)/4;poly.material_index=0 if ymid<=.00001 else 1;poly.use_smooth=True
  for li in poly.loop_indices:
   co=o.data.vertices[o.data.loops[li].vertex_index].co;px=cx+co.x/factor;py=zmin-co.z/factor;uv.data[li].uv=((px-bbox[0])/(bbox[2]-bbox[0]),1-(py-bbox[1])/(bbox[3]-bbox[1]))
 sol=o.modifiers.new('Grubosc_scianki','SOLIDIFY');sol.thickness=.008;sol.offset=-1;sol.material_offset=1;sol.material_offset_rim=1
 o['source_scan']=scan;o['folio']=entry['label'];o['source_sha256']=entry['sha256'];o['source_bbox_px']=cropbox;o['status']='CANDIDATE';o['depth']='Interpretive rotational depth; back is unobserved, solid colored.'
 # Rolled moulding bands at positions directly observed in the drawing.
 for k,(y,r) in enumerate(rings):
  bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=6,major_radius=r*factor,minor_radius=.004,location=(0,0,(zmin-y)*factor));t=bpy.context.object;t.name=ident+'_Ozdobny_pierscien_%02d'%k;t.data.materials.append(rim)
 # Rear contact base, physically closed foot.
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=profile[-1][1]*factor,depth=.008,location=(0,0,.004));bpy.context.object.name=ident+'_Spod';bpy.context.object.data.materials.append(back)
 # A separately editable traced neighboring root. Source front geometry and depth provenance retained.
 # Curves are hand-traced from the adjacent root families, not a botanical identification.
 if scan=='s0161':
  paths=[[(0,.0,.72),(-.03,.01,.59),(-.05,0,.39),(-.18,.025,.18),(-.21,0,.10)],[(0,0,.60),(.02,-.01,.43),(-.01,0,.26),(-.10,.04,.12)],[(.01,0,.56),(.10,.01,.40),(.08,.01,.25),(.13,0,.16)],[(.03,0,.60),(.16,0,.44),(.13,-.04,.33),(.20,0,.21)],[(.01,0,.74),(.06,0,.85),(.12,0,1.02)]]
 elif scan=='s0163':
  paths=[[(0,0,.72),(-.07,0,.65),(-.13,0,.51),(-.19,0,.29),(-.25,0,.24)],[(0,0,.67),(.08,.03,.62),(.10,0,.42),(.20,0,.34)],[(0,0,.66),(-.03,-.01,.46),(.03,0,.29),(.08,0,.19)],[(.02,0,.67),(.15,0,.62),(.24,0,.49),(.31,0,.44)],[(0,0,.72),(.01,0,.90),(-.04,0,1.04)]]
 else:
  paths=[[(-.23,0,.53),(-.08,0,.48),(.13,0,.47),(.34,0,.50)],[(.0,0,.49),(.01,-.02,.38),(.08,0,.29)],[(.13,0,.48),(.15,.02,.34),(.23,0,.25)],[(-.17,0,.50),(-.21,0,.35),(-.30,0,.29)],[(-.15,0,.55),(-.07,0,.68),(.09,0,.74),(.29,0,.77)]]
 offset=Vector((.75,0,0));rootpieces=[]
 for k,path in enumerate(paths):
  pts=[tuple(Vector(p)+offset) for p in path];t=curve(ident+'_Korzen_%02d'%k,pts,.014 if k<len(paths)-1 else .009,rootmat if k<len(paths)-1 else stemmat);t['source_scan']=scan;t['provenance']='Interpretive depth of neighboring root family; compare complete original scan.';rootpieces.append(t)
 # Lanceolate / lobed leaves in spatial volume rather than flat image planes.
 tips=[(.75,.0,.98),(.87,0,.92),(.67,0,.86)] if scan!='s0175' else [(1.02,0,.77),(1.0,0,.85)]
 for k,(x,y,z) in enumerate(tips):
  L=.18;W=.048;v=[(x,y,z),(x+L*.4,y-.012,z+W),(x+L,y,z+.06),(x+L*.4,y+.012,z-W),(x+L*.4,y-.028,z)]
  t=mesh(ident+'_Lisc_%02d'%k,v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],[leafmat]);sol=t.modifiers.new('Thickness','SOLIDIFY');sol.thickness=.003
 # Reference crop is embedded, hidden from GLB but visible in the editable file via image editor.
 for obj in list(bpy.data.objects):
  obj['scan']=scan;obj['folio']=entry['label'];obj['reconstruction_status']='CANDIDATE; front silhouette measured, depth/back inferred'
 sc['source']=entry['file'];sc['source_sha256']=entry['sha256'];sc['method']='Traced rotational profile, front scan projection, separate solid mouldings, hand-formed adjacent roots. No transcription.'
 bpy.ops.wm.save_as_mainfile(filepath=str(dest/(ident+'.blend')))
 bpy.ops.export_scene.gltf(filepath=str(dest/(ident+'.glb')),export_format='GLB',export_apply=True,export_extras=True)
 rec={'id':ident,'scan':scan,'folio':entry['label'],'category':'Naczynia · profile ze skanów','model':'res://assets/models/'+ident+'.glb','source_sha256':entry['sha256'],'source_bbox_px':cropbox,'profile_reference_size':list(ref),'profile_pixels':profile,'profile_center_x':cx,'status':'CANDIDATE','method':'measured front profile + scan texture; inferred rotational depth/back; adjacent root interpretation','sha256':hashlib.sha256((dest/(ident+'.glb')).read_bytes()).hexdigest()};records.append(rec)
 (out/'PROGRESS.json').write_text(json.dumps({'completed':len(records),'batch_size':10,'models':records},ensure_ascii=False,indent=2))
 print('SAVED',ident,flush=True)
# Full-resolution originals preserved separately, with proof of source relationship.
(out/'README.md').write_text('''# Partia 20: 10 naczyń / wieżyczek\n\nBlender 4.5.4 LTS. Karty f88r, f89v (część), f99r. Każdy model ma niezależną bryłę, pierścienie i sąsiadujący korzeń z liśćmi.\n\nProfil przedni wyznaczono z rysunku; front ma teksturę oryginalnego skanu. Bryła obrotowa, głębokość, tył, przekrój korzeni i zasięg ornamentów wokół naczynia są interpretacją CANDIDATE. Tył pozostaje jednolity, żeby nie powielać znaków bez dowodu. Sąsiednie korzenie są przestrzennymi szkicami do porównania, nie identyfikacją roślin. Nie ma tłumaczeń znaków.\n\nPełne skany w sali umożliwiają sprawdzenie kontekstu i napisów. Pierwsze trzy skany oryginalne zweryfikowano SHA256 względem atlasu. PROGRESS.json zawiera dokładne współrzędne profilu i źródeł.\n''')
