extends Node3D
## Source scan reader. CPU-decodes the hash-verified JPEG, without lossy GPU import.
## Display downsampling is explicit; numeric samples remain in color_probe.gd.
const DISPLAY_LIMIT := 2048
const CACHE_LIMIT := 4
var app
var pages: Array = []
var index := 0
var panel: MeshInstance3D
var leaves: Array[MeshInstance3D] = []
var captions: Array[Label3D] = []
var panel_caption: Label3D
var bindings: Dictionary = {}
var cache: Dictionary = {}
var recent: Array[String] = []
var pending: Array[String] = []
var worker: Thread
var active_scan := ""
var errors: Dictionary = {}

static func fitted_size(width: float, height: float, maximum: Vector2) -> Vector2:
	var factor := minf(maximum.x / maxf(width, 1.0), maximum.y / maxf(height, 1.0))
	return Vector2(width, height) * factor

func setup(owner_app, target: MeshInstance3D, book: Node3D):
	app = owner_app
	pages = app.pages
	panel = target
	name = "CzytnikZrodel"
	panel_caption = app.label("", 19)
	panel_caption.position = Vector3(0, .62, .025)
	panel.add_child(panel_caption)
	controls(panel, Vector3(0, -.65, .025))
	# The old GLB held two static, shaded, distorted scans. Hide those surfaces.
	for old in book.find_children("PAGE_*", "MeshInstance3D", true, false):
		old.visible = false
		for body in old.find_children("*", "StaticBody3D", true, false): body.collision_layer = 0
	for side in range(2):
		var mesh := MeshInstance3D.new()
		mesh.name = "ReaderLeaf%d" % side
		mesh.mesh = QuadMesh.new()
		mesh.rotation.x = -PI / 2
		mesh.position = Vector3(-.285 if side == 0 else .285, .09, 0)
		book.add_child(mesh)
		leaves.append(mesh)
		var caption: Label3D = app.label("", 13)
		caption.rotation.x = -PI / 2
		caption.position = Vector3(mesh.position.x, .10, -.435)
		book.add_child(caption)
		captions.append(caption)
	var toolbar := Node3D.new()
	toolbar.position = Vector3(0, .12, .52)
	toolbar.rotation.x = -PI / 3
	book.add_child(toolbar)
	controls(toolbar, Vector3.ZERO)

func controls(parent: Node3D, offset: Vector3):
	var actions: Array = [["◀ Strona", func(): app._choose_page(-1)], ["Strona ▶", func(): app._choose_page(1)], ["Wyjmij skan", app._add_page], ["Lupa / RGB", func(): if not app.probe.visible: app.probe.toggle()]]
	for i in range(actions.size()):
		var body := StaticBody3D.new()
		body.collision_layer = 2
		body.collision_mask = 0
		body.position = offset + Vector3((i % 2 - .5) * .53, -floori(i / 2.0) * .15, 0)
		body.set_meta("action", actions[i][1])
		body.set_meta("reader_control", actions[i][0])
		parent.add_child(body)
		app.box(body, Vector3.ZERO, Vector3(.50, .13, .025), Color("183741"))
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(.50, .13, .035)
		collision.shape = shape
		body.add_child(collision)
		var caption: Label3D = app.label(actions[i][0], 20)
		caption.position.z = .023
		body.add_child(caption)

func select_scan(scan: String) -> bool:
	var found := -1
	for i in range(pages.size()):
		if pages[i].id == scan: found = i; break
	if found < 0: return false
	index = found
	app.page_cursor = index
	var meta: Dictionary = pages[index]
	panel_caption.text = "%s · %d/%d\nSkan źródłowy · lupa: szczegóły" % [meta.label, index + 1, pages.size()]
	bind_page(panel, meta, Vector2(1.4, 1.0))
	for side in range(leaves.size()):
		var at := index + side
		leaves[side].visible = at < pages.size()
		captions[side].visible = at < pages.size()
		if at >= pages.size(): leaves[side].set_meta("reader_scan", "")
		if at < pages.size():
			bind_page(leaves[side], pages[at], Vector2(.53, .73))
			captions[side].text = "%s · skan %d/%d" % [pages[at].label, at + 1, pages.size()]
	if app.probe and app.probe.visible: app.probe.load_source(meta)
	return true

