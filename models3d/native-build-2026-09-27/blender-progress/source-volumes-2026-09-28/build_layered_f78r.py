"""Reversible source-registered layered reconstruction; no invented visible color.

Manual masks are hypotheses and recorded as such. Color conservation verifies
registration, never anatomical accuracy or historic three-dimensional truth.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy, bmesh, cv2, numpy as np, triangle
from PIL import Image
from mathutils import Vector
from build_source_volumes import material, check_glb

HERE=Path(__file__).resolve().parent
ORIGINS={'upper':(1180,1230,2280,1990),'lower':(1150,2600,2210,3390)}

def polygon_mask(points,shape,holes=()):
    m=np.zeros(shape,np.uint8);cv2.fillPoly(m,[np.array(points,np.int32)],255)
    for h in holes:cv2.fillPoly(m,[np.array(h,np.int32)],0)
    return m

def refine_mask(rgb,mask):
    # Restrict refinement to a five-pixel band around the explicit manual trace.
    # It cannot silently add a neighboring limb or person.
    k=np.ones((7,7),np.uint8)
    inner=cv2.erode(mask,k); outer=cv2.dilate(mask,k)
    labels=np.where(mask>0,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8)
    labels[outer==0]=cv2.GC_BGD;labels[inner>0]=cv2.GC_FGD
    cv2.grabCut(rgb,labels,None,np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_MASK)
    return np.where((labels==cv2.GC_FGD)|(labels==cv2.GC_PR_FGD),255,0).astype(np.uint8)

def triangulate_mask(mask):
    # Deterministic two-pixel raster mesh. A one-pixel contour uncertainty is
    # explicit; split diagonal contacts so independently touching lobes cannot
    # create non-manifold vertical edges. No unstable polygon tessellation.
    stride=2
    cells=mask[::stride,::stride]>0
    ch,cw=cells.shape;verts=[];faces=[];lookup={}
    def occupied(x,y):return 0<=x<cw and 0<=y<ch and cells[y,x]
    for y,x in zip(*np.where(cells)):
        ids=[]
        for vx,vy in ((x,y),(x+1,y),(x+1,y+1),(x,y+1)):
            q=[occupied(vx-1,vy-1),occupied(vx,vy-1),occupied(vx,vy),occupied(vx-1,vy)]
            diagonal=(q[0] and q[2] and not q[1] and not q[3]) or (q[1] and q[3] and not q[0] and not q[2])
            key=(int(vx),int(vy),int(y*cw+x)+1 if diagonal else 0)
            if key not in lookup:
                lookup[key]=len(verts);verts.append((vx*stride-.5,vy*stride-.5))
            ids.append(lookup[key])
        a,b,c,d=ids;faces.extend(((a,b,c),(a,c,d)))
    return np.asarray(verts,float),np.asarray(faces,np.int32)

def make_volume(name,mask,origin,kind,frontmat,backmat,source_shape):
    pts,tri=triangulate_mask(mask)
    delta1=pts[tri[:,1]]-pts[tri[:,0]];delta2=pts[tri[:,2]]-pts[tri[:,0]]
    tri=tri[np.abs(delta1[:,0]*delta2[:,1]-delta1[:,1]*delta2[:,0])>1e-8]
    _,unique=np.unique(np.sort(tri,axis=1),axis=0,return_index=True);tri=tri[np.sort(unique)];n=len(pts)
    dist=cv2.distanceTransform(mask,cv2.DIST_L2,5)
    xs=np.clip(np.rint(pts[:,0]).astype(int),0,mask.shape[1]-1);ys=np.clip(np.rint(pts[:,1]).astype(int),0,mask.shape[0]-1)
    d=dist[ys,xs]
    if kind=='figure':front=14+np.minimum(d,40)*.8;back=5+np.minimum(d,30)*.5
    elif kind=='rim':front=8+np.minimum(d,22)*.5;back=np.full(n,65.)
    else:front=np.full(n,2.);back=np.full(n,6.)
    xy=pts+np.array(origin[:2]);v=[(p[0]/1000,-front[i]/1000,-p[1]/1000) for i,p in enumerate(xy)]
    v += [(p[0]/1000,back[i]/1000,-p[1]/1000) for i,p in enumerate(xy)]
    fs=[tuple(int(j) for j in f[::-1]) for f in tri]+[tuple(int(j)+n for j in f) for f in tri]
    edge={}
    for f in tri:
        for a,b in zip(f,np.roll(f,-1)):
            key=tuple(sorted((int(a),int(b))))
            edge[key]=None if key in edge else (int(a),int(b))
    for e in edge.values():
        if e:a,b=e;fs.append((a,b,b+n,a+n))
    me=bpy.data.meshes.new(name+'_editable');me.from_pydata(v,[],fs);me.update()
    me.materials.append(frontmat);me.materials.append(backmat)
    uv=me.uv_layers.new(name='ExactSourceCoordinates')
    W,H=source_shape
    for f in me.polygons:
        f.material_index=0 if f.index<len(tri) else 1
        for li in f.loop_indices:
            p=xy[me.loops[li].vertex_index%n];uv.data[li].uv=(p[0]/W,1-p[1]/H)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    # Dissolve interior coplanar faces while retaining material borders and
    # the recorded raster silhouette. UV remains an affine source projection.
    bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(1),verts=list(bm.verts),edges=list(bm.edges),use_dissolve_boundaries=False,delimit={'MATERIAL'})
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);vol=abs(bm.calc_volume(signed=True));bm.to_mesh(me);bm.free()
    assert bad==0 and vol>0,(name,bad,vol)
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    ob['folio']='78r';ob['scan_id']='s0141';ob['role']=kind
    ob['contour_status']='manual candidate with bounded GrabCut refinement; review pending'
    ob['depth_status']='inferred rounded volume, no hidden anatomical reconstruction'
    ob['source_color']='original sRGB unlit projection; neutral unobserved sides and back'
    ob['certified_1_to_1']=False
    return ob,{'id':name,'role':kind,'vertices':len(me.vertices),'triangles':sum(len(p.vertices)-2 for p in me.polygons),'non_manifold_edges':bad,'volume_m3':vol,'mask_pixels':int((mask>0).sum()),'source_crop':origin,'contour_certified':False,'depth_certified':False}

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
    s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=1;s.render.filter_size=.01;s.render.dither_intensity=0
    s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
    s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=True
    s.world=bpy.data.worlds.new('Neutral');bpy.ops.object.camera_add();s.camera=bpy.context.object;s.camera.name='SOURCE_ORTHOGRAPHIC_CONTROL'
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    for n in ('masks','renders','glb'):(a.out/n).mkdir(exist_ok=True)
    raw=a.source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    assert digest=='6e0f3449af81da50a04a060937fdcdb4c2e2b93be98bcb9b4bd523c1e1b35ce5'
    rgb=np.array(Image.open(a.source).convert('RGB'));H,W=rgb.shape[:2]
    s=setup_scene();im=bpy.data.images.load(str(a.source.resolve()));im.colorspace_settings.name='sRGB';im.pack()
    front=material('ORIGINAL_SCAN_SRGB_UNLIT',im);back=material('UNKNOWN_BACK_NEUTRAL')
    annotations=json.loads((HERE/'figures_f78r.json').read_text())['parts']
    masks={};obs=[];records=[];group_union={g:np.zeros((v[3]-v[1],v[2]-v[0]),np.uint8) for g,v in ORIGINS.items()}
    for p in annotations:
        g=p['group'];o=ORIGINS[g];crop=rgb[o[1]:o[3],o[0]:o[2]]
        initial=polygon_mask(p['outline'],crop.shape[:2],p.get('holes',[]));m=refine_mask(crop,initial)
        # Pixel ownership is exclusive. Preserve explicit visible ordering.
        m[group_union[g]>0]=0;group_union[g]|=m;masks[p['id']]=m
        Image.fromarray(m).save(a.out/'masks'/(p['id']+'.png'))
        ob,record=make_volume('f78r_figure_'+p['id'],m,o,'figure',front,back,(W,H));obs.append(ob);records.append(record)
        print('FIGURE',record['id'],record['vertices'],flush=True)
    old=json.loads((HERE/'annotations.json').read_text())['parts']
    for g,o in ORIGINS.items():
        p=next(p for p in old if p['id']=='f78r_basin_'+g)
        points=np.array(p['boundary'])+np.array(p['crop'][:2])-np.array(o[:2])
        footprint=polygon_mask(points,group_union[g].shape)
        # Keep figure extensions outside the former merged basin footprint.
        footprint |= group_union[g]
        # Distinguish water from rim by observed pigment plus explicit basin bounds.
        crop=rgb[o[1]:o[3],o[0]:o[2]];lab=cv2.cvtColor(crop,cv2.COLOR_RGB2LAB)
        green=((lab[:,:,1].astype(float)<128)&(crop[:,:,1].astype(float)>crop[:,:,2].astype(float)*1.08)).astype(np.uint8)*255
        green=cv2.morphologyEx(green,cv2.MORPH_CLOSE,np.ones((13,13),np.uint8))
        # Outer ornament rim follows only the surrounding basin edge, not figure edges.
        edgezone=footprint-cv2.erode(footprint,np.ones((91,91),np.uint8))
        rim=np.where((edgezone>0)&(green==0)&(group_union[g]==0),255,0).astype(np.uint8)
        rim=cv2.morphologyEx(rim,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));rim[(footprint==0)|(group_union[g]>0)]=0
        water=np.where((footprint>0)&(group_union[g]==0)&(rim==0),255,0).astype(np.uint8)
        for kind,m in [('rim',rim),('water',water)]:
            Image.fromarray(m).save(a.out/'masks'/(g+'_'+kind+'.png'))
            ob,rec=make_volume('f78r_'+g+'_'+kind,m,o,kind,front,back,(W,H));obs.append(ob);records.append(rec)
        Image.fromarray(footprint).save(a.out/'masks'/(g+'_assembled.png'))
        assert np.array_equal((rim|water|group_union[g]),footprint)
    # Include existing individually modelled tubes, structures and flows in the
    # same original page coordinate frame, with their draft status preserved.
    for batch in ('batch01','batch02'):
        manifest=json.loads((a.work/batch/'PROGRESS.json').read_text())
        for record in manifest['models']:
            name=record['id']
            if not name.startswith('f78r_') or name.startswith('f78r_basin_'):continue
            use='hollow' if '_tube_' in name else batch
            if use=='hollow':
                record=next(r for r in json.loads((a.work/'hollow/PROGRESS.json').read_text())['models'] if r['id']==name)
            before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str((a.work/use/'glb'/(name+'.glb')).resolve()))
            new=set(bpy.data.objects)-before;cx=(record['crop'][0]+record['crop'][2])/2000;cy=(record['crop'][1]+record['crop'][3])/2000
            for ob in new:
                if ob.parent is None:ob.location+=Vector((cx,0,-cy))
                if ob.type=='MESH':ob['certified_1_to_1']=False;ob['source_registration']='reassembled from original crop origin';obs.append(ob)
    for ob in obs:ob['source_sha256']=digest
    # All components reference one original page, not sixteen duplicate JPEGs.
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image and node.image!=im:
                other=node.image
                if other.packed_file and hashlib.sha256(other.packed_file.data).hexdigest()==digest:node.image=im
    for other in list(bpy.data.images):
        if other!=im and other.users==0:bpy.data.images.remove(other)
    # Export coherent assembly, with original textures packed, before rendering.
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    target=a.out/'glb/f78r_layered_assembly.glb'
    bpy.ops.export_scene.gltf(filepath=str(target.resolve()),export_format='GLB',use_selection=True,export_extras=True,export_image_format='AUTO')
    exported=check_glb(target,digest)
    # Full-resolution checks include edges and missing pixels, not just an inset.
    checks=[]
    for g,o in ORIGINS.items():
        w,h=o[2]-o[0],o[3]-o[1]
        for ob in obs:ob.hide_render=ob.name not in [r['id'] for r in records if (g in r['id'])]
        s.camera.location=((o[0]+o[2])/2000,-8,-(o[1]+o[3])/2000);s.camera.rotation_euler=(math.pi/2,0,0);s.camera.data.type='ORTHO';s.camera.data.ortho_scale=max(w,h)/1000
        s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str((a.out/'renders'/(g+'_front.png')).resolve());bpy.ops.render.render(write_still=True)
        rendered=np.array(Image.open(s.render.filepath));expected=rgb[o[1]:o[3],o[0]:o[2]]
        footprint=np.array(Image.open(a.out/'masks'/(g+'_assembled.png')))>0
        visible=rendered[:,:,3]>254;inside=cv2.erode(footprint.astype(np.uint8),np.ones((5,5),np.uint8))>0
        err=np.abs(rendered[:,:,:3].astype(float)-expected.astype(float))
        checks.append({'group':g,'interior_pixels':int((inside&visible).sum()),'mean_abs_rgb_error':float(err[inside&visible].mean()),'max_abs_rgb_error':float(err[inside&visible].max()),'missing_mask_pixels':int((footprint&~visible).sum()),'excess_mask_pixels':int((~footprint&visible).sum()),'scope':'orthographic source-view including reported silhouette errors; masks themselves remain unverified'})
        # Display source and reconstruction side by side; never composite source
        # under the render because that would conceal holes or missing parts.
        plate=Image.new('RGB',(w*2,h),(38,42,48));plate.paste(Image.fromarray(expected),(0,0));plate.paste(Image.fromarray(rendered), (w,0),Image.fromarray(rendered[:,:,3]));plate.save(a.out/'renders'/(g+'_source_vs_model.png'))
    for ob in obs:ob.hide_render=False
    s.camera.location=(1.397,-8,-1.88);s.camera.rotation_euler=(math.pi/2,0,0);s.camera.data.ortho_scale=4.1
    s.render.resolution_x=1000;s.render.resolution_y=1400;s.render.filepath=str((a.out/'renders/f78r_front.png').resolve());bpy.ops.render.render(write_still=True)
    s.camera.location=(3.5,-6,-.1);targetpt=Vector((1.397,0,-1.88));s.camera.rotation_euler=(targetpt-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=4.4
    s.render.filepath=str((a.out/'renders/f78r_oblique.png').resolve());bpy.ops.render.render(write_still=True)
    s['fidelity_status']='source-colored draft geometry; no 1:1 certification';s['figure_count']=15;s['unobserved_surfaces']='neutral';s['depth_assumptions']='separate rounded bodies, thin water slab, thick rim; not measurable from scan'
    bpy.ops.wm.save_as_mainfile(filepath=str((a.out/'f78r_Baseny_Postacie_Woda_Obrzeza.blend').resolve()),compress=True)
    report={'source_sha256':digest,'new_individual_figures':15,'new_basin_components':4,'assembly_meshes':len(obs),'records':records,'checks':checks,'glb':exported,'certified_models':0,'full_manuscript_complete':False,'claim_limits':['15 visible person silhouettes; occluded anatomy is not reconstructed','Rim/water boundary is a pigment-based draft partition','Source RGB registration is separate from contour correctness','No physical headset or screen calibration performed']}
    (a.out/'VALIDATION.json').write_text(json.dumps(report,indent=2));print('DONE',json.dumps(checks),flush=True)

if __name__=='__main__':main()
