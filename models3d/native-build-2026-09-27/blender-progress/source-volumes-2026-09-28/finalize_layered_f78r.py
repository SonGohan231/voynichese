"""Deduplicate packed source images, add depth controls and exploded preview."""
import bpy, json, hashlib, sys, math
from pathlib import Path
from mathutils import Vector
from build_source_volumes import check_glb, build_part, material
import numpy as np, cv2
from PIL import Image

out=Path(sys.argv[1]).resolve();blend=out/'f78r_Baseny_Postacie_Woda_Obrzeza.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend));s=bpy.context.scene
digest='6e0f3449af81da50a04a060937fdcdb4c2e2b93be98bcb9b4bd523c1e1b35ce5'
originals=[im for im in bpy.data.images if im.packed_file and hashlib.sha256(im.packed_file.data).hexdigest()==digest]
assert originals
canonical=originals[0];canonical.name='s0141_f78r_ORIGINAL_JPEG_SRGB'
for m in bpy.data.materials:
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image in originals:n.image=canonical;n.interpolation='Closest'
for im in list(bpy.data.images):
    if im!=canonical and im.users==0:bpy.data.images.remove(im)
extra=json.loads((Path(__file__).parent/'junctions_f78r.json').read_text());newrecords=[]
fm=material('f78r_junctions_SOURCE',canonical);bm=material('f78r_junctions_UNKNOWN_BACK')
for p in extra['parts']:
    if bpy.data.objects.get(p['id']):continue
    p.update({'scan':'s0141','crop':extra['crop'],'title':p['id'],'depth':'flow','depth_px':12})
    ob,rec=build_part(p,None,{'width':2793,'height':3761,'label':'78r','sha256':digest},out,fm,bm)
    ob.location=(0,0,0);ob['certified_1_to_1']=False;newrecords.append(rec)
groups={}
for name in ('01_Postacie_widoczne','02_Woda_i_obrzeza','03_Kanaly_i_struktury_robocze'):
    col=bpy.data.collections.get(name)
    if col is None:col=bpy.data.collections.new(name);s.collection.children.link(col)
    groups[name]=col
meshobs=[o for o in bpy.data.objects if o.type=='MESH']
for ob in meshobs:
    group='01_Postacie_widoczne' if ob.get('role')=='figure' else '02_Woda_i_obrzeza' if ob.get('role') in ('water','rim') else '03_Kanaly_i_struktury_robocze'
    for c in list(ob.users_collection):c.objects.unlink(ob)
    groups[group].objects.link(ob)
    if ob.get('role')=='figure' and not ob.data.shape_keys:
        basis=ob.shape_key_add(name='Oryginalna_bryla_robocza');flat=ob.shape_key_add(name='Splaszczenie_do_zrodla')
        for p in flat.data:p.co.y=-.0005 if p.co.y<0 else .0005
        flat.value=0;ob['depth_control']='Splaszczenie_do_zrodla: 0=robocza glebiа, 1=cienka warstwa; XZ i UV bez zmian'
source_cam=s.camera.copy();source_cam.data=s.camera.data.copy();s.collection.objects.link(source_cam);source_cam.name='Kontrola_ortograficzna_calej_strony'
source_cam.location=(1.3965,-8,-1.8805);source_cam.rotation_euler=(math.pi/2,0,0);source_cam.data.ortho_scale=4.1
camera=s.camera
# Show independent figure volumes with displacement in depth only.
for ob in meshobs:
    ob.hide_render='upper' not in ob.name
    if ob.get('role')=='figure':ob.location.y=-.25
camera.location=(2.8,-3.5,-.4);focus=Vector((1.73,0,-1.65));camera.rotation_euler=(focus-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=1.6
s.render.resolution_x=1200;s.render.resolution_y=900;s.render.filepath=str(out/'renders/upper_exploded.png');bpy.ops.render.render(write_still=True)
for ob in meshobs:
    ob.hide_render=False
    if ob.get('role')=='figure':ob.location.y=0
bpy.ops.object.select_all(action='DESELECT')
for ob in meshobs:ob.select_set(True)
bpy.context.view_layer.objects.active=meshobs[0]
target=out/'glb/f78r_layered_assembly.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_extras=True,export_image_format='AUTO',export_morph=False)
receipt=check_glb(target,digest)
s.camera=source_cam;s.render.resolution_x=1000;s.render.resolution_y=1400
s.render.resolution_x=2793;s.render.resolution_y=3761;source_cam.data.ortho_scale=3.761
s.render.filepath=str(out/'renders/f78r_full_native_check.png');bpy.ops.render.render(write_still=True)
actual=np.array(Image.open(s.render.filepath).convert('RGBA'))
import io
expected=np.array(Image.open(io.BytesIO(canonical.packed_file.data)).convert('RGB'))
inside=cv2.erode((actual[:,:,3]>254).astype(np.uint8),np.ones((7,7),np.uint8))>0
error=np.abs(actual[:,:,:3].astype(float)-expected.astype(float))[inside]
nativecheck={'pixels':int(inside.sum()),'mean_absolute_rgb_error':float(error.mean()),'max_absolute_rgb_error':float(error.max()),'scope':'rendered assembly interior; no certification of missing drawings, silhouette or depth'}
s.render.resolution_x=1000;s.render.resolution_y=1400;source_cam.data.ortho_scale=4.1
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
r=json.loads((out/'VALIDATION.json').read_text());r['glb']=receipt;r['packed_original_texture_count']=len([im for im in bpy.data.images if im.packed_file]);r['depth_controls']=15;r['mesh_sampling_px']=2;r['raster_boundary_error_note']='Source-projected silhouette follows a 2-pixel grid; not subpixel accurate.';r['assembly_meshes']=len(meshobs)
r['records']+=newrecords;r['new_flow_connections']=3;r['full_assembly_color_check']=nativecheck
(out/'VALIDATION.json').write_text(json.dumps(r,indent=2))
print('FINALIZED',len(meshobs),receipt,flush=True)
