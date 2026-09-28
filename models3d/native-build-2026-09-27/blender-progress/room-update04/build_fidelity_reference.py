"""Blender source-comparison workbench, not ten claimed 3D reconstructions.

Original scan bytes are SHA-checked and packed unchanged. UVs use native pixels.
Each rectangular reference fragment is independently selectable. No root, vessel,
depth, hidden side, pigment or text is invented. Geometry modelling must be done
against these references and independently reviewed before replacing a VR model.
Run with Blender 4.5 Python: script.py --sources DIR --output DIR --pages pages.json
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    a = argparse.ArgumentParser()
    a.add_argument('--sources', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    a.add_argument('--pages', type=Path, required=True)
    args = a.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pages = {p['id']: p for p in json.loads(args.pages.read_text())}
    # Source regions specified in native full-scan pixel coordinates (x0,y0,x1,y1).
    parts = [
        ('s0004', 'f1v — podstawa rośliny', [490,2880,2310,3610]),
        ('s0005', 'f2r — czerwony korzeń', [1120,3200,2010,3640]),
        ('s0141', 'f78r — górny basen', [1190,1210,2280,2020]),
        ('s0141', 'f78r — dolny basen', [1130,2500,2240,3430]),
        ('s0141', 'f78r — lewa struktura', [60,85,480,510]),
        ('s0141', 'f78r — prawa struktura', [1910,150,2430,525]),
        ('s0141', 'f78r — górne połączenia', [430,310,2000,1260]),
        ('s0135', 'f75r — górna struktura', [555,155,1810,970]),
        ('s0135', 'f75r — środkowy przepływ', [890,870,1960,2140]),
        ('s0135', 'f75r — dolny basen', [1510,2080,2640,3220]),
    ]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    images, materials, records = {}, {}, []
    def emissive(name, color):
        m = bpy.data.materials.new(name); m.use_nodes = True
        ns=m.node_tree.nodes; ns.clear()
        e=ns.new('ShaderNodeEmission'); e.inputs['Color'].default_value=color
        out=ns.new('ShaderNodeOutputMaterial'); m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
        return m,e
    textmat,_=emissive('Neutralne_etykiety',(0.82,0.9,0.96,1))
    for i,(scan,title,bbox) in enumerate(parts):
        p=pages[scan]; source=args.sources/(scan+'.jpgbin')
        assert hashlib.sha256(source.read_bytes()).hexdigest()==p['sha256'],scan
        if scan not in images:
            im=bpy.data.images.load(str(source.resolve()),check_existing=True); im.name=scan+'_ORIGINAL_SHA256'; im.pack(); images[scan]=im
            m,e=emissive(scan+'_OriginalColor',(1,1,1,1))
            tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=im
            m.node_tree.links.new(tex.outputs['Color'],e.inputs['Color']); materials[scan]=m
        x0,y0,x1,y1=bbox; assert 0<=x0<x1<=p['width'] and 0<=y0<y1<=p['height']
        ratio=(x1-x0)/(y1-y0); w=min(2.7,1.55*ratio); h=w/ratio
        center=Vector(((i%2-.5)*3.35,0,(4-i//2)*2.05))
        vs=[(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)]
        mesh=bpy.data.meshes.new('NativePixelReference'); mesh.from_pydata(vs,[],[(0,1,2,3)]); mesh.materials.append(materials[scan])
        uv=mesh.uv_layers.new(); coords=[(x0/p['width'],1-y1/p['height']),(x1/p['width'],1-y1/p['height']),(x1/p['width'],1-y0/p['height']),(x0/p['width'],1-y0/p['height'])]
        for j,co in enumerate(coords): uv.data[j].uv=co
        obj=bpy.data.objects.new(f'REF_{i+1:02}_{scan}',mesh); bpy.context.collection.objects.link(obj); obj.location=center
        obj['source_scan']=scan; obj['source_sha256']=p['sha256']; obj['native_bbox']=bbox
        obj['status']='source_reference_only_not_a_reconstructed_object'; obj['depth_claim']='none'
        bpy.ops.object.text_add(location=center+Vector((-w/2,-.025,-h/2-.16)),rotation=(math.pi/2,0,0))
        text=bpy.context.object; text.data.body=title; text.data.size=.10; text.data.materials.append(textmat)
        records.append({'id':obj.name,'scan':scan,'folio':p['label'],'sha256':p['sha256'],'bbox_xyxy':bbox,'status':obj['status']})
    bpy.ops.object.camera_add(location=(0,-15,4.1))
    camera=bpy.context.object; camera.rotation_euler=(Vector((0,0,4.1))-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.type='ORTHO'; camera.data.ortho_scale=10.5; scene.camera=camera
    scene.render.engine='BLENDER_EEVEE_NEXT'; scene.render.resolution_x=1200; scene.render.resolution_y=1800; scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('NeutralBackground'); scene.world.color=(.04,.04,.04)
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output/'Wzorce_10_fragmentow.blend').resolve()),compress=True)
    (args.output/'WZORCE.json').write_text(json.dumps({'verified_3d_reconstructions':0,'source_references':records},ensure_ascii=False,indent=2))
    scene.render.filepath=str((args.output/'wzorce.png').resolve()); bpy.ops.render.render(write_still=True)
    print('Saved 10 source references; no new verified 3D reconstruction claimed.')

if __name__=='__main__': main()
