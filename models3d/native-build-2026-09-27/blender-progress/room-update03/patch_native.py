from pathlib import Path
R=Path(__file__).resolve().parent.parent;f=R/'quest-native/scripts/workroom.gd';s=f.read_text()
s=s.replace('var tarot: Node3D','var compound: Node3D\nvar probe: Node3D\nvar fade: Node3D\nvar teleporting:=false\nvar tarot: Node3D')
s=s.replace('\t_build_gallery()\n\t_build_room()', '\t_build_gallery()\n\tfade=load("res://addons/godot-xr-tools/effects/fade.tscn").instantiate();camera.add_child(fade)\n\tprobe=load("res://scripts/color_probe.gd").new();add_child(probe);probe.setup(self)\n\tcompound=load("res://scripts/compound.gd").new();add_child(compound);compound.setup(self)\n\t_build_room()')
a=s.index('func _build_room():');b=s.index('func _build_gallery():',a)
s=s[:a]+'''func _build_room():
	if room.get_child_count()==0:room.add_child(load("res://assets/room/compound.glb").instantiate())
	room.visible=not passthrough
	_position_workspace()

func _position_workspace():
	var pos:Vector3=compound.SPAWNS[room_index] if compound else Vector3.ZERO
	heading.position=pos+Vector3(0,2.4,-2.5);status.position=pos+Vector3(0,.82,-1.3);scan_panel.position=pos+Vector3(1.5,1.65,-1.7);preview.position=pos
	if compound and compound.active_zone!=room_index:compound.refresh_zone(room_index)

func switch_room(index:int,move:=true):
	if teleporting:return
	_release_all();room_index=clampi(index,0,room_names.size()-1)
	if move:
		teleporting=true
		var tween=create_tween();tween.tween_method(func(alpha):fade.set_fade_level(self,Color(0,0,0,alpha)),0.0,1.0,.12)
		await tween.finished
		var head_offset:=camera.position.rotated(Vector3.UP,origin.rotation.y);origin.rotation.y=0
		origin.position=compound.SPAWNS[room_index]-Vector3(camera.position.x,0,camera.position.z)
		place_menu()
		var incoming=create_tween();incoming.tween_method(func(alpha):fade.set_fade_level(self,Color(0,0,0,alpha)),1.0,0.0,.16)
		await incoming.finished;teleporting=false
	_build_room();_refresh_menu();save_workspace()

''' + s[b:]
s=s.replace('["Katalog", "Obiekt", "Badania", "Pokoje", "Tarot"]','["Katalog", "Obiekt", "Badania", "Pokoje", "Tarot", "Kolory"]')
s=s.replace('\t\t"Tarot":\n', '\t\t"Kolory":\n\t\t\tactions=probe.menu_actions()\n\t\t"Tarot":\n')
s=s.replace('\t\t\tactions.append(["Zapisz układ", save_workspace])', '\t\t\tactions.append(["◀ Wystawa",func():compound.change_page(-1)])\n\t\t\tactions.append(["Wystawa ▶",func():compound.change_page(1)])\n\t\t\tactions.append(["Zapisz układ", save_workspace])')
a=s.index('\t\t\tif room_index==0 or room_index==5:');b=s.index('\t\tvar turn :=',a)
s=s[:a]+'''\t\t\tif not compound.walkable(camera.global_position):origin.position=previous
''' + s[b:]
s=s.replace('if joy.length() > 0.2 and not hands[0]:','if joy.length() > 0.2 and not hands[0] and not teleporting:')
s=s.replace('if rays[hand].is_colliding(): _select_body(rays[hand].get_collider())','if rays[hand].is_colliding():\n\t\t\tif rays[hand].get_collider().has_meta("color_probe"):probe.sample_at(rays[hand].get_collision_point())\n\t\t\telse:_select_body(rays[hand].get_collider())')
s=s.replace('\t\t\tif b and b.has_meta("tarot"):', '\t\t\tif b and b.has_meta("color_probe"):\n\t\t\t\thover_label.text="Spust: próbka "+("A" if probe.target==0 else "B");hover_label.global_position=rays[i].get_collision_point()+Vector3(0,.1,0);hover_label.visible=true;return\n\t\t\tif b and b.has_meta("tarot"):')
s=s.replace('\tif room_index==5:origin.position.x=10;place_menu()','\torigin.position=compound.SPAWNS[room_index];place_menu()')
f.write_text(s)
p=R/'quest-native/scripts/color_probe.gd';s=p.read_text().replace('func update_text():\n','func update_text():\n\tif not pixels:return\n');p.write_text(s)
p=R/'quest-native/export_presets.cfg';s=p.read_text().replace('version/code=2','version/code=3').replace('version/name="0.2.0"','version/name="0.3.0"').replace('include_filter="assets/*.json"','include_filter="assets/*.json,assets/source_pixels/*.jpgbin,third_party/*.txt"');p.write_text(s)
p=R/'toolchain/export_native.py';s=p.read_text().replace('0.2.0','0.3.0');p.write_text(s)
