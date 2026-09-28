extends SceneTree
func _initialize(): call_deferred("run")
func settled(reader):
	while reader.worker or not reader.pending.is_empty(): await process_frame
func shot(app, position: Vector3, target: Vector3, path: String):
	app.origin.transform = Transform3D.IDENTITY
	app.camera.position = position; app.camera.look_at(target)
	for i in range(8): await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)
func run():
	var app = load("res://main.tscn").instantiate(); root.add_child(app)
	await process_frame
	app.menu.visible = false; app.heading.visible = false; app.status.visible = false
	app._show_scan("s0141"); await settled(app.reader)
	await shot(app, Vector3(0,2.10,-.60), Vector3(0,1.15,-2.12), "res://reader-book.png")
	await shot(app, Vector3(1.42,1.65,-.15), app.scan_panel.global_position, "res://reader-pool.png")
	app._show_scan("s0158"); await settled(app.reader)
	await shot(app, Vector3(1.42,1.65,-.15), app.scan_panel.global_position, "res://reader-foldout.png")
	var page = app._make_page(app.pages[140]); page.position = Vector3(0,1.5,0)
	await settled(app.reader)
	app.scan_panel.visible = false
	await shot(app, Vector3(.15,1.55,.85), Vector3(0,1.5,0), "res://reader-loose-page.png")
	print("READER_RENDERED_DESKTOP_NOT_HEADSET")
	app.queue_free(); await process_frame; quit()
