from pathlib import Path
p=Path('quest-native/scripts/workroom.gd');s=p.read_text()
s=s.replace('var drawing := false','var tarot: Node3D\nvar gallery: Node3D\nvar drawing := false')
s=s.replace('"Obserwatorium"]','"Obserwatorium", "Naczynia"]')
s=s.replace('\t_build_room()\n\t_refresh_menu()\n\t_choose(0)', '\ttarot = load("res://scripts/tarot_table.gd").new(); add_child(tarot); tarot.setup(self)\n\tgallery = Node3D.new(); gallery.name = "GaleriaZrodel"; add_child(gallery)\n\t_build_gallery()\n\t_build_room()\n\t_refresh_menu()\n\t_choose(0)',1)
start=s.index('func _build_room():');end=s.index('\nfunc _refresh_menu',start)
s=s[:start]+'''func _build_room():
	for child in room.get_children(): room.remove_child(child); child.queue_free()
	var archive := room_index == 0 or room_index == 5
	if archive and ResourceLoader.exists("res://assets/room/archive.glb"):
		room.add_child(load("res://assets/room/archive.glb").instantiate())
	else:
		var colors := [Color("263548"), Color("28443a"), Color("263f50"), Color("392f48"), Color("18253d")]
		box(room, Vector3(0, -0.06, -1), Vector3(14, 0.1, 14), colors[mini(room_index,4)])
		box(room, Vector3(0, 1.65, -5), Vector3(14, 3.4, 0.1), colors[mini(room_index,4)].darkened(0.35))
		box(room, Vector3(0, .82, -1.9), Vector3(2.3,.08,1.1), Color("6b5240"))
		var title := label(room_names[room_index].to_upper(), 56); title.position = Vector3(0, 2.5, -4.85); room.add_child(title)
	room.visible = not passthrough
	if tarot:
		tarot.visible = archive
		for body in tarot.find_children("*","StaticBody3D",true,false): body.collision_layer = 1 if archive else 0
	if gallery:
		gallery.visible = archive
		for body in gallery.find_children("*","StaticBody3D",true,false): body.collision_layer = 1 if archive else 0

func switch_room(index: int, move := true):
	_release_all(); room_index = clampi(index,0,room_names.size()-1); _build_room()
	if move:
		origin.position = Vector3(10 if room_index==5 else 0,0,0); origin.rotation.y = 0
		place_menu()
	_refresh_menu(); save_workspace()

func _build_gallery():
	var vessels: Array = catalog.filter(func(c):return c.get("id", "").begins_with("vessel_"))
	for i in range(vessels.size()):
		var meta: Dictionary=vessels[i]
		var object = load(meta.model).instantiate(); gallery.add_child(object); _normalize(object,.98)
		object.position += Vector3(6.15+float(i%5)*1.75,.99,-4.48 if i<5 else 2.4)
		_add_gallery_colliders(object,meta)
		var caption := label("f"+meta.folio+" · "+str(i+1),22); caption.position=Vector3(6.15+float(i%5)*1.75,1.01,-3.91 if i<5 else 3.11); gallery.add_child(caption)
	for i in range(3):
		var scan: String=["s0161","s0163","s0175"][i]
		var t = load("res://assets/scans/"+scan+".jpg"); var q:=QuadMesh.new();q.size=Vector2(minf(1.9,1.96*float(t.get_width())/t.get_height()),1.96)
		var n:=MeshInstance3D.new();n.mesh=q;var m:=material(Color.WHITE,true);m.albedo_texture=t;n.material_override=m;n.position=Vector3(7.4+i*2.6,2.25,-5.67);gallery.add_child(n)
		var src: Dictionary=catalog.filter(func(c):return c.scan==scan)[0];_gallery_body(n,n.get_aabb(),src)
	var book=load("res://assets/room/codex.glb").instantiate();gallery.add_child(book);_normalize(book,1.10);book.position+=Vector3(0,1.08,-2.12)
	_add_gallery_colliders(book,{"scan":"codex","folio":"kodeks · 206 skanów","category":"Kodeks","model":"res://assets/room/codex.glb"})

func _gallery_body(mesh: MeshInstance3D, bounds: AABB, meta: Dictionary):
	var body:=StaticBody3D.new();body.collision_layer=1;body.collision_mask=0;body.set_meta("gallery_source",meta);mesh.add_child(body)
	var shape:=BoxShape3D.new();shape.size=bounds.size.max(Vector3(.008,.008,.008));var collision:=CollisionShape3D.new();collision.shape=shape;collision.position=bounds.get_center();body.add_child(collision)

func _add_gallery_colliders(root: Node3D, meta: Dictionary):
	for mesh in root.find_children("*","MeshInstance3D",true,false):
		_gallery_body(mesh,mesh.get_aabb(),meta)

func _take_gallery(body, hand: int):
	if exhibits.find_children("*","Node3D",true,false).filter(func(n):return n.has_meta("source")).size()>=LIMIT: say("Limit 12 modeli roboczych");return
	checkpoint();var meta: Dictionary=body.get_meta("gallery_source");var object:=_new_exhibit(meta,load(meta.model))
	object.global_position=body.global_position
	selected=object;_grab(object,hand);say("Kopia do pracy · f"+meta.folio)
''' +s[end:]
s=s.replace('var tabs := ["Katalog", "Obiekt", "Badania", "Pokoje"]\n\tfor j in range(4)', 'var tabs := ["Katalog", "Obiekt", "Badania", "Pokoje", "Tarot"]\n\tfor j in range(tabs.size())')
s=s.replace('0.43 - (j / 2) * 0.14','0.57 - (j / 2) * 0.14')
s=s.replace('title.position.y = 0.62','title.position.y = 0.78')
s=s.replace('\t\t"Pokoje":','\t\t"Tarot":\n\t\t\tactions = tarot.menu_actions()\n\t\t"Pokoje":')
s=s.replace('func(): room_index = index; _build_room(); _refresh_menu(); save_workspace()', 'func(): switch_room(index)')
s=s.replace('root.position = Vector3(0, 1.0, -1.35); selected = root; save_workspace()', 'root.global_position = camera.global_position - camera.global_basis.z * 1.0 - Vector3(0,.5,0); selected = root; save_workspace()')
s=s.replace('\t\t\tif b and b.has_meta("exhibit"):', '''			if b and b.has_meta("tarot"):
				var card: Node3D=b.get_meta("tarot");hover_label.text=tarot.by_id[card.get_meta("tarot_card")].name
				hover_label.global_position=rays[i].get_collision_point()+Vector3(0,.13,0);hover_label.visible=true;return
			if b and b.has_meta("gallery_source"):
				hover_label.text="f"+b.get_meta("gallery_source").folio+" · chwyt: kopia do pracy"
				hover_label.global_position=rays[i].get_collision_point()+Vector3(0,.16,0);hover_label.visible=true;return
			if b and b.has_meta("exhibit"):''')
