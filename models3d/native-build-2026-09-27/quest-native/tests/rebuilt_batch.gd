extends SceneTree
var failures: Array = []
var count := 0
var texture_checks := 0
func check(ok: bool, message: String):
	count += 1
	if not ok: failures.append(message); push_error(message)
func _initialize(): call_deferred("run")
func idle_load(app):
	for i in range(600):
		if not app.loading: return
		await process_frame
func run():
	var app = load("res://main.tscn").instantiate(); root.add_child(app)
	await process_frame; await idle_load(app)
	check(app.catalog.size() == 274, "274 total catalog records")
	var added: Array = app.catalog.filter(func(m): return m.get("rebuild_batch", "") == "F01")
	check(added.size() == 20, "20 new entries")
	for meta in added:
		check(ResourceLoader.exists(meta.model), "Model available " + meta.id)
		var packed = load(meta.model)
		check(packed is PackedScene, "Packed scene " + meta.id)
		if not packed: continue
		var model = packed.instantiate(); root.add_child(model)
		var meshes = model.find_children("*", "MeshInstance3D", true, false)
		check(not meshes.is_empty(), "Visible mesh " + meta.id)
		for mesh in meshes:
			for i in range(mesh.mesh.get_surface_count()):
				var mat = mesh.mesh.surface_get_material(i)
				check(mat is StandardMaterial3D and mat.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED, "Source material unlit " + meta.id)
				if mat is StandardMaterial3D and mat.albedo_texture:
					var actual: Image = mat.albedo_texture.get_image()
					var filename: String = mat.albedo_texture.resource_path.get_file()
					# Compare imported CPU texture against the exact original crop PNG used by the importer.
					var expected := Image.load_from_file("res://tests/rebuilt-textures/" + filename)
					check(expected != null and actual != null, "Readable texture " + meta.id)
					if expected and actual:
						actual.clear_mipmaps(); actual.convert(Image.FORMAT_RGBA8); expected.convert(Image.FORMAT_RGBA8)
						check(actual.get_size() == expected.get_size() and actual.get_data() == expected.get_data(), "Imported pixels unchanged " + meta.id)
						texture_checks += 1
		model.queue_free(); await process_frame
	app._show_rebuilt(); await idle_load(app)
	check(app.filtered.size() == 20 and not app.fidelity_mode, "New batch shortcut displays 20 models")
	check(app.preview.visible and app.preview.get_child_count() == 1, "Preview visible")
	app.restore_workspace({"version":1,"models":[],"strokes":[]})
	var meta: Dictionary = added[1]
	var exhibit = app._new_exhibit(meta, load(meta.model)); exhibit.position = Vector3(.4,1.2,-1.4)
	var start: Transform3D = exhibit.global_transform
	app._grab(exhibit,0); app._release(0)
	check(exhibit.global_transform.is_equal_approx(start), "Grab/release preserves pose")
	app.selected=exhibit; app.rotate_selection(Vector3.UP,PI); app.rotate_selection(Vector3.UP,PI)
	check(exhibit.global_transform.is_equal_approx(start), "360 degree rotation round trip")
	var data: Dictionary=app.workspace_data(); app.restore_workspace(data)
	check(app.exhibits.get_child_count()==1, "New model restores once")
	var restored=app.exhibits.get_child(0)
	check(restored.get_meta("source").id==meta.id, "Restore resolves exact fragment ID, not just shared scan")
	check(restored.global_transform.is_equal_approx(start), "Restored pose")
	app._show_all_models(); await idle_load(app)
	check(app.filtered.size()==274, "All-model shortcut")
	var report := JSON.stringify({"passed":failures.is_empty(),"checks":count,"texture_checks":texture_checks,"failures":failures,"headset_tested":false})
	FileAccess.open("res://tests/rebuilt-result.json", FileAccess.WRITE).store_string(report)
	print(report)
	app.queue_free(); await process_frame; quit(0 if failures.is_empty() else 1)
