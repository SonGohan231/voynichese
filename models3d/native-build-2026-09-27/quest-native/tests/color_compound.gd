extends SceneTree
func _initialize():call_deferred("run")
func run():
	var math=load("res://scripts/color_math.gd");var cases=JSON.parse_string(FileAccess.get_file_as_string("res://tests/ciede2000.json"));var max_error:=0.0
	for pair in cases:
		var actual:float=math.delta_e(pair.a,pair.b);max_error=maxf(max_error,absf(actual-pair.expected));assert(absf(actual-pair.expected)<.000051,"CIEDE2000 mismatch")
	assert(absf(math.rgb_lab(Color.WHITE)[0]-100)<.00002);assert(math.delta_e([0,0,0],[0,0,0])==0)
	var app=load("res://main.tscn").instantiate();root.add_child(app);await process_frame
	assert(app.compound.walkable(Vector3(0,0,4)));assert(app.compound.walkable(Vector3(5,0,8)));assert(app.compound.walkable(Vector3(-5,0,-1)));assert(not app.compound.walkable(Vector3(0,0,8)))
	assert(app.compound.heroes.get_child_count()==4)
	var page:Dictionary=app.pages.filter(func(p):return p.id=="s0158")[0];app.probe.load_source(page)
	while app.probe.busy:await process_frame
	assert(app.probe.pixels.get_width()==7925);assert(app.probe.pixels.get_height()==7268)
	app.probe.set_sample(4500,1300);var color:Color=app.probe.pixels.get_pixel(4500,1300);var a:Dictionary=app.probe.samples[0]
	assert(a.rgb8==[roundi(color.r*255),roundi(color.g*255),roundi(color.b*255)])
	app.probe.target=1;app.probe.set_sample(4500,1300);assert(math.delta_e(a.lab,app.probe.samples[1].lab)==0)
	app.probe.change_zoom(4);assert(app.probe.region.has_point(Vector2i(4500,1300)))
	var previous:=a.duplicate(true);app.probe.load_source(app.pages[3]);while app.probe.busy:await process_frame
	assert(app.probe.samples[0]==previous);app.probe.set_sample(100,100);assert(app.probe.samples[1].scan=="s0004")
	app.probe.save_comparison();assert(FileAccess.file_exists("user://color_samples.json"))
	await app.switch_room(3);assert(app.room.get_child_count()==1);assert(app.room_index==3);assert(app.compound.walkable(app.camera.global_position))
	app.compound.change_page(1);assert(app.compound.page==1)
	print("COLOR_COMPOUND_PASS pairs=",cases.size()," max_error=",max_error," catalog=",app.catalog.size()," source_pixels=",page.width,"x",page.height)
	app.queue_free();await process_frame;quit()
