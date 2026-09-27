import bpy,math
from pathlib import Path
R=Path(__file__).resolve().parent;N=R.parent/'quest-native/assets';bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m
paper=mat('Pergamin_krawedzie',(.75,.64,.43));leather=mat('Oprawa',(.13,.052,.022))
for side,scan in [(-1,'s0003'),(1,'s0004')]:
 x=side*.285
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,.032));o=bpy.context.object;o.name='Okladka_'+scan;o.dimensions=(.59,.80,.022);o.data.materials.append(leather);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,.055));o=bpy.context.object;o.name='Blok_kartek_'+scan;o.dimensions=(.565,.775,.035);o.data.materials.append(paper);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 im=bpy.data.images.load(str(N/'scans'/(scan+'.jpg')));im.pack();m=bpy.data.materials.new('Strona_'+scan);m.use_nodes=True;n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;pr=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(n.outputs['Color'],pr.inputs['Base Color']);pr.inputs['Roughness'].default_value=.95
 vs=[(x-.282,-.385,.08),(x+.282,-.385,.08),(x+.282,.385,.08),(x-.282,.385,.08)]
 me=bpy.data.meshes.new(scan);me.from_pydata(vs,[],[(0,1,2,3)]);me.materials.append(m);uv=me.uv_layers.new()
 for i,u in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[i].uv=u
 o=bpy.data.objects.new('PAGE_'+scan,me);bpy.context.collection.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'architecture/Manuskrypt_otwarty.blend'))
bpy.ops.export_scene.gltf(filepath=str(N/'room/open_book.glb'),export_format='GLB',export_apply=True)
