extends SceneTree
func _initialize():call_deferred("run")
func shot(app,pos:Vector3,target:Vector3,path:String):
	app.origin.transform=Transform3D.IDENTITY;app.camera.position=pos;app.camera.look_at(target)
	for i in range(8):await process_frame
	await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(path)
func run():
	var app=load("res://main.tscn").instantiate();root.add_child(app);await process_frame
	app.restore_workspace({"version":1,"models":[],"strokes":[]});app.menu.visible=false;app.status.visible=false;app.heading.visible=false;app.scan_panel.visible=false;app.preview.visible=false
	await shot(app,Vector3(5,3.2,11),Vector3(4.8,.25,21),"res://diagrams03-preview.png")
	await shot(app,Vector3(9.3,1.9,17.3),Vector3(9.3,.38,20),"res://spatial03-preview.png")
	app.camera.position=Vector3(-11,1.8,-2);app.camera.look_at(Vector3(-11,1,14));app.compound.refresh_zone(1)
	for i in range(90):await process_frame
	await shot(app,Vector3(-11,1.8,-2),Vector3(-11,1,14),"res://garden03-preview.png")
	await shot(app,Vector3(1.4,1.7,5.8),Vector3(21,1.7,5.8),"res://corridor03-preview.png")
	app.camera.position=Vector3(0,1.65,1.7);app.camera.look_at(Vector3(0,1.65,-3));app.page_cursor=157;app.probe.toggle()
	while app.probe.busy:await process_frame
	app.probe.set_sample(4380,1100);app.probe.target=1;app.probe.set_sample(4410,1400);app.probe.change_zoom(4)
	app.menu.visible=true;app.mode="Kolory";app.place_menu();app._refresh_menu()
	await shot(app,Vector3(0,1.65,1.7),Vector3(0,1.6,-1),"res://colors03-preview.png")
	print("VISUAL03_PASS");quit()
