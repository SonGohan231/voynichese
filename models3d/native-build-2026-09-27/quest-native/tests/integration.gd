extends SceneTree
var failures: Array = []
func check(ok: bool, message: String):
	if not ok: failures.append(message); push_error(message)
func _initialize():
	call_deferred("run")
func run():
	var app = load("res://main.tscn").instantiate(); root.add_child(app)
	if app.get_script() == null: quit(1); return
	await process_frame
	for i in range(120):
		if not app.loading: break
		await process_frame
	check(app.catalog.size()==183, "All 183 models catalogued")
	check(app.pages.size()==206, "All 206 scans catalogued")
	check(app.preview.get_child_count()==1, "Real GLB preview loads")
	app.restore_workspace({"version":1,"models":[],"strokes":[]})
	var first = app._new_exhibit(app.catalog[0], load(app.catalog[0].model))
	first.transform = Transform3D(Basis.from_euler(Vector3(0.2,0.5,-0.1)),Vector3(1,1.2,-2))
	var original: Transform3D = first.global_transform
	app._grab(first,0); check(first.global_transform.is_equal_approx(original),"Grab preserves world pose")
	app.controllers[0].position = Vector3(0.4,0.1,0)
	var held: Transform3D = first.global_transform; app._release(0)
	check(first.global_transform.is_equal_approx(held),"Release preserves world pose")
	app.selected=first;app.rotate_selection(Vector3.UP,PI);app.rotate_selection(Vector3.UP,PI)
	check(first.global_transform.is_equal_approx(held),"Two 180 degree rotations preserve pose")
	var mesh = first.find_children("*","MeshInstance3D",true,false)[0]
	app.selected=mesh; app.detach_selected(); var detached: Node3D = app.selected
	check(detached.get_parent()==app.exhibits,"Independent fragment created")
	detached.position += Vector3(0.3,0.2,0.1)
	var part_pose: Transform3D = detached.global_transform
	var count_before: int = app.exhibits.find_children("*","MeshInstance3D",true,false).filter(func(n):return n.visible).size()
	var saved: Dictionary = app.workspace_data(); app.restore_workspace(saved)
	check(app.exhibits.get_child_count()==2,"Detached model and fragment restored")
	var restored_part = app.exhibits.get_children()[1]
	check(restored_part.global_transform.is_equal_approx(part_pose),"Fragment pose survives restart")
	var visible_after: int = app.exhibits.find_children("*","MeshInstance3D",true,false).filter(func(n):return n.visible).size()
	check(count_before==visible_after,"Restore does not duplicate detached geometry")
	app.selected=restored_part; app.pinned=app.exhibits.get_children()[0]; app.join_selected()
	check(restored_part.global_transform.is_equal_approx(part_pose),"Freeform join preserves pose")
	var joined: Dictionary = app.workspace_data(); app.restore_workspace(joined)
	check(app.exhibits.get_child_count()==1,"Freeform group survives restart")
	var copy: Dictionary = app.workspace_data()
	check(copy.models.size()==2,"Group retains both source records")
	check(app._decode_transform([1,2]).is_equal_approx(Transform3D.IDENTITY),"Reject malformed transforms")
	app.save_workspace()
	check(FileAccess.file_exists(app.SAVE),"Atomic workspace file exists")
	print(JSON.stringify({"passed":failures.is_empty(),"failures":failures,"catalog":app.catalog.size(),"scans":app.pages.size(),"tests":"actual Godot scenes, GLBs, transforms, split/join, restart persistence; no headset"}))
	app.queue_free(); await process_frame; quit(0 if failures.is_empty() else 1)
