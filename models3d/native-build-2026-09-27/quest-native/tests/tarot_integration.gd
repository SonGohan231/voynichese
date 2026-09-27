extends SceneTree
var failures: Array=[]
func check(ok: bool,msg: String):
	if not ok:failures.append(msg);push_error(msg)
func _initialize():call_deferred("run")
func run():
	var app=load("res://main.tscn").instantiate();root.add_child(app)
	await process_frame
	if app.get_script()==null or not app.tarot:quit(1);return
	app.restore_workspace({"version":1,"models":[],"strokes":[]})
	var t=app.tarot
	check(t.cards.size()==78,"Full 78-card catalog")
	for c in t.cards:check(ResourceLoader.exists(c.model),"Actual card GLB exists: "+c.id)
	check(app.catalog.filter(func(c):return c.get("id", "").begins_with("vessel_")).size()==10,"Ten independent vessel models")
	check(app.gallery.get_child_count()>=24,"Populated source gallery")
	var ids=["00_fool","01_magician","02_high_priestess"]
	for id in ids:t._draw(id)
	check(t.ordered_ids()==ids,"Explicit deal order")
	check(t.complete(),"Three-card layout complete")
	check(app._source_for(t.drawn["00_fool"]).card_id=="00_fool","Visual notebook records selected tarot card context")
	var magician=t.drawn["01_magician"]
	t.selected_card=magician;t.reverse_selected();check(magician.get_meta("reversed"),"Reversal metadata")
	t.interpret();check(t.reading_pages[1].contains("odwrócona"),"Reading uses reversed card")
	check(t.reading_pages[1].contains(t.by_id["01_magician"].reversed),"Correct reversed meaning")
	# Actual world-space controller grab and drop into occupied slot.
	var fool=t.drawn["00_fool"];var original: Transform3D=fool.global_transform
	app._grab(fool,0);check(fool.global_transform.is_equal_approx(original),"Card pickup preserves world pose")
	fool.global_position=t.slot_position(2);app._release(0)
	check(t.ordered_ids()[2]=="00_fool","Drop changes reading order")
	check(t.drawn["02_high_priestess"].get_meta("slot")==-1,"Occupied slot evicts old card safely")
	check(not t.complete(),"Free card is excluded from reading")
	t.finish_grab(t.drawn["02_high_priestess"])
	t._place(t.drawn["02_high_priestess"],0,false);t.interpret()
	check(t.reading_pages[0].contains("Kapłanka"),"Text follows physical slot order")
	var snapshot: Dictionary=app.workspace_data();var order: Array=t.ordered_ids();var remaining: Array=t.deck.duplicate()
	app.restore_workspace(snapshot)
	check(t.ordered_ids()==order,"Card order survives restore")
	check(t.deck==remaining,"Remaining deck order survives restore")
	check(t.drawn["01_magician"].get_meta("reversed"),"Reversal survives restore")
	check(t.reading_pages[0].contains("Kapłanka"),"Restored reading matches layout")
	t.change_layout();check(t.count==5 and t.slots.size()==5,"Five-card layout")
	t._draw("03_empress");t._draw("04_emperor");t.interpret()
	check(t.reading_pages.size()==6,"Five positions plus sequence summary")
	check(t.reading_pages[5].contains("Kolejność"),"Ordered synthesis exists")
	app.switch_room(2);check(not t.visible,"Tarot hidden in other rooms")
	check(t.find_children("*","StaticBody3D",true,false).all(func(b):return b.collision_layer==0),"Hidden cards cannot intercept rays")
	app.switch_room(5);check(app.origin.position.x==10,"Pharmacy spawn in separate chamber")
	var vmeta=app.catalog.filter(func(c):return c.get("id", "")=="vessel_s0161_02")[0]
	var v=app._new_exhibit(vmeta,load(vmeta.model));v.position=Vector3(10,1,-1)
	var saved: Dictionary=app.workspace_data();app.restore_workspace(saved)
	check(app.exhibits.get_child_count()==1,"Vessel persists independently")
	check(app.exhibits.get_child(0).get_meta("source").id=="vessel_s0161_02","Repeated source folio restores exact vessel identity")
	print(JSON.stringify({"passed":failures.is_empty(),"failures":failures,"cards":78,"vessels":10,"scope":"real GLBs, grip/drop, slot collisions, sequence/reversal, persistence; no headset"}))
	app.queue_free();await process_frame;quit(0 if failures.is_empty() else 1)
