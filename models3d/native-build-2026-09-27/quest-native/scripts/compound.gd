extends Node3D
## All rooms share one physical coordinate system. Displays are paged by category.
const SPAWNS=[Vector3(0,0,0),Vector3(-11,0,-1),Vector3(21,0,0),Vector3(5,0,10),Vector3(21,0,10),Vector3(10,0,0)]
# x,z interior rectangles (doorway rectangles bridge their wall thickness).
const RECTS=[Rect2(-4.7,-5.7,9.4,9.4),Rect2(5.3,-5.7,9.4,9.4),Rect2(15.3,-5.7,11.4,9.4),Rect2(-4.7,4.3,31.4,3.4),Rect2(-4.7,8.3,19.4,19.4),Rect2(15.3,8.3,11.4,19.4),Rect2(-18.5,-5.5,13,33)]
const DOORS=[Rect2(-5.6,-2.2,.95,2.4),Rect2(4.65,-2.35,.7,2.4),Rect2(14.65,-2.35,.7,2.4),Rect2(-1.3,3.65,2.6,.7),Rect2(8.7,3.65,2.6,.7),Rect2(19.7,3.65,2.6,.7),Rect2(-5.6,4.7,.95,2.6),Rect2(3.7,7.65,2.6,.7),Rect2(19.7,7.65,2.6,.7),Rect2(14.65,10.7,.7,2.6),Rect2(-5.6,10.7,.95,2.6)]
var app
var displays:Node3D
var heroes:Node3D
var pool:Array=[]
var page:=0
var active_zone:=-1
var pending:Array=[]
var request:Dictionary={}
var timer:=0.0
var loading:=false
var legend:Label3D
func setup(owner_app):
	app=owner_app;name="BudynekGalerie"
	heroes=Node3D.new();add_child(heroes);displays=Node3D.new();add_child(displays)
	legend=app.label("",34);legend.billboard=BaseMaterial3D.BILLBOARD_ENABLED;legend.pixel_size=.003;add_child(legend)
	for info in [["relief_s0158",Vector3(-.2,.035,20)],["spatial_s0158",Vector3(9.3,.055,20)]]:
		var meta:Dictionary=app.catalog.filter(func(c):return c.get("id","")==info[0])[0]
		var m=load(meta.model).instantiate();heroes.add_child(m);m.scale=Vector3.ONE*(8.7/12);m.position=info[1];m.set_meta("hero",info[0]);_collider(m,meta)
		var l=app.label("f85v–86r · "+("RELIEF 2.5D" if info[0].begins_with("relief") else "3D · GŁĘBIA INTERPRETACYJNA"),42);l.position=info[1]+Vector3(0,1.0,-4.65);l.billboard=BaseMaterial3D.BILLBOARD_ENABLED;l.pixel_size=.0035;heroes.add_child(l)
	refresh_zone(app.room_index)
func walkable(p:Vector3)->bool:
	var pt:=Vector2(p.x,p.z);var inside:=false
	for r in RECTS+DOORS:
		if r.has_point(pt):inside=true;break
	if not inside:return false
	# Furniture and the tall relief are solids. The flat relief may be crossed.
	for r in [Rect2(-1.5,-2.9,3,1.8),Rect2(1.55,-2.65,2.9,1.9),Rect2(8.25,-2.1,3.5,1.9),Rect2(19.3,-1.85,3.4,1.7),Rect2(19.45,16.45,3.1,3.1)]:
		if r.has_point(pt):return false
	return true
func zone_at(p:Vector3)->int:
	if p.x < -5.3:return 1
	if p.z>8.15:return 3 if p.x<15 else 4
	if p.z<3.85:
		if p.x>15:return 2
		if p.x>5:return 5
		return 0
	return app.room_index
