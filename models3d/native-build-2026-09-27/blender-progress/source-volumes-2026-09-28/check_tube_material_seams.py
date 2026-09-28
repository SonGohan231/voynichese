"""Repair material classification on non-planar tube quads before export.

The source-facing material must be assigned to final triangles, not to the
average normal of a warped quad. Preserve source UV, geometry and provenance.
Write to a new checkpoint; never overwrite the input Blender file.
"""
import argparse, json, math
from pathlib import Path
import bpy, bmesh, cv2, numpy as np
from PIL import Image
from build_source_volumes import check_glb

ap=argparse.ArgumentParser()
ap.add_argument('--input',type=Path,required=True)
ap.add_argument('--source',type=Path,required=True)
ap.add_argument('--tube-master',type=Path,required=True)
ap.add_argument('--baseline-render',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.input.resolve()))
with bpy.data.libraries.load(str(a.tube_master.resolve()),link=False) as (src,dst):
    names=[n for n in src.meshes if '_tube_' in n and '_hollow' in n]
    dst.meshes=names.copy()
masters=dict(zip([n.split('_hollow')[0] for n in names],dst.meshes))
fixed=[]
for ob in bpy.data.objects:
    if ob.type!='MESH' or '_tube_' not in ob.name:continue
    # Use the original closed Blender topology, before glTF vertex splitting.
    # Keep the original page-space positions; only face tessellation changes.
    original_mats=list(ob.data.materials)
    me=masters[ob.name].copy();ob.data=me
    me.materials.clear()
    for m in original_mats:me.materials.append(m)
    # Closed opaque shells have outward faces. Do not draw the reverse of
    # neutral back faces through subpixel gaps at the shared rim.
    for m in original_mats:m.use_backface_culling=True
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='FIXED',ngon_method='EAR_CLIP')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),ob.name
    for f in bm.faces:f.material_index=0 if f.normal.y<1e-7 else 1
    bm.to_mesh(me);bm.free();me.update()
    # Source projection remains affine after triangulation.
    for face in me.polygons:
        for li in face.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            me.uv_layers.active.data[li].uv=(co.x*1000/2793,1+co.z*1000/3761)
    ob['material_assignment']='source-facing final triangle normal, not averaged quad normal'
    fixed.append(ob.name)
assert len(fixed)==7,fixed
s=bpy.context.scene;cam=s.camera
cam.location=(1.3965,-8,-1.8805);cam.rotation_euler=(math.pi/2,0,0)
cam.data.type='ORTHO';cam.data.ortho_scale=3.761
s.render.resolution_x=2793;s.render.resolution_y=3761
s.render.resolution_percentage=100;s.render.filepath=str((a.output/'front.png').resolve())
bpy.ops.render.render(write_still=True)
actual=np.array(Image.open(s.render.filepath).convert('RGBA'))
expected=np.array(Image.open(a.source).convert('RGB'))
inside=cv2.erode((actual[:,:,3]>254).astype(np.uint8),np.ones((7,7),np.uint8))>0
err=np.abs(actual[:,:,:3].astype(int)-expected.astype(int))
report={'fixed_tubes':fixed,'interior_pixels':int(inside.sum()),
 'different_pixels':int(((err.max(axis=2)>0)&inside).sum()),
 'max_rgb_error':int(err[inside].max()),'mean_rgb_error':float(err[inside].mean()),
 'scope':'source-view interior only; contours and inferred depth remain unverified'}
baseline=np.array(Image.open(a.baseline_render).convert('RGBA'))[:,:,3]
report['coverage_lost_vs_baseline']=int(((baseline>254)&(actual[:,:,3]<=254)).sum())
report['coverage_added_vs_baseline']=int(((baseline<=254)&(actual[:,:,3]>254)).sum())
report['new_closed_models']=0
report['newly_certified_1_to_1_models']=0
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.data.objects:
    if ob.type=='MESH':ob.select_set(True)
target=a.output/'f78r_Poprawka_Materialow.glb'
bpy.ops.export_scene.gltf(filepath=str(target.resolve()),export_format='GLB',use_selection=True,export_extras=True,export_image_format='AUTO',export_morph=False)
import hashlib
report['glb']=check_glb(target,hashlib.sha256(a.source.read_bytes()).hexdigest())
(a.output/'COLOR_CHECK.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((a.output/'f78r_Poprawka_Materialow.blend').resolve()),compress=True)
print(json.dumps(report),flush=True)
