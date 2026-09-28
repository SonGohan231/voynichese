"""Source-projected closed volumes. Geometry is a draft, never a certified facsimile.

Blender 4.5 / Python 3.11. Requires triangle, scipy, pillow, opencv-python-headless.
No synthesized texture, generative image, palette substitution, or shared root template.
Front color = original, SHA-checked sRGB scan; back geometry = explicit hypothesis.
Run --sources DIR --pages pages.json --output DIR [--render].
"""
import argparse, collections, hashlib, json, math, struct
from pathlib import Path
import bpy, bmesh, cv2, numpy as np, triangle
from PIL import Image, ImageDraw
from mathutils import Vector

HERE = Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def material(name, image=None):
    m=bpy.data.materials.new(name); m.use_nodes=True
    n=m.node_tree.nodes; n.clear(); out=n.new('ShaderNodeOutputMaterial')
    if image:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.interpolation='Closest'; t.extension='EXTEND'
        # Blender's official glTF exporter recognizes a color directly connected
        # to Surface as KHR_materials_unlit. An Emission shader alone does not.
        m.node_tree.links.new(t.outputs['Color'],out.inputs['Surface'])
        m['color_policy']='original sRGB scan; unlit; no tone mapping'
    else:
        rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=(.17,.19,.21,1)
        m.node_tree.links.new(rgb.outputs[0],out.inputs['Surface'])
        m['color_policy']='neutral inferred back; not source evidence'
    return m

