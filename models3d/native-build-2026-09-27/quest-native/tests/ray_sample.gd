extends SceneTree
func _initialize():call_deferred("run")
func run():
	var app=load("res://main.tscn").instantiate();root.add_child(app);await process_frame
	var p=app.probe;p.load_source(app.pages[157]);while p.busy:await process_frame
	p.position=Vector3(1,1.8,-2);p.rotation.y=.36;p.set_sample(4200,1500);p.change_zoom(4)
	var x:=4210;var y:=1600;var uv:=Vector2((x-p.region.position.x+.5)/p.region.size.x,(y-p.region.position.y+.5)/p.region.size.y)
	var local:=Vector3((uv.x-.5)*p.panel.mesh.size.x,(.5-uv.y)*p.panel.mesh.size.y,0);p.sample_at(p.panel.to_global(local));assert(p.samples[0].x==x and p.samples[0].y==y)
	p.patch=11;p.set_sample(0,0);assert(p.samples[0].pixels_averaged==36)
	print("RAY_SAMPLE_PASS pixel=",x,",",y," clipped_patch=36");app.queue_free();await process_frame;quit()
