extends Node3D
## Native OpenXR workbench. All objects stay at the pose chosen by the researcher.

const SAVE := "user://workspace.json"
const LIMIT := 12
var catalog: Array = []
var pages: Array = []
var filtered: Array = []
var categories: Array = ["Wszystkie"]
var category_index := 0
var cursor := 0
var page_cursor := 3
var mode := "Katalog"
var pieces_mode := false
var selected: Node3D
var pinned: Node3D
var exhibits: Node3D
var preview: Node3D
var room: Node3D
var menu: Node3D
var scan_panel: MeshInstance3D
var heading: Label3D
var status: Label3D
var hover_label: Label3D
var origin: XROrigin3D
var camera: XRCamera3D
var controllers: Array[XRController3D] = []
var rays: Array[RayCast3D] = []
var hands: Array = [null, null]
var xr: XRInterface
var environment: Environment
var passthrough := false
var loading := false
var pending_path := ""
var pending_meta: Dictionary = {}
var pending_target := "preview"
var turn_lock := false
var elapsed_save := 0.0
var counter := 0
var undo_stack: Array = []
var recording := false
var record_effect: AudioEffectRecord
var microphone: AudioStreamPlayer
var note_dir := ""
var record_time := 0.0
var note_busy := false
var room_index := 0
var room_names := ["Pracownia", "Ogród", "Hydraulika", "Diagramy", "Obserwatorium"]
var drawing := false
var stroke: Array[Vector3] = []
var stroke_node: MeshInstance3D
var drawing_anchor: Node3D
var all_strokes: Array = []
var note_camera: Camera3D
var note_view: SubViewport

func _ready():
	catalog = JSON.parse_string(FileAccess.get_file_as_string("res://assets/catalog.json"))
	pages = JSON.parse_string(FileAccess.get_file_as_string("res://assets/pages.json"))
	for m in catalog:
		if not categories.has(m.category): categories.append(m.category)
	filtered = catalog.duplicate()
	exhibits = Node3D.new(); exhibits.name = "TwojUklad"; add_child(exhibits)
	preview = Node3D.new(); preview.name = "Podglad"; add_child(preview)
	room = Node3D.new(); room.name = "Pomieszczenie"; add_child(room)
	origin = XROrigin3D.new(); add_child(origin)
	camera = XRCamera3D.new(); camera.near = 0.04; camera.far = 80.0; origin.add_child(camera)
	xr = XRServer.find_interface("OpenXR")
	if xr and xr.is_initialized():
		get_viewport().use_xr = true
		xr.session_stopping.connect(_suspend)
		xr.session_focussed.connect(func(): set_process(true))
	else:
		camera.position = Vector3(0, 1.65, 1.7)
		camera.current = true
	for i in range(2):
		var c := XRController3D.new(); c.tracker = "left_hand" if i == 0 else "right_hand"; c.pose = "aim"
		origin.add_child(c); controllers.append(c)
		var ray := RayCast3D.new(); ray.target_position = Vector3(0, 0, -7); ray.collision_mask = 3; c.add_child(ray); rays.append(ray)
		var beam := MeshInstance3D.new(); var bm := CylinderMesh.new(); bm.top_radius = 0.002; bm.bottom_radius = 0.002; bm.height = 2.4
		beam.mesh = bm; beam.rotation.x = PI / 2; beam.position.z = -1.2; beam.material_override = material(Color("72d9ec"), true); c.add_child(beam)
		c.button_pressed.connect(func(action): _button(action, i))
		c.button_released.connect(func(action): _release_button(action, i))
	var world := WorldEnvironment.new(); environment = Environment.new(); world.environment = environment; add_child(world)
	environment.background_mode = Environment.BG_COLOR; environment.background_color = Color("111c2c")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; environment.ambient_light_color = Color("c5d8ef"); environment.ambient_light_energy = 0.7
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-45, -25, 0); sun.light_energy = 1.3; sun.shadow_enabled = false; add_child(sun)
	menu = Node3D.new(); menu.position = Vector3(-1.65, 1.5, -1.5); menu.rotation.y = 0.22; add_child(menu)
	heading = label("Manuskrypt VR", 30); heading.position = Vector3(0, 2.4, -2.5); add_child(heading)
	status = label("", 21); status.position = Vector3(0, 0.82, -1.3); add_child(status)
	hover_label = label("", 24); hover_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED; hover_label.no_depth_test = true; add_child(hover_label)
	scan_panel = MeshInstance3D.new(); var quad := QuadMesh.new(); quad.size = Vector2(0.72, 1.0); scan_panel.mesh = quad; scan_panel.position = Vector3(1.5, 1.65, -1.7); scan_panel.rotation.y = -0.18; add_child(scan_panel)
	_setup_notebook()
	_build_room()
	_refresh_menu()
	_choose(0)
	if FileAccess.file_exists(SAVE): restore_workspace(JSON.parse_string(FileAccess.get_file_as_string(SAVE)))
	say("Spust: wybierz · chwyt: podnieś · A/X: 180° · B/Y: panel")
	if "--smoke" in OS.get_cmdline_user_args(): _smoke()
	if "--capture" in OS.get_cmdline_user_args(): _capture_test()