func _process(dt):
	timer+=dt
	if timer>.4 and not app.teleporting:
		timer=0;var zone:=zone_at(app.camera.global_position)
		if zone!=app.room_index:app.room_index=zone;app._position_workspace();app._refresh_menu()
		if zone!=active_zone:refresh_zone(zone)
		heroes.visible=app.camera.global_position.distance_to(Vector3(5,0,20))<28
	if loading:
		var state:=ResourceLoader.load_threaded_get_status(request.path)
		if state==ResourceLoader.THREAD_LOAD_LOADED:
			var packed=ResourceLoader.load_threaded_get(request.path);loading=false
			if request.zone==active_zone:_place_display(packed,request.meta,request.index)
		elif state==ResourceLoader.THREAD_LOAD_FAILED:loading=false
	elif not pending.is_empty():
		request=pending.pop_front();loading=ResourceLoader.load_threaded_request(request.path)==OK
func refresh_zone(zone:int):
	active_zone=zone;page=0;_set_pool();_queue_page()
func _set_pool():
	pool=app.catalog.filter(func(c):
		match active_zone:
			1:return c.category=="Rośliny"
			2:return c.category=="Sceny i postacie" or c.category.begins_with("Przepływy")
			3:return c.category.begins_with("Diagramy") or c.category.begins_with("Tekst i drobne") or c.category.begins_with("Uzupełnienia")
			4:return c.category=="Zodiak"
			5:return c.category=="Małe rośliny i naczynia"
		return false)
func change_page(delta:int):
	if pool.is_empty():return
	page=posmod(page+delta,ceili(float(pool.size())/6));_queue_page()
func _queue_page():
	pending.clear()
	for child in displays.get_children():displays.remove_child(child);child.queue_free()
	var count:=mini(6,pool.size()-page*6)
	for i in range(count):
		var meta:Dictionary=pool[page*6+i];pending.append({"meta":meta,"index":i,"zone":active_zone,"path":meta.get("display_model",meta.model)})
	legend.text="%s · wystawa %d/%d\nChwyt: kopia do swobodnej pracy"%[app.room_names[active_zone],page+1,maxi(1,ceili(float(pool.size())/6))]
	legend.position=SPAWNS[active_zone]+Vector3(0,2.45,-2.7)
	legend.visible=not pool.is_empty()
func _place_display(packed,meta:Dictionary,i:int):
	var object=packed.instantiate();displays.add_child(object)
	app._normalize(object,1.5 if active_zone==1 else (.63 if active_zone==5 else 1.15))
	var pos:=Vector3.ZERO
	match active_zone:
		1:pos=Vector3(-16 if i<3 else -7.4,.37,[3,10,18][i%3])
		2:pos=Vector3(16.1+(i%3)*4.5,.81,-4.6 if i<3 else 2.5)
		3:pos=Vector3(-3.3+(i%3)*6.1,.85,11.5 if i<3 else 26.2)
		4:
			var a:=TAU*i/8;pos=Vector3(21+4.35*cos(a),.91,18-6.5*sin(a))
		5:pos=Vector3(9.05+(i%3)*.95,.94,-1.6 if i<3 else -.8)
	object.position+=pos;_collider(object,meta)
	var caption=app.label("f"+meta.folio,25);caption.position=pos+Vector3(0,-.02,.7);caption.billboard=BaseMaterial3D.BILLBOARD_ENABLED;caption.pixel_size=.003;displays.add_child(caption)
func _collider(object:Node3D,meta:Dictionary):
	var bounds:=AABB();var first:=true
	for m in object.find_children("*","MeshInstance3D",true,false):
		var b:AABB=object.global_transform.affine_inverse()*m.global_transform*m.get_aabb()
		bounds=b if first else bounds.merge(b);first=false
	if first:return
	var b:=StaticBody3D.new();b.collision_layer=1;b.collision_mask=0;b.set_meta("gallery_source",meta);object.add_child(b)
	var c:=CollisionShape3D.new();var s:=BoxShape3D.new();s.size=bounds.size.max(Vector3(.01,.01,.01));c.shape=s;c.position=bounds.get_center();b.add_child(c)
