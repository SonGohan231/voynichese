extends SceneTree
func _initialize():call_deferred("run")
func shot(app,position: Vector3,target: Vector3,path: String):
	app.origin.transform=Transform3D.IDENTITY;app.camera.position=position;app.camera.look_at(target)
	for i in range(10):await process_frame
	await RenderingServer.frame_post_draw
	var image=root.get_texture().get_image();image.save_png(path)
func run():
	var app=load("res://main.tscn").instantiate();root.add_child(app)
	await process_frame
	app.restore_workspace({"version":1,"models":[],"strokes":[]})
	app.menu.visible=false;app.status.visible=false;app.heading.visible=false;app.scan_panel.visible=false;app.preview.visible=false
	app.tarot._draw("00_fool");app.tarot._draw("01_magician");app.tarot._draw("02_high_priestess");app.tarot.interpret()
	await shot(app,Vector3(3,1.85,-.2),Vector3(3,1.14,-1.85),"res://tarot-preview.png")
	await shot(app,Vector3(9.7,1.95,.7),Vector3(10,1.5,-4.5),"res://gallery-preview.png")
	app.camera.position=Vector3(3,1.65,.25);app.camera.look_at(Vector3(3,1.4,-1.7))
	app.menu.visible=true;app.place_menu();app.mode="Tarot";app._refresh_menu()
	await shot(app,Vector3(3,1.65,.25),Vector3(3,1.4,-1.7),"res://menu-preview.png")
	print("VISUAL_CAPTURE_OK");quit()