func step(delta: int):
	if pages.is_empty(): return
	var old := index
	var target := clampi(index + delta, 0, pages.size() - 1)
	select_scan(pages[target].id)
	if target == old and (index == 0 or index == pages.size() - 1):
		app.say("%s · koniec zakresu skanów" % pages[index].label)

func bind_page(mesh: MeshInstance3D, meta: Dictionary, maximum: Vector2):
	var scan: String = meta.id
	mesh.set_meta("reader_scan", scan)
	mesh.set_meta("source_sha256", meta.sha256)
	mesh.mesh.size = fitted_size(float(meta.width), float(meta.height), maximum)
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color.WHITE
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	mesh.material_override = mat
	if not bindings.has(scan): bindings[scan] = []
	bindings[scan] = bindings[scan].filter(func(ref): return ref.get_ref() != null and ref.get_ref() != mesh)
	bindings[scan].append(weakref(mesh))
	if cache.has(scan):
		mat.albedo_texture = cache[scan]
		mesh.visible = true
		_touch(scan)
	else:
		# Never show the previous scan with the next scan's caption.
		mesh.visible = true
		if not pending.has(scan) and active_scan != scan: pending.append(scan)
		if errors.has(scan): errors.erase(scan)

func _touch(scan: String):
	recent.erase(scan)
	recent.append(scan)
	while recent.size() > CACHE_LIMIT: cache.erase(recent.pop_front())

func _decode(meta: Dictionary) -> Dictionary:
	var bytes := FileAccess.get_file_as_bytes("res://assets/source_pixels/%s.jpgbin" % meta.id)
	if bytes.is_empty(): return {"scan": meta.id, "error": "Brak pliku źródłowego"}
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(bytes)
	if hash.finish().hex_encode() != meta.sha256: return {"scan": meta.id, "error": "Niezgodny SHA-256 skanu"}
	var pixels := Image.new()
	if pixels.load_jpg_from_buffer(bytes) != OK: return {"scan": meta.id, "error": "Błąd odczytu JPEG"}
	if pixels.get_width() != int(meta.width) or pixels.get_height() != int(meta.height):
		return {"scan": meta.id, "error": "Niezgodne wymiary skanu"}
	var size := fitted_size(pixels.get_width(), pixels.get_height(), Vector2(DISPLAY_LIMIT, DISPLAY_LIMIT))
	if maxi(pixels.get_width(), pixels.get_height()) > DISPLAY_LIMIT:
		pixels.resize(maxi(1, roundi(size.x)), maxi(1, roundi(size.y)), Image.INTERPOLATE_LANCZOS)
	pixels.generate_mipmaps()
	return {"scan": meta.id, "image": pixels}

func _process(_dt):
	if worker and not worker.is_alive():
		var result: Dictionary = worker.wait_to_finish()
		worker = null
		active_scan = ""
		if result.has("error"):
			errors[result.scan] = result.error
			app.say("%s: %s" % [result.scan, result.error])
		else:
			var tex := ImageTexture.create_from_image(result.image)
			cache[result.scan] = tex
			_touch(result.scan)
			for ref in bindings.get(result.scan, []):
				var mesh = ref.get_ref()
				if mesh and mesh.get_meta("reader_scan", "") == result.scan:
					mesh.material_override.albedo_texture = tex
					mesh.visible = true
	if not worker and not pending.is_empty():
		# Superseded requests have no live targets; do not decode them while paging fast.
		pending = pending.filter(func(scan): return bindings.get(scan, []).any(func(ref): return ref.get_ref() != null and ref.get_ref().get_meta("reader_scan", "") == scan))
		if pending.is_empty(): return
		active_scan = pending.pop_front()
		var matches := pages.filter(func(p): return p.id == active_scan)
		if matches.is_empty(): active_scan = ""; return
		worker = Thread.new()
		worker.start(_decode.bind(matches[0]))

func _exit_tree():
	if worker: worker.wait_to_finish()