func material(color: Color, unshaded := false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new(); m.albedo_color = color; m.roughness = 0.8
	if unshaded: m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return m

func label(text: String, size := 22) -> Label3D:
	var l := Label3D.new(); l.text = text; l.font_size = size; l.pixel_size = 0.0018; l.outline_size = 6; l.modulate = Color("edf4fc"); l.outline_modulate = Color("111c2c"); return l

func box(parent: Node3D, pos: Vector3, size: Vector3, color: Color) -> MeshInstance3D:
	var n := MeshInstance3D.new(); var m := BoxMesh.new(); m.size = size; n.mesh = m; n.material_override = material(color); n.position = pos; parent.add_child(n); return n

func say(text: String):
	status.text = text

func _build_room():
	for child in room.get_children(): child.queue_free()
	var colors := [Color("263548"), Color("28443a"), Color("263f50"), Color("392f48"), Color("18253d")]
	box(room, Vector3(0, -0.06, -1), Vector3(14, 0.1, 14), colors[room_index])
	box(room, Vector3(0, 1.65, -5), Vector3(14, 3.4, 0.1), colors[room_index].darkened(0.35))
	box(room, Vector3(0, 0.82, -1.9), Vector3(2.3, 0.08, 1.1), Color("6b5240"))
	for x in [-1.0, 1.0]:
		for z in [-2.35, -1.45]: box(room, Vector3(x, 0.4, z), Vector3(0.08, 0.8, 0.08), Color("332c29"))
	var title := label(room_names[room_index].to_upper(), 56); title.position = Vector3(0, 2.5, -4.85); room.add_child(title)
	if ResourceLoader.exists("res://assets/room/room.glb"):
		var props = load("res://assets/room/room.glb").instantiate(); room.add_child(props)
	room.visible = not passthrough

func _refresh_menu():
	for n in menu.get_children(): menu.remove_child(n); n.queue_free()
	var title := label(mode + " · " + room_names[room_index], 28); title.position.y = 0.62; menu.add_child(title)
	var tabs := ["Katalog", "Obiekt", "Badania", "Pokoje"]
	for j in range(4): _menu_button(tabs[j], Vector3((j % 2 - 0.5) * 0.52, 0.43 - (j / 2) * 0.14, 0), func(): mode = tabs[j]; _refresh_menu())
	var actions: Array = []
	match mode:
		"Katalog":
			actions = [["◀ Model", func(): _choose(-1)], ["Model ▶", func(): _choose(1)], ["Kategoria", _cycle_category], ["Dodaj model", _add_preview], ["◀ Strona", func(): _choose_page(-1)], ["Strona ▶", func(): _choose_page(1)], ["Wyjmij stronę", _add_page], ["Cały kodeks", _add_book], ["Zapisz układ", save_workspace], ["Cofnij", undo]]
		"Obiekt":
			actions = [["Części" if not pieces_mode else "Cały model", func(): pieces_mode = not pieces_mode; _refresh_menu()], ["Obrót 180°", func(): rotate_selection(Vector3.UP, PI)], ["X +15°", func(): rotate_selection(Vector3.RIGHT, PI/12)], ["Y +15°", func(): rotate_selection(Vector3.UP, PI/12)], ["Z +15°", func(): rotate_selection(Vector3.BACK, PI/12)], ["Większy ×1.1", func(): scale_selection(1.1)], ["Mniejszy ÷1.1", func(): scale_selection(1.0/1.1)], ["Oddziel część", detach_selected], ["Przypnij bazę", pin_selection], ["Połącz z bazą", join_selected], ["Cofnij", undo], ["Zapisz układ", save_workspace]]
		"Badania":
			actions = [["Zakończ głos" if recording else "Zdjęcie + głos", toggle_recording], ["Zrób zdjęcie", take_note], ["Pióro: WŁ" if drawing else "Pióro: WYŁ", func(): drawing = not drawing; _refresh_menu()], ["Zapisz szkic", take_note], ["VR / otoczenie", toggle_passthrough], ["Własny widok", place_menu], ["Otwórz atlas", open_atlas], ["Notatki: folder", func(): say("Notatki lokalnie: Android/data/pl.manuskrypt.quest/files/notes")]]
		"Pokoje":
			for i in range(room_names.size()):
				var index := i
				actions.append([room_names[i], func(): room_index = index; _build_room(); _refresh_menu(); save_workspace()])
			actions.append(["Zapisz układ", save_workspace])
	for i in range(actions.size()):
		_menu_button(actions[i][0], Vector3((i % 2 - 0.5) * 0.52, 0.06 - (i / 2) * 0.145, 0), actions[i][1])

func _menu_button(text: String, pos: Vector3, callback: Callable):
	var body := StaticBody3D.new(); body.collision_layer = 2; body.collision_mask = 0; body.position = pos; body.set_meta("action", callback); menu.add_child(body)
	box(body, Vector3.ZERO, Vector3(0.49, 0.12, 0.025), Color("22394e"))
	var shape := CollisionShape3D.new(); var b := BoxShape3D.new(); b.size = Vector3(0.49, 0.12, 0.04); shape.shape = b; body.add_child(shape)
	var l := label(text, 21); l.position.z = 0.025; body.add_child(l)

func _cycle_category():
	category_index = (category_index + 1) % categories.size()
	filtered = catalog.filter(func(m): return category_index == 0 or m.category == categories[category_index])
	cursor = 0; _choose(0)

func _choose(delta: int):
	if loading: return
	cursor = posmod(cursor + delta, filtered.size())
	var meta: Dictionary = filtered[cursor]
	heading.text = "f" + meta.folio + " · " + meta.category + " · %d/%d" % [cursor + 1, filtered.size()]
	_show_scan(meta.scan)
	for i in range(pages.size()):
		if pages[i].id == meta.scan: page_cursor = i; break
	_request_model(meta, "preview")

func _show_scan(scan: String):
	var tex = load("res://assets/scans/" + scan + ".jpg")
	var m := material(Color.WHITE, true); m.albedo_texture = tex; m.cull_mode = BaseMaterial3D.CULL_DISABLED; scan_panel.material_override = m
	var aspect: float = float(tex.get_width()) / tex.get_height()
	scan_panel.mesh.size = Vector2(minf(aspect, 1.4), minf(1.0, 1.4/aspect))

func _choose_page(delta: int):
	page_cursor = posmod(page_cursor + delta, pages.size()); var p: Dictionary = pages[page_cursor]
	_show_scan(p.id); heading.text = "Strona " + p.label + " · %d/206" % (page_cursor + 1)

func _request_model(meta: Dictionary, target: String):
	if loading: return
	loading = true; pending_path = meta.model; pending_meta = meta; pending_target = target
	var err := ResourceLoader.load_threaded_request(pending_path)
	if err != OK: loading = false; say("Nie udało się wczytać " + meta.scan)

func _add_preview():
	if loading: return
	if exhibits.find_children("*", "Node3D", true, false).filter(func(n): return n.has_meta("source")).size() >= LIMIT: say("Limit 12 zestawów. Zachowaj układ przed zmianą."); return
	checkpoint(); _request_model(filtered[cursor], "exhibit")

func _finish_load():
	if ResourceLoader.load_threaded_get_status(pending_path) == ResourceLoader.THREAD_LOAD_FAILED:
		loading = false; say("Błąd modelu " + pending_meta.scan); return
	if ResourceLoader.load_threaded_get_status(pending_path) != ResourceLoader.THREAD_LOAD_LOADED: return
	var scene: PackedScene = ResourceLoader.load_threaded_get(pending_path)
	loading = false
	if pending_target == "preview":
		for n in preview.get_children(): preview.remove_child(n); n.queue_free()
		var object := scene.instantiate(); preview.add_child(object)
		_normalize(object, 0.95); object.position += Vector3(0, 1.1, -2.1)
	else:
		var root := _new_exhibit(pending_meta, scene)
		root.position = Vector3(0, 1.0, -1.35); selected = root; save_workspace()
	say_loaded()

func say_loaded():
	say("Gotowe · f" + pending_meta.folio + " · bryła robocza; głębokość interpretowana")

func _new_exhibit(meta: Dictionary, scene: PackedScene) -> Node3D:
	var root := Node3D.new(); exhibits.add_child(root); counter += 1
	root.name = "exhibit_%d" % counter; root.set_meta("source", meta); root.set_meta("kind", "model")
	var shape := scene.instantiate(); root.add_child(shape); shape.name = "Geometry"; _normalize(shape, 0.9)
	_add_colliders(shape, root)
	return root

func _bounds(root: Node3D) -> AABB:
	var found := false; var result := AABB()
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var a: AABB = root.global_transform.affine_inverse() * n.global_transform * n.get_aabb()
		result = result.merge(a) if found else a; found = true
	return result

func _normalize(root: Node3D, height: float):
	var a := _bounds(root); var factor := height / maxf(a.size[a.size.max_axis_index()], 0.01)
	root.scale *= factor
	root.position -= Vector3(a.get_center().x, a.position.y, a.get_center().z) * factor

func _add_colliders(node: Node3D, root: Node3D):
	for m in node.find_children("*", "MeshInstance3D", true, false):
		if not m.mesh: continue
		var b := StaticBody3D.new(); b.collision_layer = 1; b.collision_mask = 0; b.set_meta("piece", m); b.set_meta("exhibit", root); m.add_child(b)
		var c := CollisionShape3D.new(); var s := BoxShape3D.new(); var a: AABB = m.get_aabb(); s.size = a.size.max(Vector3(0.008,0.008,0.008)); c.shape = s; c.position = a.get_center(); b.add_child(c)

func _add_page():
	if exhibits.find_children("*", "Node3D", true, false).filter(func(n): return n.has_meta("source")).size() >= LIMIT: say("Limit 12 zestawów"); return
	checkpoint(); var root := _make_page(pages[page_cursor]); root.position = Vector3(0, 1.4, -1.3); selected = root; save_workspace()

func _make_page(p: Dictionary) -> Node3D:
	var root := Node3D.new(); exhibits.add_child(root); counter += 1; root.name = "page_%d" % counter
	root.set_meta("source", {"scan":p.id, "folio":p.label, "category":p.category}); root.set_meta("kind", "page")
	var width: float = 0.68 * float(p.width) / float(p.height)
	box(root, Vector3.ZERO, Vector3(width,0.68,0.004), Color("d8c9a5"))
	var mesh := MeshInstance3D.new(); var plane := QuadMesh.new(); plane.size = Vector2(width,0.68); mesh.mesh = plane; mesh.position.z = 0.0022; root.add_child(mesh)
	var mat := material(Color.WHITE, true); mat.albedo_texture = load("res://assets/scans/"+p.id+".jpg"); mesh.material_override = mat
	_add_colliders(root, root); return root

func _add_book():
	if not ResourceLoader.exists("res://assets/room/codex.glb"): say("Model kodeksu jeszcze niedostępny"); return
	if exhibits.find_children("*", "Node3D", true, false).filter(func(n): return n.has_meta("source")).size() >= LIMIT: return
	checkpoint(); var meta := {"scan":"codex", "folio":"kodeks · 206 skanów", "category":"Kodeks", "model":"res://assets/room/codex.glb"}
	var root := _new_exhibit(meta, load(meta.model)); root.position = Vector3(0, 1.3, -1.3); selected = root; save_workspace()

func _process(dt: float):
	if loading: _finish_load()
	elapsed_save += dt
	if elapsed_save > 20: elapsed_save = 0; save_workspace()
	if recording:
		record_time += dt
		if record_time > 120: toggle_recording()
	for i in range(2):
		if hands[i] and (not controllers[i].get_is_active()): _release(i)
	_update_hover()
	if xr and xr.is_initialized():
		var joy := controllers[0].get_vector2("primary")
		if joy.length() > 0.2 and not hands[0]:
			var forward := -camera.global_basis.z; forward.y = 0; forward = forward.normalized()
			origin.position += (camera.global_basis.x * joy.x + forward * joy.y) * dt * 1.1
		var turn := controllers[1].get_vector2("primary")
		if absf(turn.x) < 0.2: turn_lock = false
		if absf(turn.x) > 0.65 and not turn_lock and not hands[1]:
			var pivot := camera.global_position; origin.global_position -= pivot; origin.rotate_y(-signf(turn.x) * PI/6); origin.global_position = pivot + origin.global_position.rotated(Vector3.UP, -signf(turn.x) * PI/6); turn_lock = true
		if drawing and stroke_node and controllers[1].is_button_pressed("trigger_click"):
			_append_stroke(controllers[1].global_position - controllers[1].global_basis.z * 0.2)

func _update_hover():
	hover_label.visible = false
	for i in range(2):
		if rays[i].is_colliding():
			var b = rays[i].get_collider()
			if b and b.has_meta("exhibit"):
				var root: Node3D = b.get_meta("exhibit"); var source: Dictionary = root.get_meta("source")
				hover_label.text = "f" + _folio_label(b) + (" · część" if pieces_mode else " · cały model")
				hover_label.global_position = rays[i].get_collision_point() + Vector3(0, 0.16, 0); hover_label.visible = true; return

func _folio_label(body) -> String:
	var root: Node3D = body.get_meta("exhibit")
	var source: Dictionary = root.get_meta("source")
	var piece: Node3D = body.get_meta("piece")
	if source.scan == "codex":
		for p in pages:
			if str(piece.name).contains(p.id): return p.label
	return source.folio

func _button(action: String, hand: int):
	if action == "by_button" or action == "menu_button": menu.visible = not menu.visible; if_menu_visible(); return
	if action == "ax_button": rotate_selection(Vector3.UP, PI); return
	if action == "trigger_click":
		if drawing and hand == 1:
			_begin_stroke(); return
		if rays[hand].is_colliding(): _select_body(rays[hand].get_collider())
	if action == "grip_click" and rays[hand].is_colliding():
		var body = rays[hand].get_collider()
		if body and body.has_meta("exhibit"):
			selected = body.get_meta("piece") if pieces_mode and body.get_meta("exhibit").get_meta("kind") != "page" else body.get_meta("exhibit")
			_grab(selected, hand)

func _select_body(body):
	if body.has_meta("action"): body.get_meta("action").call_deferred(); return
	if body.has_meta("exhibit"):
		selected = body.get_meta("piece") if pieces_mode and body.get_meta("exhibit").get_meta("kind") != "page" else body.get_meta("exhibit")
		var src: Dictionary = body.get_meta("exhibit").get_meta("source")
		if src.scan != "codex": _show_scan(src.scan)
		say("Wybrano f" + src.folio + (" · fragment" if pieces_mode else " · zestaw"))

func _grab(node: Node3D, hand: int):
	for h in range(2):
		if hands[h] and (hands[h].node == node or hands[h].node.is_ancestor_of(node) or node.is_ancestor_of(hands[h].node)): return
	checkpoint(); hands[hand] = {"node":node, "parent":node.get_parent()}; node.reparent(controllers[hand], true)

func _release_button(action: String, hand: int):
	if action == "grip_click": _release(hand)
	if action == "trigger_click" and hand == 1: _end_stroke()

func _release(hand: int):
	if not hands[hand]: return
	var info: Dictionary = hands[hand]; hands[hand] = null
	if is_instance_valid(info.node) and is_instance_valid(info.parent): info.node.reparent(info.parent, true)
	save_workspace()

func _release_all():
	for i in range(2): _release(i)

func rotate_selection(axis: Vector3, radians: float):
	if not is_instance_valid(selected): say("Najpierw wybierz model spustem"); return
	checkpoint(); selected.rotate_object_local(axis, radians); save_workspace()

func scale_selection(factor: float):
	if not is_instance_valid(selected): return
	var current := selected.global_basis.get_scale().length()
	if current * factor < 0.01 or current * factor > 20: return
	checkpoint(); selected.scale *= factor; save_workspace()

func detach_selected():
	if not is_instance_valid(selected) or selected.get_parent() == exhibits: say("Włącz Części i wybierz fragment"); return
	if exhibits.find_children("*", "Node3D", true, false).filter(func(n): return n.has_meta("source")).size() >= LIMIT: return
	_release_all(); checkpoint(); var source := _source_for(selected)
	var root := Node3D.new(); exhibits.add_child(root); counter += 1; root.name = "fragment_%d" % counter
	root.set_meta("source", source); root.set_meta("kind", "fragment"); root.set_meta("original_path", str(_root_for(selected).get_path_to(selected)))
	root.global_transform = selected.global_transform; selected.reparent(root, true)
	for b in selected.find_children("*", "StaticBody3D", true, false): b.set_meta("exhibit", root)
	selected = root; save_workspace(); say("Fragment oddzielony. Możesz ułożyć go dowolnie.")

func _root_for(node: Node3D) -> Node3D:
	var n := node
	while n and not n.has_meta("source"): n = n.get_parent()
	return n

func _source_for(node: Node3D) -> Dictionary:
	var root := _root_for(node); return root.get_meta("source") if root else {}

func pin_selection():
	if is_instance_valid(selected): pinned = selected; say("Baza wybrana. Wybierz inny element i Połącz z bazą.")

func join_selected():
	_release_all()
	if not is_instance_valid(selected) or not is_instance_valid(pinned) or selected == pinned: return
	if selected.is_ancestor_of(pinned) or pinned.is_ancestor_of(selected): return
	checkpoint(); selected.reparent(pinned, true); save_workspace(); say("Połączono w Twoim układzie; pozycje zachowane.")

func if_menu_visible():
	if menu.visible: place_menu()

func place_menu():
	var direction := -camera.global_basis.z; direction.y = 0; direction = direction.normalized()
	menu.global_position = camera.global_position + direction * 1.25 - camera.global_basis.x * 0.65
	menu.look_at(Vector3(camera.global_position.x, menu.global_position.y, camera.global_position.z), Vector3.UP, true)

func toggle_passthrough():
	if not xr or not xr.is_initialized(): say("Otoczenie jest dostępne wyłącznie w goglach"); return
	if passthrough:
		xr.environment_blend_mode = XRInterface.XR_ENV_BLEND_MODE_OPAQUE; get_viewport().transparent_bg = false; passthrough = false
	elif xr.get_supported_environment_blend_modes().has(XRInterface.XR_ENV_BLEND_MODE_ALPHA_BLEND):
		xr.environment_blend_mode = XRInterface.XR_ENV_BLEND_MODE_ALPHA_BLEND; get_viewport().transparent_bg = true; passthrough = true
		environment.background_mode = Environment.BG_CLEAR_COLOR
	else: say("Ten runtime nie udostępnia trybu otoczenia"); return
	if not passthrough:
		environment.background_mode = Environment.BG_COLOR
	room.visible = not passthrough

func open_atlas():
	save_workspace(); OS.shell_open("https://voynich-herbarium-3d.songoku222.chatgpt.site")

func _encode_transform(t: Transform3D) -> Array:
	return [t.basis.x.x,t.basis.x.y,t.basis.x.z,t.basis.y.x,t.basis.y.y,t.basis.y.z,t.basis.z.x,t.basis.z.y,t.basis.z.z,t.origin.x,t.origin.y,t.origin.z]

func _decode_transform(a: Array) -> Transform3D:
	if a.size() != 12: return Transform3D.IDENTITY
	for v in a:
		if not (v is float or v is int) or not is_finite(float(v)): return Transform3D.IDENTITY
	return Transform3D(Basis(Vector3(a[0],a[1],a[2]),Vector3(a[3],a[4],a[5]),Vector3(a[6],a[7],a[8])),Vector3(a[9],a[10],a[11]))

func workspace_data() -> Dictionary:
	var data: Array = []
	for root in exhibits.find_children("*", "Node3D", true, false):
		if not root.has_meta("source"): continue
		var parts: Dictionary = {}
		for part in root.find_children("*", "MeshInstance3D", true, false):
			if _root_for(part) == root: parts[str(root.get_path_to(part))] = _encode_transform(part.global_transform)
		data.append({"name":str(root.name),"source":root.get_meta("source"),"kind":root.get_meta("kind"),"transform":_encode_transform(root.global_transform),"parts":parts,"original_path":root.get_meta("original_path", ""),"parent":str(exhibits.get_path_to(root.get_parent()))})
	return {"version":1,"room":room_index,"models":data,"strokes":all_strokes,"saved_at":Time.get_datetime_string_from_system(true)}

func _atomic_json(path: String, data: Dictionary) -> bool:
	var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
	if not file: say("Nie udało się zapisać pliku"); return false
	file.store_string(JSON.stringify(data, "\t")); file.flush(); var error := file.get_error(); file.close()
	if error != OK: return false
	if FileAccess.file_exists(path): DirAccess.copy_absolute(path, path + ".bak")
	return DirAccess.rename_absolute(path + ".tmp", path) == OK

func save_workspace():
	if hands[0] or hands[1]: return
	_atomic_json(SAVE, workspace_data())

func checkpoint():
	if hands[0] or hands[1]: return
	undo_stack.append(workspace_data()); if undo_stack.size() > 12: undo_stack.pop_front()

func undo():
	_release_all()
	if not undo_stack.is_empty(): restore_workspace(undo_stack.pop_back()); save_workspace(); say("Cofnięto ostatnią zmianę")

func restore_workspace(data):
	if not data is Dictionary or data.get("version") != 1: return
	selected = null; pinned = null
	for n in exhibits.get_children(): exhibits.remove_child(n); n.queue_free()
	var entries: Array = data.get("models", []); var restored: Dictionary = {}
	for item in entries.slice(0, LIMIT):
		if not item is Dictionary: continue
		var source: Dictionary = item.get("source", {}); var scan: String = source.get("scan", "")
		var root: Node3D
		if item.get("kind") == "page":
			var matches := pages.filter(func(p): return p.id == scan)
			if matches.is_empty(): continue
			root = _make_page(matches[0])
		else:
			var matches := catalog.filter(func(m): return m.scan == scan)
			var meta: Dictionary
			if scan == "codex": meta = {"scan":"codex","folio":"kodeks · 206 skanów","category":"Kodeks","model":"res://assets/room/codex.glb"}
			elif not matches.is_empty(): meta = matches[0]
			else: continue
			if not ResourceLoader.exists(meta.model): continue
			root = _new_exhibit(meta, load(meta.model))
			if item.get("kind") == "fragment":
				var part = root.get_node_or_null(item.get("original_path", ""))
				if part:
					part.reparent(root, true)
					for child in root.get_children():
						if child != part: root.remove_child(child); child.queue_free()
					root.set_meta("kind", "fragment"); root.set_meta("original_path", item.original_path)
		root.name = item.get("name", str(root.name)); root.global_transform = _decode_transform(item.get("transform", []))
		restored[str(root.name)] = root
		var parts: Dictionary = item.get("parts", {})
		for mesh in root.find_children("*", "MeshInstance3D", true, false):
			var key := str(root.get_path_to(mesh))
			if parts.has(key): mesh.global_transform = _decode_transform(parts[key])
			elif item.get("kind") == "model": mesh.visible = false; for b in mesh.find_children("*", "StaticBody3D", true, false): b.collision_layer = 0
	# Restore freeform connections after all independent sources have been reconstructed.
	for item in entries:
		var root: Node3D = restored.get(item.get("name", ""))
		if root and item.get("parent", ".") != ".":
			var parent = exhibits.get_node_or_null(item.parent)
			if parent and parent != root and not root.is_ancestor_of(parent): root.reparent(parent, true)
	room_index = clampi(int(data.get("room", 0)), 0, room_names.size()-1); _build_room()
	all_strokes = data.get("strokes", []); _restore_strokes()

func _setup_notebook():
	DirAccess.make_dir_recursive_absolute("user://notes")
	AudioServer.add_bus(); var bus := AudioServer.bus_count - 1; AudioServer.set_bus_name(bus, "NotebookMic")
	record_effect = AudioEffectRecord.new(); record_effect.format = AudioStreamWAV.FORMAT_16_BITS; AudioServer.add_bus_effect(bus, record_effect)
	AudioServer.set_bus_mute(bus, true)
	microphone = AudioStreamPlayer.new(); microphone.stream = AudioStreamMicrophone.new(); microphone.bus = "NotebookMic"; add_child(microphone)
	note_view = SubViewport.new(); note_view.size = Vector2i(1280, 960); note_view.world_3d = get_world_3d(); note_view.render_target_update_mode = SubViewport.UPDATE_DISABLED; add_child(note_view)
	note_camera = Camera3D.new(); note_camera.near = 0.04; note_camera.far = 80; note_camera.fov = 75; note_view.add_child(note_camera)

func take_note():
	if note_busy: return
	if recording: say("Nagrywanie trwa. Zakończ głos, aby zamknąć notatkę."); return
	await _capture_note()
	say("Zdjęcie widoku i opis sceny zapisane lokalnie")

func _capture_note():
	note_busy = true
	note_dir = "user://notes/%s_%d" % [Time.get_datetime_string_from_system(true).replace(":", "-"),Time.get_ticks_msec()]
	DirAccess.make_dir_recursive_absolute(note_dir)
	var metadata := {"created_at":Time.get_datetime_string_from_system(true),"source":_source_for(selected) if is_instance_valid(selected) else {},"head_pose":_encode_transform(camera.global_transform),"workspace":workspace_data(),"audio":"","image":"view.png","status":"local","capture":"virtual_scene_monoscopic; passthrough cameras not captured","transcription_status":"not_configured"}
	_atomic_json(note_dir + "/note.json", metadata)
	note_camera.global_transform = camera.global_transform
	menu.visible = false; hover_label.visible = false; note_view.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	var image := note_view.get_texture().get_image()
	if image: image.save_png(note_dir + "/view.png")
	menu.visible = true
	note_busy = false

func toggle_recording():
	if note_busy: return
	if recording:
		record_effect.set_recording_active(false); var wav := record_effect.get_recording(); microphone.stop(); recording = false
		if wav: wav.save_to_wav(note_dir + "/voice.wav")
		var meta = JSON.parse_string(FileAccess.get_file_as_string(note_dir + "/note.json")); meta.audio = "voice.wav"; meta.duration = record_time; meta.status = "local_recorded"; _atomic_json(note_dir + "/note.json", meta)
		say("Zapisano głos, zdjęcie i układ. Transkrypcja AI jeszcze niepołączona.")
	else:
		if OS.get_name() == "Android" and not OS.get_granted_permissions().has("android.permission.RECORD_AUDIO"):
			OS.request_permission("android.permission.RECORD_AUDIO"); say("Zezwól na mikrofon, następnie ponownie wybierz Zdjęcie + głos"); return
		await _capture_note(); microphone.play(); record_time = 0; record_effect.set_recording_active(true); recording = true; say("Nagrywam głos · do 2 min · zakończ tym samym przyciskiem")
	_refresh_menu()

func _begin_stroke():
	stroke = []; drawing_anchor = selected if is_instance_valid(selected) else exhibits
	stroke_node = MeshInstance3D.new(); drawing_anchor.add_child(stroke_node); stroke_node.material_override = material(Color("ffc45b"), true)
	_append_stroke(controllers[1].global_position - controllers[1].global_basis.z * 0.2)

func _append_stroke(world: Vector3):
	var p := drawing_anchor.to_local(world)
	if stroke.size() > 2000 or (not stroke.is_empty() and p.distance_to(stroke.back()) < 0.003): return
	stroke.append(p); _draw_stroke(stroke_node, stroke)

func _draw_stroke(node: MeshInstance3D, points: Array):
	if points.size() < 2: return
	var mesh := ImmediateMesh.new(); mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
	for p in points: mesh.surface_add_vertex(p)
	mesh.surface_end(); node.mesh = mesh

func _end_stroke():
	if not stroke_node: return
	var points: Array = []
	for p in stroke: points.append([p.x,p.y,p.z])
	all_strokes.append({"anchor":str(exhibits.get_path_to(drawing_anchor)),"points":points}); stroke_node = null; save_workspace()

func _restore_strokes():
	for s in all_strokes:
		var anchor = exhibits.get_node_or_null(s.get("anchor", "."))
		if not anchor: continue
		var node := MeshInstance3D.new(); anchor.add_child(node); node.material_override = material(Color("ffc45b"), true)
		var points: Array = []
		for p in s.points: points.append(Vector3(p[0],p[1],p[2]))
		_draw_stroke(node, points)

func _suspend():
	_release_all(); _end_stroke()
	if recording: toggle_recording()
	save_workspace()

func _notification(what):
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST:
		if is_instance_valid(exhibits): _suspend()

func _unhandled_input(event):
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var start := camera.project_ray_origin(event.position); var end := start + camera.project_ray_normal(event.position) * 20
		var query := PhysicsRayQueryParameters3D.create(start,end,3); var hit := get_world_3d().direct_space_state.intersect_ray(query)
		if hit: _select_body(hit.collider)
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE: _suspend(); get_tree().quit()
		if event.keycode == KEY_R: rotate_selection(Vector3.UP, PI)

func _smoke():
	await get_tree().process_frame
	print("SMOKE catalog=%d pages=%d controllers=%d actions=%s" % [catalog.size(),pages.size(),controllers.size(),ResourceLoader.exists("res://actions.tres")])
	for i in range(600):
		if not loading: break
		await get_tree().process_frame
	print("SMOKE preview=%d" % preview.get_child_count())
	get_tree().quit()

func _capture_test():
	for i in range(120):
		await get_tree().process_frame
		if not loading and i > 10: break
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://native-preview.png")
	print("RENDER_CAPTURE_SAVED")
	get_tree().quit()