s=s.replace('\t\tif body and body.has_meta("exhibit"):', '''		if body and body.has_meta("tarot"):
			selected=body.get_meta("tarot");_grab(selected,hand);return
		if body and body.has_meta("gallery_source"):_take_gallery(body,hand);return
		if body and body.has_meta("exhibit"):''')
s=s.replace('func _select_body(body):\n', '''func _select_body(body):
	if body.has_meta("tarot"):
		selected=body.get_meta("tarot");tarot.selected_card=selected;say(tarot.by_id[selected.get_meta("tarot_card")].name);return
	if body.has_meta("gallery_source"):
		var src: Dictionary=body.get_meta("gallery_source")
		if src.scan!="codex":_show_scan(src.scan)
		say("f"+src.folio+" · naciśnij chwyt, aby wziąć kopię");return
''')
s=s.replace('checkpoint(); hands[hand] = {"node":node, "parent":node.get_parent()}; node.reparent(controllers[hand], true)', 'checkpoint(); hands[hand] = {"node":node, "parent":node.get_parent()}\n\tif node.has_meta("tarot_card"): tarot.begin_grab(node)\n\tnode.reparent(controllers[hand], true)')
s=s.replace('\tif is_instance_valid(info.node) and is_instance_valid(info.parent): info.node.reparent(info.parent, true)', '\tif is_instance_valid(info.node) and is_instance_valid(info.parent):\n\t\tinfo.node.reparent(info.parent, true)\n\t\tif info.node.has_meta("tarot_card"):tarot.finish_grab(info.node)')
s=s.replace('func rotate_selection(axis: Vector3, radians: float):\n', 'func rotate_selection(axis: Vector3, radians: float):\n\tif is_instance_valid(selected) and selected.has_meta("tarot_card"):\n\t\ttarot.selected_card=selected;tarot.reverse_selected();return\n')
s=s.replace('func scale_selection(factor: float):\n', 'func scale_selection(factor: float):\n\tif is_instance_valid(selected) and selected.has_meta("tarot_card"):return\n')
s=s.replace('func detach_selected():\n', 'func detach_selected():\n\tif is_instance_valid(selected) and selected.has_meta("tarot_card"):say("Karty przenosisz chwytem jako całość");return\n')
s=s.replace('func pin_selection():\n', 'func pin_selection():\n\tif is_instance_valid(selected) and selected.has_meta("tarot_card"):return\n')
s=s.replace('func join_selected():\n', 'func join_selected():\n\tif is_instance_valid(selected) and selected.has_meta("tarot_card"):return\n')
s=s.replace('"version":1,"room":room_index,"models":data', '"version":1,"room":room_index,"tarot":tarot.data() if tarot else {},"models":data')
s=s.replace('var matches := catalog.filter(func(m): return m.scan == scan)', 'var matches := catalog.filter(func(m): return m.get("id",m.scan)==source.get("id",scan))')
s=s.replace('\tall_strokes = data.get("strokes", []); _restore_strokes()', '\tif tarot:tarot.restore(data.get("tarot",{}))\n\tall_strokes = data.get("strokes", []); _restore_strokes()')
s=s.replace('drawing_anchor = selected if is_instance_valid(selected) else exhibits', 'drawing_anchor = selected if is_instance_valid(selected) and not selected.has_meta("tarot_card") else exhibits')
# Constrain joystick travel to the two rooms and doorway, while physical headset movement stays untouched.
s=s.replace('\t\t\torigin.position += (camera.global_basis.x * joy.x + forward * joy.y) * dt * 1.1', '''			var previous:=origin.position
			origin.position += (camera.global_basis.x * joy.x + forward * joy.y) * dt * 1.1
			if room_index==0 or room_index==5:
				origin.position.x=clampf(origin.position.x,-4.5,14.5);origin.position.z=clampf(origin.position.z,-5.4,3.4)
				if absf(origin.position.x-5)<.4 and (origin.position.z < -2.35 or origin.position.z > .05):origin.position=previous''')
p.write_text(s)
