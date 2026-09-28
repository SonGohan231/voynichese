"""Seven hollow tube candidates with reversible depth assumptions.

Lofted outer wall, annular mouth, inner wall and interpreted blind bottom.
An invertible 2D warp registers the projected outline to the traced source.
Depth is not inferred from pigment brightness. No image is generated.
"""
import argparse, hashlib, json, math
from pathlib import Path
import bpy, bmesh, numpy as np
from PIL import Image
from mathutils import Vector
from build_source_volumes import material, render_part, check_glb

HERE=Path(__file__).resolve().parent
# Opening centre, far end centre, radius and foreshortening, in original annotation crop pixels.
FITS={
 '01':((75,105),(199,107),43,.52),
 '02':((269,107),(413,124),52,.55),
 '03':((548,133),(677,148),49,.54),
 '04':((846,210),(957,292),55,.54),
 '05':((1175,280),(1124,390),56,.53),
 '06':((1077,476),(1073,655),64,.53),
 '07':((1090,795),(1096,939),60,.53),
}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--sources',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 out=args.output;out.mkdir(parents=True,exist_ok=True)
 for name in ('glb','renders','masks'):(out/name).mkdir(exist_ok=True)
 source=next(args.sources.glob('0141*.jpg'));rawsha=hashlib.sha256(source.read_bytes()).hexdigest();W,H=Image.open(source).size
 assert rawsha=='6e0f3449af81da50a04a060937fdcdb4c2e2b93be98bcb9b4bd523c1e1b35ce5'
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 sc.render.engine='BLENDER_EEVEE_NEXT';sc.render.resolution_percentage=100;sc.render.image_settings.color_mode='RGBA';sc.eevee.taa_render_samples=1;sc.render.filter_size=.01;sc.render.dither_intensity=0
 sc.world=bpy.data.worlds.new('Neutral');bpy.ops.object.camera_add();sc.camera=bpy.context.object
 img=bpy.data.images.load(str(source.resolve()));img.colorspace_settings.name='sRGB';img.pack()
 frontmat=material('SOURCE_SRGB_UNLIT',img);backmat=material('UNOBSERVED_BACK_NEUTRAL')
 parts=[]
 for name in ('annotations.json','annotations_02.json'):parts+=json.loads((HERE/name).read_text())['parts']
 records=[]
 for part in sorted([p for p in parts if '_tube_' in p['id']],key=lambda p:p['id']):
  num=part['id'][-2:];a,b,R,c=FITS[num];a=np.array(a,float);b=np.array(b,float);length=float(np.linalg.norm(b-a));axis=(b-a)/length;cross=np.array([-axis[1],axis[0]])
  poly=np.array(part['boundary'],float);s_poly=(poly-a)@axis;t_poly=(poly-a)@cross;slo,shi=s_poly.min(),s_poly.max()
  def limits(s):
   hits=[]
   for k in range(len(poly)):
    j=(k+1)%len(poly);u,v=s_poly[k],s_poly[j]
    if min(u,v)<=s<=max(u,v) and abs(v-u)>1e-9:hits.append(t_poly[k]+(s-u)/(v-u)*(t_poly[j]-t_poly[k]))
   if not hits:return 0.,.001
   return (min(hits)+max(hits))/2,max((max(hits)-min(hits))/2,.001)
  def project(l,r,theta):
   # Physical cross section before source registration.
   s=l-c*r*math.sin(theta);t=r*math.cos(theta);y=l*c/math.sqrt(1-c*c)+r*math.sqrt(1-c*c)*math.sin(theta)
   sd=slo+(s+c*R)/(length+2*c*R)*(shi-slo);sd=float(np.clip(sd,slo+.0001,shi-.0001))
   centre,half=limits(sd)
   delta=s if s<0 else s-length if s>length else 0
   env=R*math.sqrt(max(1-(delta/(c*R))**2,1e-10))
   td=centre+t/env*half;xy=a+axis*sd+cross*td+np.array(part['crop'][:2])
   return (float(xy[0]/1000),float(y/1000),float(-xy[1]/1000))
  N=128;K=32;wall=max(5,R*.1);vertices=[];faces=[]
  for radius,end in ((R,length),(R-wall,length-wall)):
   for k in range(K+1):
    for j in range(N):vertices.append(project(end*k/K,radius,2*math.pi*j/N))
  stride=(K+1)*N
  for offset in (0,stride):
   for k in range(K):
    for j in range(N):
     a0=offset+k*N+j;a1=offset+k*N+(j+1)%N;b0=a0+N;b1=a1+N
     faces.append((a0,a1,b1,b0) if offset==0 else (a0,b0,b1,a1))
  for j in range(N):faces.append((j,stride+j,stride+(j+1)%N,(j+1)%N))
  # Distinct inside/outside bottom surfaces close the wall, while the mouth remains a cavity.
  for offset,end in ((0,length),(stride,length-wall)):
   center=len(vertices);vertices.append(project(end,0,0))
   for j in range(N):faces.append((offset+K*N+j,offset+K*N+(j+1)%N,center))
  mesh=bpy.data.meshes.new(part['id']+'_hollow');mesh.from_pydata(vertices,[],faces);mesh.update();mesh.materials.append(frontmat);mesh.materials.append(backmat)
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));nonmanifold=sum(not e.is_manifold for e in bm.edges);volume=abs(bm.calc_volume(signed=True));bm.to_mesh(mesh);bm.free()
  assert nonmanifold==0 and volume>0
  uv=mesh.uv_layers.new(name='NativeSourceProjection')
  for f in mesh.polygons:
   f.material_index=0 if f.normal.y<1e-7 else 1;f.use_smooth=True
   for li in f.loop_indices:
    co=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(co.x*1000/W,1+co.z*1000/H)
  obj=bpy.data.objects.new(part['id'],mesh);bpy.context.collection.objects.link(obj)
  # Tight crop and source-view centre, identical coordinate system to the earlier fragments.
  pmin=poly.min(axis=0).astype(int)-10;pmax=poly.max(axis=0).astype(int)+11;old=part['crop'];part['crop']=[old[0]+int(pmin[0]),old[1]+int(pmin[1]),old[0]+int(pmax[0]),old[1]+int(pmax[1])]
  x0,y0,x1,y1=part['crop'];obj.location=(-(x0+x1)/2000,0,(y0+y1)/2000)
  import cv2
  mask=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillPoly(mask,[np.rint(poly-pmin).astype(np.int32)],255);Image.fromarray(mask).save(out/'masks'/(part['id']+'.png'))
  obj['source_scan']='s0141';obj['folio']='78r';obj['source_sha256']=rawsha;obj['status']='DRAFT_HOLLOW_VOLUME';obj['depth_assumption']='foreshortened circular section, inferred blind bottom and wall thickness; not confirmed by manuscript';obj['contour_review']='manual trace, not certified'
  bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
  target=out/'glb'/(part['id']+'.glb');bpy.ops.export_scene.gltf(filepath=str(target.resolve()),export_format='GLB',use_selection=True,export_extras=True,export_image_format='AUTO')
  rec={'id':part['id'],'scan':'s0141','folio':'78r','crop':part['crop'],'source_sha256':rawsha,'vertices':len(vertices),'triangles':sum(len(f)-2 for f in faces),'non_manifold_edges':nonmanifold,'volume_m3':volume,'status':'DRAFT_HOLLOW_VOLUME','glb':check_glb(target,rawsha),'front_color_check':render_part(obj,part,sc,out,source),'depth_assumption':obj['depth_assumption']}
  records.append(rec);(out/'PROGRESS.json').write_text(json.dumps({'models':records,'completed_hollow_candidates':len(records),'certified_1_to_1':0},indent=2))
  bpy.ops.wm.save_as_mainfile(filepath=str((out/'Tuleje_7_Wnetrza.blend').resolve()),compress=True);print('HOLLOW',part['id'],rec['front_color_check'],flush=True)
 for i,obj in enumerate(o for o in bpy.data.objects if o.type=='MESH'):obj.hide_render=False;obj.location.x+=(i%4)*.35;obj.location.z-=(i//4)*.4
 bpy.ops.wm.save_as_mainfile(filepath=str((out/'Tuleje_7_Wnetrza.blend').resolve()),compress=True)

if __name__=='__main__':main()
