"""Blender 4.5.4: separate disconnected botanical components, preserve source geometry.
No invented botanical details, no automatic species or manuscript interpretation.
"""
import bpy, bmesh, json, pathlib, hashlib, math
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'blender-progress' / 'Partia01_Elementy'
OUT.mkdir(parents=True, exist_ok=True)
CATALOG = json.loads((ROOT/'quest-native/assets/catalog.json').read_text())
REPORT = []

def material(name, color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1)
    return m

for entry in CATALOG[:10]:
    scan=entry['scan'];bpy.ops.wm.read_factory_settings(use_empty=True)
    source=ROOT/'checkpoint-archives/raw-first-ten'/f'{scan}.glb'
    bpy.ops.import_scene.gltf(filepath=str(source))
    parent=bpy.data.objects.get('PLANT_'+scan)
    parent['folio']=entry['folio'];parent['source_sha256']=entry['source_sha256']
    parent['reconstruction_status']='CANDIDATE_VOLUME_INTERPRETATION'
    parent['depth_status']='Unpictured sides interpreted; no physical scale claim'
    before=sum(len(o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
    semantic_counts={}
    for obj in list(parent.children):
        if obj.type!='MESH':continue
        role=obj.name.removeprefix('PLANT_'+scan+'_')
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        # Group connected islands through coincident seam vertices without altering triangles.
        old=obj.data; verts=[v.co.copy() for v in old.vertices]; parents=list(range(len(verts)))
        def find(x):
            while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
            return x
        def union(a,b):
            a,b=find(a),find(b)
            if a!=b:parents[b]=a
        positions={}
        for i,v in enumerate(verts):
            key=tuple(round(float(c),6) for c in v)
            if key in positions:union(i,positions[key])
            else:positions[key]=i
        for face in old.polygons:
            for v in face.vertices[1:]:union(face.vertices[0],v)
        groups={}
        for face in old.polygons:groups.setdefault(find(face.vertices[0]),[]).append(face)
        parts=[]
        for faces in groups.values():
            ids=sorted({i for face in faces for i in face.vertices}); remap={v:i for i,v in enumerate(ids)}
            mesh=bpy.data.meshes.new(obj.name+'_component')
            mesh.from_pydata([verts[i] for i in ids],[],[[remap[i] for i in face.vertices] for face in faces]);mesh.update()
            for mat in old.materials:mesh.materials.append(mat)
            for oldface,newface in zip(faces,mesh.polygons):
                newface.material_index=oldface.material_index;newface.use_smooth=oldface.use_smooth
            normals=[old.corner_normals[i].vector[:] for face in faces for i in face.loop_indices]
            mesh.normals_split_custom_set(normals)
            part=bpy.data.objects.new(obj.name,mesh);bpy.context.collection.objects.link(part);part.parent=parent;part.matrix_world=obj.matrix_world.copy();parts.append(part)
        bpy.data.objects.remove(obj,do_unlink=True)
        semantic_counts[role]=len(parts)
        for i,part in enumerate(parts):
            part.name=f'{scan}__{role}__{i+1:03d}'
            part['folio']=entry['folio'];part['role']=role;part['piece_id']=part.name
            part['source_sha256']=entry['source_sha256']
            bpy.context.view_layer.objects.active=part
            for p in parts:p.select_set(p==part)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS')
    meshes=[o for o in parent.children_recursive if o.type=='MESH']
    after=sum(len(o.data.polygons) for o in meshes)
    assert before==after,(scan,before,after)
    bpy.ops.object.select_all(action='DESELECT');parent.select_set(True)
    for o in parent.children_recursive:o.select_set(True)
    output=OUT/f'{scan}.glb'
    bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
    # Editable reference board, stored only in the .blend, with exact supplied scan aspect.
    image=bpy.data.images.load(str(ROOT/'quest-native/assets/scans'/f'{scan}.jpg'));image.pack()
    ref=bpy.data.objects.new('SOURCE_'+scan+'_f'+entry['folio'],None);bpy.context.collection.objects.link(ref)
    ref.empty_display_type='IMAGE';ref.data=image;ref.empty_display_size=3.6;ref.location=(-3.1,0,2);ref.rotation_euler=(math.pi/2,0,0)
    ref['source_sha256']=entry['source_sha256'];ref['view']='source only; depths of volumes are hypotheses'
    bpy.ops.object.camera_add(location=(0,-8,2.3));camera=bpy.context.object;camera.name='Front_reference_camera'
    camera.rotation_euler=((Vector((0,0,2))-camera.location).to_track_quat('-Z','Y').to_euler());camera.data.type='ORTHO';camera.data.ortho_scale=4.8
    scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.samples=12
    scene.render.resolution_x=550;scene.render.resolution_y=700;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new("StudioWorld");scene.world.color=(0.18,0.18,0.18)
    for loc,power,size in [((2,-4,6),700,5),((-4,-2,3),450,4)]:
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size
        light.rotation_euler=((Vector((0,0,2))-light.location).to_track_quat('-Z','Y').to_euler())
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{scan}_f{entry["folio"]}.blend'))
    item={'scan':scan,'folio':entry['folio'],'parts':len(meshes),'semantic_counts':semantic_counts,'triangles_before':before,'triangles_after':after,'glb_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'source_sha256':entry['source_sha256'],'shape_changed':False,'status':'CANDIDATE_VOLUME_INTERPRETATION'}
    REPORT.append(item)
    (OUT/'PROGRESS.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
    print('CHECKPOINT',json.dumps(item),flush=True)
    if scan=='s0004':
        scene.render.filepath=str(OUT/'preview_s0004.png');bpy.ops.render.render(write_still=True)

(OUT/'README.md').write_text('''# Pierwsze 10 modeli · osobne elementy
Każdy plik .blend jest edytowalnym projektem Blender 4.5.4 LTS z zapakowanym skanem referencyjnym.
Zachowano wszystkie trójkąty i kształt brył. Współrzędne szwów służą wyłącznie do grupowania części; nie usunięto wierzchołków ani ścian. Rozłączono niezależne wyspy siatki i ustawiono lokalne środki obrotu.
Modele nadal są roboczą interpretacją głębokości, nie potwierdzoną rekonstrukcją botaniczną.
Pliki GLB zawierają wyłącznie roślinę z nazwanymi częściami i identyfikatorem folio.
Skan referencyjny znajduje się obok bryły w pliku Blender; nie jest dodatkową rośliną.
Źródła: dostarczone archiwa i istniejąca partia 01; żadnego skanu nie zastąpiono generowanym obrazem.
''')