def build_part(part, source, page, out, srcmat, backmat):
    poly=np.array(part['boundary'],np.float64)
    x0,y0,x1,y1=part['crop']; W,H=x1-x0,y1-y0
    mask=np.zeros((H,W),np.uint8); cv2.fillPoly(mask,[np.rint(poly).astype(np.int32)],255)
    Image.fromarray(mask).save(out/'masks'/(part['id']+'.png'))
    segments=np.array([(i,(i+1)%len(poly)) for i in range(len(poly))],np.int32)
    tri=triangle.triangulate({'vertices':poly,'segments':segments},'pq25a45')
    pts=tri['vertices']; faces=tri['triangles']; n=len(pts)
    dist=cv2.distanceTransform(mask,cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    xi=np.clip(np.rint(pts[:,0]).astype(int),0,W-1); yi=np.clip(np.rint(pts[:,1]).astype(int),0,H-1)
    d=dist[yi,xi]; depth=part['depth_px']
    # Depth only: these assumptions never shift observed X/Z or UV coordinates.
    if part['depth']=='basin':
        rim=depth*.8*np.exp(-((d-14)/24)**2)
        front=7+rim
        back=12+depth*np.sqrt(np.clip(d/(dist.max()+1),0,1))
    elif part['depth']=='canopy':
        front=2+depth*np.sqrt(np.clip(d/(dist.max()+1),0,1))
        back=2+front*.7
    else:
        front=2+np.minimum(depth,d*.85)**.5*math.sqrt(depth)
        back=front.copy()
    vertices=[((p[0]+x0)/1000,-float(front[i])/1000,-(p[1]+y0)/1000) for i,p in enumerate(pts)]
    vertices += [((p[0]+x0)/1000,float(back[i])/1000,-(p[1]+y0)/1000) for i,p in enumerate(pts)]
    # Triangle input is 2D XY counterclockwise. Mapping y -> -Z gives +Y normal;
    # reverse front winding to face the source-view camera at negative Y.
    polys=[tuple(int(v) for v in f[::-1]) for f in faces]
    polys += [tuple(int(v)+n for v in f) for f in faces]
    edges=collections.Counter(tuple(sorted((int(f[j]),int(f[(j+1)%3])))) for f in faces for j in range(3))
    border={e for e,c in edges.items() if c==1}
    for f in faces:
        for j in range(3):
            a,b=int(f[j]),int(f[(j+1)%3])
            if tuple(sorted((a,b))) in border: polys.append((a,b,b+n,a+n))
    mesh=bpy.data.meshes.new(part['id']+'_closed_mesh');mesh.from_pydata(vertices,[],polys);mesh.update()
    mesh.materials.append(srcmat);mesh.materials.append(backmat)
    uv=mesh.uv_layers.new(name='NativeScanProjection')
    for face in mesh.polygons:
        face.material_index=0 if face.index<len(faces) else 1
        face.use_smooth=True
        for li in face.loop_indices:
            vi=mesh.loops[li].vertex_index % n; p=pts[vi]
            uv.data[li].uv=((p[0]+x0)/page['width'],1-(p[1]+y0)/page['height'])
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bad=sum(not e.is_manifold for e in bm.edges); volume=abs(bm.calc_volume(signed=True));bm.to_mesh(mesh);bm.free()
    assert not bad and volume>0,(part['id'],bad,volume)
    obj=bpy.data.objects.new(part['id'],mesh);bpy.context.collection.objects.link(obj)
    for k,v in {'source_scan':part['scan'],'folio':page['label'],'source_sha256':page['sha256'],
                'title':part['title'],'reconstruction_status':'DRAFT_SOURCE_PROJECTED_VOLUME',
                'depth_status':'inferred, not determined by manuscript',
                'contour_status':'manually traced; independent review pending',
                'unseen_surface_status':'neutral back; no invented historical pattern',
                'source_crop_native_pixels':part['crop']}.items():obj[k]=v
    obj['source_camera']='orthographic, looking +Y, up +Z; original XY preserved at 1000 px/m'
    # Useful rig: editable vertices remain in the page coordinate system.
    origin=Vector(((x0+x1)/2000,0,-(y0+y1)/2000))
    obj.location=-origin
    return obj,{'id':part['id'],'folio':page['label'],'scan':part['scan'],'source_sha256':page['sha256'],
                'crop':part['crop'],'vertices':len(mesh.vertices),'triangles':sum(len(f.vertices)-2 for f in mesh.polygons),
                'non_manifold_edges':bad,'volume_m3':volume,'status':obj['reconstruction_status'],
                'contour_review':'pending','depth':'inferred','front_color':'original scan, unlit',
                'back_color':'neutral, explicitly unobserved'}

def render_part(obj,part,scene,out,source):
    for o in bpy.data.objects:
        if o.type=='MESH':o.hide_render=o!=obj
    x0,y0,x1,y1=part['crop']; w,h=x1-x0,y1-y0
    # Native resolution gives a direct pixel-coordinate test without a resampling reference.
    scene.render.resolution_x=w;scene.render.resolution_y=h
    cam=scene.camera;cam.location=(0,-8,0);cam.rotation_euler=(math.pi/2,0,0)
    cam.data.type='ORTHO';cam.data.ortho_scale=max(w,h)/1000
    scene.render.film_transparent=True
    scene.render.filepath=str((out/'renders'/(part['id']+'_front.png')).resolve());bpy.ops.render.render(write_still=True)
    actual=np.array(Image.open(scene.render.filepath).convert('RGBA'))
    expected=np.array(Image.open(source).convert('RGB').crop(part['crop']))
    mask=np.array(Image.open(out/'masks'/(part['id']+'.png')))>0
    inside=cv2.erode(mask.astype(np.uint8),np.ones((15,15),np.uint8))>0
    inside &= actual[:,:,3]>254
    assert inside.sum()>100,(part['id'],'no comparable pixels')
    err=np.abs(actual[:,:,:3].astype(float)-expected.astype(float))[inside]
    color={'compared_pixels':int(inside.sum()),'rgb_mean_absolute_error_255':float(err.mean()),
           'rgb_channel_error_p95_255':float(np.percentile(err,95)),
           'test_scope':'front interior render versus original crop; excludes traced boundary; does not certify contour or depth'}
    cam.location=(2.4,-5.8,1.5);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=max(400,min(1000,w));scene.render.resolution_y=max(400,min(1000,h));cam.data.ortho_scale=max(w,h)/1000*1.15
    scene.render.filepath=str((out/'renders'/(part['id']+'_oblique.png')).resolve());bpy.ops.render.render(write_still=True)
    return color

def check_glb(path,source_hash):
    raw=path.read_bytes();assert raw[:4]==b'glTF'
    length,kind=struct.unpack_from('<I4s',raw,12);doc=json.loads(raw[20:20+length]);off=20+length
    blen,btype=struct.unpack_from('<I4s',raw,off);blob=raw[off+8:off+8+blen]
    image_hashes=[]
    for im in doc.get('images',[]):
        view=doc['bufferViews'][im['bufferView']];start=view.get('byteOffset',0)
        image_hashes.append(hashlib.sha256(blob[start:start+view['byteLength']]).hexdigest())
    assert source_hash in image_hashes,'GLB exporter changed source texture bytes'
    assert 'KHR_materials_unlit' in doc.get('extensionsUsed',[]),'source material must export unlit'
    return {'sha256':sha(path),'bytes':path.stat().st_size,'source_texture_bytes_preserved':True,'unlit':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sources',type=Path,required=True);ap.add_argument('--pages',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--render',action='store_true')
    ap.add_argument('--annotations',type=Path,default=HERE/'annotations.json');ap.add_argument('--batch',default='01');args=ap.parse_args()
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    for p in ('masks','renders','glb'): (out/p).mkdir(exist_ok=True)
    pages={p['id']:p for p in json.loads(args.pages.read_text())};parts=json.loads(args.annotations.read_text())['parts']
    # Tight, source-registered viewing bounds. Annotation coordinates stay unchanged on disk.
    for part in parts:
        p=np.asarray(part['boundary']);c=part['crop'];lo=np.maximum(0,p.min(axis=0)-10).astype(int)
        hi=np.minimum([c[2]-c[0],c[3]-c[1]],p.max(axis=0)+11).astype(int)
        part['boundary']=(p-lo).tolist();part['crop']=[c[0]+int(lo[0]),c[1]+int(lo[1]),c[0]+int(hi[0]),c[1]+int(hi[1])]
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.eevee.taa_render_samples=1;scene.render.filter_size=.01;scene.render.dither_intensity=0
    scene.world=bpy.data.worlds.new('Neutral background');scene.world.color=(.02,.02,.02)
    bpy.ops.object.camera_add();scene.camera=bpy.context.object;scene.camera.name='SOURCE_REGISTERED_CAMERA'
    backmat=material('INFERRED_BACK_NOT_SOURCE');mats={};sources={};records=[];objects=[]
    for part in parts:
        s=part['scan'];page=pages[s]
        if s not in sources:
            sources[s]=next(args.sources.glob(s[1:]+'*.jpg'));assert sha(sources[s])==page['sha256'],s
            im=bpy.data.images.load(str(sources[s].resolve()));im.name=s+'_ORIGINAL_BYTES';im.colorspace_settings.name='sRGB';im.pack();mats[s]=material(s+'_SOURCE_COLOR_UNLIT',im)
        obj,record=build_part(part,sources[s],page,out,mats[s],backmat);objects.append(obj)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        target=out/'glb'/(part['id']+'.glb')
        bpy.ops.export_scene.gltf(filepath=str(target.resolve()),export_format='GLB',use_selection=True,export_extras=True,export_image_format='AUTO')
        record['glb']=check_glb(target,page['sha256'])
        if args.render: record['front_color_check']=render_part(obj,part,scene,out,sources[s])
        records.append(record)
        (out/'PROGRESS.json').write_text(json.dumps({'completed_volumes':len(records),'verified_1_to_1_models':0,'scope':'selected fragments, not complete corpus','models':records},ensure_ascii=False,indent=2))
        # A recovery checkpoint after each model; final named batch after ten.
        bpy.ops.wm.save_as_mainfile(filepath=str((out/f'Przebudowa_{args.batch}_10_Bryl.blend').resolve()),compress=True)
        print('CHECKPOINT',part['id'],record,flush=True)
    for i,obj in enumerate(objects):
        obj.hide_render=False;obj.location.x+=(i%5)*2.4;obj.location.z-=(i//5)*2.2
    scene.camera.location=(4.8,-15,-1.1);scene.camera.rotation_euler=(math.pi/2,0,0);scene.camera.data.ortho_scale=12.6
    scene.render.resolution_x=1800;scene.render.resolution_y=720
    bpy.ops.wm.save_as_mainfile(filepath=str((out/f'Przebudowa_{args.batch}_10_Bryl.blend').resolve()),compress=True)
    print('DONE',len(records),'closed source-projected draft volumes; 0 certified 1:1 reconstructions',flush=True)

if __name__=='__main__':main()
