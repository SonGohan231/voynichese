extends SceneTree
var failures: Array = []
var checks := 0
func check(condition: bool, message: String):
	checks += 1
	if not condition: failures.append(message); push_error(message)
func _initialize(): call_deferred("run")
func settled(reader):
	var deadline := Time.get_ticks_msec() + 20000
	while reader.worker or not reader.pending.is_empty():
		if Time.get_ticks_msec() > deadline: check(false, "Reader decode timed out"); return
		await process_frame
func run():
	var app = load("res://main.tscn").instantiate(); root.add_child(app)
	await process_frame
	var reader = app.reader
	check(app.fidelity_mode, "Source mode is the default")
	check(not app.preview.visible, "Unverified preview hidden in source mode")
	var body := StaticBody3D.new()
	body.set_meta("gallery_source", {"scan":"s0141", "folio":"78r"})
	app._select_body(body); body.free()
	check(app.page_cursor == 140 and reader.index == 140, "Gallery selection synchronizes reader cursor")
	app._choose_page(1)
	check(app.pages[app.page_cursor].id == "s0142", "Next page follows selected gallery source")
	app._show_scan("s0001")
	app._choose_page(-1)
	check(reader.index == 0, "Previous at first scan stays at first")
	# All scans navigable, no pair stepping or accidental skips.
	for i in range(1, app.pages.size()):
		app._choose_page(1)
		check(app.page_cursor == i and reader.index == i, "Sequential page %d" % i)
	app._choose_page(1)
	check(reader.index == 205, "Next at last scan stays at last")
	await settled(reader)
	check(not reader.leaves[1].visible, "Async load cannot resurrect blank last-page neighbor")
	check(not reader.select_scan("invalid") and reader.index == 205, "Invalid scan cannot change cursor")
	app._show_scan("s0158")
	await settled(reader)
	var p: Dictionary = app.pages[157]
	check(absf(app.scan_panel.mesh.size.x/app.scan_panel.mesh.size.y - float(p.width)/p.height) < .00001, "Foldout preserves source aspect")
	check(reader.leaves[0].material_override.albedo_texture == app.scan_panel.material_override.albedo_texture, "Book and wall share the same source texture")
	check(app.scan_panel.material_override.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED, "Source unaffected by colored room lighting")
	check(reader.cache.size() <= reader.CACHE_LIMIT, "Bounded texture cache")
	# A real source JPEG is decoded; no .ctex resource is used.
	var result: Dictionary = reader._decode(p)
	check(not result.has("error"), "Real original JPEG SHA and dimensions verified")
	var actual: Image = app.scan_panel.material_override.albedo_texture.get_image()
	check(actual.get_size() == result.image.get_size(), "Display dimensions match verified decode")
	for uv in [Vector2(.1,.1), Vector2(.5,.34), Vector2(.8,.66), Vector2(.5,.95)]:
		var pixel := Vector2i(uv * Vector2(actual.get_size() - Vector2i.ONE))
		check(actual.get_pixelv(pixel).is_equal_approx(result.image.get_pixelv(pixel)), "Source pixel preserved at %s" % str(pixel))
	var bad := p.duplicate(); bad.sha256 = "incorrect"
	check(reader._decode(bad).has("error"), "Reject mismatched source instead of showing wrong texture")
	var page = app._make_page(p)
	var face = page.get_node("SourceFace")
	check(face.position.z - .002 >= .0059, "At least 6 mm separation from page backing")
	var saved: Dictionary = app.workspace_data()
	app._show_scan("s0004")
	app.restore_workspace(saved)
	check(app.page_cursor == 157, "Reader scan survives workspace restore")
	app._toggle_fidelity()
	check(not app.fidelity_mode and app.preview.visible, "Hypothesis mode can be enabled explicitly")
	app._toggle_fidelity()
	check(app.fidelity_mode and not app.preview.visible, "Return to source mode")
	await settled(reader)
	print(JSON.stringify({"suite":"source_reader", "checks":checks, "passed":failures.is_empty(), "failures":failures, "headset_tested":false}))
	app.queue_free(); await process_frame; quit(0 if failures.is_empty() else 1)
